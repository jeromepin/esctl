import pytest

from esctl.config import ConfigFileParser
from esctl.exceptions import ConfigurationError


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("clusters: {}\ncontexts: {}\nfoo: 1\n", "Invalid configuration at 'foo': unknown field"),
        (
            "clusters:\n  c:\n    servers: nope\ncontexts: {}\n",
            "Invalid configuration at 'clusters.c.servers': must be of list type",
        ),
        ("contexts: {}\n", "Invalid configuration at 'clusters': required field"),
        ("settings:\n  timeout: soon\nclusters: {}\ncontexts: {}\n", "'settings.timeout': must be of integer type"),
    ],
)
def test_schema_errors_are_reported_with_their_path(tmp_path, caplog, content, expected):
    path = tmp_path / "esctlrc"
    path.write_text(content)

    with pytest.raises(ConfigurationError, match="doesn't match expected schema"):
        ConfigFileParser().load_configuration(str(path))

    assert expected in caplog.text


def test_invalid_yaml_raises_a_configuration_error(tmp_path):
    path = tmp_path / "esctlrc"
    path.write_text("clusters: [\n")

    with pytest.raises(ConfigurationError, match="Cannot read YAML"):
        ConfigFileParser().load_configuration(str(path))


def test_the_cli_exits_with_1_on_an_invalid_config(run_esctl, tmp_path):
    path = tmp_path / "esctlrc"
    path.write_text("clusters: {}\ncontexts: {}\nfoo: 1\n")

    result = run_esctl("config", "context", "list", config=path)

    assert result.code == 1
    assert "doesn't match expected schema" in result.err
