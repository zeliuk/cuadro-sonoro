"""HTTP API for frame-scoped configuration and imports."""
import os
import re
import secrets
import time
from urllib.parse import quote, urlparse

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import ACTIVE, MAX_DURATION
from .identity import frame_key_for
from .lifecycle import lifespan
from .media import delete_orphaned_media
from .models import Import, Search, Station
from .state import cancelled, patch_job, store


app = FastAPI(
    title='Sonoro API',
    version='0.3.0',
    description='API experimental de Sonoro. El identificador del cuadro viaja como Bearer y deriva un ámbito SHA-256; no autentica ni autoriza usuarios. La configuración publicada y los medios tienen lectura directa por URL conocida.',
    lifespan=lifespan,
)
origins = [x.strip() for x in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])
security = HTTPBearer(auto_error=False, description='Identificador público del cuadro (1–128 caracteres ASCII; no es una credencial).')


def identify_frame(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if not credentials:
        raise HTTPException(401, 'Falta el identificador del cuadro.')
    try:
        return frame_key_for(credentials.credentials)
    except ValueError:
        raise HTTPException(401, 'El identificador del cuadro no es válido.') from None


@app.get('/health')
def health():
    return {'ok': True, 'storage_configured': bool(os.getenv('FIREBASE_STORAGE_BUCKET')), 'durable_state': store.cloud}


@app.post('/search', responses={401: {'description': 'Identificador ausente o no válido.'}, 502: {'description': 'Falló la búsqueda en la fuente.'}})
def search(body: Search, _frame_key: str = Depends(identify_frame)):
    import yt_dlp
    query = f'{body.artist} {body.title} official audio'
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': 'in_playlist', 'skip_download': True, 'socket_timeout': 20, 'retries': 1}) as ydl:
            result = ydl.extract_info('ytsearch5:' + query, download=False)
        entries = []
        for entry in result.get('entries', []):
            if not entry or not re.fullmatch(r'[A-Za-z0-9_-]{11}', entry.get('id', '')):
                continue
            duration = entry.get('duration')
            if entry.get('is_live') or (duration and duration > MAX_DURATION):
                continue
            entries.append({'id': entry['id'], 'title': entry.get('title', body.title), 'artist': entry.get('channel') or entry.get('uploader') or body.artist, 'duration': duration, 'image': f"https://i.ytimg.com/vi/{entry['id']}/mqdefault.jpg"})
        return {'results': entries}
    except Exception:
        raise HTTPException(502, 'No se pudo completar la búsqueda. La fuente puede estar bloqueando al servidor; vuelve a intentarlo.')


@app.post('/imports', status_code=202, responses={401: {'description': 'Identificador ausente o no válido.'}, 409: {'description': 'El cuadro ya tiene una importación activa.'}, 503: {'description': 'Firebase Storage no está configurado.'}})
def create_import(body: Import, frame_key: str = Depends(identify_frame)):
    if not os.getenv('FIREBASE_STORAGE_BUCKET'):
        raise HTTPException(503, 'Configura Firebase Storage antes de importar.')
    job = {**body.model_dump(), 'id': secrets.token_hex(12), 'status': 'queued', 'percent': None, 'message': 'Esperando turno', 'created_at': time.time()}
    def add(state):
        if any(j['status'] in ACTIVE for j in state['jobs'].values()):
            raise HTTPException(409, 'Este cuadro ya tiene una importación en curso.')
        # Keep state bounded. A slot replacement preserves the previous track until success.
        finished = sorted((j for j in state['jobs'].values() if j['status'] not in ACTIVE), key=lambda j: j['created_at'])
        for old in finished[:-30]:
            del state['jobs'][old['id']]
        state['jobs'][job['id']] = job
    store.mutate(frame_key, add)
    return job


@app.get('/state', responses={401: {'description': 'Identificador ausente o no válido.'}})
def state(frame_key: str = Depends(identify_frame)):
    return store.ensure(frame_key)


@app.post('/jobs/{job_id}/cancel', responses={401: {'description': 'Identificador ausente o no válido.'}, 404: {'description': 'Tarea no encontrada en este cuadro.'}})
def cancel(job_id: str, frame_key: str = Depends(identify_frame)):
    job = store.read(frame_key)['jobs'].get(job_id)
    if not job:
        raise HTTPException(404, 'Tarea no encontrada.')
    if job['status'] in ACTIVE:
        cancelled.add(job_id)
        patch_job(frame_key, job_id, status='cancelled', percent=None, message='Cancelando importación')
    return {'ok': True}


@app.post('/stations', responses={401: {'description': 'Identificador ausente o no válido.'}, 409: {'description': 'El cuadro ya tiene una importación activa.'}})
def station(body: Station, frame_key: str = Depends(identify_frame)):
    parsed = urlparse(body.url)
    # Backend never fetches this URL: prevents a generic SSRF/download endpoint.
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(422, 'Utiliza una URL HTTPS directa de streaming.')
    def add(state):
        if any(j['status'] in ACTIVE for j in state['jobs'].values()):
            raise HTTPException(409, 'Este cuadro tiene una importación en curso.')
        state['slots']['slot-' + str(body.slot)] = {'id': secrets.token_hex(12), 'kind': 'station', 'title': body.title, 'artist': 'Radio en directo', 'url': body.url}
    store.mutate(frame_key, add)
    try:
        cleanup = delete_orphaned_media(frame_key, store.read(frame_key))
        return {'ok': True, **cleanup}
    except Exception:
        return {'ok': True, 'deleted_objects': 0, 'cleanup_pending': True}


@app.delete('/slots/{slot}', responses={401: {'description': 'Identificador ausente o no válido.'}})
def delete_slot(slot: int, frame_key: str = Depends(identify_frame)):
    if slot not in range(3):
        raise HTTPException(422, 'Espacio no válido.')
    def remove(state):
        for job in state['jobs'].values():
            if job['slot'] == slot:
                if job['status'] in ACTIVE:
                    cancelled.add(job['id'])
                job.update(status='cancelled', message='Espacio vaciado', percent=None)
        state['slots'].pop('slot-' + str(slot), None)
    store.mutate(frame_key, remove)
    try:
        cleanup = delete_orphaned_media(frame_key, store.read(frame_key))
        return {'ok': True, **cleanup}
    except Exception:
        return {'ok': True, 'deleted_objects': 0, 'cleanup_pending': True}


@app.get('/media/{slot}', responses={401: {'description': 'Identificador ausente o no válido.'}, 404: {'description': 'Hueco vacío en este cuadro.'}, 503: {'description': 'Firebase Storage no está configurado.'}})
def media(slot: int, frame_key: str = Depends(identify_frame)):
    track = store.read(frame_key)['slots'].get('slot-' + str(slot))
    if not track:
        raise HTTPException(404, 'Espacio vacío.')
    if track['kind'] == 'station':
        return {'audio_url': track['url'], 'image_url': None}
    bucket = os.getenv('FIREBASE_STORAGE_BUCKET', '').strip()
    if not bucket:
        raise HTTPException(503, 'Configura Firebase Storage antes de obtener enlaces de medios.')
    def public_url(key):
        if not key:
            return None
        return f'https://firebasestorage.googleapis.com/v0/b/{quote(bucket, safe="")}/o/{quote(key, safe="")}?alt=media'
    return {'audio_url': public_url(track['audio_key']), 'image_url': public_url(track.get('image_key'))}
