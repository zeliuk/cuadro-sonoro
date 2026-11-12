"""Provision the existing per-frame token as a read-only Firebase device account."""
import argparse
import getpass
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def frame_key_for(token: str) -> str:
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,}', token):
        raise ValueError('El token del cuadro no tiene el formato esperado.')
    frame_key = hashlib.sha256(token.encode('utf-8')).hexdigest()
    allowed = {
        item.strip().lower()
        for item in os.getenv('FRAME_TOKEN_HASHES', '').split(',')
        if re.fullmatch(r'[0-9a-fA-F]{64}', item.strip())
    }
    if frame_key not in allowed:
        raise ValueError('El hash del cuadro no está incluido en FRAME_TOKEN_HASHES.')
    return frame_key


def write_private(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2)
        stream.write('\n')


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Relaciona el token existente del cuadro con una cuenta Firebase de solo lectura.'
    )
    parser.add_argument('--output', type=Path, default=Path('device-private/device-config.json'))
    parser.add_argument('--env-file', type=Path, default=Path('backend/.env'))
    args = parser.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(args.env_file, override=False)
        frame_token = getpass.getpass('Token fijo del cuadro: ')
        frame_key = frame_key_for(frame_token)
        api_key = os.getenv('FIREBASE_WEB_API_KEY', '').strip()
        required = ('FIREBASE_DATABASE_URL', 'FIREBASE_STORAGE_BUCKET')
        missing = [name for name in required if not os.getenv(name, '').strip()]
        if missing or not api_key:
            raise ValueError('Completa FIREBASE_DATABASE_URL, FIREBASE_STORAGE_BUCKET y FIREBASE_WEB_API_KEY en el entorno privado.')
        from backend.firebase_client import firebase
        from firebase_admin import auth

        app = firebase()
        project_id = app.project_id or os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCLOUD_PROJECT')
        if not project_id:
            raise ValueError('No se pudo determinar el project_id Firebase.')
        uid = 'frame-reader-' + frame_key
        email = f'device-{frame_key[:32]}@sonoro.example'
        try:
            auth.update_user(uid, email=email, password=frame_token, disabled=False, app=app)
        except auth.UserNotFoundError:
            auth.create_user(uid=uid, email=email, password=frame_token, app=app)

        auth_emulator = os.getenv('FIREBASE_AUTH_EMULATOR_HOST', '').strip()
        storage_emulator = os.getenv('FIREBASE_STORAGE_EMULATOR_HOST', '').strip()
        config = {
            'project_id': project_id,
            'api_key': api_key,
            'uid': uid,
            'frame_key': frame_key,
            'email': email,
            'database_url': os.environ['FIREBASE_DATABASE_URL'].rstrip('/'),
            'storage_bucket': os.environ['FIREBASE_STORAGE_BUCKET'],
            'auth_base': f'http://{auth_emulator}/identitytoolkit.googleapis.com/v1' if auth_emulator else 'https://identitytoolkit.googleapis.com/v1',
            'secure_token_base': f'http://{auth_emulator}/securetoken.googleapis.com/v1' if auth_emulator else 'https://securetoken.googleapis.com/v1',
            'storage_base': f'http://{storage_emulator}' if storage_emulator else 'https://firebasestorage.googleapis.com',
        }
        write_private(args.output, config)
    except FileExistsError:
        print('El archivo de configuración ya existe; no se ha sobrescrito.', file=sys.stderr)
        return 2
    except (KeyError, ValueError, OSError) as error:
        print(f'Aprovisionamiento no completado: {error}', file=sys.stderr)
        return 2
    finally:
        if 'frame_token' in locals():
            del frame_token
    print(f'Cuenta Firebase del cuadro preparada. Configuración privada guardada en {args.output}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
