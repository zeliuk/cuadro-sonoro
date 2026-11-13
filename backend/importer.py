import logging
import re
import tempfile
import time
from pathlib import Path

from .config import MAX_BYTES, MAX_DURATION
from .media import delete_orphaned_media, persist_media
from .state import begin_execution, check_cancel, patch_job, store

logger = logging.getLogger('uvicorn.error')
URL_PATTERN = re.compile(r"(?:https?|gs)://[^\s'\"]+", re.IGNORECASE)


def _safe_error_detail(exc, source_id, temp_dir, frame_key, job_id, run_id):
    """Keep useful exception context in service logs without leaking URLs or IDs."""
    detail = str(exc)
    for private_value in (source_id, frame_key, job_id, run_id):
        if private_value:
            detail = detail.replace(private_value, '[redacted-id]')
    if temp_dir:
        detail = detail.replace(str(temp_dir), '[temp-dir]')
    detail = URL_PATTERN.sub('[url]', detail)
    detail = re.sub(r'(?i)\bBearer\s+\S+', 'Bearer [redacted]', detail)
    detail = re.sub(r'(?i)(authorization|token|key|password)(\s*[:=]\s*)([^&\s,]+)', r'\1\2[redacted]', detail)
    detail = detail.replace('\r', ' ').replace('\n', ' ')
    return detail[:500]


class _YtDlpDiagnosticLogger:
    """Forward extractor diagnostics after removing URLs and frame/task IDs."""
    def __init__(self, source_id, temp_dir, frame_key, job_id, run_id):
        self.context = (source_id, temp_dir, frame_key, job_id, run_id)

    def debug(self, message):
        if str(message).startswith('[debug]'):
            logger.info('yt_dlp_diagnostic %s', _safe_error_detail(RuntimeError(message), *self.context))

    def warning(self, message):
        logger.warning('yt_dlp_diagnostic %s', _safe_error_detail(RuntimeError(message), *self.context))

    def error(self, message):
        logger.error('yt_dlp_diagnostic %s', _safe_error_detail(RuntimeError(message), *self.context))


def execute_import(frame_key, queued_job):
    job_id = queued_job['id']
    job = begin_execution(frame_key, job_id)
    if not job:
        return
    run_id = job['execution_id']
    stage = 'initialize'
    temp_dir = None
    logger.info('import_checkpoint stage=%s result=start', stage)
    try:
        check_cancel(frame_key, job_id, run_id)
        import yt_dlp
        with tempfile.TemporaryDirectory(prefix='sonoro-') as tmp:
            base = Path(tmp)
            temp_dir = base
            last = [0.0]
            conversion_logged = [False]
            def progress(data):
                nonlocal stage
                check_cancel(frame_key, job_id, run_id)
                if data.get('downloaded_bytes', 0) > MAX_BYTES:
                    raise RuntimeError('El archivo supera el tamaño permitido.')
                if data['status'] == 'downloading' and time.monotonic() - last[0] > .6:
                    last[0] = time.monotonic()
                    total = data.get('total_bytes') or data.get('total_bytes_estimate')
                    percent = min(99, int(data.get('downloaded_bytes', 0) * 100 / total)) if total else None
                    patch_job(frame_key, job_id, run_id, status='downloading', percent=percent, estimated=not bool(data.get('total_bytes')), message='Descargando audio')
                elif data['status'] == 'finished':
                    stage = 'audio_conversion'
                    if not conversion_logged[0]:
                        logger.info('import_checkpoint stage=audio_conversion result=start')
                        conversion_logged[0] = True
                    patch_job(frame_key, job_id, run_id, status='processing', percent=None, message='Preparando el MP3')
            def processing(data):
                check_cancel(frame_key, job_id, run_id)
                patch_job(frame_key, job_id, run_id, status='processing', percent=None, message='Preparando audio e imagen')
            options = {
                'quiet': True, 'no_warnings': False, 'verbose': True,
                'logger': _YtDlpDiagnosticLogger(job.get('source_id', ''), base, frame_key, job_id, run_id),
                'noplaylist': True,
                'format': 'bestaudio/best', 'outtmpl': str(base / 'audio.%(ext)s'),
                'writethumbnail': True, 'max_filesize': MAX_BYTES,
                'socket_timeout': 25, 'retries': 2, 'fragment_retries': 2,
                'progress_hooks': [progress], 'postprocessor_hooks': [processing],
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
            }
            url = 'https://www.youtube.com/watch?v=' + job['source_id']
            with yt_dlp.YoutubeDL(options) as ydl:
                stage = 'source_lookup'
                logger.info('import_checkpoint stage=%s result=start', stage)
                info = ydl.extract_info(url, download=False)
                logger.info('import_checkpoint stage=%s result=complete', stage)
                stage = 'metadata_validation'
                logger.info('import_checkpoint stage=%s result=start', stage)
                if info.get('is_live') or info.get('live_status') in {'is_live', 'is_upcoming'}:
                    raise RuntimeError('Selecciona una canción grabada, no una emisión en directo.')
                if not info.get('duration') or info['duration'] > MAX_DURATION:
                    raise RuntimeError('La duración máxima es de 15 minutos.')
                check_cancel(frame_key, job_id, run_id)
                logger.info('import_checkpoint stage=%s result=complete', stage)
                stage = 'source_download'
                logger.info('import_checkpoint stage=%s result=start', stage)
                ydl.download([url])
                logger.info('import_checkpoint stage=%s result=complete', stage)
            stage = 'audio_conversion'
            audio = base / 'audio.mp3'
            if not audio.is_file():
                raise RuntimeError('No se ha generado el archivo de audio.')
            logger.info('import_checkpoint stage=%s result=complete', stage)
            check_cancel(frame_key, job_id, run_id)
            stage = 'cover_processing'
            image_path = None
            thumbnails = [p for p in base.glob('audio.*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
            if thumbnails:
                from PIL import Image, ImageOps
                image_path = base / 'cover.jpg'
                with Image.open(thumbnails[0]) as image:
                    ImageOps.fit(image.convert('RGB'), (320, 320)).save(image_path, quality=85)
            logger.info('import_checkpoint stage=%s result=complete cover=%s', stage, bool(image_path))
            patch_job(frame_key, job_id, run_id, status='uploading', percent=0, message='Guardando en tu biblioteca')
            stage = 'firebase_upload'
            logger.info('import_checkpoint stage=%s result=start', stage)
            audio_key, image_key = persist_media(frame_key, job_id, audio, image_path, execution_id=run_id)
            logger.info('import_checkpoint stage=%s result=complete image=%s', stage, bool(image_key))
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
            stage = 'publish'
            store.mutate(frame_key, complete)
            logger.info('import_checkpoint stage=%s result=complete', stage)
    except Exception as exc:
        logger.error(
            'import_checkpoint stage=%s result=error type=%s detail=%s',
            stage,
            type(exc).__name__,
            _safe_error_detail(exc, job.get('source_id', ''), temp_dir, frame_key, job_id, run_id),
        )
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
        logger.info('import_checkpoint stage=cleanup result=start')
        try:
            delete_orphaned_media(frame_key, store.read(frame_key))
            logger.info('import_checkpoint stage=cleanup result=complete')
        except Exception as cleanup_exc:
            logger.warning(
                'import_checkpoint stage=cleanup result=error type=%s detail=%s',
                type(cleanup_exc).__name__,
                _safe_error_detail(cleanup_exc, job.get('source_id', ''), temp_dir, frame_key, job_id, run_id),
            )
