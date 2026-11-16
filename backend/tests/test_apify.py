"""Apify integration tests use patched provider boundaries; no network or credentials."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ['STATE_DB'] = str(Path(tempfile.mkdtemp()) / 'apify-tests.sqlite3')
from backend import apify, importer, lifecycle, main
from backend.identity import frame_key_for

AUTH = {'Authorization': 'Bearer apify-isolated-test'}
KEY = frame_key_for('apify-isolated-test')
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset():
    if not main.store.cloud:
        main.store.conn.execute('DELETE FROM frame_states')
        main.store.conn.commit()


def test_search_success_empty_failure_and_missing_configuration(monkeypatch):
    monkeypatch.setenv('APIFY_TOKEN', 'fake-secret')
    monkeypatch.setattr(main.apify, 'search', lambda artist, title, maximum: [{'id':'BaW_jenozKc','title':'Song','artist':'Artist','duration':120,'image':'https://example.test/a.jpg'}])
    assert client.post('/search', headers=AUTH, json={'artist':'Artist','title':'Song'}).json()['results'][0]['id'] == 'BaW_jenozKc'
    monkeypatch.setattr(main.apify, 'search', lambda *args: [])
    assert client.post('/search', headers=AUTH, json={'artist':'Artist','title':'Missing'}).json() == {'results': []}
    monkeypatch.setattr(main.apify, 'search', lambda *args: (_ for _ in ()).throw(apify.ApifyError('provider failed')))
    assert client.post('/search', headers=AUTH, json={'artist':'Artist','title':'Bad'}).status_code == 502
    monkeypatch.setenv('APIFY_TOKEN', '')
    monkeypatch.setattr(main.apify, 'search', apify.search)
    assert client.post('/search', headers=AUTH, json={'artist':'Artist','title':'Bad'}).status_code == 503


def test_search_normalizes_schema_and_filters_invalid_live_and_long(monkeypatch):
    monkeypatch.setenv('APIFY_TOKEN', 'fake')
    monkeypatch.setattr(apify, 'create_run', lambda *args: {'id':'search-run'})
    monkeypatch.setattr(apify, 'wait_run', lambda *args: {'status':'SUCCEEDED','defaultDatasetId':'ds'})
    monkeypatch.setattr(apify, 'dataset_items', lambda *args: [
        {'id':'BaW_jenozKc','title':'Ok','channelName':'Channel','duration':'00:04:20','type':'video','thumbnailUrl':'https://img.test/a'},
        {'id':'bad','duration':'00:01:00','type':'video'},
        {'id':'aaaaaaaaaaa','duration':'00:20:00','type':'video'},
        {'id':'bbbbbbbbbbb','duration':'00:01:00','type':'shorts'},
    ])
    results = apify.search('Artist', 'Title', 900)
    assert results == [{'id':'BaW_jenozKc','title':'Ok','artist':'Channel','duration':260,'image':'https://img.test/a'}]


def test_search_global_cooldown_is_enforced_without_starting_an_actor(monkeypatch):
    monkeypatch.setenv('APIFY_TOKEN','fake')
    monkeypatch.setenv('APIFY_SEARCH_MIN_INTERVAL_SECONDS','100')
    apify._cache.clear()
    monkeypatch.setattr(apify,'_last_search',1e20)
    with pytest.raises(apify.ApifyRateLimit):
        apify.search('Artist','Title',900)


def seed_job(job_id='job', run_id=None):
    job = {'id':job_id,'slot':0,'source_id':'BaW_jenozKc','title':'Song','artist':'Artist','status':'queued','created_at':1}
    if run_id: job['apify_run_id'] = run_id
    main.store.mutate(KEY, lambda state: state['jobs'].update({job_id:job}))
    return job


def test_import_success_publishes_after_download_and_preserves_previous_until_commit(monkeypatch, tmp_path):
    monkeypatch.setenv('APIFY_TOKEN', 'fake')
    old = {'id':'old','kind':'station','title':'Previous','url':'https://stream.example/a'}
    main.store.mutate(KEY, lambda state: state['slots'].update({'slot-0':old}))
    job = seed_job()
    monkeypatch.setattr(importer.apify, 'create_run', lambda *args: {'id':'remote-1'})
    monkeypatch.setattr(importer.apify, 'wait_run', lambda run_id: {'id':run_id,'status':'SUCCEEDED'})
    monkeypatch.setattr(importer.apify, 'download_result', lambda run: {'videoId':'BaW_jenozKc','duration':30,'audioFileUrl':'https://audio.example/test.mp3','thumbnailFileUrl':None})
    monkeypatch.setattr(importer.apify, 'validate_public_url', lambda url: url)
    class Response:
        headers = {'Content-Length':'4'}
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def geturl(self): return 'https://audio.example/test.mp3'
        def read(self, n=-1):
            if not hasattr(self,'done'): self.done=True; return b'fake'
            return b''
    monkeypatch.setattr(importer.apify, 'open_media', lambda *args, **kwargs: Response())
    class Probe:
        stdout=json.dumps({'format':{'duration':'30','format_name':'mp3'}})
    monkeypatch.setattr(importer.subprocess, 'run', lambda *args, **kwargs: Probe())
    def persist(frame, job_id, audio, image, execution_id=None):
        assert main.store.read(KEY)['slots']['slot-0'] == old
        assert audio.stat().st_size == 4
        return ('private/audio.mp3', None)
    monkeypatch.setattr(importer, 'persist_media', persist)
    importer.execute_import(KEY, job)
    state = main.store.read(KEY)
    assert state['jobs']['job']['status'] == 'ready', state['jobs']['job']
    assert state['slots']['slot-0']['audio_key'] == 'private/audio.mp3'


@pytest.mark.parametrize('result,expected', [
    ({'videoId':'BaW_jenozKc','duration':20,'status':'failed','error':'denied','audioFileUrl':'https://audio.example/a.mp3'}, 'error'),
    ({'videoId':'BaW_jenozKc','duration':999,'status':'success','audioFileUrl':'https://audio.example/a.mp3'}, 'error'),
])
def test_failed_individual_result_and_duration_leave_previous_track(monkeypatch, result, expected):
    monkeypatch.setenv('APIFY_TOKEN','fake')
    previous={'id':'old','kind':'station','title':'Previous','url':'https://example.test/a'}
    main.store.mutate(KEY, lambda state: state['slots'].update({'slot-0':previous}))
    job=seed_job()
    monkeypatch.setattr(importer.apify, 'create_run', lambda *args: {'id':'run'})
    monkeypatch.setattr(importer.apify, 'wait_run', lambda *args: {'status':'SUCCEEDED'})
    monkeypatch.setattr(importer.apify, 'download_result', lambda *args: result if result.get('status') == 'failed' else (_ for _ in ()).throw(apify.ApifyError('too long')))
    monkeypatch.setattr(importer.apify, 'validate_public_url', lambda url: url)
    importer.execute_import(KEY, job)
    state=main.store.read(KEY)
    assert state['jobs']['job']['status']==expected
    assert state['slots']['slot-0']==previous


def test_resume_existing_apify_run_without_new_post(monkeypatch):
    job=seed_job(run_id='already-created')
    monkeypatch.setattr(importer.apify, 'wait_run', lambda run_id: {'id':run_id,'status':'FAILED'})
    monkeypatch.setattr(importer.apify, 'create_run', lambda *args: pytest.fail('must not create a second run'))
    importer.execute_import(KEY, job)
    assert main.store.read(KEY)['jobs']['job']['status']=='error'


def test_worker_timeout_requeues_existing_run_for_bounded_followup(monkeypatch):
    job=seed_job(run_id='continue-same-run')
    monkeypatch.setattr(importer.apify,'wait_run',lambda *args:(_ for _ in ()).throw(apify.ApifyError('Se alcanzó el tiempo máximo de seguimiento de Apify.')))
    monkeypatch.setattr(importer.apify,'create_run',lambda *args:pytest.fail('must not start another Actor'))
    importer.execute_import(KEY,job)
    current=main.store.read(KEY)['jobs']['job']
    assert current['status']=='queued'
    assert current['apify_run_id']=='continue-same-run'


@pytest.mark.parametrize('payload,probe,limit', [
    (b'larger', {'format':{'duration':'5','format_name':'mp3'}}, 2),
    (b'data', {'format':{'duration':'5','format_name':'mov,mp4,m4a'}}, 40*1024*1024),
    (b'data', {'format':{'duration':'901','format_name':'mp3'}}, 40*1024*1024),
])
def test_invalid_oversized_or_too_long_audio_is_not_published(monkeypatch, payload, probe, limit):
    monkeypatch.setenv('APIFY_TOKEN','fake')
    previous={'id':'previous','kind':'station','title':'Existing','url':'https://station.example/live'}
    main.store.mutate(KEY, lambda state: state['slots'].update({'slot-0':previous}))
    job=seed_job('validation-'+str(limit)+'-'+str(len(payload)))
    monkeypatch.setattr(importer,'MAX_BYTES',limit)
    monkeypatch.setattr(importer.apify,'create_run',lambda *args:{'id':'remote'})
    monkeypatch.setattr(importer.apify,'wait_run',lambda *args:{'status':'SUCCEEDED'})
    monkeypatch.setattr(importer.apify,'download_result',lambda *args:{'videoId':'BaW_jenozKc','duration':5,'audioFileUrl':'https://audio.example/file.mp3','thumbnailFileUrl':None})
    monkeypatch.setattr(importer.apify,'validate_public_url',lambda url:url)
    class Response:
        headers={}
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def geturl(self): return 'https://audio.example/file.mp3'
        def read(self,size=-1):
            if not hasattr(self,'done'): self.done=True; return payload
            return b''
    monkeypatch.setattr(importer.apify,'open_media',lambda *args,**kwargs:Response())
    monkeypatch.setattr(importer.subprocess,'run',lambda *args,**kwargs:type('Probe',(),{'stdout':json.dumps(probe)})())
    importer.execute_import(KEY,job)
    state=main.store.read(KEY)
    assert state['jobs'][job['id']]['status']=='error'
    assert state['slots']['slot-0']==previous


def test_interrupted_job_keeps_remote_id_and_ambiguous_create_does_not_retry(monkeypatch):
    job=seed_job(run_id='persisted-run')
    main.store.mutate(KEY, lambda state: state['jobs']['job'].update(status='downloading',execution_id='old-execution'))
    lifecycle.recover_interrupted_jobs()
    assert main.store.read(KEY)['jobs']['job']['apify_run_id']=='persisted-run'
    assert main.store.read(KEY)['jobs']['job']['status']=='queued'
    monkeypatch.setenv('APIFY_TOKEN','fake')
    no_run=seed_job('ambiguous')
    monkeypatch.setattr(importer.apify, 'create_run', lambda *args: (_ for _ in ()).throw(apify.ApifyError('ambiguous')))
    importer.execute_import(KEY, no_run)
    current=main.store.read(KEY)['jobs']['ambiguous']
    assert current['status']=='error' and current['apify_creation_ambiguous'] is True


def test_cancel_requests_remote_abort_and_keeps_retry_marker_on_temporary_failure(monkeypatch):
    job=seed_job('cancel-remote','remote-cancel-id')
    main.store.mutate(KEY,lambda state:state['jobs']['cancel-remote'].update(status='downloading',execution_id='execution'))
    monkeypatch.setattr(main.apify,'abort_run',lambda run_id: (_ for _ in ()).throw(apify.ApifyError('temporary')))
    response=client.post('/jobs/cancel-remote/cancel',headers=AUTH)
    assert response.status_code==200
    current=main.store.read(KEY)['jobs']['cancel-remote']
    assert current['status']=='cancelled' and current['apify_cancel_pending'] is True
    aborted=[]
    monkeypatch.setattr(main.apify,'abort_run',lambda run_id:aborted.append(run_id))
    lifecycle.retry_pending_apify_cancellations()
    assert aborted==['remote-cancel-id']
    assert main.store.read(KEY)['jobs']['cancel-remote']['apify_cancel_pending'] is False


def test_cancel_racing_with_run_creation_aborts_run_before_any_download(monkeypatch):
    monkeypatch.setenv('APIFY_TOKEN','fake')
    job=seed_job('cancel-race')
    aborted=[]
    def create(*args):
        main.store.mutate(KEY,lambda state:state['jobs']['cancel-race'].update(status='cancelled',execution_id=None))
        return {'id':'race-run'}
    monkeypatch.setattr(importer.apify,'create_run',create)
    monkeypatch.setattr(importer.apify,'abort_run',lambda run_id:aborted.append(run_id))
    monkeypatch.setattr(importer.apify,'wait_run',lambda *args:pytest.fail('cancelled run must not be followed'))
    importer.execute_import(KEY,job)
    current=main.store.read(KEY)['jobs']['cancel-race']
    assert current['status']=='cancelled'
    assert current['apify_run_id']=='race-run'
    assert current['apify_cancel_pending'] is False
    assert aborted==['race-run']


def test_download_url_rejects_non_public_and_import_rate_limit(monkeypatch):
    with pytest.raises(apify.ApifyError): apify.validate_public_url('http://127.0.0.1/private')
    monkeypatch.setenv('APIFY_TOKEN', '')
    assert client.post('/imports', headers=AUTH, json={'slot':0,'source_id':'BaW_jenozKc','title':'Song','artist':'Artist'}).status_code == 503


def test_apify_downloader_documented_success_casing_and_actor_path(monkeypatch):
    monkeypatch.setenv('APIFY_TOKEN','fake')
    monkeypatch.setattr(apify,'dataset_items',lambda dataset:[{'status':'Success','videoId':'BaW_jenozKc','audioFileUrl':'https://api.apify.com/file','thumbnailFileUrl':'https://api.apify.com/image'}])
    monkeypatch.setattr(apify,'validate_public_url',lambda url:url)
    assert apify.download_result({'status':'SUCCEEDED','defaultDatasetId':'dataset'})['audioFileUrl']=='https://api.apify.com/file'
    assert apify._actor_path('streamers/youtube-scraper')=='/acts/streamers~youtube-scraper'


def test_failed_dataset_item_reports_stage_without_logging_provider_error(monkeypatch, caplog):
    monkeypatch.setenv('APIFY_TOKEN','fake')
    monkeypatch.setattr(apify,'dataset_items',lambda dataset:[{'status':'Video is age restricted','error':'private provider detail','audioFileUrl':None}])
    with pytest.raises(apify.ApifyError, match='falló la descarga individual'):
        apify.download_result({'status':'SUCCEEDED','defaultDatasetId':'dataset'})
    assert 'status_success=False' in caplog.text
    assert 'error_present=True' in caplog.text
    assert 'private provider detail' not in caplog.text


def test_run_poll_retries_temporary_api_failure_with_bounded_backoff(monkeypatch):
    calls=[]
    def get_run(run_id):
        calls.append(run_id)
        if len(calls)==1: raise apify.ApifyError('temporary')
        return {'status':'SUCCEEDED'}
    monkeypatch.setattr(apify,'get_run',get_run)
    monkeypatch.setattr(apify.time,'sleep',lambda delay:None)
    assert apify.wait_run('same-run',max_seconds=5)['status']=='SUCCEEDED'
    assert calls==['same-run','same-run']
