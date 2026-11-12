import os
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch
import sqlite3
import json

import pytest
from fastapi.testclient import TestClient

os.environ['STATE_DB'] = str(Path(tempfile.mkdtemp()) / 'state.sqlite3')
from backend import main as m
from backend import importer as worker

TOKEN_A = 'frame-a-' + 'x' * 40
TOKEN_B = 'frame-b-' + 'y' * 40
KEY_A = hashlib.sha256(TOKEN_A.encode()).hexdigest()
KEY_B = hashlib.sha256(TOKEN_B.encode()).hexdigest()
os.environ['FRAME_TOKEN_HASHES'] = f'{KEY_A},{KEY_B}'
AUTH = {'Authorization': f'Bearer {TOKEN_A}'}
AUTH_B = {'Authorization': f'Bearer {TOKEN_B}'}
client = TestClient(m.app)

@pytest.fixture(autouse=True)
def reset():
    def empty(state):
        state['slots'] = {}
        state['jobs'] = {}
    m.store.mutate(KEY_A, empty)
    m.store.mutate(KEY_B, empty)
    m.cancelled.clear()


def test_auth_and_configuration_fail_closed():
    assert client.get('/state').status_code == 401
    assert client.get('/state', headers={'Authorization': 'Bearer short'}).status_code == 401
    assert client.get('/state', headers={'Authorization': 'Bearer ' + 'z' * 43}).status_code == 401
    assert client.post('/imports',headers=AUTH,json={'slot':0,'source_id':'BaW_jenozKc','title':'Test','artist':'Test'}).status_code == 503
    assert client.get('/health').json()['storage_configured'] is False


def test_local_token_is_not_accepted_in_a_firebase_deployment(monkeypatch):
    monkeypatch.setenv('LOCAL_FRAME_TOKEN', TOKEN_A)
    monkeypatch.setenv('FIREBASE_DATABASE_URL', 'https://database.example.invalid')
    monkeypatch.setenv('FIREBASE_STORAGE_BUCKET', 'test-bucket')
    monkeypatch.delenv('FRAME_TOKEN_HASHES', raising=False)
    assert KEY_A not in m.allowed_frame_keys()


def test_validate_id_slot_and_duplicate_jobs(monkeypatch):
    monkeypatch.setenv('FIREBASE_STORAGE_BUCKET','test-bucket')
    base={'slot':0,'source_id':'BaW_jenozKc','title':'Test','artist':'Test'}
    assert client.post('/imports',headers=AUTH,json={**base,'source_id':'https://internal/'}).status_code == 422
    assert client.post('/imports',headers=AUTH,json={**base,'slot':3}).status_code == 422
    first=client.post('/imports',headers=AUTH,json=base)
    assert first.status_code == 202
    second_slot={**base,'slot':1}
    assert client.post('/imports',headers=AUTH,json=second_slot).status_code == 409
    job_id=first.json()['id']
    assert client.post('/jobs/'+job_id+'/cancel',headers=AUTH).status_code == 200
    assert client.post('/imports',headers=AUTH,json=base).status_code == 202


def test_failing_import_preserves_old_track_and_never_marks_ready():
    old={'id':'old','kind':'station','title':'Existing','url':'https://example.com/audio'}
    job={'id':'test','slot':0,'source_id':'BaW_jenozKc','title':'Test','artist':'Test','status':'queued','created_at':0}
    def seed(state):
        state['slots']['slot-0']=old
        state['jobs']['test']=job
    m.store.mutate(KEY_A, seed)
    with patch('yt_dlp.YoutubeDL') as ydl:
        ydl.return_value.__enter__.return_value.extract_info.side_effect=RuntimeError('SECRET=do-not-expose')
        worker.execute_import(KEY_A, job)
    state=m.store.read(KEY_A)
    assert state['slots']['slot-0']==old
    assert state['jobs']['test']['status']=='error'
    assert 'SECRET' not in state['jobs']['test']['message']


