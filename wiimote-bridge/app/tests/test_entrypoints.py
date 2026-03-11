import importlib
import runpy
import sys
import types


def test_package_main_module_executes(monkeypatch):
    monkeypatch.setenv("WIIMOTE_BRIDGE_AUTORUN", "0")
    runpy.run_module("wiimote_bridge", run_name="__main__")


def test_package_autorun_on_import(monkeypatch):
    monkeypatch.setenv("WIIMOTE_BRIDGE_AUTORUN", "1")

    core_pkg = types.ModuleType("wiimote_bridge.core")
    core_run_mod = types.ModuleType("wiimote_bridge.core.run")

    def fake_run():
        return 0

    core_run_mod.run = fake_run

    monkeypatch.setitem(sys.modules, "wiimote_bridge.core", core_pkg)
    monkeypatch.setitem(sys.modules, "wiimote_bridge.core.run", core_run_mod)
    sys.modules.pop("wiimote_bridge", None)

    try:
        with __import__("pytest").raises(SystemExit) as exc:
            importlib.import_module("wiimote_bridge")
        assert exc.value.code == 0
    finally:
        sys.modules.pop("wiimote_bridge", None)
