"""Computer test client for the Firebase reads intended for the ESP32."""
import argparse
import getpass
import hashlib
import json
import os
import re
import stat
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


def request_json(url: str, *, method: str = 'GET', headers: dict | None = None, body: dict | None = None) -> dict:
    data = json.dumps(body).encode('utf-8') if body is not None else None
    request_headers = dict(headers or {})
    if data is not None:
        request_headers['Content-Type'] = 'application/json'
    try:
        with urlopen(Request(url, data=data, headers=request_headers, method=method), timeout=25) as response:
            payload = response.read()
            return json.loads(payload) if payload else {}
    except HTTPError as error:
        raise RuntimeError(f'Firebase devolvió HTTP {error.code}.') from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError('No se pudo completar la petición a Firebase.') from None


def request_bytes(url: str, headers: dict) -> bytes:
    try:
        with urlopen(Request(url, headers=headers), timeout=90) as response:
            return response.read()
    except HTTPError as error:
        raise RuntimeError(f'Firebase Storage devolvió HTTP {error.code}.') from None
    except (URLError, TimeoutError):
        raise RuntimeError('No se pudo descargar el medio desde Firebase Storage.') from None


def write_private(path: Path, value: dict, *, create: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if create else os.O_TRUNC)
    descriptor = os.open(temp, flags, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    os.replace(temp, path)
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def read_private(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def auth_url(config: dict, endpoint: str) -> str:
    return f"{config['auth_base'].rstrip('/')}/{endpoint}?key={quote(config['api_key'], safe='')}"


def sign_in(config: dict, frame_token: str) -> dict:
    expected = hashlib.sha256(frame_token.encode('utf-8')).hexdigest()
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,}', frame_token) or expected != config['frame_key']:
        raise ValueError('El token no corresponde a esta configuración de cuadro.')
    return request_json(
        auth_url(config, 'accounts:signInWithPassword'),
        method='POST',
        body={'email': config['email'], 'password': frame_token, 'returnSecureToken': True},
    )


def login(config_path: Path, state_path: Path) -> None:
    if state_path.exists():
        raise FileExistsError('El archivo de sesión ya existe; no se ha sobrescrito.')
    config = read_private(config_path)
    frame_token = getpass.getpass('Token fijo del cuadro: ')
    try:
        result = sign_in(config, frame_token)
        state = dict(config)
        state.update(
            frame_token=frame_token,
            id_token=result['idToken'],
            refresh_token=result['refreshToken'],
            expires_at=int(time.time()) + int(result['expiresIn']),
        )
        write_private(state_path, state, create=True)
    finally:
        del frame_token
    print('Sesión local creada. El token fijo del cuadro no cambia; la sesión Firebase se renueva automáticamente.')


def refresh(state: dict, force: bool = False) -> dict:
    if not force and int(state.get('expires_at', 0)) > int(time.time()) + 60:
        return state
    endpoint = f"{state['secure_token_base'].rstrip('/')}/token?key={quote(state['api_key'], safe='')}"
    payload = urlencode({'grant_type': 'refresh_token', 'refresh_token': state['refresh_token']}).encode('ascii')
    request = Request(endpoint, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    try:
        with urlopen(request, timeout=25) as response:
            result = json.loads(response.read())
    except HTTPError as error:
        if error.code in (400, 401):
            result = sign_in(state, state['frame_token'])
            state['id_token'] = result['idToken']
            state['refresh_token'] = result['refreshToken']
            state['expires_at'] = int(time.time()) + int(result['expiresIn'])
            return state
        raise RuntimeError(f'Firebase Auth devolvió HTTP {error.code} al renovar la sesión.') from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError('No se pudo renovar la sesión en Firebase Auth.') from None
    state['id_token'] = result['id_token']
    state['refresh_token'] = result.get('refresh_token', state['refresh_token'])
    state['expires_at'] = int(time.time()) + int(result.get('expires_in', 3600))
    return state


def add_query(url: str, values: dict) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(values)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ''))


def read_slots(state: dict) -> dict:
    url = f"{state['database_url'].rstrip('/')}/frames/{state['frame_key']}/slots.json"
    query = {'auth': state['id_token']}
    if state.get('database_namespace'):
        query['ns'] = state['database_namespace']
    return request_json(add_query(url, query)) or {}


def read_object(state: dict, key: str) -> bytes:
    encoded_key = quote(key, safe='')
    url = f"{state['storage_base'].rstrip('/')}/v0/b/{quote(state['storage_bucket'], safe='')}/o/{encoded_key}?alt=media"
    return request_bytes(url, {'Authorization': f"Firebase {state['id_token']}"})


def save_media(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)


def read_slot(state_path: Path, slot: int, output: Path, force_refresh: bool = False) -> None:
    if slot not in (0, 1, 2):
        raise ValueError('El hueco debe ser 0, 1 o 2.')
    state = read_private(state_path)
    old_expiry = int(state.get('expires_at', 0))
    old_id_token = state.get('id_token')
    state = refresh(state, force=force_refresh)
    renewed = state['id_token'] != old_id_token
    slots = read_slots(state)
    item = slots.get(f'slot-{slot}')
    if not item:
        raise RuntimeError('El cuadro no tiene una selección en ese hueco.')
    audio_key = item.get('audio_key')
    if not audio_key:
        raise RuntimeError('El hueco no tiene un medio de Storage para descargar.')
    audio = read_object(state, audio_key)
    save_media(output, audio)
    image_size = 0
    if item.get('image_key'):
        image = read_object(state, item['image_key'])
        image_suffix = Path(item['image_key']).suffix or '.img'
        save_media(output.with_name(output.stem + '.cover' + image_suffix), image)
        image_size = len(image)
    write_private(state_path, state)
    print(json.dumps({
        'slot': slot,
        'title': item.get('title', ''),
        'audio_bytes': len(audio),
        'image_bytes': image_size,
        'session_renewed': renewed or old_expiry <= int(time.time()) + 60,
    }, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description='Cliente de ordenador que simula lecturas directas del ESP32.')
    subparsers = parser.add_subparsers(dest='command', required=True)
    login_parser = subparsers.add_parser('login', help='Iniciar sesión con el token fijo del cuadro.')
    login_parser.add_argument('--config', type=Path, required=True)
    login_parser.add_argument('--state', type=Path, required=True)
    read_parser = subparsers.add_parser('read', help='Leer configuración y descargar medios de un hueco.')
    read_parser.add_argument('--state', type=Path, required=True)
    read_parser.add_argument('--slot', type=int, default=0)
    read_parser.add_argument('--out', type=Path, required=True)
    read_parser.add_argument('--force-refresh', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'login':
            login(args.config, args.state)
        else:
            read_slot(args.state, args.slot, args.out, args.force_refresh)
    except (OSError, ValueError, KeyError, RuntimeError, json.JSONDecodeError) as error:
        print(f'Lectura no completada: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
