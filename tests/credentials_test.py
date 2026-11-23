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


def counting_password_command(default_config, tmp_path):
    counter = tmp_path / "calls"
    return config_with_password_command(default_config, f"echo call >> {counter}; echo s3cret"), counter


@pytest.mark.parametrize(
    "argv",
    [
        ("config", "context", "list"),
        ("config", "show"),
        ("help", "cluster", "health"),
    ],
)
def test_local_commands_do_not_run_the_password_command(run_esctl, default_config, tmp_path, argv):
    config, counter = counting_password_command(default_config, tmp_path)

    result = run_esctl(*argv, config=config)

    assert result.code == 0, result.err
    assert not counter.exists()


def test_the_password_command_runs_once_per_session(write_config, default_config, tmp_path):
    from esctl.main import Esctl

    config, counter = counting_password_command(default_config, tmp_path)
    app = Esctl()
    app.options, _ = app.parser.parse_known_args(["--config", str(write_config(config))])
    app.initialize_app([])

    app.connect()
    app.connect()

    assert counter.read_text().splitlines() == ["call"]
