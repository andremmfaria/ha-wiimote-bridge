#!/usr/bin/with-contenv bashio

set -euo pipefail

export RADIOS
export DISCOVER_ENABLED
export MQTT_HOST
export MQTT_PORT
export MQTT_USERNAME
export MQTT_PASSWORD
export TOPIC_PREFIX
export LOG_LEVEL

RADIOS="$(bashio::config 'radios')"
DISCOVER_ENABLED="$(bashio::config 'discover_enabled')"
MQTT_HOST="$(bashio::config 'mqtt_host')"
MQTT_PORT="$(bashio::config 'mqtt_port')"
MQTT_USERNAME="$(bashio::config 'mqtt_username')"
MQTT_PASSWORD="$(bashio::config 'mqtt_password')"
TOPIC_PREFIX="$(bashio::config 'topic_prefix')"
LOG_LEVEL="$(bashio::config 'log_level')"

bashio::log.info "Starting WiiMote Bridge"
bashio::log.info "Application log level: ${LOG_LEVEL}"
bashio::log.info "MQTT discovery enabled: ${DISCOVER_ENABLED}"
bashio::log.info "MQTT host: ${MQTT_HOST}:${MQTT_PORT}"
bashio::log.info "Topic prefix: ${TOPIC_PREFIX}"

exec /app/.venv/bin/python -m wiimote_bridge
