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
export HEALTH_PORT

RADIOS="$(bashio::config 'radios')"
DISCOVER_ENABLED="$(bashio::config 'mqtt.discover_enabled')"
MQTT_HOST="$(bashio::config 'mqtt.host')"
MQTT_PORT="$(bashio::config 'mqtt.port')"
MQTT_USERNAME="$(bashio::config 'mqtt.username')"
MQTT_PASSWORD="$(bashio::config 'mqtt.password')"
MQTT_TRANSPORT="$(bashio::config 'mqtt.transport')"
MQTT_SSL="$(bashio::config 'mqtt.ssl')"
MQTT_SSL_INSECURE="$(bashio::config 'mqtt.ssl_insecure')"
TOPIC_PREFIX="$(bashio::config 'mqtt.topic_prefix')"
LOG_LEVEL="$(bashio::config 'log_level')"
HEALTH_PORT="$(bashio::config 'health_port')"

if [[ -z "${MQTT_PORT}" || "${MQTT_PORT}" == "0" ]]; then
	transport_normalized="${MQTT_TRANSPORT,,}"
	ssl_normalized="${MQTT_SSL,,}"

	if [[ "${transport_normalized}" == "websockets" ]]; then
		if [[ "${ssl_normalized}" == "true" ]]; then
			MQTT_PORT="8884"
		else
			MQTT_PORT="1884"
		fi
	else
		if [[ "${ssl_normalized}" == "true" ]]; then
			MQTT_PORT="8883"
		else
			MQTT_PORT="1883"
		fi
	fi
fi

bashio::log.info "Starting WiiMote Bridge"
bashio::log.info "Application log level: ${LOG_LEVEL}"
bashio::log.info "MQTT discovery enabled: ${DISCOVER_ENABLED}"
bashio::log.info "MQTT host: ${MQTT_HOST}:${MQTT_PORT}"
bashio::log.info "MQTT transport: ${MQTT_TRANSPORT}"
bashio::log.info "MQTT SSL enabled: ${MQTT_SSL}"
bashio::log.info "MQTT SSL insecure cert verification: ${MQTT_SSL_INSECURE}"
bashio::log.info "Topic prefix: ${TOPIC_PREFIX}"
bashio::log.info "Health endpoint port: ${HEALTH_PORT}"

exec /app/.venv/bin/python -m wiimote_bridge
