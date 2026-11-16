#!/usr/bin/env python3
"""Generate a QR opening Sonoro's public configuration web page."""
import argparse
import re
from pathlib import Path

PUBLIC_ORIGIN = 'https://sonoro.zeliuk.xyz'
TOKEN_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--token', default='cuadro-demo', help='ID del cuadro (por defecto, ficticio)')
    parser.add_argument('--output', help='PNG de salida; para un ID asignado, usa un nombre de archivo genérico')
    args = parser.parse_args()
    if not TOKEN_RE.fullmatch(args.token):
        parser.error('identificador no válido: 1–128 caracteres ASCII alfanuméricos, guion o guion bajo')
    if args.token != 'cuadro-demo' and not args.output:
        parser.error('indica --output con un nombre genérico cuando uses un ID asignado')

    try:
        import qrcode
    except ImportError:
        parser.error('falta qrcode: instala con python3 -m pip install "qrcode[pil]"')

    target = Path(args.output or 'artifacts/qr/sonoro-cuadro-demo.png')
    target.parent.mkdir(parents=True, exist_ok=True)
    url = PUBLIC_ORIGIN + '/#token=' + args.token
    qrcode.make(url).save(target)
    print('QR público guardado en: ' + str(target))
    if args.token == 'cuadro-demo':
        print('Enlace ficticio/de prueba: ' + url)
    else:
        print('QR generado para el identificador indicado; el enlace no se muestra en la terminal.')


if __name__ == '__main__':
    main()
