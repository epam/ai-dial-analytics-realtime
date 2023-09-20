.PHONY: all install test lint format

all:
	nox

install:
	poetry install

test:
	nox -s tests

lint:
	nox -s lint

format:
	nox -s format
