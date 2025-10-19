.PHONY: build mypy test all

all: test mypy

test: build
	docker compose run monitor /bin/sh -c 'cd /srv; python3 -m pytest tests'

mypy: build
	docker compose run monitor-dev /bin/sh -c 'cd /srv; mypy .'

build:
	docker compose down --remove-orphans
	docker compose build monitor
	docker compose build monitor-dev
