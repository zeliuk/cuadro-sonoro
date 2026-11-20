"""Direct, unauthenticated Firebase reader representing the ESP32."""
import argparse
import getpass
import ipaddress
import json
import os
import socket
import stat
import sys
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.identity import frame_key_for


def request_json(url: str) -> dict:
    try:
        with urlopen(Request(url), timeout=25) as response:
            payload = response.read()
            return json.loads(payload) if payload else {}
    except HTTPError as error:
        raise RuntimeError(f'Firebase RTDB devolvió HTTP {error.code}.') from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError('No se pudo leer la configuración desde Firebase RTDB.') from None


def request_bytes(url: str, max_bytes: Optional[int] = None) -> bytes:
    try:
        with urlopen(Request(url), timeout=90) as response:
            payload = response.read(max_bytes + 1) if max_bytes else response.read()
            if max_bytes and len(payload) > max_bytes:
                raise RuntimeError('El medio supera el tamaño máximo permitido para la descarga.')
            return payload
    except HTTPError as error:
        raise RuntimeError(f'Firebase Storage devolvió HTTP {error.code}.') from None
    except (URLError, TimeoutError):
        raise RuntimeError('No se pudo descargar el medio desde Firebase Storage.') from None


def _public_https_url(url: str) -> str:
    parsed = urlparse(url or '')
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError('La URL del favicon no es HTTPS pública.')
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise RuntimeError('El favicon apunta a una red no pública.')
    except (socket.gaierror, ValueError):
        raise RuntimeError('No se pudo validar el destino del favicon.') from None
    return url


class _SafeImageRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        _public_https_url(new_url)
        return super().redirect_request(request, fp, code, message, headers, new_url)


def request_public_image(url: str, max_bytes: int = 2 * 1024 * 1024) -> tuple[bytes, str]:
    """Fetch an HTTPS favicon only from public hosts, including each redirect."""
    _public_https_url(url)
    request = Request(url, headers={
        'User-Agent': 'CuadroSonoro/0.1 (desktop simulator)',
        'Accept': 'image/*',
    })
    try:
        with build_opener(_SafeImageRedirect()).open(request, timeout=20) as response:
            content_type = response.headers.get_content_type().lower()
            suffix = Path(urlparse(response.geturl()).path).suffix.lower()
            raster_suffixes = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tga', '.psd', '.pic'}
            if not content_type.startswith('image/') and suffix not in raster_suffixes and suffix != '.ico':
                raise RuntimeError('La URL de favicon no devolvió una imagen.')
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise RuntimeError('El favicon supera el tamaño máximo permitido.')
            return payload, content_type
    except HTTPError as error:
        raise RuntimeError(f'El servidor del favicon respondió HTTP {error.code}.') from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError('No se pudo descargar el favicon de la emisora.') from None


def load_config(path: Path) -> dict:
    try:
        config = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        raise ValueError('No se pudo leer el archivo de conexión pública Firebase.') from None
    for field in ('database_url', 'storage_bucket'):
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise ValueError(f'Falta {field} en la configuración pública Firebase.')
    config.setdefault('storage_base', 'https://firebasestorage.googleapis.com')
    config['database_url'] = config['database_url'].rstrip('/')
    config['storage_base'] = config['storage_base'].rstrip('/')
    return config


def read_slots(config: dict, identifier: str) -> dict:
    frame_key = frame_key_for(identifier)
    url = f"{config['database_url']}/frames/{frame_key}/slots.json"
    query = {}
    if config.get('database_namespace'):
        query['ns'] = config['database_namespace']
    if query:
        url += '?' + urlencode(query)
    return request_json(url) or {}


def media_url(config: dict, object_key: str) -> str:
    bucket = quote(config['storage_bucket'], safe='')
    key = quote(object_key, safe='')
    return f"{config['storage_base']}/v0/b/{bucket}/o/{key}?alt=media"


def save_media(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def selection_from_slots(slots: dict, slot: int, require_song: bool = True) -> dict:
    """Validate and extract one published song or station from an RTDB slots map."""
    if slot not in (0, 1, 2):
        raise ValueError('El hueco debe ser 0, 1 o 2.')
    if not isinstance(slots, dict):
        raise RuntimeError('La configuración publicada en Firebase no tiene un formato válido.')
    item = slots.get(f'slot-{slot}')
    if not item:
        raise RuntimeError('El cuadro no tiene una selección en ese hueco.')
    if not isinstance(item, dict):
        raise RuntimeError('La selección publicada en Firebase no tiene un formato válido.')
    kind = item.get('kind', 'song')
    if require_song and kind != 'song':
        raise RuntimeError('El hueco elegido no contiene una canción.')
    if kind == 'station':
        if not isinstance(item.get('url'), str) or not item['url'].startswith('https://'):
            raise RuntimeError('La emisora no tiene una dirección HTTPS publicada.')
        return {
            'slot': slot,
            'kind': 'station',
            'title': item.get('title', ''),
            'artist': item.get('artist', 'Radio en directo'),
            'favicon': item.get('favicon'),
            'url': item['url'],
        }
    if kind != 'song' or not item.get('audio_key'):
        raise RuntimeError('La canción no tiene un medio de audio publicado.')
    return {
        'slot': slot,
        'kind': 'song',
        'title': item.get('title', ''),
        'artist': item.get('artist', ''),
        'image_key': item.get('image_key'),
        'audio_key': item['audio_key'],
    }


def read_selection(config: dict, identifier: str, slot: int, require_song: bool = True) -> dict:
    """Read one published song record from RTDB without downloading its audio."""
    return selection_from_slots(read_slots(config, identifier), slot, require_song)


def read_slot(config: dict, identifier: str, slot: int, output: Path) -> dict:
    item = read_selection(config, identifier, slot)
    audio = request_bytes(media_url(config, item['audio_key']))
    save_media(output, audio)
    image_size = 0
    if item['image_key']:
        image = request_bytes(media_url(config, item['image_key']))
        suffix = Path(item['image_key']).suffix or '.img'
        save_media(output.with_name(output.stem + '.cover' + suffix), image)
        image_size = len(image)
    return {
        'slot': slot,
        'title': item['title'],
        'artist': item['artist'],
        'audio_bytes': len(audio),
        'image_bytes': image_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Cliente de ordenador para lectura pública directa, como el futuro ESP32.')
    read_parser = parser.add_subparsers(dest='command', required=True).add_parser(
        'read', help='Leer un hueco de RTDB y descargar sus medios de Storage sin sesión.'
    )
    read_parser.add_argument('--config', type=Path, required=True, help='Configuración pública de conexión Firebase.')
    read_parser.add_argument('--slot', type=int, default=0)
    read_parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        identifier = getpass.getpass('Identificador fijo del cuadro: ')
        result = read_slot(config, identifier, args.slot, args.out)
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f'Lectura no completada: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
