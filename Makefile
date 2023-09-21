PORT = 5001
IMAGE_NAME = ai-dial-analytics-realtime


.PHONY: all build serve docker_serve lint format test clean help


all: build


build:                  ## build the source and wheels archives
	poetry build


serve:                  ## run the server locally
	poetry install
	poetry run uvicorn ai_dial_analytics_realtime.app:app --host=0.0.0.0 --port=$(PORT)


docker_serve:           ## run the server from the docker
	docker build --platform linux/amd64 -t $(IMAGE_NAME):latest .
	docker run --platform linux/amd64 --env-file ./.env --rm -p $(PORT):5000 $(IMAGE_NAME):latest


lint:                   ## run linters
	nox -s lint


format:                 ## run code formatters
	nox -s format


test:                   ## run unit tests
	nox -s tests


clean:                  ## clean virtual env and build artifacts
	@rm -rf .venv
	@rm -rf .nox
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete


help:                   ## show this help
	@echo '===================='
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sed -e 's/##/- /'
