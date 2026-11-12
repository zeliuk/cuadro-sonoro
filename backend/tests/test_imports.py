import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import sqlite3
import json
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

os.environ['STATE_DB'] = str(Path(tempfile.mkdtemp()) / 'state.sqlite3')
from backend import main as m
from backend import importer as worker
from backend.identity import frame_key_for

IDENTIFIER_A = 'mi-cuadro-prueba'
IDENTIFIER_B = 'otro-cuadro-prueba'
KEY_A = frame_key_for(IDENTIFIER_A)
KEY_B = frame_key_for(IDENTIFIER_B)
AUTH = {'Authorization': f'Bearer {IDENTIFIER_A}'}
AUTH_B = {'Authorization': f'Bearer {IDENTIFIER_B}'}
client = TestClient(m.app)

@pytest.fixture(autouse=True)
def reset():
    if not m.store.cloud:
        m.store.conn.execute('DELETE FROM frame_states')
        m.store.conn.commit()


def test_missing_or_malformed_identifier_is_rejected_but_short_valid_id_works():
    assert client.get('/state').status_code == 401
    assert client.get('/state', headers={'Authorization': 'Bearer bad!id'}).status_code == 401
    assert client.get('/state', headers={'Authorization': 'Bearer ' + 'a' * 129}).status_code == 401
    assert client.get('/state', headers={'Authorization': 'Bearer mi-cuadro-prueba'}).json() == {'slots': {}, 'jobs': {}}
    assert client.post('/imports',headers=AUTH,json={'slot':0,'source_id':'BaW_jenozKc','title':'Test','artist':'Test'}).status_code == 503
    assert client.get('/health').json()['storage_configured'] is False


def test_first_identifier_read_creates_three_empty_slots_and_reuses_the_same_record():
    identifier = 'mi-cuadro-prueba'
    frame_key = frame_key_for(identifier)
    assert frame_key not in m.store.read_all()
    first = client.get('/state', headers={'Authorization': f'Bearer {identifier}'})
    assert first.status_code == 200
    assert first.json() == {'slots': {}, 'jobs': {}}
    assert m.store.read_all()[frame_key] == {'slots': {}, 'jobs': {}}

    m.store.mutate(frame_key, lambda state: state['slots'].update({
        'slot-0': {'id': 'existing', 'kind': 'station', 'title': 'Radio', 'url': 'https://example.org/radio'}
    }))
    second = client.get('/state', headers={'Authorization': f'Bearer {identifier}'})
    assert second.json()['slots']['slot-0']['id'] == 'existing'
    assert len([key for key in m.store.read_all() if key == frame_key]) == 1

    other = client.get('/state', headers={'Authorization': f'Bearer {IDENTIFIER_B}'})
    assert other.json() == {'slots': {}, 'jobs': {}}
    assert frame_key_for(IDENTIFIER_B) != frame_key
    assert client.get('/state', headers=AUTH).json()['slots']['slot-0']['title'] == 'Radio'


def test_cloud_ensure_transaction_persists_and_reuses_initial_state(monkeypatch):
    from backend import state as state_module
    from firebase_admin import db

    class Reference:
        value = None

        def transaction(self, update):
            self.value = update(self.value)
            return self.value

    reference = Reference()
    monkeypatch.setenv('FIREBASE_DATABASE_URL', 'https://example.invalid')
    monkeypatch.setattr(state_module, 'firebase', lambda: object())
    monkeypatch.setattr(db, 'reference', lambda *args, **kwargs: reference)
    cloud_store = state_module.StateStore()
    cloud_store.cloud = True
    cloud_store.ensure(KEY_A)
    reference.value['slots']['slot-0'] = {'id': 'published'}

    second = cloud_store.ensure(KEY_A)
    assert second == {'slots': {'slot-0': {'id': 'published'}}, 'jobs': {}}
    assert reference.value == second


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
    assert m.store.read(KEY_A)['jobs'][job_id]['status'] == 'cancelled'
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
        def uploaded(*args, **kwargs):
            state=m.store.read(KEY_A)
            assert state['jobs']['pipeline']['status']=='uploading'
            assert 'slot-1' not in state['slots']
            return f'private/frames/{KEY_A}/pipeline/audio.mp3',None
        upload.side_effect=uploaded
        worker.execute_import(KEY_A, job)
    state=m.store.read(KEY_A)
    assert state['jobs']['pipeline']['status']=='ready', state['jobs']['pipeline']
    assert state['slots']['slot-1']['audio_key'].startswith(f'private/frames/{KEY_A}/pipeline/')
    assert state['slots']['slot-1']['audio_key'].endswith('/audio.mp3')