def test_progress_pipeline_only_commits_after_upload():
    job={'id':'pipeline','slot':1,'source_id':'BaW_jenozKc','title':'Test','artist':'Test','status':'queued','created_at':0}
    m.store.mutate(KEY_A, lambda state: state['jobs'].update(pipeline=job))
    with patch('yt_dlp.YoutubeDL') as ydl, patch.object(worker,'persist_media') as upload:
        instance=ydl.return_value.__enter__.return_value
        instance.extract_info.return_value={'duration':30}
        def download(urls):
            options=ydl.call_args.args[0]
            audio=Path(options['outtmpl'].replace('%(ext)s','mp3'))
            audio.write_bytes(b'test-audio')
            options['progress_hooks'][0]({'status':'downloading','downloaded_bytes':5,'total_bytes':10})
            assert m.store.read(KEY_A)['jobs']['pipeline']['percent']==50
            options['progress_hooks'][0]({'status':'finished'})
        instance.download.side_effect=download
        def uploaded(*args):
            state=m.store.read(KEY_A)
            assert state['jobs']['pipeline']['status']=='uploading'
            assert 'slot-1' not in state['slots']
            return f'private/frames/{KEY_A}/pipeline/audio.mp3',None
        upload.side_effect=uploaded
        worker.execute_import(KEY_A, job)
    state=m.store.read(KEY_A)
    assert state['jobs']['pipeline']['status']=='ready'
    assert state['slots']['slot-1']['audio_key']==f'private/frames/{KEY_A}/pipeline/audio.mp3'


def test_cancel_before_download_and_station_validation():
    job={'id':'cancel','slot':2,'source_id':'BaW_jenozKc','title':'Test','artist':'Test','status':'queued','created_at':0}
    m.store.mutate(KEY_A, lambda state: state['jobs'].update(cancel=job))
    m.cancelled.add('cancel')
    with patch('yt_dlp.YoutubeDL') as ydl:
        worker.execute_import(KEY_A, job)
        ydl.assert_not_called()
    assert m.store.read(KEY_A)['jobs']['cancel']['status']=='cancelled'
    assert client.post('/stations',headers=AUTH,json={'slot':0,'title':'Radio','url':'http://localhost/private'}).status_code==422
    assert client.post('/stations',headers=AUTH,json={'slot':0,'title':'Radio','url':'https://example.org/stream.mp3'}).status_code==200
    assert 'slot-0' in client.get('/state',headers=AUTH).json()['slots']


def test_frames_cannot_read_cancel_or_change_each_others_data():
    active={'id':'job-a','slot':1,'source_id':'BaW_jenozKc','title':'Test','artist':'Test','status':'queued','created_at':0}
    def seed(state):
        state['slots']['slot-1']={'id':'owned-by-a','kind':'station','title':'Radio A','url':'https://example.org/a.mp3'}
        state['jobs']['job-a']=active
    m.store.mutate(KEY_A, seed)

    assert client.get('/state',headers=AUTH).json()['slots']['slot-1']['title']=='Radio A'
    assert client.get('/state',headers=AUTH_B).json()=={'slots':{},'jobs':{}}
    assert client.get('/media/1',headers=AUTH_B).status_code==404
    assert client.post('/jobs/job-a/cancel',headers=AUTH_B).status_code==404
    assert client.delete('/slots/1',headers=AUTH_B).status_code==200
    assert client.get('/media/1',headers=AUTH).status_code==200
    assert m.store.read(KEY_A)['jobs']['job-a']['status']=='queued'


def test_legacy_sqlite_collection_is_not_assigned_to_a_frame(tmp_path, monkeypatch):
    from backend.state import StateStore
    database=tmp_path/'legacy.sqlite3'
    connection=sqlite3.connect(database)
    connection.execute('CREATE TABLE state (id INTEGER PRIMARY KEY, data TEXT)')
    connection.execute('INSERT INTO state VALUES (1, ?)', (json.dumps({'slots':{'slot-0':{'title':'Legacy'}}}),))
    connection.commit()
    connection.close()
    monkeypatch.setenv('STATE_DB',str(database))

    migrated=StateStore()
    assert migrated.read(KEY_A)=={'slots':{},'jobs':{}}
    assert migrated.read_all()=={}
    migrated.conn.close()
