.PHONY: build test

test: build
	docker compose run monitor /bin/sh -c 'cd /srv; python3 -m pytest tests'

build:
	docker compose down
	docker compose build monitor


