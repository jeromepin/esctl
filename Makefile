SHELL:=bash

install:
	@python3 setup.py install >> /dev/null

test: install
	@cd tests && ward

lint:
	flake8 esctl --count --show-source --statistics --show-source
	flake8 esctl --count --exit-zero --max-complexity=10 --statistics --show-source

fmt:
	black --exclude=esctl/\(interactive\|override\).py --verbose esctl/

tag:
	git tag $(shell \grep VERSION setup.py | \egrep -oh "[.0-9]+")
