FROM debian:bullseye

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/root/.cache/pip \
    apt update && apt -y install python3 python3-setuptools python3-pytest iputils-ping pip && pip install mypy==1.18.2

RUN ln -s pytest-3 /usr/bin/pytest

