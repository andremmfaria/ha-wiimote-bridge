# Changelog

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
