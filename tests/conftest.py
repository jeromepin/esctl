"""Shared fixtures.

`run_esctl` runs the real application end-to-end (argument parsing, config
loading, cliff formatters, and the real elasticsearch-py client). Only the
HTTP node is faked by `fake_es`, so serialization, response wrapping, error
mapping and client-side argument validation all behave like in production.
"""

import copy
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml
from elastic_transport import ApiResponseMeta, HttpHeaders, Urllib3HttpNode
from elastic_transport._node._base import NodeApiResponse

from esctl.elasticsearch import Client
from esctl.main import Esctl

DEFAULT_CONFIG: dict[str, Any] = {
    "clusters": {"local": {"servers": ["https://localhost:9200"]}},
    "users": {"admin": {"username": "admin", "password": "secret"}},
    "contexts": {"local": {"cluster": "local", "user": "admin"}},
    "default-context": "local",
    "settings": {"max_retries": 0},
}


@dataclass
class Request:
    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    raw_body: bytes | None

    @property
    def body(self) -> Any:
        if self.raw_body is None:
            return None
        try:
            return json.loads(self.raw_body)
        except ValueError:
            return self.raw_body.decode()


@dataclass
class Response:
    body: Any
    status: int = 200
    content_type: str = "application/json"

    def encode(self) -> bytes:
        if isinstance(self.body, bytes):
            return self.body
        if isinstance(self.body, str) and not self.content_type.endswith("json"):
            return self.body.encode()
        return json.dumps(self.body).encode()


@dataclass
class FakeElasticsearch:
    routes: dict[tuple[str, str], Response] = field(default_factory=dict)
    requests: list[Request] = field(default_factory=list)
    unexpected: list[Request] = field(default_factory=list)

    def on(self, method: str, path: str, body: Any = None, status: int = 200, content_type="application/json"):
        self.routes[(method.upper(), path)] = Response(copy.deepcopy(body), status, content_type)

    def last(self, method: str, path: str) -> Request:
        matching = [r for r in self.requests if r.method == method.upper() and r.path == path]
        assert matching, f"no {method} {path} request was sent; got {[(r.method, r.path) for r in self.requests]}"
        return matching[-1]

    def handle(self, node_config, method, target, body=None, headers=None, **_kwargs):
        url = urlsplit(target)
        request = Request(
            method=method,
            path=url.path,
            query=parse_qs(url.query),
            headers={k.lower(): v for k, v in (headers or {}).items()},
            raw_body=body,
        )
        self.requests.append(request)

        response = self.routes.get((method, url.path))
        if response is None:
            self.unexpected.append(request)
            response = Response({"error": f"no fake route for {method} {url.path}"}, status=404)

        meta = ApiResponseMeta(
            status=response.status,
            http_version="1.1",
            headers=HttpHeaders(
                {"content-type": response.content_type, "x-elastic-product": "Elasticsearch"},
            ),
            duration=0.0,
            node=node_config,
        )
        return NodeApiResponse(meta, response.encode())


@pytest.fixture
def fake_es(monkeypatch):
    fake = FakeElasticsearch()

    def perform_request(node_self, method, target, body=None, headers=None, **kwargs):
        return fake.handle(node_self.config, method, target, body=body, headers=headers, **kwargs)

    monkeypatch.setattr(Urllib3HttpNode, "perform_request", perform_request)
    yield fake

    unexpected = [(r.method, r.path) for r in fake.unexpected]
    assert not unexpected, f"requests without a fake route: {unexpected}"


@pytest.fixture
def write_config(tmp_path):
    def write(config: dict[str, Any] | None = None, name: str = "esctlrc.yml") -> Path:
        path = tmp_path / name
        path.write_text(yaml.safe_dump(DEFAULT_CONFIG if config is None else config))
        return path

    return write


@pytest.fixture
def default_config() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_CONFIG)


@dataclass
class Result:
    code: int
    out: str
    err: str

    def json(self) -> Any:
        return json.loads(self.out)


@pytest.fixture
def run_esctl(write_config, fake_es, capsys):
    """Run `esctl <argv>` and return its exit code and captured output."""

    def run(*argv: str, config: dict[str, Any] | Path | None = None, app_class=Esctl) -> Result:
        config_path = config if isinstance(config, Path) else write_config(config)
        try:
            code = app_class().run(["--config", str(config_path), *argv])
        except SystemExit as exit_:
            code = exit_.code if isinstance(exit_.code, int) else 1
        out, err = capsys.readouterr()
        return Result(code, out, err)

    return run


@pytest.fixture(autouse=True)
def _isolate_global_state():
    """Esctl configures the root logger and the client on every run: undo it."""
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    for handler in root.handlers:
        if handler not in handlers:
            root.removeHandler(handler)
            handler.close()
    root.setLevel(level)
    Client.reset()

    # A test that starts a patch without stopping it leaks into every later test.
    from esctl.commands import EsctlCommon
    from esctl.settings import Settings

    for owner in (EsctlCommon, Settings):
        assert isinstance(owner.__dict__["es"], property), f"{owner.__name__}.es was left patched"
