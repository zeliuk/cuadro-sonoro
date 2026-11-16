"""HTTP client for the RapidAPI YouTube MP3 endpoint."""
import ipaddress
import hashlib
import json
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

HOST = 'youtube-mp36.p.rapidapi.com'
ENDPOINT = 'https://' + HOST + '/dl'


class RapidAPIError(RuntimeError):
    pass


def _public_https_url(url):
    parsed = urlparse(url or '')
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise RapidAPIError('RapidAPI devolvió una URL de audio no permitida.')
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        if any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise RapidAPIError('RapidAPI devolvió un destino de red no permitido.')
    except (socket.gaierror, ValueError):
        raise RapidAPIError('No se pudo validar el destino del audio.') from None
    return url


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        _public_https_url(new_url)
        return super().redirect_request(request, fp, code, message, headers, new_url)


def open_public_media(url, timeout=45):
    _public_https_url(url)
    username = os.getenv('RAPIDAPI_USERNAME', '').strip()
    if not username:
        raise RapidAPIError('Configura RAPIDAPI_USERNAME en el backend para descargar el MP3.')
    username_hash = hashlib.md5(username.encode('utf-8')).hexdigest()
    request = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; ' + username,
        'X-RUN': username_hash,
        'Accept': 'audio/mpeg,application/octet-stream,*/*;q=0.8',
    })
    try:
        return build_opener(_SafeRedirect()).open(request, timeout=timeout)
    except HTTPError as exc:
        # The signed media URL can contain temporary credentials; log only its host.
        host = urlparse(exc.geturl()).hostname or 'desconocido'
        raise RapidAPIError(
            f'El servidor del MP3 rechazó la descarga con HTTP {exc.code} (host: {host}).'
        ) from None


def download_link(video_id):
    key = os.getenv('RAPIDAPI_KEY', '').strip()
    if not key:
        raise RapidAPIError('Configura RAPIDAPI_KEY en el backend antes de importar.')
    request = Request(ENDPOINT + '?' + urlencode({'id': video_id}), headers={
        'X-RapidAPI-Key': key, 'X-RapidAPI-Host': HOST, 'Accept': 'application/json',
    })
    try:
        with urlopen(request, timeout=45) as response:
            data = json.loads(response.read(256 * 1024))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        raise RapidAPIError('RapidAPI no pudo preparar el audio. Vuelve a intentarlo.') from None
    if not isinstance(data, dict) or data.get('status') != 'ok' or not data.get('link'):
        raise RapidAPIError('RapidAPI no pudo preparar este vídeo. Elige otra versión.')
    return _public_https_url(data['link'])

