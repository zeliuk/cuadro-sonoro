import logging
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import Request

from .config import MAX_BYTES, MAX_DURATION
from . import apify
from .media import delete_orphaned_media, persist_media
from .state import begin_execution, check_cancel, patch_job, store

logger = logging.getLogger('uvicorn.error')
URL_PATTERN = re.compile(r"(?:https?|gs)://[^\s'\"]+", re.IGNORECASE)


def _download_with_yt_dlp(job, frame_key, job_id, run_id, audio_path):
    """Download and convert the explicitly selected YouTube video on this host."""
    import yt_dlp

    def progress(data):
        check_cancel(frame_key, job_id, run_id)
        if data.get('status') != 'downloading':
            return
        downloaded = data.get('downloaded_bytes', 0)
        if downloaded > MAX_BYTES:
            raise RuntimeError('El archivo supera el tamaño permitido.')
        total = data.get('total_bytes') or data.get('total_bytes_estimate')
        percent = min(99, int(downloaded * 100 / total)) if total else None
        patch_job(frame_key, job_id, run_id, status='downloading', percent=percent,
                  estimated=not bool(data.get('total_bytes')), message='Descargando audio con yt-dlp en este servidor')

    def match_filter(info, *, incomplete=False):
        if info.get('is_live') or info.get('live_status') in {'is_live', 'is_upcoming'}:
            return 'No se importan emisiones en directo.'
        duration = info.get('duration')
        if duration is not None and duration > MAX_DURATION:
            return 'La duración máxima es de 15 minutos.'
        return None

    options = {
        'format': 'bestaudio/best', 'outtmpl': str(audio_path.with_suffix('.%(ext)s')),
        'noplaylist': True, 'quiet': True, 'no_warnings': True,
        'socket_timeout': 20, 'retries': 1, 'max_filesize': MAX_BYTES,
        'progress_hooks': [progress], 'match_filter': match_filter,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
    }
    video_url = 'https://www.youtube.com/watch?v=' + job['source_id']
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(video_url, download=True)
    duration = info.get('duration')
    if not isinstance(duration, (int, float)) or duration <= 0 or duration > MAX_DURATION:
        raise RuntimeError('La duración máxima es de 15 minutos.')
    if not audio_path.is_file() or audio_path.stat().st_size > MAX_BYTES:
        raise RuntimeError('El archivo supera el tamaño permitido o no se generó el MP3.')
    return info


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
        with tempfile.TemporaryDirectory(prefix='sonoro-') as tmp:
            base = Path(tmp)
            temp_dir = base
            stage = 'source_download'
            logger.info('import_checkpoint stage=%s result=start', stage)
            check_cancel(frame_key, job_id, run_id)
            current = store.read(frame_key)['jobs'][job_id]
            audio = base / 'audio.mp3'
            provider = current.get('provider', 'apify')
            if provider == 'yt_dlp':
                patch_job(frame_key, job_id, run_id, status='downloading', percent=None,
                          message='Descargando audio con yt-dlp en este servidor')
                info = _download_with_yt_dlp(job, frame_key, job_id, run_id, audio)
                info['thumbnailFileUrl'] = info.get('thumbnail')
            else:
                remote_run_id = current.get('apify_run_id')
                actor = current.get('apify_actor') or os.getenv('APIFY_DOWNLOAD_ACTOR', 'lurkapi/youtube-to-mp3-audio-downloader').strip()
                if not remote_run_id:
                    if current.get('apify_creation_started'):
                        raise apify.ApifyError('La creación remota quedó ambigua; comprueba Apify antes de reintentar.')
                    patch_job(frame_key, job_id, run_id, apify_creation_started=True)
                    patch_job(frame_key, job_id, run_id, status='processing', percent=None, message='Preparando descarga con Apify')
                    try:
                        remote = apify.create_run(actor, apify.download_input(actor, job['source_id'], MAX_DURATION, MAX_BYTES))
                    except Exception:
                        logger.error('apify_run_creation_ambiguous actor=%s', actor)
                        changed = patch_job(frame_key, job_id, run_id, status='error', message='No se pudo confirmar si Apify creó la descarga. Revisa Apify antes de cancelar y reintentar.', apify_creation_ambiguous=True)
                        if not changed:
                            def mark_ambiguous_cancel(state):
                                current = state['jobs'].get(job_id)
                                if current and current.get('status') == 'cancelled':
                                    current.update(apify_creation_ambiguous=True, message='Cancelada localmente; comprueba Apify porque la creación remota no se pudo confirmar.')
                            store.mutate(frame_key, mark_ambiguous_cancel)
                        return
                    remote_run_id = remote['id']
                    recorded = patch_job(frame_key, job_id, run_id, apify_run_id=remote_run_id, apify_creation_started=False, status='downloading', percent=None,
                                         message='Apify está preparando el audio', apify_actor=actor)
                    if not recorded:
                        def attach_cancelled_run(state):
                            current = state['jobs'].get(job_id)
                            if current and current.get('status') == 'cancelled':
                                current.update(apify_run_id=remote_run_id, apify_creation_started=False, apify_cancel_pending=True)
                        store.mutate(frame_key, attach_cancelled_run)
                        try:
                            apify.abort_run(remote_run_id)
                            store.mutate(frame_key, lambda state: state['jobs'][job_id].update(apify_cancel_pending=False))
                        except apify.ApifyError:
                            pass
                        check_cancel(frame_key, job_id, run_id)
                else:
                    patch_job(frame_key, job_id, run_id, status='downloading', percent=None, message='Recuperando ejecución de Apify')
                remote = apify.wait_run(remote_run_id)
                check_cancel(frame_key, job_id, run_id)
                info = apify.download_result(remote, actor=actor)
                if info.get('videoId') != job['source_id']:
                    raise RuntimeError('Apify devolvió un vídeo distinto al seleccionado.')
                duration = info.get('duration')
                if not isinstance(duration, (int, float)) or duration <= 0 or duration > MAX_DURATION:
                    raise RuntimeError('La duración máxima es de 15 minutos.')
                request = Request(info['audioFileUrl'], headers={'Accept': 'audio/mpeg,application/octet-stream'})
                with apify.open_media(request, timeout=30) as response, audio.open('wb') as output:
                    apify.validate_public_url(response.geturl())
                    length = response.headers.get('Content-Length')
                    total = int(length) if length and length.isdigit() else None
                    downloaded = 0
                    while True:
                        check_cancel(frame_key, job_id, run_id)
                        chunk = response.read(64 * 1024)
                        if not chunk:
                            break
                        downloaded += len(chunk)
                        if downloaded > MAX_BYTES:
                            raise RuntimeError('El archivo supera el tamaño permitido.')
                        output.write(chunk)
                        percent = min(99, int(downloaded * 100 / total)) if total else None
                        patch_job(frame_key, job_id, run_id, status='downloading', percent=percent,
                                  estimated=not bool(total), message='Descargando audio preparado por Apify')
            stage = 'audio_validation'
            probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,format_name', '-of', 'json', str(audio)], capture_output=True, text=True, timeout=20, check=True)
            measured = json.loads(probe.stdout).get('format', {})
            if 'mp3' not in measured.get('format_name', ''):
                raise RuntimeError('El archivo de audio no tiene formato MP3 válido.')
            real_duration = float(measured.get('duration', 0))
            if not real_duration or real_duration > MAX_DURATION:
                raise RuntimeError('La duración máxima es de 15 minutos.')
            patch_job(frame_key, job_id, run_id, status='processing', percent=None, message='Preparando imagen y metadatos')
            logger.info('import_checkpoint stage=%s result=complete', stage)
            check_cancel(frame_key, job_id, run_id)
            stage = 'cover_processing'
            image_path = None
            if info.get('thumbnailFileUrl'):
                from PIL import Image, ImageOps
                image_path = base / 'cover.jpg'
                thumbnail_path = base / 'thumbnail'
                with apify.open_media(Request(info['thumbnailFileUrl']), timeout=20) as response:
                    thumbnail_path.write_bytes(response.read(5 * 1024 * 1024 + 1))
                if thumbnail_path.stat().st_size > 5 * 1024 * 1024:
                    raise RuntimeError('La portada supera el tamaño permitido.')
                with Image.open(thumbnail_path) as image:
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
                'source_id': job['source_id'], 'duration': int(real_duration),
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
        if isinstance(exc, apify.ApifyError) and 'tiempo máximo de seguimiento' in str(exc):
            patch_job(frame_key, job_id, run_id, status='queued', percent=None,
                      message='Apify sigue trabajando; se retomará el seguimiento automáticamente.')
            return
        message = str(exc)
        known = ('duración máxima', 'emisión en directo', 'tamaño permitido', 'generado el archivo',
                 'falló la descarga individual', 'no se importan emisiones en directo')
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
