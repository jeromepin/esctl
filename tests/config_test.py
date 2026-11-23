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


def load(tmp_path, content):
    path = tmp_path / "esctlrc"
    path.write_text(content)
    parser = ConfigFileParser()
    parser.load_configuration(str(path))
    return parser


BASE = """
clusters:
  c:
    servers: [https://localhost:9200]
users:
  u:
    username: bob
    password: pw
"""


def test_unknown_context_names_the_known_ones(tmp_path):
    parser = load(tmp_path, BASE + "contexts:\n  a:\n    cluster: c\n")

    with pytest.raises(ConfigurationError, match="Unknown context `nope`.*: a"):
        parser.create_context("nope")


def test_missing_default_context_asks_for_one(tmp_path):
    parser = load(tmp_path, BASE + "contexts:\n  a:\n    cluster: c\n")

    with pytest.raises(ConfigurationError, match="No context selected"):
        parser.create_context(None)


def test_unknown_user_is_an_error_instead_of_silently_unauthenticated(tmp_path):
    parser = load(tmp_path, BASE + "contexts:\n  a:\n    cluster: c\n    user: typo\n")

    with pytest.raises(ConfigurationError, match="requires a user named `typo`.*: u"):
        parser.create_context("a")


def test_context_without_user_has_no_user(tmp_path):
    parser = load(tmp_path, BASE + "contexts:\n  a:\n    cluster: c\n")

    assert parser.create_context("a").user is None


@pytest.mark.parametrize(
    ("cluster", "expected"),
    [
        ("settings: {}", "'clusters.c.servers': required field"),
        ("servers: []", "'clusters.c.servers': min length is 1"),
    ],
)
def test_clusters_need_at_least_one_server(tmp_path, caplog, cluster, expected):
    path = tmp_path / "esctlrc"
    path.write_text(f"clusters:\n  c:\n    {cluster}\ncontexts: {{}}\n")

    with pytest.raises(ConfigurationError):
        ConfigFileParser().load_configuration(str(path))

    assert expected in caplog.text
