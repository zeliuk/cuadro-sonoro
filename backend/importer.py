import tempfile
import time
from pathlib import Path

from .config import MAX_BYTES, MAX_DURATION
from .media import delete_orphaned_media, persist_media
from .state import begin_execution, check_cancel, patch_job, store


def execute_import(frame_key, queued_job):
    job_id = queued_job['id']
    job = begin_execution(frame_key, job_id)
    if not job:
        return
    run_id = job['execution_id']
    try:
        check_cancel(frame_key, job_id, run_id)
        import yt_dlp
        with tempfile.TemporaryDirectory(prefix='sonoro-') as tmp:
            base = Path(tmp)
            last = [0.0]
            def progress(data):
                check_cancel(frame_key, job_id, run_id)
                if data.get('downloaded_bytes', 0) > MAX_BYTES:
                    raise RuntimeError('El archivo supera el tamaño permitido.')
                if data['status'] == 'downloading' and time.monotonic() - last[0] > .6:
                    last[0] = time.monotonic()
                    total = data.get('total_bytes') or data.get('total_bytes_estimate')
                    percent = min(99, int(data.get('downloaded_bytes', 0) * 100 / total)) if total else None
                    patch_job(frame_key, job_id, run_id, status='downloading', percent=percent, estimated=not bool(data.get('total_bytes')), message='Descargando audio')
                elif data['status'] == 'finished':
                    patch_job(frame_key, job_id, run_id, status='processing', percent=None, message='Preparando el MP3')
            def processing(data):
                check_cancel(frame_key, job_id, run_id)
                patch_job(frame_key, job_id, run_id, status='processing', percent=None, message='Preparando audio e imagen')
            options = {
                'quiet': True, 'no_warnings': True, 'noplaylist': True,
                'format': 'bestaudio/best', 'outtmpl': str(base / 'audio.%(ext)s'),
                'writethumbnail': True, 'max_filesize': MAX_BYTES,
                'socket_timeout': 25, 'retries': 2, 'fragment_retries': 2,
                'progress_hooks': [progress], 'postprocessor_hooks': [processing],
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
            }
            url = 'https://www.youtube.com/watch?v=' + job['source_id']
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                if info.get('is_live') or info.get('live_status') in {'is_live', 'is_upcoming'}:
                    raise RuntimeError('Selecciona una canción grabada, no una emisión en directo.')
                if not info.get('duration') or info['duration'] > MAX_DURATION:
                    raise RuntimeError('La duración máxima es de 15 minutos.')
                check_cancel(frame_key, job_id, run_id)
                ydl.download([url])
            audio = base / 'audio.mp3'
            if not audio.is_file():
                raise RuntimeError('No se ha generado el archivo de audio.')
            check_cancel(frame_key, job_id, run_id)
            image_path = None
            thumbnails = [p for p in base.glob('audio.*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
            if thumbnails:
                from PIL import Image, ImageOps
                image_path = base / 'cover.jpg'
                with Image.open(thumbnails[0]) as image:
                    ImageOps.fit(image.convert('RGB'), (320, 320)).save(image_path, quality=85)
            patch_job(frame_key, job_id, run_id, status='uploading', percent=0, message='Guardando en tu biblioteca')
            audio_key, image_key = persist_media(frame_key, job_id, audio, image_path, execution_id=run_id)
            check_cancel(frame_key, job_id, run_id)
            track = {
                'id': job_id, 'kind': 'song', 'title': job['title'], 'artist': job['artist'],
                'source_id': job['source_id'], 'duration': info['duration'],
                'audio_key': audio_key, 'image_key': image_key, 'created_at': time.time(),
            }
            def complete(state):
                current = state['jobs'].get(job_id)
                if not current or current.get('status') != 'uploading' or current.get('execution_id') != run_id:
                    raise RuntimeError('La ejecución ya no está vigente.')
                # Slot publication and terminal state share the same durable transaction.
                state['slots']['slot-' + str(job['slot'])] = track
                current.update(status='ready', percent=100, message='Disponible', updated_at=time.time())
                current.pop('execution_id', None)
            store.mutate(frame_key, complete)
    except Exception as exc:
        message = str(exc)
        known = ('duración máxima', 'emisión en directo', 'tamaño permitido', 'generado el archivo')
        safe = message if any(x in message for x in known) else 'La fuente no ha permitido completar la importación. Puedes reintentar o elegir otra versión.'
        def finish(state):
            current = state['jobs'].get(job_id)
            if current and current.get('status') in {'queued', 'downloading', 'processing', 'uploading'} and current.get('execution_id') == run_id:
                current.update(status='error', percent=None, message=safe, updated_at=time.time())
                current.pop('execution_id', None)
        store.mutate(frame_key, finish)
    finally:
        try:
            delete_orphaned_media(frame_key, store.read(frame_key))
        except Exception:
            pass
