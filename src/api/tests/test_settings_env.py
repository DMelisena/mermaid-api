import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[2]

# Each case builds settings in a fresh interpreter, because Django settings are
# read once at import.
PRINT_SETTINGS = (
    "import json, app.settings as s; "
    "print(json.dumps({'debug': s.DEBUG, 'hosts': s.ALLOWED_HOSTS, "
    "'db_options': s.DATABASES['default']['OPTIONS'], 'sqs': s.ENDPOINT_URL}))"
)
VARS = (
    "ENV",
    "DEBUG",
    "ALLOWED_HOSTS",
    "DB_SSLMODE",
    "SQS_ENDPOINT_URL",
    "ECS_CONTAINER_METADATA_URI",
)


def _settings(**env):
    base = {k: v for k, v in os.environ.items() if k not in VARS}
    base["SECRET_KEY"] = base.get("SECRET_KEY") or "test"
    base.update(env)
    out = subprocess.run(
        [sys.executable, "-c", PRINT_SETTINGS],
        cwd=SRC_DIR,
        env=base,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("env", ["local", "dev", "prod"])
def test_debug_off_unless_set(env):
    assert _settings(ENV=env)["debug"] is False


@pytest.mark.parametrize(
    "value,expected",
    [
        ("True", True),
        ("true", True),
        ("TRUE", True),
        ("False", False),
        ("1", False),
        ("yes", False),
    ],
)
def test_debug_from_env(value, expected):
    assert _settings(ENV="local", DEBUG=value)["debug"] is expected


def test_local_allowed_hosts_default_any():
    assert _settings(ENV="local")["hosts"] == ["*"]


def test_local_allowed_hosts_from_env():
    hosts = _settings(ENV="local", ALLOWED_HOSTS="api.example.org, other.example.org")["hosts"]
    assert hosts == ["api.example.org", "other.example.org", "localhost", "127.0.0.1"]


def test_db_sslmode_defaults():
    assert _settings(ENV="local")["db_options"] == {}
    assert _settings(ENV="prod")["db_options"] == {"sslmode": "require"}


def test_db_sslmode_from_env():
    assert _settings(ENV="local", DB_SSLMODE="require")["db_options"] == {"sslmode": "require"}
    assert _settings(ENV="local", DB_SSLMODE="disable")["db_options"] == {"sslmode": "disable"}


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_db_sslmode_env_ignored_in_dev_prod(env):
    assert _settings(ENV=env, DB_SSLMODE="disable")["db_options"] == {"sslmode": "require"}


def test_sqs_endpoint_from_env_in_any_env():
    assert _settings(ENV="local")["sqs"] == "http://sqs:9324"
    assert _settings(ENV="prod")["sqs"] is None
    assert _settings(ENV="prod", SQS_ENDPOINT_URL="http://q:9324")["sqs"] == "http://q:9324"
