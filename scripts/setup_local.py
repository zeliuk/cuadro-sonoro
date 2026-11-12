"""Create local-only development settings without overwriting existing secrets."""
from pathlib import Path
import secrets


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / 'backend' / '.env'
    template = root / 'backend' / '.env.example'
    if target.exists():
        print('backend/.env ya existe; se conserva sin mostrar sus valores.')
        return
    lines = template.read_text(encoding='utf-8').splitlines()
    for index, line in enumerate(lines):
        if line == 'IMPORT_API_TOKEN=':
            lines[index] = line + secrets.token_urlsafe(32)
    contents = '\n'.join(lines) + '\n'
    # Exclusive create protects an existing file even if another process created it.
    with target.open('x', encoding='utf-8') as output:
        target.chmod(0o600)
        output.write(contents)
    print('Configuración local creada. Firebase permanece sin configurar; no se muestran secretos.')


if __name__ == '__main__':
    main()
