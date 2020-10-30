SHELL:=bash

install:
	@python3 setup.py install >> /dev/null

test: install
	@cd tests && ward test --no-capture-output

test-install:
	docker run --entrypoint=/bin/bash -v `pwd`:/opt:ro python:3.7 -c "cd /opt && pip3 install . && esctl config context list && cat ~/.esctlrc && esctl cluster health"

lint:
	flake8 esctl --count --show-source --statistics --show-source
	flake8 esctl --count --exit-zero --max-complexity=10 --statistics --show-source

fmt:
	black --exclude=esctl/\(interactive\|override\).py --verbose esctl/

tag:
	git tag $(shell \grep VERSION setup.py | \egrep -oh "[.0-9]+")
