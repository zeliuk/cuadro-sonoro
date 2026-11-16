import asyncio
import contextlib
import time
from contextlib import asynccontextmanager

from .config import ACTIVE
from .importer import execute_import
from .media import delete_orphaned_media
from .state import store

MAX_RECOVERIES = 2
CLEANUP_INTERVAL_SECONDS = 300


def recover_interrupted_jobs():
    """Queue interrupted work a bounded number of times; cancelled jobs stay terminal."""
    def recover(state):
        for job in state['jobs'].values():
            status = job.get('status')
            if status not in ACTIVE - {'queued'}:
                continue
            recoveries = job.get('recoveries', 0)
            job.pop('execution_id', None)
            if recoveries < MAX_RECOVERIES:
                job.update(status='queued', recoveries=recoveries + 1, percent=None,
                           message='El servicio se reinició; se repetirá la importación desde el inicio.', updated_at=time.time())
            else:
                job.update(status='error', percent=None,
                           message='No se pudo recuperar automáticamente tras varios reinicios. Cancela esta tarea y vuelve a elegir la canción.', updated_at=time.time())
    store.mutate_all(recover)


async def work_loop():
    last_cleanup = time.monotonic()
    while True:
        queued = sorted(
            ((frame_key, job) for frame_key, state in store.read_all().items() for job in state['jobs'].values() if job.get('status') == 'queued'),
            key=lambda item: item[1].get('created_at', 0),
        )
        if queued:
            await asyncio.to_thread(execute_import, *queued[0])
        else:
            if time.monotonic() - last_cleanup >= CLEANUP_INTERVAL_SECONDS:
                await asyncio.to_thread(cleanup_orphaned_media)
                last_cleanup = time.monotonic()
            await asyncio.sleep(1)


def cleanup_orphaned_media():
    for frame_key, state in store.read_all().items():
        try:
            delete_orphaned_media(frame_key, state)
        except Exception:
            continue


@asynccontextmanager
async def lifespan(app):
    recover_interrupted_jobs()
    cleanup_orphaned_media()
    task = asyncio.create_task(work_loop())
    try:
        yield
    finally:
        # Service shutdown is not a user cancellation. Leave durable active states for
        # startup recovery. The worker's execution id prevents a late result publishing.
        def release_runs(state):
            for job in state['jobs'].values():
                if job.get('status') in ACTIVE - {'queued'}:
                    job.update(status='queued', percent=None,
                               message='El servicio se está deteniendo; la importación continuará al volver a iniciar.', updated_at=time.time())
                    job.pop('execution_id', None)
        store.mutate_all(release_runs)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
