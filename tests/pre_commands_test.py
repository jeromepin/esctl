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


def is_running(pid: int) -> bool:
    import os

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def background_pre_command(pid_file):
    return {
        "command": f"sh -c 'echo $$ > {pid_file}; echo ready; exec sleep 30'",
        "wait_for_exit": False,
        "wait_for_output": "ready",
    }


def test_background_pre_commands_are_stopped_and_reaped(run_esctl, fake_es, default_config, tmp_path):
    fake_es.on("GET", "/_cluster/health", {"status": "green"})
    pid_file = tmp_path / "pid"
    config = config_with_pre_commands(default_config, background_pre_command(pid_file))

    result = run_esctl("cluster", "health", config=config)

    assert result.code == 0, result.err
    # A terminated but never awaited child stays as a zombie, which still "exists"
    assert not is_running(int(pid_file.read_text()))


def test_started_pre_commands_are_stopped_when_a_later_one_cannot_start(run_esctl, default_config, tmp_path):
    pid_file = tmp_path / "pid"
    config = config_with_pre_commands(
        default_config,
        background_pre_command(pid_file),
        {"command": "/nonexistent/binary"},
    )

    result = run_esctl("cluster", "health", config=config)

    assert result.code == 1
    assert "/nonexistent/binary" in result.err
    assert "Could not clean up" not in result.err
    assert not is_running(int(pid_file.read_text()))
