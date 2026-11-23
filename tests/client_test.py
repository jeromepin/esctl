import random

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


def test_every_configured_server_is_used():
    servers = ("https://es-1:9200", "https://es-2:9200", "https://es-3:9200")

    es = Client.configure(make_context(servers=servers))

    assert sorted(node.base_url for node in es.transport.node_pool.all()) == list(servers)


def test_a_failing_node_is_retried_on_another_one(run_esctl, fake_es, default_config, monkeypatch):
    from elastic_transport import ConnectionError as TransportConnectionError
    from elastic_transport import Urllib3HttpNode

    default_config["clusters"]["local"]["servers"] = ["https://down:9200", "https://up:9200"]
    default_config["settings"]["max_retries"] = 1
    fake_es.on("GET", "/_cluster/health", {"status": "green"})
    healthy = Urllib3HttpNode.perform_request

    def perform_request(node, *args, **kwargs):
        if node.config.host == "down":
            msg = "connection refused"
            raise TransportConnectionError(msg)
        return healthy(node, *args, **kwargs)

    monkeypatch.setattr(Urllib3HttpNode, "perform_request", perform_request)

    # The previous implementation picked one server at random: it would fail one run in two.
    # Reseed so the outcome doesn't depend on the seed a test plugin may have set.
    for seed in range(20):
        random.seed(seed)
        assert run_esctl("cluster", "health", config=default_config).code == 0
