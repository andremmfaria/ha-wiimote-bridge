ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
ARG BUILD_ARCH=amd64
ARG BUILD_VERSION=dev
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8

LABEL \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.arch="${BUILD_ARCH}"

RUN apk add --no-cache \
    bash \
    py3-pip \
    python3

# Use uv to install pinned runtime dependencies and the local package.
RUN pip3 install --no-cache-dir uv==0.6.6

COPY app/pyproject.toml /app/pyproject.toml
COPY app/src /app/src
RUN uv pip install --system /app

COPY run.sh /run.sh
COPY app /app

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
