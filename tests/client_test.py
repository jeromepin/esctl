import pytest

from esctl.commands import EsctlCommon
from esctl.config import Context
from esctl.elasticsearch import Client, ClientNotConfiguredError


def make_context(servers=("https://localhost:9200",), settings=None):
    return Context("test", None, {"servers": list(servers)}, settings or {})


@pytest.fixture(autouse=True)
def _reset_client():
    Client.reset()
    yield
    Client.reset()


def test_commands_resolve_the_client_lazily():
    # `esctl.commands` is imported (and its classes built) before the client
    # is configured, exactly like when cliff loads a command.
    common = EsctlCommon()

    with pytest.raises(ClientNotConfiguredError):
        _ = common.es

    es = Client.configure(make_context())

    assert common.es is es
    assert common.cluster_settings.es is es
    assert common.index_settings.es is es


def test_configuring_again_replaces_the_client():
    first = Client.configure(make_context(servers=("https://first:9200",)))
    second = Client.configure(make_context(servers=("https://second:9200",)))

    assert first is not second
    assert Client.get() is second
