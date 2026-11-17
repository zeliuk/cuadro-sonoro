import socket

import pytest

from backend.rapidapi import RapidAPIError, _public_https_url


def test_public_https_url_accepts_public_dns_result(monkeypatch):
    monkeypatch.setattr(
        socket,
        'getaddrinfo',
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))],
    )

    assert _public_https_url('https://media.example/audio.mp3') == 'https://media.example/audio.mp3'


@pytest.mark.parametrize('address', ['127.0.0.1', '10.0.0.8', '::1'])
def test_public_https_url_rejects_non_public_dns_result(monkeypatch, address):
    family = socket.AF_INET6 if ':' in address else socket.AF_INET
    monkeypatch.setattr(
        socket,
        'getaddrinfo',
        lambda *args, **kwargs: [(family, socket.SOCK_STREAM, 6, '', (address, 443))],
    )

    with pytest.raises(RapidAPIError, match='destino de red no permitido'):
        _public_https_url('https://media.example/audio.mp3')
