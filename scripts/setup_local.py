"""Create local-only development settings without overwriting existing secrets."""
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / 'backend' / '.env'
    template = root / 'backend' / '.env.example'
    if target.exists():
        print('backend/.env ya existe; se conserva sin mostrar sus valores.')
        return
    contents = template.read_text(encoding='utf-8')
    # Exclusive create protects an existing file even if another process created it.
    with target.open('x', encoding='utf-8') as output:
        target.chmod(0o600)
        output.write(contents)
    print('Configuración local creada. Firebase permanece sin configurar; no se muestran secretos.')


if __name__ == '__main__':
    main()
