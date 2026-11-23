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


def test_failing_pre_command_aborts_before_any_request(run_esctl, fake_es, default_config):
    config = config_with_pre_commands(default_config, {"command": "sh -c 'echo cannot connect >&2; exit 4'"})

    result = run_esctl("cluster", "health", config=config)

    assert result.code == 1
    assert "failed with exit code 4" in result.err
    assert "cannot connect" in result.err
    assert fake_es.requests == []


def test_pre_command_exiting_before_the_expected_output_aborts(run_esctl, fake_es, default_config):
    config = config_with_pre_commands(
        default_config,
        {
            "command": "sh -c 'echo starting; echo address already in use >&2; exit 1'",
            "wait_for_exit": False,
            "wait_for_output": "^Forwarding from",
        },
    )

    result = run_esctl("cluster", "health", config=config)

    assert result.code == 1
    assert "exited with code 1 before printing a line matching `^Forwarding from`" in result.err
    assert "address already in use" in result.err
    assert fake_es.requests == []


# Well above the 64 KiB a pipe buffers before blocking the writer
FLOOD = "head -c 1000000 /dev/zero >{fd}"


def test_a_chatty_stderr_does_not_block_the_expected_output(write_config, default_config, tmp_path):
    import subprocess
    import sys

    config = config_with_pre_commands(
        default_config,
        {
            "command": f"sh -c '{FLOOD.format(fd='&2')}; echo ready; exec sleep 30'",
            "wait_for_exit": False,
            "wait_for_output": "ready",
        },
    )
    # Nothing listens there: the command fails fast once the pre-command is ready
    config["clusters"]["local"]["servers"] = ["https://127.0.0.1:1"]

    # Run in a subprocess: a deadlock must fail the test, not hang it
    result = subprocess.run(
        [sys.executable, "-m", "esctl.main", "--config", str(write_config(config)), "cluster", "health"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 1
    assert "Connection error" in result.stderr


def test_output_printed_after_the_expected_line_keeps_being_read(write_config, default_config, tmp_path):
    import time
    from types import SimpleNamespace

    from esctl.main import Esctl

    done = tmp_path / "done"
    config = config_with_pre_commands(
        default_config,
        {
            "command": f"sh -c 'echo ready; {FLOOD.format(fd='&1')}; touch {done}; exec sleep 30'",
            "wait_for_exit": False,
            "wait_for_output": "ready",
        },
    )
    app = Esctl()
    app.options, _ = app.parser.parse_known_args(["--config", str(write_config(config))])
    app.initialize_app([])
    cmd = SimpleNamespace(requires_cluster=True)

    app.prepare_to_run_command(cmd)
    try:
        deadline = time.monotonic() + 20
        while not done.exists() and time.monotonic() < deadline:
            time.sleep(0.05)

        assert done.exists(), "the pre-command blocked writing to a full stdout pipe"
    finally:
        app.clean_up(cmd, 0, None)
