#!/usr/bin/env python3
"""Load published songs directly from Firebase and show them in the SDL view."""
import argparse
import getpass
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts import device_client


MAX_COVER_BYTES = 2 * 1024 * 1024
DEFAULT_SIMULATOR = ROOT / 'firmware/simulator/build/cuadro-sonoro'
if not DEFAULT_SIMULATOR.is_file():
    alternate = ROOT / 'firmware/simulator/build-run/cuadro-sonoro'
    if alternate.is_file():
        DEFAULT_SIMULATOR = alternate


def main() -> int:
    parser = argparse.ArgumentParser(description='Consulta RTDB y Storage y abre la vista LVGL de escritorio.')
    parser.add_argument('--config', type=Path, default=ROOT / 'firebase/device-config.json',
                        help='Configuración pública local de RTDB y Storage.')
    parser.add_argument('--simulator', type=Path, default=DEFAULT_SIMULATOR,
                        help='Ejecutable SDL ya compilado.')
    args = parser.parse_args()

    try:
        config = device_client.load_config(args.config)
        identifier = getpass.getpass('Identificador fijo del cuadro: ')
        if not args.simulator.is_file():
            raise RuntimeError(f'No se encuentra el simulador compilado: {args.simulator}')

        slots = device_client.read_slots(config, identifier)
        selections = []
        for slot in range(3):
            item = slots.get(f'slot-{slot}') if isinstance(slots, dict) else None
            if not item:
                continue
            selection = device_client.selection_from_slots(slots, slot, require_song=False)
            if selection['kind'] == 'station':
                icon = None
                if selection.get('favicon'):
                    try:
                        icon, _content_type = device_client.request_public_image(
                            selection['favicon'], max_bytes=MAX_COVER_BYTES
                        )
                    except RuntimeError:
                        icon = None
                selections.append((slot, selection, icon, '.favicon'))
                continue

            image_key = selection.get('image_key')
            if not image_key:
                continue
            suffix = Path(image_key).suffix.lower()
            if suffix not in ('.jpg', '.jpeg'):
                continue
            cover = device_client.request_bytes(
                device_client.media_url(config, image_key), max_bytes=MAX_COVER_BYTES
            )
            selections.append((slot, selection, cover, suffix))
        if not selections:
            raise RuntimeError('No hay canciones con carátula o emisoras publicadas en los tres huecos.')

        with tempfile.TemporaryDirectory(prefix='cuadro-sonoro-firebase-') as temporary:
            qr_path = Path(temporary) / 'qr-url.txt'
            device_client.save_media(
                qr_path,
                f"https://sonoro.zeliuk.xyz/#token={identifier}".encode('ascii'),
            )
            command = [str(args.simulator.resolve()), '--firebase-data', str(qr_path)]
            for slot, selection, image, suffix in selections:
                image_path = '-'
                if image:
                    image_path = str(Path(temporary) / f'imagen-slot-{slot}{suffix}')
                    device_client.save_media(Path(image_path), image)
                command.extend([
                    str(slot), selection['kind'], image_path,
                    selection.get('title') or 'Sin título',
                    selection.get('artist') or 'Artista desconocido',
                ])
            print(f'{len(selections)} selección(es) de canción/radio cargadas directamente de Firebase.')
            return subprocess.run(
                command,
                cwd=ROOT,
                check=False,
            ).returncode
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f'No se pudo cargar la selección desde Firebase: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
