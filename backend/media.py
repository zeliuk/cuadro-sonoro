import contextlib
from pathlib import Path

from .firebase_client import firebase
from .config import ACTIVE
from .state import check_cancel, patch_job


def delete_orphaned_media(frame_key, state, bucket=None):
    """Delete frame media not referenced by a published slot or active import."""
    from firebase_admin import storage
    if bucket is None:
        bucket = storage.bucket(app=firebase())
    prefix = f'private/frames/{frame_key}/'
    referenced = {
        track.get(key)
        for track in state.get('slots', {}).values()
        for key in ('audio_key', 'image_key')
        if track.get(key)
    }
    active_jobs = {job_id for job_id, job in state.get('jobs', {}).items() if job.get('status') in ACTIVE}
    deleted = 0
    pending = False
    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name in referenced:
            continue
        relative = blob.name[len(prefix):]
        job_id = relative.split('/', 1)[0]
        if job_id in active_jobs:
            continue
        try:
            blob.delete()
            deleted += 1
        except Exception:
            pending = True
    return {'deleted_objects': deleted, 'cleanup_pending': pending}


def persist_media(frame_key, job_id, audio: Path, image: Path | None, execution_id=None):
    from firebase_admin import storage
    bucket = storage.bucket(app=firebase())
    uploaded = []
    try:
        run_prefix = f'private/frames/{frame_key}/{job_id}/{execution_id or "legacy"}'
        audio_key = run_prefix + '/audio.mp3'
        uploaded.append(audio_key)
        # Resumable chunks expose actual completed byte counts.
        from google.auth.transport.requests import AuthorizedSession
        from google.resumable_media.requests import ResumableUpload
        creds = firebase().credential.get_credential()
        transport = AuthorizedSession(creds)
        endpoint = f'https://storage.googleapis.com/upload/storage/v1/b/{bucket.name}/o?uploadType=resumable'
        upload = ResumableUpload(endpoint, 256 * 1024)
        total = audio.stat().st_size
        with audio.open('rb') as stream:
            upload.initiate(transport, stream, {'name': audio_key}, 'audio/mpeg', total_bytes=total)
            while not upload.finished:
                check_cancel(frame_key, job_id, execution_id)
                upload.transmit_next_chunk(transport)
                patch_job(frame_key, job_id, execution_id, status='uploading', percent=min(99, int(upload.bytes_uploaded / total * 100)), message='Guardando audio')
        image_key = None
        if image:
            check_cancel(frame_key, job_id, execution_id)
            image_key = run_prefix + '/cover.jpg'
            uploaded.append(image_key)
            bucket.blob(image_key).upload_from_filename(str(image), content_type='image/jpeg')
            check_cancel(frame_key, job_id, execution_id)
        return audio_key, image_key
    except Exception:
        for key in uploaded:
            with contextlib.suppress(Exception):
                bucket.blob(key).delete()
        raise

