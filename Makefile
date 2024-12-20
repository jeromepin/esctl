SHELL:=bash
ESCTL_VERSION = $(shell \grep version pyproject.toml | \egrep -oh "[.0-9]+")

install:
	@rm -rf dist/*
	uv build
	uv run pipx install --force dist/esctl-*-py3-none-any.whl

test:
	uv run pytest

test-install:
	docker run --entrypoint=/bin/bash -v `pwd`:/tmp/esctl:ro python:$(shell cat .python-version) -c "pip install uv && cp -r /tmp/esctl /opt && cd /opt/esctl && uv build && uv run pipx install --force dist/esctl-*-py3-none-any.whl && uv run pipx ensurepath && source ~/.bashrc && esctl config context list && cat ~/.esctlrc && esctl cluster health"

format:
	uv run ruff check --select I --fix
	uv run ruff check --fix
	uv run ruff format
	# uv run mypy esctl/

tag:
	git tag $(ESCTL_VERSION)
