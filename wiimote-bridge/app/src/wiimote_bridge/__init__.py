"""WiiMote bridge runtime package."""

import os

from wiimote_bridge.core.run import run


if os.environ.get("WIIMOTE_BRIDGE_AUTORUN", "1") == "1":
	raise SystemExit(run())

