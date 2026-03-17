# Changelog

## 0.4.1

- Fix MQTT discovery publish timing by running discovery only after a confirmed connection and off the MQTT loop thread, preventing keepalive starvation/disconnect timeouts.
- Republish retained MQTT discovery configs on reconnect so entities recover after broker restarts without duplicate creation.
- Add discovery observability logs, including expected entity counts and publish success/failure summaries.
- Add MQTT connection mode controls for transport/TLS and normalize runtime wiring end-to-end.
- Add automatic MQTT port selection when `port: 0` based on mode: `tcp=1883`, `websockets=1884`, `tcp+ssl=8883`, `websockets+ssl=8884`.
- Migrate add-on options/schema to nested `mqtt` configuration (`host`, `port`, `username`, `password`, `transport`, `ssl`, `ssl_insecure`, `topic_prefix`, `discover_enabled`) and update `run.sh` key paths accordingly.
- Update docs and release checklist for discovery behavior, retained-topic validation, and nested MQTT configuration.
- Expand and update automated tests for reconnect-safe discovery, transport/TLS handling, and auto-port defaults.
- Update all translation files to the nested `mqtt.fields` format required by Home Assistant for object options, restoring option descriptions in the UI.
- Harmonize localized `mqtt.port` descriptions and add localized `mqtt` group descriptions (including an "expand to modify" hint).

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
