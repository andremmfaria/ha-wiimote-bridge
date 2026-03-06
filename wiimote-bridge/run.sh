#!/usr/bin/with-contenv bashio

set -euo pipefail

export SERIAL_PORT
export SERIAL_BAUD
export MQTT_HOST
export MQTT_PORT
export MQTT_USERNAME
export MQTT_PASSWORD
export TOPIC_PREFIX

SERIAL_PORT="$(bashio::config 'serial_port')"
SERIAL_BAUD="$(bashio::config 'serial_baud')"
MQTT_HOST="$(bashio::config 'mqtt_host')"
MQTT_PORT="$(bashio::config 'mqtt_port')"
MQTT_USERNAME="$(bashio::config 'mqtt_username')"
MQTT_PASSWORD="$(bashio::config 'mqtt_password')"
TOPIC_PREFIX="$(bashio::config 'topic_prefix')"

bashio::log.info "Starting WiiMote Bridge"
bashio::log.info "Serial port: ${SERIAL_PORT}"
bashio::log.info "Serial baud: ${SERIAL_BAUD}"
bashio::log.info "MQTT host: ${MQTT_HOST}:${MQTT_PORT}"
bashio::log.info "Topic prefix: ${TOPIC_PREFIX}"

exec python3 /app/main.py
