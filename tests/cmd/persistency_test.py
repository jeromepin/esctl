import pytest

SETTINGS = {"transient": {}, "persistent": {}, "defaults": {}}


@pytest.mark.parametrize(
    ("argv", "setting", "value"),
    [
        (("cluster", "routing", "allocation", "enable", "primaries"), "cluster.routing.allocation.enable", "primaries"),
        (("cluster", "settings", "set", "a.b", "c"), "a.b", "c"),
        (("cluster", "settings", "reset", "a.b"), "a.b", None),
        (("logging", "set", "org.x", "DEBUG"), "logger.org.x", "DEBUG"),
        (("logging", "reset", "org.x"), "logger.org.x", None),
    ],
)
@pytest.mark.parametrize(
    ("flags", "persistency"),
    [((), "transient"), (("--transient",), "transient"), (("--persistent",), "persistent")],
)
def test_persistency_flags(run_esctl, fake_es, argv, setting, value, flags, persistency):
    fake_es.on("PUT", "/_cluster/settings", {"acknowledged": True})
    fake_es.on("GET", "/_cluster/settings", SETTINGS)

    result = run_esctl(*argv, *flags)

    assert result.code == 0, result.err
    assert fake_es.last("PUT", "/_cluster/settings").body == {persistency: {setting: value}}


def test_persistency_flags_are_mutually_exclusive(run_esctl):
    result = run_esctl("cluster", "settings", "set", "--transient", "--persistent", "a.b", "c")

    assert result.code == 2
    assert "not allowed with argument" in result.err


def test_routing_allocation_enable_only_reads_without_a_status(run_esctl, fake_es):
    fake_es.on(
        "GET",
        "/_cluster/settings",
        {**SETTINGS, "persistent": {"cluster.routing.allocation.enable": "primaries"}},
    )

    result = run_esctl("cluster", "routing", "allocation", "enable", "-f", "json")

    assert result.code == 0, result.err
    assert result.json()["Persistent"] == "primaries"
