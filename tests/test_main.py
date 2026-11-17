"""Test cases for the __main__ module."""

import json

import pytest
from click.testing import CliRunner

import thymed
from thymed import __main__


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    """Point Thymed at throwaway files so the CLI never touches ~/.thymed."""
    data = tmp_path / "punches.dat"
    charges = tmp_path / "codes.json"
    data.write_text("{}")
    charges.write_text("{}")
    monkeypatch.setattr(thymed, "_DATA", data)
    monkeypatch.setattr(thymed, "_CHARGES", charges)
    monkeypatch.setattr(thymed, "_CONFIG", tmp_path / "config.toml")
    monkeypatch.setitem(
        thymed.get_options(),
        "database",
        {"data": data.as_posix(), "charges": charges.as_posix(), "default": 0},
    )
    return data, charges


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def create_code(runner: CliRunner, id: int, name: str = "test_code") -> None:
    """Create a ChargeCode through the CLI."""
    result = runner.invoke(
        __main__.create, input="\n".join([name, "description", str(id), "y"])
    )
    assert result.exit_code == 0


def punches(id: int) -> list:
    """Return the stored punches for a ChargeCode id."""
    return json.loads(thymed._DATA.read_text()).get(str(id), [])


# # #      T E S T S     # # #


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.main, ["--help"])
    assert result.exit_code == 0


def test_main_hello(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.hello)
    assert result.exit_code == 0


def test_main_create(runner: CliRunner, isolated_data) -> None:
    """Creating a ChargeCode writes it to the charges file."""
    _, charges = isolated_data
    create_code(runner, 7, name="seven")
    stored = json.loads(charges.read_text())
    assert stored["7"]["name"] == "seven"


def test_main_punch_default_missing(runner: CliRunner) -> None:
    """Punching a default code that doesn't exist exits cleanly."""
    result = runner.invoke(__main__.punch)
    assert result.exit_code == 0
    assert "No code to punch" in result.output
    assert punches(0) == []


def test_main_punch_default(runner: CliRunner) -> None:
    """Punching with no id toggles the default code."""
    create_code(runner, 0)
    result = runner.invoke(__main__.punch)
    assert result.exit_code == 0
    assert len(punches(0)) == 1
    assert len(punches(0)[0]) == 1  # clocked in


def test_main_punch_code(runner: CliRunner) -> None:
    """Punching a specific code twice clocks in, then out."""
    create_code(runner, 42)
    runner.invoke(__main__.punch, ["42"])
    result = runner.invoke(__main__.punch, ["42"])
    assert result.exit_code == 0
    assert len(punches(42)) == 1
    assert len(punches(42)[0]) == 2  # clocked out


def test_main_punch_unknown_code(runner: CliRunner) -> None:
    """Punching an unknown code exits cleanly without writing data."""
    result = runner.invoke(__main__.punch, ["123"])
    assert result.exit_code == 0
    assert punches(123) == []


def test_main_list_generic(runner: CliRunner) -> None:
    """Listing codes shows the codes in the database."""
    create_code(runner, 5, name="listed")
    result = runner.invoke(__main__.list)
    assert result.exit_code == 0
    assert "listed" in result.output
