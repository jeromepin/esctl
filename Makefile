install:
	python3 setup.py install >> /dev/null

test: install
	pytest -sv