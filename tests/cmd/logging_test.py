import pytest


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (("org.elasticsearch.discovery",), "logger.org.elasticsearch.discovery : DEBUG\n"),
        (("--persistent", "org.elasticsearch.discovery"), "logger.org.elasticsearch.discovery : TRACE\n"),
        (("logger.org.elasticsearch.http",), "logger.org.elasticsearch.http : \n"),
    ],
)
def test_logging_get_prints_the_level(run_esctl, fake_es, argv, expected):
    fake_es.on(
        "GET",
        "/_cluster/settings",
        {
            "transient": {"logger.org.elasticsearch.discovery": "DEBUG"},
            "persistent": {"logger.org.elasticsearch.discovery": "TRACE"},
            "defaults": {},
        },
    )

    result = run_esctl("logging", "get", *argv)

    assert result.code == 0, result.err
    assert result.out == expected
