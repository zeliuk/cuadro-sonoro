#!/usr/bin/env python3
"""Generate a local QR image for a frame URL without using a remote service."""
import argparse
import re
from pathlib import Path

SUFFIX_RE = re.compile(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$')
TOKEN_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suffix', default='dev001')
    parser.add_argument('--token', default='cuadro-prueba')
    parser.add_argument('--output', help='PNG de salida; por defecto artifacts/local-preview/cuadro-sonoro-<sufijo>.png')
    parser.add_argument('--port', type=int, default=80, help='usa 80 para el enlace acordado; otros puertos se incluyen en el QR')
    args = parser.parse_args()
    if not SUFFIX_RE.fullmatch(args.suffix) or len(args.suffix) > 49:
        parser.error('sufijo DNS no válido: minúsculas, números y guiones, máximo 49 caracteres')
    if not TOKEN_RE.fullmatch(args.token):
        parser.error('identificador no válido: 1–128 caracteres ASCII alfanuméricos, guion o guion bajo')
    if not 1 <= args.port <= 65535:
        parser.error('el puerto debe estar entre 1 y 65535')
    hostname = 'cuadro-sonoro-' + args.suffix + '.local'
    if len(hostname) > 253:
        parser.error('hostname superior al límite DNS')
    url = 'http://' + hostname + ('' if args.port == 80 else ':' + str(args.port)) + '/#token=' + args.token
    try:
        import qrcode
    except ImportError:
        parser.error('falta qrcode: instala con python3 -m pip install "qrcode[pil]"')
    target = Path(args.output or ('artifacts/local-preview/cuadro-sonoro-' + args.suffix + '.png'))
    target.parent.mkdir(parents=True, exist_ok=True)
    image = qrcode.make(url)
    image.save(target)
    print('QR guardado en: ' + str(target))
    if args.token == 'cuadro-prueba':
        print('Enlace ficticio/de prueba: ' + url)
    else:
        print('Enlace generado para el identificador indicado; no se muestra en la terminal.')


if __name__ == '__main__':
    main()
