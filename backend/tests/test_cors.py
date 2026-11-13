"""CORS contract for local .local previews and exact development origins."""
import importlib

from fastapi.testclient import TestClient

import backend.main as main


REGEX = r'^http://cuadro-sonoro-[a-z0-9-]+\.local$'


def client_for(monkeypatch, regex=None, exact='https://trusted.example'):
    monkeypatch.setenv('ALLOWED_ORIGINS', exact)
    if regex is None:
        monkeypatch.delenv('ALLOWED_ORIGIN_REGEX', raising=False)
    else:
        monkeypatch.setenv('ALLOWED_ORIGIN_REGEX', regex)
    app_module = importlib.reload(main)
    return TestClient(app_module.app)


def test_local_hostnames_and_preflight_authorization(monkeypatch):
    client = client_for(monkeypatch, REGEX)
    for origin in ('http://cuadro-sonoro-dev001.local', 'http://cuadro-sonoro-cuadro-2.local'):
        response = client.options(
            '/state',
            headers={
                'Origin': origin,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'authorization,content-type',
            },
        )
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == origin
        allowed = response.headers['access-control-allow-headers'].lower()
        assert 'authorization' in allowed
        assert 'content-type' in allowed


def test_unrelated_and_suffix_spoof_origins_rejected(monkeypatch):
    client = client_for(monkeypatch, REGEX)
    for origin in (
        'https://cuadro-sonoro-dev001.local',
        'http://cuadro-sonoro-dev001.local.ejemplo.com',
        'http://evil.example',
    ):
        response = client.get('/health', headers={'Origin': origin})
        assert 'access-control-allow-origin' not in response.headers


def test_exact_origins_remain_allowed_with_regex(monkeypatch):
    client = client_for(monkeypatch, REGEX, exact='https://trusted.example,http://127.0.0.1:5173')
    for origin in ('https://trusted.example', 'http://127.0.0.1:5173'):
        response = client.get('/health', headers={'Origin': origin})
        assert response.headers['access-control-allow-origin'] == origin


def test_absent_regex_preserves_previous_exact_origin_behavior(monkeypatch):
    for regex in (None, ''):
        client = client_for(monkeypatch, regex)
        allowed = client.get('/health', headers={'Origin': 'https://trusted.example'})
        denied = client.get('/health', headers={'Origin': 'http://cuadro-sonoro-dev001.local'})
        assert allowed.headers['access-control-allow-origin'] == 'https://trusted.example'
        assert 'access-control-allow-origin' not in denied.headers
