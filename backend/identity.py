"""Stable, non-secret frame namespace derived from its public identifier."""
import hashlib
import re

IDENTIFIER_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z')


def frame_key_for(identifier: str) -> str:
    if not isinstance(identifier, str) or not IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValueError('El identificador debe tener entre 1 y 128 caracteres ASCII: letras, números, guion o guion bajo.')
    return hashlib.sha256(identifier.encode('utf-8')).hexdigest()
