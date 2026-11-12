"""Verify public, URL-scoped device reads against local RTDB and Storage emulators."""
import hashlib
import json
import os
import secrets
import socket
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from device_client import read_slot, read_slots


PROJECT = 'demo-sonoro-device'
DATABASE_HOST = '127.0.0.1:9000'
STORAGE_HOST = '127.0.0.1:9199'
BUCKET = f'{PROJECT}.appspot.com'
AUDIO_A = b'local-test-audio-frame-a'
AUDIO_B = b'local-test-audio-frame-b'
IMAGE_A = b'local-test-image-frame-a'


def require_emulators() -> None:
    expected = {
        'FIREBASE_DATABASE_EMULATOR_HOST': DATABASE_HOST,
        'FIREBASE_STORAGE_EMULATOR_HOST': STORAGE_HOST,
    }
    if any(os.getenv(name) != value for name, value in expected.items()):
        raise RuntimeError('Inicia este script solo con los emuladores locales RTDB y Storage.')
    try:
        with socket.create_connection(('127.0.0.1', 8000), timeout=0.2):
            raise RuntimeError('Detén la API local en el puerto 8000 para verificar independencia de Render.')
    except OSError:
        pass


def request(url: str, *, method='GET', body=None, content_type='application/json', admin=False):
    headers = {'Content-Type': content_type}
    if admin:
        headers['Authorization'] = 'Bearer owner'
    req = Request(url, data=body, headers=headers, method=method)
    with urlopen(req, timeout=20) as response:
        return response.read()


def seed_json(url: str, body: dict) -> None:
    request(url, method='PUT', body=json.dumps(body).encode(), admin=True)


def seed_object(key: str, content: bytes, mime: str) -> None:
    url = (
        f'http://{STORAGE_HOST}/upload/storage/v1/b/{quote(BUCKET, safe="")}/o'
        f'?uploadType=media&name={quote(key, safe="")}'
    )
    request(url, method='POST', body=content, content_type=mime, admin=True)


def denied(url: str, *, method='GET', body=None, content_type='application/json') -> bool:
    try:
        request(url, method=method, body=body, content_type=content_type)
        return False
    except HTTPError as error:
        return error.code in (401, 403)


def run() -> None:
    require_emulators()
    namespace = PROJECT + '-default-rtdb'
    identifier_a = 'local-frame-a-' + secrets.token_urlsafe(24)
    identifier_b = 'local-frame-b-' + secrets.token_urlsafe(24)
    key_a, key_b = (hashlib.sha256(value.encode()).hexdigest() for value in (identifier_a, identifier_b))
    audio_a = f'private/frames/{key_a}/test/audio.mp3'
    image_a = f'private/frames/{key_a}/test/cover.jpg'
    audio_b = f'private/frames/{key_b}/test/audio.mp3'
    database_url = f'http://{DATABASE_HOST}'
    storage_base = f'http://{STORAGE_HOST}'
    config = {
        'database_url': database_url,
        'database_namespace': namespace,
        'storage_bucket': BUCKET,
        'storage_base': storage_base,
    }

    seed_json(
        f'{database_url}/frames/{key_a}.json?ns={namespace}',
        {'slots': {'slot-0': {
            'id': 'local-song-a', 'kind': 'song', 'title': 'Pista local A',
            'artist': 'Prueba', 'audio_key': audio_a, 'image_key': image_a,
        }}, 'jobs': {'internal-test-job': {'status': 'secret-fixture'}}},
    )
    seed_json(
        f'{database_url}/frames/{key_b}.json?ns={namespace}',
        {'slots': {'slot-0': {
            'id': 'local-song-b', 'kind': 'song', 'title': 'Pista local B',
            'artist': 'Prueba', 'audio_key': audio_b,
        }}, 'jobs': {}},
    )
    seed_object(audio_a, AUDIO_A, 'audio/mpeg')
    seed_object(image_a, IMAGE_A, 'image/jpeg')
    seed_object(audio_b, AUDIO_B, 'audio/mpeg')

    slots_a = read_slots(config, identifier_a)
    slots_b = read_slots(config, identifier_b)
    if slots_a.get('slot-0', {}).get('title') != 'Pista local A':
        raise AssertionError('La lectura pública no devolvió la configuración del cuadro A.')
    if slots_b.get('slot-0', {}).get('title') != 'Pista local B':
        raise AssertionError('La lectura pública no devolvió la configuración del cuadro B.')
    if 'jobs' in slots_a:
        raise AssertionError('La ruta de lectura pública expuso tareas internas.')

    frames_url = f'{database_url}/frames.json?ns={namespace}'
    jobs_url = f'{database_url}/frames/{key_a}/jobs.json?ns={namespace}'
    if not denied(frames_url):
        raise AssertionError('RTDB permitió listar todos los cuadros.')
    if not denied(jobs_url):
        raise AssertionError('RTDB permitió leer tareas internas.')
    slots_url = f'{database_url}/frames/{key_a}/slots.json?ns={namespace}'
    if not denied(slots_url, method='PUT', body=b'{"public_write":true}'):
        raise AssertionError('RTDB permitió escritura pública.')

    direct_audio_url = (
        f'{storage_base}/v0/b/{quote(BUCKET, safe="")}/o/{quote(audio_a, safe="")}?alt=media'
    )
    list_url = f'{storage_base}/v0/b/{quote(BUCKET, safe="")}/o?{urlencode({"prefix": "private/frames/"})}'
    upload_url = f'{storage_base}/v0/b/{quote(BUCKET, safe="")}/o?uploadType=media&name={quote(audio_a, safe="")}'
    if not denied(list_url):
        raise AssertionError('Storage permitió listar objetos del bucket.')
    if not denied(upload_url, method='POST', body=b'forbidden', content_type='audio/mpeg'):
        raise AssertionError('Storage permitió escritura pública.')
    if request(direct_audio_url) != AUDIO_A:
        raise AssertionError('La URL directa de Storage no entregó el medio sin sesión.')

    with tempfile.TemporaryDirectory(prefix='sonoro-public-device-') as directory:
        output_a = Path(directory) / 'frame-a.mp3'
        output_b = Path(directory) / 'frame-b.mp3'
        result_a = read_slot(config, identifier_a, 0, output_a)
        result_b = read_slot(config, identifier_b, 0, output_b)
        if output_a.read_bytes() != AUDIO_A or output_b.read_bytes() != AUDIO_B:
            raise AssertionError('El cliente mezcló o no descargó los medios separados por cuadro.')
        if result_a['title'] != 'Pista local A' or result_b['title'] != 'Pista local B':
            raise AssertionError('El cliente no conservó la separación de configuración entre cuadros.')

    print('PASS: RTDB y Storage legibles sin sesión por URL conocida; listados/tareas y escrituras denegados; dos cuadros separados; cliente completó las lecturas con la API detenida.')


if __name__ == '__main__':
    try:
        run()
    except Exception as error:
        print(f'Fallo de prueba de emuladores: {error}', file=sys.stderr)
        raise SystemExit(1)
