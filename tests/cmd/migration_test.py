DEPRECATIONS = {
    "cluster_settings": [
        {
            "level": "critical",
            "message": "Cluster name cannot contain ':'",
            "url": "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.0.html#_literal_literal_is_no_longer_allowed_in_cluster_name",
            "details": "This cluster is named [mycompany:logging], which contains the illegal character ':'.",
        },
    ],
    "node_settings": [],
    "index_settings": {
        "logs:apache": [
            {
                "level": "warning",
                "message": "Index name cannot contain ':'",
                "url": "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.0.html#_literal_literal_is_no_longer_allowed_in_index_name",
                "details": "This index is named [logs:apache], which contains the illegal character ':'.",
            },
        ],
        "foobar": [
            {
                "level": "critical",
                "message": "Foo bar baz qux.",
                "url": "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.0.html#_literal_literal_is_no_longer_allowed_in_index_name",
                "details": "This is a random string.",
            },
            {
                "level": "warning",
                "message": "Index name cannot contain ':'",
                "url": "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.0.html#_literal_literal_is_no_longer_allowed_in_index_name",
                "details": "This index is named [logs:apache], which contains the illegal character ':'.",
            },
        ],
    },
    "ml_settings": [],
}


def test_index_settings_deprecations_are_prefixed_with_the_index_name(run_esctl, fake_es):
    fake_es.on("GET", "/_migration/deprecations", DEPRECATIONS)

    result = run_esctl("migration", "deprecations", "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == [
        {
            "Kind": "cluster_settings",
            "Level": "critical",
            "Message": "Cluster name cannot contain ':'",
            "Doc": "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.0.html#_literal_literal_is_no_longer_allowed_in_cluster_name",
        },
        {
            "Kind": "index_settings",
            "Level": "warning",
            "Message": "[logs:apache] Index name cannot contain ':'",
            "Doc": "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.0.html#_literal_literal_is_no_longer_allowed_in_index_name",
        },
        {
            "Kind": "index_settings",
            "Level": "critical",
            "Message": "[foobar] Foo bar baz qux.",
            "Doc": "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.0.html#_literal_literal_is_no_longer_allowed_in_index_name",
        },
        {
            "Kind": "index_settings",
            "Level": "warning",
            "Message": "[foobar] Index name cannot contain ':'",
            "Doc": "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.0.html#_literal_literal_is_no_longer_allowed_in_index_name",
        },
    ]


def test_migration_deprecations(run_esctl, fake_es):
    fake_es.on(
        "GET",
        "/_migration/deprecations",
        {
            "cluster_settings": [{"level": "critical", "message": "m", "url": "u", "details": "d"}],
            "node_settings": [],
            "index_settings": {},
        },
    )

    result = run_esctl("migration", "deprecations", "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == [{"Kind": "cluster_settings", "Level": "critical", "Message": "m", "Doc": "u"}]


def test_migration_deprecations_grouped_by_resource(run_esctl, fake_es):
    def deprecation(message):
        return {"level": "warning", "message": message, "url": "u", "details": "d"}

    fake_es.on(
        "GET",
        "/_migration/deprecations",
        {
            "cluster_settings": [],
            "node_settings": [deprecation("node")],
            "index_settings": {"logs": [deprecation("index")]},
            "data_streams": {"metrics-ds": [deprecation("data stream")]},
            "templates": {"logs-template": [deprecation("template")]},
            "ilm_policies": {"hot-warm": [deprecation("policy")]},
            "ml_settings": [],
        },
    )

    result = run_esctl("migration", "deprecations", "-f", "json")

    assert result.code == 0, result.err
    assert [(row["Kind"], row["Message"]) for row in result.json()] == [
        ("node_settings", "node"),
        ("index_settings", "[logs] index"),
        ("data_streams", "[metrics-ds] data stream"),
        ("templates", "[logs-template] template"),
        ("ilm_policies", "[hot-warm] policy"),
    ]
