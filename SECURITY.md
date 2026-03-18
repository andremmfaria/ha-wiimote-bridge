# Security Policy

## Supported Versions

Security fixes are applied to the latest released version on the `main` branch.

## Reporting a Vulnerability

Please do not open public issues for suspected vulnerabilities.

Report privately using one of the following:

- GitHub Security Advisories (preferred):
  - Go to the repository Security tab.
  - Click "Report a vulnerability".
- Direct maintainer contact if advisory flow is unavailable.

Include:

- Description of the issue
- Impact and potential exploitability
- Reproduction steps or proof of concept
- Affected versions and environment details
- Any proposed mitigation

## Response Expectations

- Initial acknowledgment target: within 72 hours
- Triage and severity assessment after acknowledgment
- Fix timeline depends on severity and complexity
- Coordinated disclosure after a fix is available

## Hardening Notes

This project follows least-privilege defaults for Home Assistant add-ons:

- `privileged: false`
- explicit API access flags disabled unless required
- only minimal runtime permissions enabled

If you identify unnecessary permissions or risky defaults, please report them as a security concern.
