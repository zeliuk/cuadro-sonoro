"""HTTP API for frame-scoped configuration and imports."""
import hashlib
import os
import re
import secrets
import time
from datetime import timedelta
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import ACTIVE, MAX_DURATION
from .firebase_client import firebase
from .lifecycle import lifespan
from .models import Import, Search, Station
from .state import cancelled, patch_job, store


app = FastAPI(
    title='Sonoro API',
    version='0.2.0',
    description='API experimental de Sonoro. Las operaciones de cuadro usan un token Bearer y separan datos mediante su huella SHA-256. No proporciona acceso autónomo a medios para el ESP32.',
    lifespan=lifespan,
)
origins = [x.strip() for x in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])
security = HTTPBearer(auto_error=False, description='Token aleatorio provisionado para el cuadro, mínimo 32 caracteres. No usar una credencial administrativa de Firebase.')


def allowed_frame_keys():
    configured = {
        value.strip().lower()
        for value in os.getenv('FRAME_TOKEN_HASHES', '').split(',')
        if re.fullmatch(r'[0-9a-fA-F]{64}', value.strip())
    }
    # A local convenience token is never accepted in a Firebase-backed deployment.
    if not os.getenv('FIREBASE_DATABASE_URL') and not os.getenv('FIREBASE_STORAGE_BUCKET'):
        local_token = os.getenv('LOCAL_FRAME_TOKEN', '')
        if re.fullmatch(r'[A-Za-z0-9_-]{32,}', local_token):
            configured.add(hashlib.sha256(local_token.encode('utf-8')).hexdigest())
    return configured

def authorized(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if not credentials or not re.fullmatch(r'[A-Za-z0-9_-]{32,}', credentials.credentials):
        raise HTTPException(401, 'Acceso no autorizado.')
    # The raw capability is never stored in RTDB, SQLite, jobs, or Storage paths.
    frame_key = hashlib.sha256(credentials.credentials.encode('utf-8')).hexdigest()
    if frame_key not in allowed_frame_keys():
        raise HTTPException(401, 'Acceso no autorizado.')
    return frame_key


@app.get('/health')
def health():
    return {'ok': True, 'storage_configured': bool(os.getenv('FIREBASE_STORAGE_BUCKET')), 'durable_state': store.cloud}


@app.post('/search', responses={401: {'description': 'Token ausente, inválido o no provisionado.'}, 502: {'description': 'Falló la búsqueda en la fuente.'}})
def search(body: Search, _frame_key: str = Depends(authorized)):
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


@app.post('/imports', status_code=202, responses={401: {'description': 'Token ausente, inválido o no provisionado.'}, 409: {'description': 'El cuadro ya tiene una importación activa.'}, 503: {'description': 'Firebase Storage no está configurado.'}})
def create_import(body: Import, frame_key: str = Depends(authorized)):
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


@app.get('/state', responses={401: {'description': 'Token ausente, inválido o no provisionado.'}})
def state(frame_key: str = Depends(authorized)):
    return store.read(frame_key)


@app.post('/jobs/{job_id}/cancel', responses={401: {'description': 'Token ausente, inválido o no provisionado.'}, 404: {'description': 'Tarea no encontrada en este cuadro.'}})
def cancel(job_id: str, frame_key: str = Depends(authorized)):
    job = store.read(frame_key)['jobs'].get(job_id)
    if not job:
        raise HTTPException(404, 'Tarea no encontrada.')
    if job['status'] in ACTIVE:
        cancelled.add(job_id)
        patch_job(frame_key, job_id, status='cancelled', percent=None, message='Cancelando importación')
    return {'ok': True}


@app.post('/stations', responses={401: {'description': 'Token ausente, inválido o no provisionado.'}, 409: {'description': 'El cuadro ya tiene una importación activa.'}})
def station(body: Station, frame_key: str = Depends(authorized)):
    parsed = urlparse(body.url)
    # Backend never fetches this URL: prevents a generic SSRF/download endpoint.
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(422, 'Utiliza una URL HTTPS directa de streaming.')
    def add(state):
        if any(j['status'] in ACTIVE for j in state['jobs'].values()):
            raise HTTPException(409, 'Este cuadro tiene una importación en curso.')
        state['slots']['slot-' + str(body.slot)] = {'id': secrets.token_hex(12), 'kind': 'station', 'title': body.title, 'artist': 'Radio en directo', 'url': body.url}
    store.mutate(frame_key, add)
    return {'ok': True}


@app.delete('/slots/{slot}', responses={401: {'description': 'Token ausente, inválido o no provisionado.'}})
def delete_slot(slot: int, frame_key: str = Depends(authorized)):
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
    return {'ok': True}


@app.get('/media/{slot}', responses={401: {'description': 'Token ausente, inválido o no provisionado.'}, 404: {'description': 'Hueco vacío en este cuadro.'}})
def media(slot: int, frame_key: str = Depends(authorized)):
    track = store.read(frame_key)['slots'].get('slot-' + str(slot))
    if not track:
        raise HTTPException(404, 'Espacio vacío.')
    if track['kind'] == 'station':
        return {'audio_url': track['url'], 'image_url': None}
    from firebase_admin import storage
    bucket = storage.bucket(app=firebase())
    def signed(key):
        return bucket.blob(key).generate_signed_url(version='v4', expiration=timedelta(minutes=30), method='GET') if key else None
    return {'audio_url': signed(track['audio_key']), 'image_url': signed(track.get('image_key'))}
