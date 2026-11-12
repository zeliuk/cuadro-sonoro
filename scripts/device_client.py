"""Direct, unauthenticated Firebase reader representing the ESP32."""
import argparse
import getpass
import json
import os
import stat
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

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


def request_bytes(url: str) -> bytes:
    try:
        with urlopen(Request(url), timeout=90) as response:
            return response.read()
    except HTTPError as error:
        raise RuntimeError(f'Firebase Storage devolvió HTTP {error.code}.') from None
    except (URLError, TimeoutError):
        raise RuntimeError('No se pudo descargar el medio desde Firebase Storage.') from None


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


def read_slot(config: dict, identifier: str, slot: int, output: Path) -> dict:
    if slot not in (0, 1, 2):
        raise ValueError('El hueco debe ser 0, 1 o 2.')
    slots = read_slots(config, identifier)
    item = slots.get(f'slot-{slot}')
    if not item:
        raise RuntimeError('El cuadro no tiene una selección en ese hueco.')
    audio_key = item.get('audio_key')
    if not audio_key:
        raise RuntimeError('El hueco no contiene una canción con medio en Storage.')
    audio = request_bytes(media_url(config, audio_key))
    save_media(output, audio)
    image_size = 0
    if item.get('image_key'):
        image = request_bytes(media_url(config, item['image_key']))
        suffix = Path(item['image_key']).suffix or '.img'
        save_media(output.with_name(output.stem + '.cover' + suffix), image)
        image_size = len(image)
    return {
        'slot': slot,
        'title': item.get('title', ''),
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
