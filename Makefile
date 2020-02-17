install:
	python3 setup.py install >> /dev/null

test: install
	pytest -sv

lint: install
	flake8 esctl --count --show-source --statistics --show-source
	flake8 esctl --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --show-source
	mypy esctl/

fmt:
	black --exclude=esctl/\(interactive\|override\).py --verbose esctl/
