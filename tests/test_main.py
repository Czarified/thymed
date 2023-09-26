"""Test cases for the __main__ module."""
import json

import pytest
from click.testing import CliRunner

from thymed import _CHARGES
from thymed import __main__
from thymed import object_decoder


# CLEANUP UTILITIES
def remove_test_charge(id: str = "99999999") -> None:
    """Cleanup the test ChargeCode.

    Testing creates a ChargeCode. This function
    manually removes the data, since deleting/removing
    ChargeCode objects is not currently supported.
    """
    with open(_CHARGES) as f:
        # We know it won't be blank, since we only call
        # this function after we tested it already. So
        # no try:except like the rest of the codebase.
        codes = json.load(f, object_hook=object_decoder)

    with open(_CHARGES, "w") as f:
        # Remove the testing code with a pop method.
        _ = codes.pop(id)
        # Convert the dict of ChargeCodes into a plain dict
        out = {}
        for k, v in codes.items():
            dict_val = v.__dict__
            dict_val["__type__"] = "ChargeCode"
            del dict_val["times"]
            out[k] = dict_val
        # Write the new set of codes back to the file.
        _ = f.write(json.dumps(out, indent=2))


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


# # #      T E S T S     # # #


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.main)
    assert result.exit_code == 0


def test_main_hello(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.hello)
    assert result.exit_code == 0


def test_main_create(runner: CliRunner) -> None:
    """It exits with a status code of zero.

    Create a simple ChargeCode for testing.
    """
    result = runner.invoke(
        __main__.create, input="\n".join(["test_code", "description", "99999999", "y"])
    )
    assert result.exit_code == 0

    remove_test_charge()


def test_main_punch_default(runner: CliRunner) -> None:
    """It exits with a status code of zero.

    This test will call the default code. In the CI,
    this chargecode will not exist, but the error is
    handled and the command continues on.

    TODO: We need to _actually_ test punching charge codes...
    """
    result = runner.invoke(__main__.punch)
    assert result.exit_code == 0


def test_main_punch_code(runner: CliRunner) -> None:
    """It exits with a status code of zero.

    This test will call a specific punch code. Again,
    in the automated CI this will not exist.
    """
    result = runner.invoke(__main__.punch, "99999999")
    assert result.exit_code == 0


def test_main_punch_multiple(runner: CliRunner) -> None:
    """It exits with a status code of zero.

    This will execute all the remaining cleanup
    lines in our cleanup function.
    """
    _ = runner.invoke(
        __main__.create, input="\n".join(["test_code", "description", "99999999", "y"])
    )
    _ = runner.invoke(
        __main__.create, input="\n".join(["test_code", "description", "99999998", "y"])
    )

    remove_test_charge()
    remove_test_charge("99999998")


def test_main_list_generic(runner: CliRunner) -> None:
    """It exits with a status code of zero.

    This test runs the list function. There are a couple
    more cases that should be specifically tested, for 100%.

    TODO: Break this out into multiple list-testers:
        (No charges defined, Charges defined but not
        initialized, and Charges defined and initialized
        to active/passive states)
    """
    result = runner.invoke(__main__.list)
    assert result.exit_code == 0
