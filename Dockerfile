FROM debian:bookworm AS runtime

RUN --mount=type=cache,target=/var/cache/apt \
    apt update && apt -y install python3 iputils-ping python3-setuptools python3-pytest

FROM runtime AS dev

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/root/.cache/pip \
    apt -y install pip && pip install --break-system-packages 'mypy>=2.4,<2.5'

