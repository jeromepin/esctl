def config_with_pre_commands(default_config, *pre_commands):
    default_config["contexts"]["local"]["pre_commands"] = list(pre_commands)
    return default_config


def test_pre_command_arguments_follow_shell_quoting(run_esctl, fake_es, default_config, tmp_path):
    fake_es.on("GET", "/_cluster/health", {"status": "green"})
    marker = tmp_path / "marker"
    config = config_with_pre_commands(default_config, {"command": f"sh -c 'echo started > {marker}'"})

    result = run_esctl("cluster", "health", config=config)

    assert result.code == 0, result.err
    assert marker.read_text() == "started\n"
