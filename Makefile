SHELL:=bash
# Same uv as CI (.github/workflows): uv >= 0.13 cannot extract the prettytable sdist required by cliff 3.2
UV_VERSION = 0.9.30
ESCTL_VERSION = $(shell \grep version pyproject.toml | \egrep -oh "[.0-9]+")

install:
	@rm -rf dist/*
	uv build
	uv tool install --force --reinstall dist/esctl-*-py3-none-any.whl

test:
	uv run pytest

# The uv image puts tool executables in /usr/local/bin: no PATH setup needed
test-install:
	docker run --entrypoint=/bin/bash -v `pwd`:/tmp/esctl:ro ghcr.io/astral-sh/uv:$(UV_VERSION)-python$(shell cat .python-version)-bookworm -c "cp -r /tmp/esctl /opt && cd /opt/esctl && uv build && uv tool install dist/esctl-*-py3-none-any.whl && esctl config context list && cat ~/.esctlrc && esctl cluster health"

format:
	uv run ruff check --select I --fix
	uv run ruff check --fix
	uv run ruff format

lint:
	uv run ruff check
	uv run ruff format --check
	uv run ty check

tag:
	git tag $(ESCTL_VERSION)
