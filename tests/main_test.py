import logging


def test_log_files_do_not_contain_color_codes(run_esctl, tmp_path):
    log_file = tmp_path / "esctl.log"

    run_esctl("--log-file", str(log_file), "-v", "-v", "-v", "config", "show")

    content = log_file.read_text()
    assert "DEBUG" in content
    assert "\x1b[" not in content


def test_console_levels_are_colored_once_and_names_stay_untouched(run_esctl, fake_es):
    fake_es.on("GET", "/_cluster/health", {"error": "boom"}, status=500)

    for _ in range(3):
        result = run_esctl("cluster", "health")

    assert "[\x1b[95mERROR\x1b[0m]" in result.err
    assert "\x1b[95m\x1b[95m" not in result.err
    assert logging.getLevelName(logging.ERROR) == "ERROR"
