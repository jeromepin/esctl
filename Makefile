SHELL:=bash

install:
	@pip3 install .

# Only for storing dev requirements
venv:
	python3 -m venv venv

install-dev: venv
	venv/bin/pip3 install -r dev-requirements.txt

test: install venv
	venv/bin/pytest -svv

test-install:
	docker run --entrypoint=/bin/bash -v `pwd`:/opt:ro python:3.7 -c "cd /opt && pip3 install . && esctl config context list && cat ~/.esctlrc && esctl cluster health"

lint:
	venv/bin/black --exclude=esctl/\(interactive\|override\).py esctl/
	venv/bin/flake8 esctl --count --show-source --statistics --show-source
	venv/bin/flake8 esctl --count --exit-zero --max-complexity=10 --statistics --show-source
	venv/bin/isort . --color
	# venv/bin/mypy esctl/

tag:
	git tag $(shell \grep VERSION setup.py | \egrep -oh "[.0-9]+")
