"""Exercise device-scoped Firebase reads against the local Auth/RTDB/Storage emulators."""
import hashlib
import json
import os
import base64
import secrets
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from device_client import read_object, read_slots, request_json, sign_in, write_private


PROJECT = 'demo-sonoro-device'
AUTH_HOST = '127.0.0.1:9099'
DATABASE_HOST = '127.0.0.1:9000'
STORAGE_HOST = '127.0.0.1:9199'
BUCKET = f'{PROJECT}.appspot.com'
API_KEY = 'fake-device-test-api-key'
AUDIO = b'local-test-audio-frame-a'
IMAGE = b'local-test-image-frame-a'


def require_emulators() -> None:
    expected = {
        'FIREBASE_AUTH_EMULATOR_HOST': AUTH_HOST,
        'FIREBASE_DATABASE_EMULATOR_HOST': DATABASE_HOST,
        'FIREBASE_STORAGE_EMULATOR_HOST': STORAGE_HOST,
    }
    if any(os.getenv(name) != value for name, value in expected.items()):
        raise RuntimeError('Inicia este script solo con los emuladores locales Auth, Database y Storage.')


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def emulator_custom_token(uid: str) -> str:
    now = int(time.time())
    header = b64url(json.dumps({'alg': 'none', 'typ': 'JWT'}, separators=(',', ':')).encode())
    claims = {
        'iss': f'emulator-seed@{PROJECT}.iam.gserviceaccount.com',
        'sub': f'emulator-seed@{PROJECT}.iam.gserviceaccount.com',
        'aud': 'https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit',
        'iat': now, 'exp': now + 3600, 'uid': uid,
    }
    body = b64url(json.dumps(claims, separators=(',', ':')).encode())
    return f'{header}.{body}.'


def emulator_sign_in(custom_token: str) -> dict:
    return request_json(
        f'http://{AUTH_HOST}/identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}',
        method='POST',
        body={'token': custom_token, 'returnSecureToken': True},
    )


def create_auth_users(users: list[tuple[str, str, str]]) -> None:
    for uid, email, password in users:
        initial = emulator_sign_in(emulator_custom_token(uid))
        request_json(
            f'http://{AUTH_HOST}/identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEY}',
            method='POST',
            body={'idToken': initial['idToken'], 'email': email, 'password': password, 'returnSecureToken': True},
        )


def admin_json(url: str, *, method='PUT', body=None, content_type='application/json'):
    payload = json.dumps(body).encode() if isinstance(body, dict) else body
    headers = {'Content-Type': content_type}
    if urlsplit(url).netloc in (STORAGE_HOST, DATABASE_HOST):
        headers['Authorization'] = 'Bearer owner'
    request = Request(
        url,
        data=payload,
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=20) as response:
        raw = response.read()
        return json.loads(raw) if raw and content_type == 'application/json' else raw


def denied(url: str, headers: dict | None = None, *, method='GET', body=None) -> bool:
    try:
        with urlopen(Request(url, data=body, headers=headers or {}, method=method), timeout=20):
            return False
    except HTTPError as error:
        return error.code in (401, 403)


