SHELL:=bash

install:
	@pip3 install .

test:
	@pytest -svv

test-install:
	docker run --entrypoint=/bin/bash -v `pwd`:/opt:ro python:3.7 -c "cd /opt && pip3 install . && esctl config context list && cat ~/.esctlrc && esctl cluster health"

lint:
	flake8 esctl --count --show-source --statistics --show-source
	flake8 esctl --count --exit-zero --max-complexity=10 --statistics --show-source

fmt:
	python3 -m isort . --color
	black --exclude=esctl/\(interactive\|override\).py esctl/

tag:
	git tag $(shell \grep VERSION setup.py | \egrep -oh "[.0-9]+")
