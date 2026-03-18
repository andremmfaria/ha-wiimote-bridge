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

# Install uv in an isolated virtual environment to avoid PEP 668 issues.
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir uv==0.10.9

ENV PATH="/venv/bin:${PATH}"

COPY app /app
RUN cd /app && uv sync --frozen --no-dev

COPY run.sh /run.sh

RUN chmod a+x /run.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:9000/health || exit 1

CMD [ "/run.sh" ]
