PORT = 5001
IMAGE_NAME = ai-dial-analytics-realtime
ARGS =


.PHONY: all build serve docker_build docker_serve lint format test test_all docs clean help


all: build


build:
	poetry build


serve:
	poetry install --only main
	poetry run uvicorn aidial_analytics_realtime.app:app --port=$(PORT) --env-file .env


docker_build:
	docker build --platform linux/amd64 -t $(IMAGE_NAME):dev .


docker_serve: docker_build
	docker run --platform linux/amd64 --env-file ./.env --rm -p $(PORT):5000 $(IMAGE_NAME):dev


lint:
	poetry install --only nox
	poetry run nox -s lint


format:
	poetry install --only nox
	poetry run nox -s format


test:
	poetry install --only nox
	poetry run -- nox -s tests -- -m "not with_external" $(ARGS)


test_all:
	poetry install --only nox
	poetry run -- nox -s tests -- $(ARGS)


docs:
	# Do nothing


clean:
	@rm -rf .venv
	@rm -rf .nox
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete


help:
	@echo '===================='
	@echo 'build                        - build the source and wheels archives'
	@echo 'docker_build                 - build the docker image'
	@echo 'clean                        - clean virtual env and build artifacts'
	@echo '-- LINTING --'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
	@echo '-- RUN --'
	@echo 'serve                        - run the server locally'
	@echo 'docker_serve                 - run the server using docker'
	@echo '-- TESTS --'
	@echo 'test                         - run unit tests'
