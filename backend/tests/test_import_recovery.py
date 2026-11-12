import os
import subprocess
import sys
import asyncio

import pytest
from pathlib import Path
from unittest.mock import patch

from backend import lifecycle
from backend import importer
from backend.identity import frame_key_for
from backend.state import StateStore, patch_job, store

FRAME = frame_key_for('recovery-isolated-test')


@pytest.fixture(autouse=True)
def clean_frame():
    if not store.cloud:
        store.conn.execute('DELETE FROM frame_states WHERE frame_key=?', (FRAME,))
        store.conn.commit()
    yield


def seed(status='downloading', **extra):
    job = {
        'id': 'job-recovery', 'slot': 0, 'source_id': 'BaW_jenozKc', 'title': 'Prueba',
        'artist': 'Artista', 'status': status, 'created_at': 1, **extra,
    }
    store.mutate(FRAME, lambda state: state['jobs'].update({job['id']: job}))
    return job


@pytest.mark.parametrize('stage', ['downloading', 'processing', 'uploading'])
def test_interrupted_stage_is_queued_for_fresh_execution(stage):
    seed(stage, execution_id='dead-run')
    lifecycle.recover_interrupted_jobs()
    job = store.read(FRAME)['jobs']['job-recovery']
    assert job['status'] == 'queued'
    assert job['recoveries'] == 1
    assert 'desde el inicio' in job['message']
    assert 'execution_id' not in job


def test_cancelled_task_survives_recovery_and_stale_progress():
    seed('cancelled', message='Importación cancelada')
    assert patch_job(FRAME, 'job-recovery', 'old-run', status='downloading', percent=80) is False
    lifecycle.recover_interrupted_jobs()
    job = store.read(FRAME)['jobs']['job-recovery']
    assert job['status'] == 'cancelled'
    assert job['message'] == 'Importación cancelada'


def test_clearing_slot_cancels_durable_job_across_recovery():
    from backend import main
    from fastapi.testclient import TestClient
    job = seed('uploading', execution_id='lost-run')
    response = TestClient(main.app).delete('/slots/0', headers={'Authorization': 'Bearer recovery-isolated-test'})
    assert response.status_code == 200
    lifecycle.recover_interrupted_jobs()
    current = store.read(FRAME)
    assert current['jobs'][job['id']]['status'] == 'cancelled'
    assert 'slot-0' not in current['slots']


def test_late_upload_completion_cannot_publish_after_cancel():
    previous = {'id': 'old-track', 'kind': 'station', 'title': 'Anterior'}
    job = seed('queued')
    store.mutate(FRAME, lambda state: state['slots'].update({'slot-0': previous}))
    with patch('yt_dlp.YoutubeDL') as ydl, patch.object(importer, 'persist_media') as upload:
        instance = ydl.return_value.__enter__.return_value
        instance.extract_info.return_value = {'duration': 20}
        def download(urls):
            options = ydl.call_args.args[0]
            Path(options['outtmpl'].replace('%(ext)s', 'mp3')).write_bytes(b'mp3')
        instance.download.side_effect = download
        def finish_upload(*args, **kwargs):
            store.mutate(FRAME, lambda state: state['jobs'][job['id']].update(
                status='cancelled', message='Importación cancelada', execution_id=None
            ))
            return ('private/audio.mp3', None)
        upload.side_effect = finish_upload
        importer.execute_import(FRAME, job)
    current = store.read(FRAME)
    assert current['jobs'][job['id']]['status'] == 'cancelled'
    assert current['slots']['slot-0'] == previous


def test_recovery_is_bounded_and_explains_manual_action():
    seed('uploading', recoveries=2, execution_id='dead-run')
    lifecycle.recover_interrupted_jobs()
    job = store.read(FRAME)['jobs']['job-recovery']
    assert job['status'] == 'error'
    assert 'Cancela esta tarea' in job['message']


def test_api_lifespan_recovers_before_worker_starts(monkeypatch):
    seed('processing', execution_id='lost-run')
    async def idle_worker():
        await asyncio.Event().wait()
    monkeypatch.setattr(lifecycle, 'work_loop', idle_worker)
    async def run():
        async with lifecycle.lifespan(None):
            job = store.read(FRAME)['jobs']['job-recovery']
            assert job['status'] == 'queued'
            assert job['recoveries'] == 1
    asyncio.run(run())


def test_recovery_state_is_visible_to_a_separate_process(tmp_path, monkeypatch):
    database = tmp_path / 'isolated.sqlite3'
    monkeypatch.setenv('STATE_DB', str(database))
    first = StateStore()
    first.mutate(FRAME, lambda state: state['jobs'].update({
        'cross-process': {'id': 'cross-process', 'status': 'uploading', 'slot': 0, 'created_at': 1}
    }))
    first.conn.close()
    code = (
        'from backend.state import store; '
        f"print(store.read('{FRAME}')['jobs']['cross-process']['status'])"
    )
    child = subprocess.run([sys.executable, '-c', code], env={**os.environ, 'STATE_DB': str(database)},
                           check=True, capture_output=True, text=True)
    assert child.stdout.strip() == 'uploading'


def test_failed_publication_transaction_keeps_previous_selection_and_job_unfinished():
    previous = {'id': 'old', 'kind': 'station', 'title': 'Anterior'}
    seed('uploading', execution_id='current-run')
    store.mutate(FRAME, lambda state: state['slots'].update({'slot-0': previous}))
    def interrupted(state):
        state['slots']['slot-0'] = {'id': 'job-recovery', 'kind': 'song'}
        raise RuntimeError('simulated process interruption before commit')
    with pytest.raises(RuntimeError):
        store.mutate(FRAME, interrupted)
    state = store.read(FRAME)
    assert state['slots']['slot-0'] == previous
    assert state['jobs']['job-recovery']['status'] == 'uploading'
