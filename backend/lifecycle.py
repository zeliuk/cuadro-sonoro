import asyncio
import contextlib
from contextlib import asynccontextmanager

from .config import ACTIVE
from .importer import execute_import
from .media import delete_orphaned_media
from .state import cancelled, store


async def work_loop():
    while True:
        queued = sorted(
            ((frame_key, job) for frame_key, state in store.read_all().items() for job in state['jobs'].values() if job['status'] == 'queued'),
            key=lambda item: item[1]['created_at'],
        )
        if queued:
            await asyncio.to_thread(execute_import, *queued[0])
        else:
            await asyncio.sleep(1)


def cleanup_orphaned_media():
    for frame_key, state in store.read_all().items():
        try:
            delete_orphaned_media(frame_key, state)
        except Exception:
            # Keep the service available; a later restart or explicit empty-slot
            # deletion retries the cleanup without exposing frame identifiers.
            continue


@asynccontextmanager
async def lifespan(app):
    def recover(state):
        for job in state['jobs'].values():
            if job['status'] in ACTIVE - {'queued'}:
                job.update(status='error', percent=None, message='El servicio se reinició. Reintenta la importación.')
    store.mutate_all(recover)
    cleanup_orphaned_media()
    task = asyncio.create_task(work_loop())
    yield
    for state in store.read_all().values():
        for job in state['jobs'].values():
            if job['status'] in ACTIVE:
                cancelled.add(job['id'])
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

