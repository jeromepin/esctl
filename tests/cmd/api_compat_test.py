"""Commands must only pass arguments the elasticsearch-py client accepts."""


def test_document_get(run_esctl, fake_es):
    fake_es.on("GET", "/logs/_doc/42", {"_index": "logs", "_id": "42", "found": True, "_source": {"msg": "hi"}})

    result = run_esctl("document", "get", "logs", "42", "-f", "json")

    assert result.code == 0, result.err
    assert result.json()["_Source Msg"] == "hi"


def test_repository_show(run_esctl, fake_es):
    fake_es.on("GET", "/_snapshot/backups", {"backups": {"type": "fs", "settings": {"location": "/mnt"}}})

    result = run_esctl("repository", "show", "backups", "-f", "json")

    assert result.code == 0, result.err
    assert result.json()["Type"] == "fs"


def test_repository_verify(run_esctl, fake_es):
    fake_es.on("POST", "/_snapshot/backups/_verify", {"nodes": {"abc": {"name": "node-1"}}})

    result = run_esctl("repository", "verify", "backups")

    assert result.code == 0, result.err
    assert "node-1" in result.out


def test_roles_get(run_esctl, fake_es):
    fake_es.on(
        "GET",
        "/_security/role",
        {"admin": {"cluster": ["all"], "indices": [], "applications": [], "run_as": []}},
    )

    result = run_esctl("roles", "get", "-f", "json")

    assert result.code == 0, result.err
    assert result.json()[0]["Role"] == "admin"


def test_users_get(run_esctl, fake_es):
    fake_es.on("GET", "/_security/user", {"bob": {"username": "bob", "roles": ["admin", "dev"], "enabled": True}})

    result = run_esctl("users", "get", "-f", "json")

    assert result.code == 0, result.err
    assert result.json()[0]["Roles"] == "admin, dev"
