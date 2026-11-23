import yaml


def config_with_external_password(default_config):
    default_config["users"]["admin"] = {
        "username": "admin",
        "external_password": {"command": {"run": "echo s3cret"}},
    }
    default_config["contexts"]["other"] = {
        "cluster": "local",
        "pre_commands": [{"command": "true"}],
    }
    return default_config


def test_config_context_set_does_not_write_resolved_secrets(run_esctl, write_config, default_config):
    config = config_with_external_password(default_config)
    path = write_config(config)

    result = run_esctl("config", "context", "set", "other", config=path)

    assert result.code == 0, result.err
    written = yaml.safe_load(path.read_text())
    assert written["default-context"] == "other"
    assert written["users"] == config["users"]
    assert written["contexts"] == config["contexts"]
    assert "password: s3cret" not in path.read_text()


def test_config_show_prints_the_file_not_resolved_secrets(run_esctl, default_config):
    result = run_esctl("config", "show", config=config_with_external_password(default_config))

    assert result.code == 0, result.err
    assert "password: s3cret" not in result.out
    assert "echo s3cret" in result.out
