import contextlib
from pathlib import Path

from .firebase_client import firebase
from .state import check_cancel, patch_job


def persist_media(job_id, audio: Path, image: Path | None):
    from firebase_admin import storage
    bucket = storage.bucket(app=firebase())
    uploaded = []
    try:
        audio_key = f'private/sonoro/{job_id}/audio.mp3'
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
                check_cancel(job_id)
                upload.transmit_next_chunk(transport)
                patch_job(job_id, status='uploading', percent=min(99, int(upload.bytes_uploaded / total * 100)), message='Guardando audio')
        image_key = None
        if image:
            check_cancel(job_id)
            image_key = f'private/sonoro/{job_id}/cover.jpg'
            uploaded.append(image_key)
            bucket.blob(image_key).upload_from_filename(str(image), content_type='image/jpeg')
        return audio_key, image_key
    except Exception:
        for key in uploaded:
            with contextlib.suppress(Exception):
                bucket.blob(key).delete()
        raise

