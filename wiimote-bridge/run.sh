#!/usr/bin/with-contenv bashio

set -euo pipefail

export RADIOS
export DISCOVER_ENABLED
export MQTT_HOST
export MQTT_PORT
export MQTT_USERNAME
export MQTT_PASSWORD
export MQTT_TRANSPORT
export MQTT_SSL
export MQTT_SSL_INSECURE
export TOPIC_PREFIX
export LOG_LEVEL

RADIOS="$(bashio::config 'radios')"
DISCOVER_ENABLED="$(bashio::config 'discover_enabled')"
MQTT_HOST="$(bashio::config 'mqtt_host')"
MQTT_PORT="$(bashio::config 'mqtt_port')"
MQTT_USERNAME="$(bashio::config 'mqtt_username')"
MQTT_PASSWORD="$(bashio::config 'mqtt_password')"
MQTT_TRANSPORT="$(bashio::config 'mqtt_transport')"
MQTT_SSL="$(bashio::config 'mqtt_ssl')"
MQTT_SSL_INSECURE="$(bashio::config 'mqtt_ssl_insecure')"
TOPIC_PREFIX="$(bashio::config 'topic_prefix')"
LOG_LEVEL="$(bashio::config 'log_level')"

bashio::log.info "Starting WiiMote Bridge"
bashio::log.info "Application log level: ${LOG_LEVEL}"
bashio::log.info "MQTT discovery enabled: ${DISCOVER_ENABLED}"
bashio::log.info "MQTT host: ${MQTT_HOST}:${MQTT_PORT}"
bashio::log.info "MQTT transport: ${MQTT_TRANSPORT}"
bashio::log.info "MQTT SSL enabled: ${MQTT_SSL}"
bashio::log.info "MQTT SSL insecure cert verification: ${MQTT_SSL_INSECURE}"
bashio::log.info "Topic prefix: ${TOPIC_PREFIX}"

exec /app/.venv/bin/python -m wiimote_bridge
