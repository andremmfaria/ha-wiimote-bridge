# Contributing

Thanks for contributing to Home Assistant WiiMote Bridge.

## Development Scope

This repository has two implementation areas:

- Home Assistant add-on in `wiimote-bridge/`
- ESP32 firmware in `esp32/wiimote-serial-bridge/`

## Prerequisites

Install:

- Python 3.13+
- `uv`
- Docker (for add-on image builds)
- `arduino-cli` with ESP32 core 3.3.7 (for firmware work)
- ESP32 board with Bluetooth Classic support

## Add-on Development Setup

1. Open a shell in `wiimote-bridge/app`.
2. Run tests:

    ```bash
    uv run --dev pytest -q
    ```

3. Optional test targeting:

    ```bash
    uv run --dev pytest -q tests/test_runtime.py
    ```

4. Build add-on image from repository root:

    ```bash
    docker build -f wiimote-bridge/Dockerfile wiimote-bridge
    ```

## Firmware Development Setup

See full guide in `docs/firmware-setup.md`.

Quick commands:

```bash
cd esp32/wiimote-serial-bridge
arduino-cli core install esp32:esp32@3.3.7
arduino-cli lib install --git-url https://github.com/andremmfaria/ESP32Wiimote
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 .
```

## Pull Request Process

1. Create a focused branch.
2. Keep changes scoped to one concern.
3. Run tests and include evidence in PR description.
4. Update `wiimote-bridge/CHANGELOG.md` for user-visible changes.
5. Update docs if behavior, config, or setup changed.
6. If config UI keys changed, update translations in `wiimote-bridge/translations/`.

## Commit Style

Use concise, intent-first messages.

Examples:

- `docs: add issue and PR templates`
- `feat: add watchdog health endpoint`
- `fix: handle malformed serial payload`

## Reporting Issues

- Use GitHub issue templates for bugs and feature requests.
- Include reproducible steps and relevant logs.
- Remove secrets from all shared snippets.
