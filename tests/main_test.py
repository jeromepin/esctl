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


def urllib3_warnings_are_silenced() -> bool:
    import warnings

    from urllib3.exceptions import HTTPWarning

    return any(
        action == "ignore" and module is None and issubclass(HTTPWarning, category)
        for action, _, category, module, _ in warnings.filters
    )


def test_tls_warnings_are_kept_when_certificates_are_verified(run_esctl, fake_es):
    fake_es.on("GET", "/_cluster/health", {"status": "green"})

    result = run_esctl("cluster", "health")

    assert result.code == 0, result.err
    assert not urllib3_warnings_are_silenced()


def test_no_insecure_warning_when_certificate_checks_are_disabled_on_purpose(run_esctl, fake_es, default_config):
    import warnings

    from elastic_transport import SecurityWarning

    fake_es.on("GET", "/_cluster/health", {"status": "green"})
    default_config["settings"]["no_check_certificate"] = True

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = run_esctl("cluster", "health", config=default_config)

    assert result.code == 0, result.err
    assert not [w for w in caught if issubclass(w.category, SecurityWarning)]


def test_the_terminal_width_is_not_overridden(monkeypatch):
    import os

    from esctl.main import Esctl

    monkeypatch.delenv("COLUMNS", raising=False)

    Esctl()

    assert "COLUMNS" not in os.environ


def test_unused_es_version_option_is_gone():
    from esctl.main import Esctl

    options = {option for action in Esctl().parser._actions for option in action.option_strings}

    assert "--es-version" not in options
