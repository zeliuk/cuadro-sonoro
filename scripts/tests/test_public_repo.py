import importlib.util
import json
from pathlib import Path
import subprocess
import sys

spec = importlib.util.spec_from_file_location('public_guard', Path(__file__).parents[1] / 'check_public_repo.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_private_names_and_public_templates():
    for path in ['backend/.env', '.env.production', 'serviceAccountKey.json', 'secrets/firebase.json', 'credentials.json', 'cookies.txt', 'music.mp3', '.firebaserc']:
        assert guard.sensitive_path(path)
    for path in ['backend/.env.example', '.firebaserc.example', 'firebase.json', 'firebase/database.rules.json', 'README.md', 'backend/config.py']:
        assert not guard.sensitive_path(path)


def test_empty_examples_allowed_and_literal_secrets_reported():
    assert list(guard.findings('backend/.env.example', b'FIREBASE_SERVICE_ACCOUNT_JSON=\n')) == []
    assert list(guard.findings('settings.py', b"IMPORT_API_TOKEN='not-a-real-credential-but-must-be-rejected'"))
    field = 'IMPORT_' + 'API_TOKEN'
    assignment = f"os.environ[{field!r}] = 'must-be-rejected'"
    assert list(guard.findings('settings.py', assignment.encode()))
    assert list(guard.findings('fixture.py', b"os.environ['IMPORT_API_TOKEN'] = 'test-token-only'")) == []


def test_detects_provider_and_private_key_without_returning_values():
    token = 'ghp_' + 'A' * 36
    key = '-----' + 'BEGIN PRIVATE KEY' + '-----'
    for value in (token, key):
        result = list(guard.findings('file.txt', value.encode()))
        assert result
        assert all(value not in label for label in result)
    credential = json.dumps(dict(type='service_account', private_key='synthetic-placeholder'))
    assert 'JSON de cuenta de servicio' in list(guard.findings('sample.txt', credential.encode()))


def test_cli_uses_staged_content_and_redacts(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    example = tmp_path / 'config.txt'
    value = 'ghp_' + 'B' * 36
    example.write_text(value)
    subprocess.run(['git', '-C', str(tmp_path), 'add', 'config.txt'], check=True)
    example.write_text('clean working tree, but the secret remains staged')
    result = subprocess.run([sys.executable, str(Path(guard.__file__)), '--staged'], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert 'config.txt' in result.stderr
    assert value not in result.stderr + result.stdout


def test_tracked_mode_catches_force_added_private_path(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / '.env').write_text('NON_SECRET=example\n')
    subprocess.run(['git', '-C', str(tmp_path), 'add', '.env'], check=True)
    result = subprocess.run([sys.executable, str(Path(guard.__file__)), '--tracked'], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert '.env' in result.stderr
