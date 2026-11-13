#!/usr/bin/env python3
"""Serve web/ on LAN and advertise its configurable .local hostname on macOS."""
import argparse
import ipaddress
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUFFIX_RE = re.compile(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$')


def lan_ip(interface=None):
    if interface:
        result = subprocess.run(['ipconfig', 'getifaddr', interface], text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
        raise RuntimeError('No se pudo obtener una IPv4 para la interfaz ' + interface + '.')
    route = subprocess.run(['route', '-n', 'get', 'default'], text=True, capture_output=True)
    match = re.search(r'^\s*interface:\s*(\S+)', route.stdout, re.MULTILINE)
    if match:
        result = subprocess.run(['ipconfig', 'getifaddr', match.group(1)], text=True, capture_output=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    # Fallback for hosts with an unusual default-route setup.
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(('192.0.2.1', 9))
        return probe.getsockname()[0]
    finally:
        probe.close()


def validate(suffix, ip):
    hostname = 'cuadro-sonoro-' + suffix + '.local'
    if len(suffix) > 49 or not SUFFIX_RE.fullmatch(suffix):
        raise ValueError('El sufijo debe ser una etiqueta DNS de 1 a 49 caracteres: minúsculas, números y guiones; sin guion al inicio/final.')
    if len(hostname) > 253:
        raise ValueError('El hostname supera el límite DNS de 253 caracteres.')
    address = ipaddress.ip_address(ip)
    if address.version != 4 or address.is_loopback or address.is_unspecified or address.is_multicast:
        raise ValueError('Indica una dirección IPv4 LAN válida, no loopback, comodín ni multicast.')
    return hostname, str(address)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suffix', default='dev001', help='sufijo DNS estable (por defecto: dev001)')
    parser.add_argument('--token', default='cuadro-prueba', help='ID del cuadro para el QR (por defecto: ficticio)')
    parser.add_argument('--qr-output', help='PNG QR de salida; por defecto artifacts/local-preview/cuadro-sonoro-<sufijo>.png')
    parser.add_argument('--interface', help='interfaz macOS para detectar la IP, por ejemplo en0')
    parser.add_argument('--ip', help='IPv4 LAN explícita; prevalece sobre --interface')
    parser.add_argument('--port', type=int, default=80, help='puerto HTTP (por defecto: 80; puerto alternativo cambia la URL/CORS)')
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('el anuncio Bonjour con dns-sd de este script requiere macOS')
    if not 1 <= args.port <= 65535:
        parser.error('el puerto debe estar entre 1 y 65535')
    try:
        address = args.ip or lan_ip(args.interface)
        hostname, address = validate(args.suffix, address)
    except (RuntimeError, ValueError, OSError) as exc:
        parser.error(str(exc))
    dns_sd = shutil.which('dns-sd')
    if not dns_sd:
        parser.error('no se encontró dns-sd; macOS debe tener Bonjour disponible')

    probe = socket.socket()
    try:
        probe.bind(('0.0.0.0', args.port))
    except PermissionError:
        parser.error('no hay permiso para escuchar en el puerto %d. No se elevaron permisos; usa --port 8080 para diagnóstico.' % args.port)
    except OSError as exc:
        parser.error('el puerto %d no está disponible (%s). Detén solo el servicio que lo ocupa o usa --port 8080.' % (args.port, exc))
    finally:
        probe.close()

    qr_python = ROOT / '.venv-qr' / 'bin' / 'python'
    if not qr_python.exists():
        qr_python = Path(sys.executable)
    qr_cmd = [str(qr_python), str(ROOT / 'scripts' / 'generate_local_qr.py'), '--suffix', args.suffix, '--token', args.token]
    if args.qr_output:
        qr_cmd.extend(['--output', args.qr_output])
    if args.port != 80:
        qr_cmd.extend(['--port', str(args.port)])
    generated = subprocess.run(qr_cmd)
    if generated.returncode:
        return generated.returncode

    server_cmd = [sys.executable, '-m', 'http.server', str(args.port), '--bind', '0.0.0.0', '--directory', str(ROOT / 'web')]
    mdns_cmd = [dns_sd, '-P', hostname, '_http._tcp', 'local', str(args.port), hostname, address]
    children = []
    try:
        server = subprocess.Popen(server_cmd)
        children.append(server)
        time.sleep(0.35)
        if server.poll() is not None:
            raise RuntimeError('el servidor HTTP terminó al arrancar; comprueba puerto y permisos')
        bonjour = subprocess.Popen(mdns_cmd)
        children.append(bonjour)
        time.sleep(1.0)
        if bonjour.poll() is not None:
            raise RuntimeError('dns-sd terminó al arrancar; revisa el soporte Bonjour y la interfaz de red')
        print('Servidor estático: web/ en 0.0.0.0:%d' % args.port, flush=True)
        print('Anuncio Bonjour: http://%s%s' % (hostname, '' if args.port == 80 else ':' + str(args.port)), flush=True)
        print('IP LAN de diagnóstico: http://%s:%d' % (address, args.port), flush=True)
        print('Logs HTTP y mDNS aparecen debajo. Ctrl+C detiene ambos procesos.', flush=True)
        while True:
            for child, label in ((server, 'HTTP'), (bonjour, 'Bonjour')):
                code = child.poll()
                if code is not None:
                    raise RuntimeError('%s terminó inesperadamente (código %s)' % (label, code))
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('\nDeteniendo servidor y anuncio Bonjour…', flush=True)
    except RuntimeError as exc:
        print('Error: ' + str(exc), file=sys.stderr)
        return 1
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
        for child in reversed(children):
            if child.poll() is None:
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
