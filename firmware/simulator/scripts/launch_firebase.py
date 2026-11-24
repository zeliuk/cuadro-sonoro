#!/usr/bin/env python3
"""Load published songs directly from Firebase and show them in the SDL view."""
import argparse
import getpass
import json
import queue
import subprocess
import sys
import threading
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts import device_client


MAX_COVER_BYTES = 2 * 1024 * 1024
DEFAULT_SIMULATOR = ROOT / 'firmware/simulator/build-lvgl95/cuadro-sonoro'
if not DEFAULT_SIMULATOR.is_file():
    for alternate in (ROOT / 'firmware/simulator/build/cuadro-sonoro',
                      ROOT / 'firmware/simulator/build-run/cuadro-sonoro'):
        if alternate.is_file():
            DEFAULT_SIMULATOR = alternate
            break


def prepare_snapshot(config: dict, identifier: str, slots: dict, temporary: Path,
                     simulator: Path) -> tuple[str, list[str], int]:
    """Download current cover art and build the SDL command for a slot snapshot."""
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

    qr_path = temporary / 'qr-url.txt'
    device_client.save_media(
        qr_path,
        f"https://sonoro.zeliuk.xyz/#token={identifier}".encode('ascii'),
    )
    command = [str(simulator.resolve()), '--firebase-data', str(qr_path)]
    for slot, selection, image, suffix in selections:
        image_path = '-'
        if image:
            image_path = str(temporary / f'imagen-slot-{slot}{suffix}')
            device_client.save_media(Path(image_path), image)
        command.extend([
            str(slot), selection['kind'], image_path,
            selection.get('title') or 'Sin título',
            selection.get('artist') or 'Artista desconocido',
        ])
    return json.dumps(slots, sort_keys=True, ensure_ascii=False), command, len(selections)


def watch_firebase(config: dict, identifier: str, updates: queue.Queue,
                   stop: threading.Event) -> None:
    """Keep an RTDB SSE listener alive and back off when connectivity is lost."""
    retry_seconds = 1
    while not stop.is_set():
        connected_at = time.monotonic()
        try:
            for slots in device_client.iter_slot_updates(config, identifier):
                if stop.is_set():
                    return
                updates.put(('slots', slots))
            if stop.is_set():
                return
            raise RuntimeError('Firebase cerró el flujo de cambios.')
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            updates.put(('error', str(error)))
            stop.wait(retry_seconds)
            if time.monotonic() - connected_at >= 10:
                retry_seconds = 1
            else:
                retry_seconds = min(retry_seconds * 2, 30)


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
        with tempfile.TemporaryDirectory(prefix='cuadro-sonoro-firebase-') as temporary:
            temporary_path = Path(temporary)
            snapshot, command, count = prepare_snapshot(
                config, identifier, slots, temporary_path, args.simulator
            )
            updates = queue.Queue()
            stop = threading.Event()
            watcher = threading.Thread(
                target=watch_firebase,
                args=(config, identifier, updates, stop),
                name='firebase-slots-listener',
                daemon=True,
            )
            watcher.start()
            print('Escuchando cambios de los tres huecos en Firebase RTDB.')
            if not count:
                print('Los tres huecos están vacíos; QR persistente visible.')
            process = subprocess.Popen(command, cwd=ROOT)
            try:
                while process.poll() is None:
                    try:
                        kind, update = updates.get(timeout=0.25)
                    except queue.Empty:
                        continue
                    if kind == 'error':
                        print(f'{update} Se reintentará conectar.', file=sys.stderr)
                        continue
                    latest_slots = update
                    latest_snapshot = json.dumps(latest_slots, sort_keys=True, ensure_ascii=False)
                    if latest_snapshot == snapshot:
                        continue

                    try:
                        next_snapshot, next_command, next_count = prepare_snapshot(
                            config, identifier, latest_slots, temporary_path, args.simulator
                        )
                    except (OSError, ValueError, RuntimeError, KeyError) as error:
                        print(f'Cambió Firebase, pero no se pudieron preparar los medios; se conserva la vista: {error}',
                              file=sys.stderr)
                        continue

                    process.terminate()
                    process.wait()
                    snapshot, command, count = next_snapshot, next_command, next_count
                    process = subprocess.Popen(command, cwd=ROOT)
                    if count:
                        print(f'Estado actualizado ({count} selección(es)); ventana reiniciada.')
                    else:
                        print('Los tres huecos vuelven a estar vacíos; se muestra el QR.')
                return process.wait()
            except KeyboardInterrupt:
                return_code = 130
                return return_code
            finally:
                stop.set()
                if process.poll() is None:
                    process.terminate()
                    process.wait()
                watcher.join(timeout=2)
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f'No se pudo cargar la selección desde Firebase: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
