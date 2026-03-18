# Changelog

## 0.4.5

- Add a reusable Home Assistant automation blueprint for common Wii Remote button actions in `blueprints/automation/wiimote_common.yaml`.
- Make multi-controller support more prominent in the README and add-on documentation.
- Expand protocol and add-on docs to clarify how MQTT Discovery maps connection, battery, and button topics into Home Assistant entities.
- Add FAQ, troubleshooting, and reserved screenshot file references to `wiimote-bridge/DOCS.md`.
- Add `hacs.json` with baseline metadata for HACS compatibility.

## 0.4.4

- Add internal HTTP health endpoint (`GET /health`) with configurable `health_port` option (default `9000`).
- Add native Docker `HEALTHCHECK` directive to the add-on image that probes the health endpoint every 30 seconds.
- The Home Assistant supervisor restarts the add-on automatically when the container is marked unhealthy by Docker.
- Update startup/runtime wiring (`run.sh`, settings parsing, and runtime loop) to start and stop the health endpoint safely.
- Add tests for health port configuration parsing and document health-check behavior in add-on docs.
- Automate firmware release assets by building `wiimote-serial-bridge.bin` in the release workflow and attaching it to GitHub releases.
- Update firmware setup docs to reference the prebuilt release binary.

## 0.4.3

- Add add-on runtime hardening with a custom AppArmor profile at `wiimote-bridge/apparmor.txt`.
- Document that seccomp is not supported as an add-on `config.yaml` key in the current Home Assistant schema.
- Document the security hardening model and rationale in `wiimote-bridge/DOCS.md`.
- Enhance CI with add-on linting (`frenck/action-addon-linter`), Ruff checks, MyPy checks, and coverage test execution.
- Add Dependabot configuration for Python (`wiimote-bridge/app`), Docker (`wiimote-bridge`), and GitHub Actions updates.
- Add development tooling configuration for Ruff and MyPy in `wiimote-bridge/app/pyproject.toml` and refresh `uv.lock`.

## 0.4.2

- Add add-on metadata and hardening declarations in `wiimote-bridge/config.yaml`: `stage: stable`, minimum Home Assistant version, `privileged: []`, and explicit `auth_api`, `hassio_api`, and `homeassistant_api` flags.
- Add GitHub community health files: issue templates, pull request template, `CONTRIBUTING.md`, and `SECURITY.md`.
- Add README badges for CI workflow status and project license.
- Ignore local planning notes by adding `plans/` to `.gitignore`.

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
