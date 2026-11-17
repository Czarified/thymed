"""Tests for Thymed settings helpers and the Settings applet."""

import json

import pytest
import toml
from textual.widgets import Button, Input, Select

import thymed
from thymed.tui import Settings, ThymedApp


@pytest.fixture
def settings_env(tmp_path):
    """Point Thymed at throwaway data and config files."""
    data_file = tmp_path / "data.dat"
    charges_file = tmp_path / "charges.json"
    config_file = tmp_path / "config.toml"
    data_file.write_text("{}")
    charges_file.write_text(
        json.dumps(
            {
                "5": {
                    "name": "Five",
                    "description": "D",
                    "id": 5,
                    "__type__": "ChargeCode",
                }
            }
        )
    )

    options = thymed.get_options()
    orig_options = {
        k: dict(v) if isinstance(v, dict) else v for k, v in options.items()
    }
    orig = (thymed._DATA, thymed._CHARGES, thymed._CONFIG)

    options.clear()
    options.update(
        {
            "database": {
                "default": 0,
                "data": data_file.as_posix(),
                "charges": charges_file.as_posix(),
            }
        }
    )
    thymed._DATA, thymed._CHARGES, thymed._CONFIG = data_file, charges_file, config_file

    yield tmp_path

    options.clear()
    options.update(orig_options)
    thymed._DATA, thymed._CHARGES, thymed._CONFIG = orig


def test_set_data_file_creates_and_persists(settings_env):
    """A new punch file is created and saved to the config."""
    new = settings_env / "sub" / "punches.json"
    result = thymed.set_data_file(new)

    assert result == new.resolve()
    assert thymed._DATA == new.resolve()
    assert json.loads(new.read_text()) == {}
    saved = toml.loads(thymed._CONFIG.read_text())
    assert saved["database"]["data"] == new.resolve().as_posix()


def test_set_charges_file_rejects_bad_data(settings_env):
    """Invalid JSON or non-dict content is refused and nothing changes."""
    bad = settings_env / "bad.json"
    bad.write_text("not json")
    listy = settings_env / "list.json"
    listy.write_text("[1, 2]")
    before = thymed._CHARGES

    with pytest.raises(thymed.ThymedError):
        thymed.set_charges_file(bad)
    with pytest.raises(thymed.ThymedError):
        thymed.set_charges_file(listy)
    with pytest.raises(thymed.ThymedError):
        thymed.set_charges_file(settings_env)
    assert thymed._CHARGES == before


def test_write_json_follows_current_data_file(settings_env):
    """write_json uses the data file configured at call time."""
    new = thymed.set_data_file(settings_env / "other.dat")
    code = thymed.ChargeCode("Five", "D", 5)
    code.punch()
    code.write_json()

    assert "5" in json.loads(new.read_text())


def test_default_code_and_generic_settings(settings_env):
    """Default code and arbitrary settings round-trip through the config."""
    thymed.set_default_code(5)
    thymed.set_setting("tui", "theme", "nord")

    saved = toml.loads(thymed._CONFIG.read_text())
    assert saved["database"]["default"] == 5
    assert saved["tui"]["theme"] == "nord"
    assert thymed.get_setting("tui", "theme") == "nord"
    assert thymed.get_setting("missing", "key", "fallback") == "fallback"


@pytest.mark.asyncio
async def test_settings_applet(settings_env):
    """Drive the Settings applet end to end."""
    app = ThymedApp()
    async with app.run_test() as pilot:
        await app.action_launch_settings()
        await pilot.pause()
        settings = app.query_one(Settings)

        # Change the punch data file via the Apply button.
        new_data = settings_env / "tui" / "punches.dat"
        settings.query_one("#setting_data", Input).value = str(new_data)
        settings.query_one("#apply_data", Button).press()
        await pilot.pause()
        assert thymed._DATA == new_data.resolve()

        # Bad charges file shows an error and keeps the old file.
        before = thymed._CHARGES
        bad = settings_env / "bad.json"
        bad.write_text("nope")
        settings.query_one("#setting_charges", Input).value = str(bad)
        settings.apply_charges_file()
        await pilot.pause()
        assert thymed._CHARGES == before

        # A fresh charges file empties the default-code picker.
        settings.query_one("#setting_charges", Input).value = str(
            settings_env / "fresh.json"
        )
        settings.apply_charges_file()
        await pilot.pause()
        assert settings.query_one("#setting_default", Select).is_blank()

        # Export folder.
        export = settings_env / "exports"
        settings.query_one("#setting_export", Input).value = str(export)
        settings.apply_export_dir()
        await pilot.pause()
        assert export.is_dir()
        assert (
            thymed.get_setting("reporting", "export_dir") == export.resolve().as_posix()
        )

        # Theme.
        settings.query_one("#setting_theme", Select).value = "nord"
        await pilot.pause()
        assert app.theme == "nord"
        assert thymed.get_setting("tui", "theme") == "nord"

        # Default code.
        settings.query_one("#setting_charges", Input).value = str(before)
        settings.apply_charges_file()
        await pilot.pause()
        settings.query_one("#setting_default", Select).value = "5"
        await pilot.pause()
        assert thymed.get_setting("database", "default") == 5
