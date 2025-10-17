FROM debian:bullseye

RUN apt update && apt -y install python3 python3-setuptools python3-pytest iputils-ping mypy

RUN ln -s pytest-3 /usr/bin/pytest