def run() -> None:
    require_emulators()
    from device_client import add_query

    frame_token_a = 'device-frame-a-' + secrets.token_urlsafe(24)
    frame_token_b = 'device-frame-b-' + secrets.token_urlsafe(24)
    key_a, key_b = (hashlib.sha256(token.encode()).hexdigest() for token in (frame_token_a, frame_token_b))
    uid_a, uid_b = f'frame-reader-{key_a}', f'frame-reader-{key_b}'
    email_a, email_b = f'device-{key_a[:32]}@sonoro.example', f'device-{key_b[:32]}@sonoro.example'
    object_audio = f'private/frames/{key_a}/emulator-audio.mp3'
    object_image = f'private/frames/{key_a}/emulator-cover.jpg'
    try:
        create_auth_users([
            (uid_a, email_a, frame_token_a),
            (uid_b, email_b, frame_token_b),
        ])
    except Exception as error:
        raise RuntimeError(f'No se pudieron preparar usuarios Auth de emulador ({type(error).__name__}).') from None

    namespace = PROJECT + '-default-rtdb'
    db_root = f'http://{DATABASE_HOST}/frames/{key_a}.json?ns={namespace}'
    try:
        admin_json(db_root, body={'slots': {'slot-0': {
            'id': 'emulator-song-a', 'kind': 'song', 'title': 'Pista de prueba A',
            'artist': 'Emulador', 'audio_key': object_audio, 'image_key': object_image,
        }}, 'jobs': {}})
        admin_json(db_root.replace(key_a, key_b), body={'slots': {'slot-0': {
            'id': 'emulator-song-b', 'kind': 'song', 'title': 'Pista de prueba B',
            'artist': 'Emulador', 'audio_key': f'private/frames/{key_b}/b.mp3',
        }}, 'jobs': {}})
    except Exception as error:
        raise RuntimeError(f'No se pudo sembrar RTDB en emulador ({type(error).__name__}).') from None

    storage_base = f'http://{STORAGE_HOST}'
    try:
        for object_key, content, mime in (
            (object_audio, AUDIO, 'audio/mpeg'), (object_image, IMAGE, 'image/jpeg'),
        ):
            url = f'{storage_base}/upload/storage/v1/b/{quote(BUCKET, safe="")}/o?uploadType=media&name={quote(object_key, safe="")}'
            admin_json(url, method='POST', body=content, content_type=mime)
    except Exception as error:
        raise RuntimeError(f'No se pudo sembrar Storage en emulador ({type(error).__name__}).') from None

    auth_base = f'http://{AUTH_HOST}/identitytoolkit.googleapis.com/v1'
    config_a = {
        'project_id': PROJECT, 'api_key': API_KEY, 'uid': uid_a, 'email': email_a,
        'frame_key': key_a, 'database_url': f'http://{DATABASE_HOST}', 'database_namespace': namespace,
        'storage_bucket': BUCKET, 'storage_base': storage_base,
        'auth_base': auth_base, 'secure_token_base': f'http://{AUTH_HOST}/securetoken.googleapis.com/v1',
    }
    config_b = {**config_a, 'uid': uid_b, 'email': email_b, 'frame_key': key_b}
    session_a = sign_in(config_a, frame_token_a)
    session_b = sign_in(config_b, frame_token_b)
    state_a = {
        **config_a, 'frame_token': frame_token_a, 'id_token': session_a['idToken'],
        'refresh_token': session_a['refreshToken'], 'expires_at': 0,
    }
    state_b = {
        **config_b, 'frame_token': frame_token_b, 'id_token': session_b['idToken'],
        'refresh_token': session_b['refreshToken'], 'expires_at': int(session_b['expiresIn']),
    }

    own_slots = read_slots(state_a)
    if own_slots.get('slot-0', {}).get('title') != 'Pista de prueba A':
        raise AssertionError('El dispositivo no leyó la configuración de su cuadro.')
    other_url = add_query(
        f"{config_a['database_url']}/frames/{key_a}/slots.json",
        {'ns': namespace, 'auth': state_b['id_token']},
    )
    if not denied(other_url):
        raise AssertionError('Firebase permitió leer el cuadro A con la sesión del cuadro B.')
    unauth_url = add_query(f"{config_a['database_url']}/frames/{key_a}/slots.json", {'ns': namespace})
    if not denied(unauth_url):
        raise AssertionError('Firebase permitió una lectura sin sesión Firebase.')
    own_url = add_query(
        f"{config_a['database_url']}/frames/{key_a}/slots.json",
        {'ns': namespace, 'auth': state_a['id_token']},
    )
    if not denied(own_url, method='PUT', body=b'{"unauthorized_write":true}'):
        raise AssertionError('Firebase permitió escribir datos usando la sesión de solo lectura.')

    if read_object(state_a, object_audio) != AUDIO:
        raise AssertionError('No se descargaron los bytes esperados del audio propio.')
    if not denied(
        f'{storage_base}/v0/b/{quote(BUCKET, safe="")}/o/{quote(object_audio, safe="")}?alt=media',
        {'Authorization': f"Firebase {state_b['id_token']}"},
    ):
        raise AssertionError('Firebase Storage permitió al cuadro B leer el medio del cuadro A.')
    if not denied(f'{storage_base}/v0/b/{quote(BUCKET, safe="")}/o/{quote(object_audio, safe="")}?alt=media'):
        raise AssertionError('Firebase Storage permitió descargar medios sin sesión Firebase.')
    upload_url = f'{storage_base}/v0/b/{quote(BUCKET, safe="")}/o?uploadType=media&name={quote(object_audio, safe="")}'
    if not denied(
        upload_url,
        {'Authorization': f"Firebase {state_a['id_token']}", 'Content-Type': 'audio/mpeg'},
        method='POST', body=b'forbidden-write',
    ):
        raise AssertionError('Firebase Storage permitió escribir medios con la sesión de solo lectura.')

    with tempfile.TemporaryDirectory(prefix='sonoro-device-client-') as directory:
        state_path = Path(directory) / 'device-session.json'
        output = Path(directory) / 'audio.mp3'
        write_private(state_path, state_a, create=True)
        from device_client import read_slot
        read_slot(state_path, 0, output, force_refresh=True)
        persisted = json.loads(state_path.read_text())
        if persisted['frame_token'] != frame_token_a or persisted['expires_at'] < int(time.time()) + 300:
            raise AssertionError('La sesión no renovó el ID token conservando el Bearer fijo del cuadro.')
        if output.read_bytes() != AUDIO:
            raise AssertionError('El cliente de prueba no guardó el medio propio completo.')

    print('PASS: lectura propia de RTDB y Storage; rechazo cruzado, sin sesión y en escrituras; renovación Firebase forzada sin API Render; Bearer de cuadro original conservado.')


if __name__ == '__main__':
    try:
        run()
    except Exception as error:
        print(f'Fallo de prueba de emuladores: {error}', file=sys.stderr)
        raise SystemExit(1)
