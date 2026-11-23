import base64

import pytest


def config_with_password_command(default_config, command):
    default_config["users"]["admin"] = {
        "username": "admin",
        "external_password": {"command": {"run": command}},
    }
    return default_config


def basic_auth(user, password):
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


def test_password_is_read_from_the_command_output(run_esctl, fake_es, default_config):
    fake_es.on("GET", "/_cluster/health", {"status": "green"})

    result = run_esctl(
        "cluster", "health", config=config_with_password_command(default_config, "echo s3cret | tr a-z A-Z")
    )

    assert result.code == 0, result.err
    assert fake_es.last("GET", "/_cluster/health").headers["authorization"] == basic_auth("admin", "S3CRET")


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("echo boom >&2; exit 3", "failed with exit code 3"),
        ("true", "printed nothing"),
    ],
)
def test_failing_password_command_aborts_before_any_request(run_esctl, fake_es, default_config, command, expected):
    result = run_esctl("cluster", "health", config=config_with_password_command(default_config, command))

    assert result.code == 1
    assert expected in result.err
    assert fake_es.requests == []


def test_failing_password_command_shows_its_stderr(run_esctl, default_config):
    result = run_esctl(
        "cluster", "health", config=config_with_password_command(default_config, "echo boom >&2; exit 3")
    )

    assert "boom" in result.err


def test_external_password_requires_a_command(run_esctl, fake_es, default_config):
    default_config["users"]["admin"] = {"username": "admin", "external_password": {}}

    result = run_esctl("cluster", "health", config=default_config)

    assert result.code == 1
    assert "users.admin.external_password.command': required field" in result.err
    assert fake_es.requests == []