def test_cancel_before_download_and_station_validation():
    job={'id':'cancel','slot':2,'source_id':'BaW_jenozKc','title':'Test','artist':'Test','status':'queued','created_at':0}
    m.store.mutate(KEY_A, lambda state: state['jobs'].update(cancel=job))
    m.store.mutate(KEY_A, lambda state: state['jobs']['cancel'].update(status='cancelled'))
    with patch('yt_dlp.YoutubeDL') as ydl:
        worker.execute_import(KEY_A, job)
        ydl.assert_not_called()
    assert m.store.read(KEY_A)['jobs']['cancel']['status']=='cancelled'
    assert client.post('/stations',headers=AUTH,json={'slot':0,'title':'Radio','url':'http://localhost/private'}).status_code==422
    assert client.post('/stations',headers=AUTH,json={'slot':0,'title':'Radio','url':'https://example.org/stream.mp3'}).status_code==200
    assert 'slot-0' in client.get('/state',headers=AUTH).json()['slots']


def test_radio_browser_search_normalizes_results_and_filters_unsafe_urls(monkeypatch):
    payload = [
        {'stationuuid':'radio-1','name':'Radio Uno','country':'España','url_resolved':'https://stream.example/radio','favicon':'https://img.example/logo.png','codec':'MP3','bitrate':128},
        {'stationuuid':'radio-2','name':'No segura','url_resolved':'http://127.0.0.1/admin'},
        {'stationuuid':'radio-3','name':'Sin URL','url_resolved':''},
    ]
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return json.dumps(payload).encode()
    captured = {}
    def open_request(request, timeout):
        captured['url'] = request.full_url
        captured['timeout'] = timeout
        captured['agent'] = request.get_header('User-agent')
        return Response()
    monkeypatch.setattr(m, 'urlopen', open_request)
    response = client.post('/stations/search', headers=AUTH, json={'name':'Radio Uno','country':'España'})
    assert response.status_code == 200
    assert response.json()['results'] == [{
        'stationuuid':'radio-1','name':'Radio Uno','country':'España','url':'https://stream.example/radio',
        'favicon':'https://img.example/logo.png','homepage':None,'codec':'MP3','bitrate':128,
    }]
    assert 'country=Espa%C3%B1a' in captured['url']
    assert captured['timeout'] == 12
    assert captured['agent'].startswith('CuadroSonoro/')


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


def test_media_api_returns_stable_public_storage_urls(monkeypatch):
    monkeypatch.setenv('FIREBASE_STORAGE_BUCKET', 'demo-sonoro.firebasestorage.app')
    media_key = f'private/frames/{KEY_A}/job%20id/audio.mp3'
    m.store.mutate(KEY_A, lambda state: state['slots'].update({
        'slot-0': {'id': 'song', 'kind': 'song', 'audio_key': media_key, 'image_key': None}
    }))

    response = client.get('/media/0', headers=AUTH)
    assert response.status_code == 200
    assert response.json()['audio_url'] == (
        'https://firebasestorage.googleapis.com/v0/b/demo-sonoro.firebasestorage.app/o/'
        + quote(media_key, safe='') + '?alt=media'
    )


def test_delete_slot_removes_selection_then_cleans_unreferenced_storage(monkeypatch):
    track = {
        'id': 'song', 'kind': 'song',
        'audio_key': f'private/frames/{KEY_A}/song/audio.mp3',
        'image_key': f'private/frames/{KEY_A}/song/cover.jpg',
    }
    m.store.mutate(KEY_A, lambda state: state['slots'].update({'slot-0': track}))
    observed = []

    def cleanup(frame_key, state):
        observed.append((frame_key, state))
        return {'deleted_objects': 2, 'cleanup_pending': False}

    monkeypatch.setattr(m, 'delete_orphaned_media', cleanup)
    response = client.delete('/slots/0', headers=AUTH)

    assert response.status_code == 200
    assert response.json() == {'ok': True, 'deleted_objects': 2, 'cleanup_pending': False}
    assert 'slot-0' not in observed[0][1]['slots']
    assert 'slot-0' not in m.store.read(KEY_A)['slots']


def test_storage_cleanup_preserves_published_and_active_import_objects():
    from backend.media import delete_orphaned_media

    prefix = f'private/frames/{KEY_A}/'

    class Blob:
        def __init__(self, name):
            self.name = name
            self.deleted = False

        def delete(self):
            self.deleted = True

    class Bucket:
        def __init__(self, blobs):
            self.blobs = blobs

        def list_blobs(self, prefix):
            assert prefix == self_prefix
            return self.blobs

    self_prefix = prefix
    referenced = Blob(prefix + 'published/audio.mp3')
    active = Blob(prefix + 'in-progress/audio.mp3')
    orphan = Blob(prefix + 'removed/cover.jpg')
    bucket = Bucket([referenced, active, orphan])
    state = {
        'slots': {'slot-0': {'audio_key': referenced.name}},
        'jobs': {'in-progress': {'status': 'uploading', 'slot': 1}},
    }

    assert delete_orphaned_media(KEY_A, state, bucket=bucket) == {
        'deleted_objects': 1, 'cleanup_pending': False
    }
    assert not referenced.deleted
    assert not active.deleted
    assert orphan.deleted


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
