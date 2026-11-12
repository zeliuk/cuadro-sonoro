import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ['STATE_DB'] = str(Path(tempfile.mkdtemp()) / 'state.sqlite3')
os.environ['IMPORT_API_TOKEN'] = 'test-token-only'
from backend import main as m
from backend import importer as worker

AUTH = {'Authorization': 'Bearer test-token-only'}
client = TestClient(m.app)

@pytest.fixture(autouse=True)
def reset():
    def empty(state):
        state['slots'] = {}
        state['jobs'] = {}
    m.store.mutate(empty)
    m.cancelled.clear()


def test_auth_and_configuration_fail_closed():
    assert client.get('/state').status_code == 401
    assert client.post('/imports',headers=AUTH,json={'slot':0,'source_id':'BaW_jenozKc','title':'Test','artist':'Test'}).status_code == 503
    assert client.get('/health').json()['storage_configured'] is False


def test_validate_id_slot_and_duplicate_jobs(monkeypatch):
    monkeypatch.setenv('FIREBASE_STORAGE_BUCKET','test-bucket')
    base={'slot':0,'source_id':'BaW_jenozKc','title':'Test','artist':'Test'}
    assert client.post('/imports',headers=AUTH,json={**base,'source_id':'https://internal/'}).status_code == 422
    assert client.post('/imports',headers=AUTH,json={**base,'slot':3}).status_code == 422
    first=client.post('/imports',headers=AUTH,json=base)
    assert first.status_code == 202
    assert client.post('/imports',headers=AUTH,json=base).status_code == 409
    job_id=first.json()['id']
    assert client.post('/jobs/'+job_id+'/cancel',headers=AUTH).status_code == 200
    assert client.post('/imports',headers=AUTH,json=base).status_code == 202


def test_failing_import_preserves_old_track_and_never_marks_ready():
    old={'id':'old','kind':'station','title':'Existing','url':'https://example.com/audio'}
    job={'id':'test','slot':0,'source_id':'BaW_jenozKc','title':'Test','artist':'Test','status':'queued','created_at':0}
    def seed(state):
        state['slots']['slot-0']=old
        state['jobs']['test']=job
    m.store.mutate(seed)
    with patch('yt_dlp.YoutubeDL') as ydl:
        ydl.return_value.__enter__.return_value.extract_info.side_effect=RuntimeError('SECRET=do-not-expose')
        worker.execute_import(job)
    state=m.store.read()
    assert state['slots']['slot-0']==old
    assert state['jobs']['test']['status']=='error'
    assert 'SECRET' not in state['jobs']['test']['message']


def test_progress_pipeline_only_commits_after_upload():
    job={'id':'pipeline','slot':1,'source_id':'BaW_jenozKc','title':'Test','artist':'Test','status':'queued','created_at':0}
    m.store.mutate(lambda state: state['jobs'].update(pipeline=job))
    with patch('yt_dlp.YoutubeDL') as ydl, patch.object(worker,'persist_media') as upload:
        instance=ydl.return_value.__enter__.return_value
        instance.extract_info.return_value={'duration':30}
        def download(urls):
            options=ydl.call_args.args[0]
            audio=Path(options['outtmpl'].replace('%(ext)s','mp3'))
            audio.write_bytes(b'test-audio')
            options['progress_hooks'][0]({'status':'downloading','downloaded_bytes':5,'total_bytes':10})
            assert m.store.read()['jobs']['pipeline']['percent']==50
            options['progress_hooks'][0]({'status':'finished'})
        instance.download.side_effect=download
        def uploaded(*args):
            state=m.store.read()
            assert state['jobs']['pipeline']['status']=='uploading'
            assert 'slot-1' not in state['slots']
            return 'private/audio.mp3',None
        upload.side_effect=uploaded
        worker.execute_import(job)
    state=m.store.read()
    assert state['jobs']['pipeline']['status']=='ready'
    assert state['slots']['slot-1']['audio_key']=='private/audio.mp3'


def test_cancel_before_download_and_station_validation():
    job={'id':'cancel','slot':2,'source_id':'BaW_jenozKc','title':'Test','artist':'Test','status':'queued','created_at':0}
    m.store.mutate(lambda state: state['jobs'].update(cancel=job))
    m.cancelled.add('cancel')
    with patch('yt_dlp.YoutubeDL') as ydl:
        worker.execute_import(job)
        ydl.assert_not_called()
    assert m.store.read()['jobs']['cancel']['status']=='cancelled'
    assert client.post('/stations',headers=AUTH,json={'slot':0,'title':'Radio','url':'http://localhost/private'}).status_code==422
    assert client.post('/stations',headers=AUTH,json={'slot':0,'title':'Radio','url':'https://example.org/stream.mp3'}).status_code==200
    assert 'slot-0' in client.get('/state',headers=AUTH).json()['slots']
