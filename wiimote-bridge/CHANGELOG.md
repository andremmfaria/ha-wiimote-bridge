# Changelog

## 0.4.1

- Fix MQTT Discovery timing by publishing discovery configs only after a confirmed MQTT connection (`on_connect`) instead of immediately after async connect startup.
- Republish retained MQTT Discovery configs on reconnect so entities recover after broker outages/restarts without duplicate entity creation.
- Add discovery publication observability with startup/reconnect logs and per-run entity publish success/failure counts.
- Improve Home Assistant discovery metadata consistency by simplifying device metadata and keeping stable retained discovery topics as source of truth.
- Add MQTT transport and security options: `mqtt_transport` (`tcp` or `websockets`), `mqtt_ssl`, and `mqtt_ssl_insecure`.
- Add mode-based MQTT auto-port defaults when `mqtt_port: 0`: `tcp=1883`, `websockets=1884`, `tcp/ssl=8883`, `websockets/ssl=8884`.
- Wire new MQTT options end-to-end from add-on `config.yaml` through `run.sh` into runtime settings.
- Update tests for discovery reconnect behavior, MQTT transport/TLS configuration, and auto-port selection.
- Update documentation and release checklist to describe discovery behavior, retained-topic verification, entities vs raw topics, and new MQTT security/transport options.
- Add translation entries for the new MQTT options across all locale files.

## 0.4.0

- Replace single-radio config (`serial_port`, `serial_baud`, `controller_id`) with a `radios` list so one add-on instance can manage multiple ESP32 radios.
- Run one serial reader thread per configured radio and route events with each radio's `controller_id`.
- Add Home Assistant MQTT Discovery publishing for connection, battery, and button entities per controller.
- Add `discover_enabled` option to enable or disable MQTT Discovery publishing.
- Update add-on schema, startup environment wiring, translations, and documentation for the new `radios` and `discover_enabled` options.
- Expand automated tests to cover multi-radio runtime behavior and MQTT Discovery publishing.

## 0.3.1

- Add add-on artwork files at `wiimote-bridge/icon.png` and `wiimote-bridge/logo.png` so Home Assistant can render the add-on icon and detail logo.
- Handle MQTT publish failures when disconnected without raising runtime tracebacks in the serial processing loop.
- Rate-limit disconnected MQTT publish warnings to once every 15 seconds.

## 0.3.0

- Improve runtime logging and add configurable log levels.
- Add translation updates for the new log-level option.
- Improve documentation coverage for setup and operation.
- Implement full serial message forwarding to MQTT events topics.
- Update compatibility with the newer WiiMote library version.

## 0.2.0

- Add Home Assistant add-on extension files and translations.
- Restructure application architecture for maintainability.
- Add lock file and automated tests for the Python app.
- Update Python package dependencies and Docker build setup.
- Add GitHub Actions workflows for CI and release publishing.

## 0.1.0

- Initial repository scaffolding for Home Assistant add-on distribution.
- Add Python bridge application and ESP32 firmware project.
- Add add-on and project documentation (README, setup, and protocol docs).
- Implement controller disconnection and battery-level handling.
- Refactor serial bridge processing flow for runtime stability.
- Add initial add-on artwork and docs before first tagged release.
