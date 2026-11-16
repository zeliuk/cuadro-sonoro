"""Narrow Apify API client for the two explicitly configured Actors."""
import ipaddress
import json
import logging
import os
import socket
import threading
import time
from urllib.parse import urlencode
from collections import OrderedDict
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

API = 'https://api.apify.com/v2'
JOHNVC_DOWNLOAD_ACTOR = 'johnvc/youtube-download-api'
_lock = threading.Lock()
_cache = OrderedDict()
_last_search = 0.0


class ApifyError(RuntimeError):
    pass


class ApifyRateLimit(ApifyError):
    pass


def configured():
    token = os.getenv('APIFY_TOKEN', '').strip()
    if not token:
        raise ApifyError('La búsqueda/importación requiere configurar APIFY_TOKEN en el backend.')
    return token


def _request(path, *, method='GET', payload=None, timeout=20):
    token = configured()
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(API + path, data=data, method=method, headers={
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/json', 'Content-Type': 'application/json',
    })
    try:
        with build_opener(_ApifyRedirect()).open(req, timeout=timeout) as response:
            return json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        # Never include exception text: urllib errors can contain the request URL.
        raise ApifyError('Apify no respondió correctamente a la operación solicitada.') from None


def _actor_path(actor):
    return '/acts/' + quote(actor.replace('/', '~'), safe='~')


def create_run(actor, payload):
    actor_timeout = int(os.getenv('APIFY_ACTOR_TIMEOUT_SECONDS', '240'))
    try:
        response = _request(_actor_path(actor) + '/runs?' + urlencode({'timeout': actor_timeout}), method='POST', payload=payload, timeout=30)
    except ApifyError:
        logging.getLogger('uvicorn.error').error('apify_run_creation_ambiguous actor=%s', actor)
        raise ApifyError('No se pudo confirmar si Apify inició la ejecución. Revisa Apify antes de volver a intentarlo.') from None
    run = response.get('data') or {}
    run_id = run.get('id')
    if not run_id:
        logging.getLogger('uvicorn.error').error('apify_run_creation_ambiguous actor=%s response_without_run_id=true', actor)
        raise ApifyError('Apify aceptó la solicitud sin devolver un identificador recuperable; revisa la consola antes de reintentar.')
    return run


def get_run(run_id):
    result = _request('/actor-runs/' + quote(run_id, safe=''), timeout=20)
    return result.get('data') or {}


def abort_run(run_id):
    return _request('/actor-runs/' + quote(run_id, safe='') + '/abort', method='POST', timeout=20)


def dataset_items(dataset_id):
    result = _request('/datasets/' + quote(dataset_id, safe='') + '/items?clean=true&format=json', timeout=30)
    if not isinstance(result, list):
        raise ApifyError('Apify devolvió un resultado con formato no válido.')
    return result


def wait_run(run_id, max_seconds=None):
    deadline = time.monotonic() + (max_seconds or int(os.getenv('APIFY_RUN_TIMEOUT_SECONDS', '180')))
    delay = 1.0
    while time.monotonic() < deadline:
        try:
            run = get_run(run_id)
        except ApifyError:
            time.sleep(delay)
            delay = min(8.0, delay * 1.6)
            continue
        status = run.get('status')
        if status in {'SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'}:
            return run
        time.sleep(delay)
        delay = min(8.0, delay * 1.6)
    raise ApifyError('Se alcanzó el tiempo máximo de seguimiento de Apify.')


def _duration(value):
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return None
    try:
        parts = [int(part) for part in value.split(':')]
        seconds = 0
        for part in parts:
            seconds = seconds * 60 + part
        return seconds
    except (TypeError, ValueError):
        return None


def search(artist, title, max_duration):
    global _last_search
    token = configured()
    actor = os.getenv('APIFY_SEARCH_ACTOR', 'streamers/youtube-scraper').strip()
    key = (actor, artist.strip().casefold(), title.strip().casefold())
    with _lock:
        now = time.monotonic()
        cached = _cache.get(key)
        if cached and now - cached[0] < int(os.getenv('APIFY_SEARCH_CACHE_SECONDS', '300')):
            _cache.move_to_end(key)
            return cached[1]
        interval = float(os.getenv('APIFY_SEARCH_MIN_INTERVAL_SECONDS', '2'))
        if now - _last_search < interval:
            raise ApifyRateLimit('Búsqueda limitada temporalmente; espera unos segundos y vuelve a intentarlo.')
        _last_search = now
    run = create_run(actor, {
        'searchQueries': [f'{artist.strip()} {title.strip()}'],
        'maxResults': 5, 'maxResultsShorts': 0, 'maxResultStreams': 0,
    })
    try:
        run = wait_run(run['id'], int(os.getenv('APIFY_SEARCH_TIMEOUT_SECONDS', '90')))
    except ApifyError:
        try:
            abort_run(run['id'])
        except ApifyError:
            logging.getLogger('uvicorn.error').error('apify_search_abort_pending actor=%s', actor)
        raise ApifyError('La búsqueda superó el tiempo máximo. Revisa Apify antes de volver a intentarlo.') from None
    if run.get('status') != 'SUCCEEDED':
        raise ApifyError('El Actor de búsqueda de Apify no terminó correctamente.')
    items = dataset_items(run.get('defaultDatasetId', '')) if run.get('defaultDatasetId') else []
    import re
    results = []
    for item in items:
        video_id = item.get('id')
        duration = _duration(item.get('duration'))
        if (not isinstance(video_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id)
                or item.get('type') not in (None, 'video') or not duration or duration > max_duration):
            continue
        image = item.get('thumbnailUrl')
        parsed = urlparse(image or '')
        if parsed.scheme != 'https' or not parsed.hostname:
            image = f'https://i.ytimg.com/vi/{video_id}/mqdefault.jpg'
        results.append({'id': video_id, 'title': str(item.get('title') or title)[:200],
                        'artist': str(item.get('channelName') or artist)[:200],
                        'duration': duration, 'image': image})
        if len(results) == 5:
            break
    with _lock:
        _cache[key] = (time.monotonic(), results)
        while len(_cache) > 128:
            _cache.popitem(last=False)
    return results


