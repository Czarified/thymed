"""Test Cases for the ChargeCode class."""
import datetime as dt
import json
import random
import time

import pandas as pd
import pytest
from rich.console import Console

from thymed import _CHARGES
from thymed import _DATA
from thymed import ChargeCode
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


def remove_test_data(id: str = "99999999") -> None:
    """Cleanup the test ChargeCode punch data.

    Testing creates a ChargeCode. This function
    manually removes the data, since deleting/removing
    ChargeCode objects is not currently supported.
    """
    with open(_DATA) as f:
        # We know it won't be blank, since we only call
        # this function after we tested it already. So
        # no try:except like the rest of the codebase.
        times = json.load(f)

    with open(_DATA, "w") as f:
        # Remove the testing code with a pop method.
        _ = times.pop(id)
        # Write the rest of times back to the file.
        _ = f.write(json.dumps(times, indent=2))


# FIXTURES
@pytest.fixture
def blank_code() -> ChargeCode:
    """Return a blank ChargeCode for testing."""
    blank = ChargeCode("Blank boi", "Nothing here...", 99999998)
    return blank


@pytest.fixture
def fake_times(
    start: dt.datetime = None,
    end: dt.datetime = None,
    name: str = "FakeCode",
    description: str = "These times are fake.",
    id: int = 99999999,
    n: int = 250,
    console: Console = None,
) -> None:
    """Temporary function for testing."""
    # Initialize default inputs
    if not start:
        start = dt.datetime(2022, 5, 31)
    if not end:
        end = dt.datetime.today()
    if not console:
        console = Console()
    # Initialize the output variables
    ins = []
    outs = []
    # Iteration variable. We don't want to repeat days or "work" them out of order.
    iter_start = start
    for _i in range(n):
        # Pick a random timestamp in the time range
        date = dt.timedelta(days=random.randint(0, 2)) + iter_start
        iter_start = date
        # Check if we should stop here (beyond the end date)
        if (iter_start >= end) or (date > end):
            break

        # Generate the timedelta for punch in/out on that day
        in_delta = random.randint(-220, 1850)
        out_delta = random.randint(-1000, 1550)

        # Add the deltas for in/out
        in_punch = dt.datetime(
            year=date.year, month=date.month, day=date.day, hour=8
        ) + dt.timedelta(seconds=in_delta)
        ins.append(in_punch)

        out_punch = dt.datetime(
            year=date.year, month=date.month, day=date.day, hour=15
        ) + dt.timedelta(seconds=out_delta)
        outs.append(out_punch)

    df = pd.DataFrame()
    df["in_punch"] = ins
    df["out_punch"] = outs

    console.print(df)

    my_code = ChargeCode(name, description, id)
    console.print(my_code)

    my_code.times = tuple(zip(ins, outs))
    my_code.write_class()
    my_code.write_json()


# # #      T E S T S     # # #


def test_create() -> None:
    """If a ChargeCode can be created."""
    the_code = ChargeCode("test_code", "description", 0)
    assert not the_code.is_active


def test_punch(blank_code) -> None:
    """Punches a charge code, sees active. Punches again, sees inactive."""
    blank_code.punch()
    assert blank_code.is_active
    time.sleep(0.1)
    blank_code.punch()
    assert not blank_code.is_active


def test_data(blank_code) -> None:
    """Write some data, and instantiate a code that recognizes the times."""
    blank_code.punch()
    time.sleep(0.1)
    blank_code.punch()

    blank_code.write_class()
    blank_code.write_json()

    _ = ChargeCode("New Blank Boi", "There's something here.", 99999998)
    remove_test_charge("99999998")
    remove_test_data("99999998")


def test_multiple() -> None:
    """Make multiple for post_init checks."""
    one = ChargeCode("One", "Tester 1, Tester One.", 1)
    one.write_class()
    assert one.is_active is None
    two = ChargeCode("Two", "Tester 2, Tester Two.", 2)
    two.write_class()
    three = ChargeCode("Two", "Tester 3, Tester Two?", 2)
    three.write_class()

    remove_test_charge("1")
    remove_test_charge("2")


def test_fake_time(fake_times, blank_code) -> None:
    """Build some real data to work with."""
    blank_code.punch()
    time.sleep(0.1)
    # Writing JSON after json already has been written,
    # tests different lines of code.
    blank_code.write_class()
    blank_code.write_json()

    remove_test_charge()
    remove_test_data()

    time.sleep(0.1)
    blank_code.punch()
    blank_code.write_json(log=True)
    remove_test_charge("99999998")
    remove_test_data("99999998")


if __name__ == "__main__":  # pragma: no cover
    with open(_DATA) as f:
        times = json.load(f)
        print(times)
        _ = times.pop("99999998")
        print(times)
