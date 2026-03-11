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

# Use uv with a frozen lockfile for reproducible dependency installs.
RUN pip3 install --no-cache-dir uv==0.10.9

COPY app /app
RUN cd /app && uv sync --frozen --no-dev

COPY run.sh /run.sh

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