def download_input(actor, video_id, max_duration, max_bytes):
    video_url = 'https://www.youtube.com/watch?v=' + video_id
    if actor == JOHNVC_DOWNLOAD_ACTOR:
        return {
            'videoUrls': [video_url],
            'format': 'audio',
            'audioFormat': 'mp3',
            'audioQuality': 'standard',
            'maxMinutes': max(1, (max_duration + 59) // 60),
            'maxMegabytes': max(1, max_bytes // (1024 * 1024)),
        }
    return {
        'videoUrls': [video_url],
        'audioFormat': 'mp3',
        'audioBitrate': '128k',
        'maxVideosPerUrl': 1,
    }


def validate_public_url(url):
    parsed = urlparse(url or '')
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ApifyError('Apify devolvió una URL de medio no permitida.')
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        if any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ApifyError('Apify devolvió un destino de red no permitido.')
    except (socket.gaierror, ValueError):
        raise ApifyError('No se pudo validar el destino del medio.') from None
    return url


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


class _ApifyRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        old = urlparse(request.full_url)
        new = urlparse(newurl)
        if new.scheme != 'https' or new.hostname != old.hostname or new.port not in (None, 443):
            raise ApifyError('Apify API devolvió una redirección no permitida.')
        return super().redirect_request(request, response, code, message, headers, newurl)


def open_media(request, timeout=30):
    """Fetch media safely; Apify key-value-store records require backend authentication."""
    url = request.full_url if isinstance(request, Request) else str(request)
    validate_public_url(url)
    parsed = urlparse(url)
    headers = dict(request.header_items()) if isinstance(request, Request) else {}
    # Never forward caller-supplied credentials to media hosts. Apify's output
    # points to private run key-value-store records, which require API auth.
    headers.pop('Authorization', None)
    headers.pop('Proxy-Authorization', None)
    if parsed.hostname == 'api.apify.com':
        headers['Authorization'] = f'Bearer {configured()}'
    media_request = Request(url, headers=headers)
    return build_opener(_SafeRedirect()).open(media_request, timeout=timeout)


def download_result(run, actor=None):
    if run.get('status') != 'SUCCEEDED':
        raise ApifyError('La ejecución de descarga de Apify no terminó correctamente.')
    items = dataset_items(run.get('defaultDatasetId', '')) if run.get('defaultDatasetId') else []
    if not items:
        raise ApifyError('El Actor terminó sin resultados de descarga.')
    result = items[0]
    if actor == JOHNVC_DOWNLOAD_ACTOR:
        if (result.get('resultType') != 'file' or result.get('error')
                or result.get('format') != 'audio' or result.get('container') != 'mp3'):
            logging.getLogger('uvicorn.error').warning(
                'apify_download_item_failed actor=johnvc result_file=%s error_present=%s file_url_present=%s',
                result.get('resultType') == 'file', bool(result.get('error')), bool(result.get('fileUrl')),
            )
            raise ApifyError('El run de Apify terminó, pero no entregó un MP3. Revisa el campo error del resultado en Apify.')
        return {
            'videoId': result.get('videoId'),
            'duration': result.get('durationSeconds'),
            'audioFileUrl': validate_public_url(result.get('fileUrl')),
            'thumbnailFileUrl': validate_public_url(result.get('thumbnailUrl')) if result.get('thumbnailUrl') else None,
        }
    if str(result.get('status', '')).casefold() != 'success' or result.get('error'):
        logging.getLogger('uvicorn.error').warning(
            'apify_download_item_failed run_succeeded=true status_success=%s error_present=%s audio_url_present=%s',
            str(result.get('status', '')).casefold() == 'success',
            bool(result.get('error')),
            bool(result.get('audioFileUrl')),
        )
        raise ApifyError('El run de Apify terminó, pero falló la descarga individual. Revisa el campo status/error de ese run; YouTube puede bloquear la descarga incluso en vídeos públicos.')
    result['audioFileUrl'] = validate_public_url(result.get('audioFileUrl'))
    thumbnail = result.get('thumbnailFileUrl') or result.get('thumbnailYoutubeUrl')
    result['thumbnailFileUrl'] = validate_public_url(thumbnail) if thumbnail else None
    return result
