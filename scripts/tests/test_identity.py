import pytest

from backend.identity import frame_key_for as api_frame_key
from scripts.device_client import frame_key_for as device_frame_key


@pytest.mark.parametrize('identifier', ['mi-cuadro-prueba', 'x', 'A_0', 'a' * 128])
def test_api_and_device_client_use_the_same_stable_frame_key(identifier):
    assert api_frame_key(identifier) == device_frame_key(identifier)


@pytest.mark.parametrize('identifier', ['', '-bad', '_bad', 'bad/id', 'bad id', 'bad!', 'á', 'a' * 129])
def test_invalid_frame_identifiers_are_rejected_consistently(identifier):
    with pytest.raises(ValueError):
        api_frame_key(identifier)
    with pytest.raises(ValueError):
        device_frame_key(identifier)
