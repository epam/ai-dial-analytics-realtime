.PHONY: all install lint test

all: lint test


install:
	poetry install

test:
	nox -s test

lint:
	nox -s lint
