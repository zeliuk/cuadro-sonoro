#!/usr/bin/env python3
"""Limited, redacted check of staged or tracked content; not a history scanner."""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import PurePosixPath


PRIVATE_PATTERNS = (
    ('clave privada', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----')),
    ('token de proveedor', re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16})\b')),
    ('URL de acceso temporal', re.compile(r'[?&](?:X-Goog-Signature|X-Amz-Signature|token)=[A-Za-z0-9%_-]{24,}', re.I)),
)
DOTENV_SECRET = re.compile(r'''(?im)^[ \t]*(?:export[ \t]+)?(?:FRAME_TOKEN_HASHES|LOCAL_FRAME_TOKEN|IMPORT_API_TOKEN|FIREBASE_SERVICE_ACCOUNT_JSON|GH_TOKEN|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY)[ \t]*[:=][ \t]*["']?([^\r\n#]*)''')
CODE_SECRET = re.compile(r'''(?im)["'](?:FRAME_TOKEN_HASHES|LOCAL_FRAME_TOKEN|IMPORT_API_TOKEN|GH_TOKEN|GITHUB_TOKEN)["']\]?\s*[:=]\s*["']([^"'\r\n]+)["']''')
TEST_VALUES = {'test-token-only', 'test-only', 'CHANGE_ME', 'YOUR_TOKEN', 'YOUR_SECRET'}
PRIVATE_DIRS = {'secrets', 'credentials', '.aws', '.ssh', 'downloads', 'runtime-data'}


def sensitive_path(path: str) -> bool:
    p = PurePosixPath(path)
    name = p.name.lower()
    if any(part.lower() in PRIVATE_DIRS for part in p.parts):
        return True
    if name != '.env.example' and (name in {'.env', '.envrc'} or name.startswith('.env.') or name.endswith('.env')):
        return True
    if name == '.firebaserc' or name in {'.netrc', '.npmrc', '.pypirc', 'google-services.json', 'googleservice-info.plist'}:
        return True
    if p.suffix.lower() in {'.pem', '.key', '.p12', '.pfx', '.jks', '.sqlite3', '.db', '.log', '.mp3', '.wav', '.flac', '.aac', '.m4a', '.mp4', '.webm'}:
        return True
    if name.startswith('cookies') and name.endswith('.txt'):
        return True
    if name.endswith('.json') and any(x in name for x in ('service-account', 'service_account', 'serviceaccount', 'firebase-adminsdk', 'credentials')):
        return True
    return False


def findings(path: str, data: bytes):
    if sensitive_path(path):
        yield 'archivo de configuración, credenciales o datos privados'
    text = data.decode('utf-8', errors='replace')
    for label, pattern in PRIVATE_PATTERNS:
        if pattern.search(text):
            yield label
    if re.search(r'"type"\s*:\s*"service_account"', text) and re.search(r'"private_key"\s*:', text):
        yield 'JSON de cuenta de servicio'
    for pattern in (DOTENV_SECRET, CODE_SECRET):
        for match in pattern.finditer(text):
            value = match.group(1).strip().strip('"\'').strip()
            if value and value not in TEST_VALUES and not (value.startswith('<') and value.endswith('>')):
                yield 'posible secreto literal en configuración'
                break


def git(*args):
    return subprocess.check_output(['git', *args], stderr=subprocess.DEVNULL)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--staged', action='store_true', help='revisar los blobs preparados para commit')
    mode.add_argument('--tracked', action='store_true', help='revisar los archivos actuales del índice Git')
    args = parser.parse_args(argv)
    try:
        if args.staged:
            raw = git('diff', '--cached', '--name-only', '--diff-filter=ACMRT', '-z')
        else:
            raw = git('ls-files', '-z')
        paths = sorted(set(p.decode('utf-8') for p in raw.split(b'\0') if p))
        errors = []
        for path in paths:
            # Read index blobs rather than a potentially modified working tree.
            content = git('show', ':' + path)
            for label in sorted(set(findings(path, content))):
                errors.append(f'{path}: {label}')
    except (subprocess.CalledProcessError, UnicodeError):
        print('No se pudo revisar el índice Git. Ejecuta desde la raíz de un repositorio válido.', file=sys.stderr)
        return 2
    if errors:
        print('Revisar antes de publicar (valores omitidos):', file=sys.stderr)
        for error in errors:
            print(' - ' + error, file=sys.stderr)
        return 1
    if not paths:
        print('No hay archivos para revisar en este modo. Esto no valida el historial ni futuros commits.')
    else:
        print(f'Control básico: {len(paths)} archivos del índice sin hallazgos de estos patrones. No analiza historial ni detecta todos los secretos.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
