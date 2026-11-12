"""HTTP API for the private, single-owner prototype."""
import hmac
import os
import re
import secrets
import time
from datetime import timedelta
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import ACTIVE, MAX_DURATION, TOKEN
from .firebase_client import firebase
from .lifecycle import lifespan
from .models import Import, Search, Station
from .state import cancelled, patch_job, store


app = FastAPI(title='Sonoro import service', lifespan=lifespan)
origins = [x.strip() for x in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])
security = HTTPBearer(auto_error=False)

def authorized(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if not TOKEN:
        raise HTTPException(503, 'Configura IMPORT_API_TOKEN en el servidor.')
    if not credentials or not hmac.compare_digest(credentials.credentials, TOKEN):
        raise HTTPException(401, 'Acceso no autorizado.')


@app.get('/health')
def health():
    return {'ok': True, 'storage_configured': bool(os.getenv('FIREBASE_STORAGE_BUCKET')), 'durable_state': store.cloud}


@app.post('/search', dependencies=[Depends(authorized)])
def search(body: Search):
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


@app.post('/imports', dependencies=[Depends(authorized)], status_code=202)
def create_import(body: Import):
    if not os.getenv('FIREBASE_STORAGE_BUCKET'):
        raise HTTPException(503, 'Configura Firebase Storage antes de importar.')
    job = {**body.model_dump(), 'id': secrets.token_hex(12), 'status': 'queued', 'percent': None, 'message': 'Esperando turno', 'created_at': time.time()}
    def add(state):
        if any(j['slot'] == body.slot and j['status'] in ACTIVE for j in state['jobs'].values()):
            raise HTTPException(409, 'Este espacio ya tiene una importación en curso.')
        # Keep state bounded. A slot replacement preserves the previous track until success.
        finished = sorted((j for j in state['jobs'].values() if j['status'] not in ACTIVE), key=lambda j: j['created_at'])
        for old in finished[:-30]:
            del state['jobs'][old['id']]
        state['jobs'][job['id']] = job
    store.mutate(add)
    return job


@app.get('/state', dependencies=[Depends(authorized)])
def state():
    return store.read()


@app.post('/jobs/{job_id}/cancel', dependencies=[Depends(authorized)])
def cancel(job_id: str):
    job = store.read()['jobs'].get(job_id)
    if not job:
        raise HTTPException(404, 'Tarea no encontrada.')
    if job['status'] in ACTIVE:
        cancelled.add(job_id)
        patch_job(job_id, status='cancelled', percent=None, message='Cancelando importación')
    return {'ok': True}


@app.post('/stations', dependencies=[Depends(authorized)])
def station(body: Station):
    parsed = urlparse(body.url)
    # Backend never fetches this URL: prevents a generic SSRF/download endpoint.
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(422, 'Utiliza una URL HTTPS directa de streaming.')
    def add(state):
        if any(j['slot'] == body.slot and j['status'] in ACTIVE for j in state['jobs'].values()):
            raise HTTPException(409, 'Este espacio tiene una importación en curso.')
        state['slots']['slot-' + str(body.slot)] = {'id': secrets.token_hex(12), 'kind': 'station', 'title': body.title, 'artist': 'Radio en directo', 'url': body.url}
    store.mutate(add)
    return {'ok': True}


@app.delete('/slots/{slot}', dependencies=[Depends(authorized)])
def delete_slot(slot: int):
    if slot not in range(3):
        raise HTTPException(422, 'Espacio no válido.')
    def remove(state):
        for job in state['jobs'].values():
            if job['slot'] == slot:
                if job['status'] in ACTIVE:
                    cancelled.add(job['id'])
                job.update(status='cancelled', message='Espacio vaciado', percent=None)
        state['slots'].pop('slot-' + str(slot), None)
    store.mutate(remove)
    return {'ok': True}


@app.get('/media/{slot}', dependencies=[Depends(authorized)])
def media(slot: int):
    track = store.read()['slots'].get('slot-' + str(slot))
    if not track:
        raise HTTPException(404, 'Espacio vacío.')
    if track['kind'] == 'station':
        return {'audio_url': track['url'], 'image_url': None}
    from firebase_admin import storage
    bucket = storage.bucket(app=firebase())
    def signed(key):
        return bucket.blob(key).generate_signed_url(version='v4', expiration=timedelta(minutes=30), method='GET') if key else None
    return {'audio_url': signed(track['audio_key']), 'image_url': signed(track.get('image_key'))}
