"""Test Cases for the ChargeCode class."""

import datetime as dt
import random

import pandas as pd
import pytest
from rich.console import Console

from thymed import ChargeCode
from thymed import TimeCard
from thymed import delete_charge


# CLEANUP UTILITIES


# FIXTURES
@pytest.fixture
def fake_times(
    start: dt.datetime = None,
    end: dt.datetime = None,
    name: str = "FakeCode",
    description: str = "These times are fake.",
    id: int = 99999999,
    n: int = 60,
    console: Console = None,
) -> None:
    """Temporary function for testing."""
    # Initialize default inputs
    if not end:
        end = dt.datetime.today()
    if not start:
        start = end - dt.timedelta(days=35)
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

    my_code = ChargeCode(name, description, id)

    my_code.times = tuple(zip(ins, outs))
    my_code.write_class()
    my_code.write_json()


# # #      T E S T S     # # #


def test_timecard():
    """Doesn't raise an Exception.

    We pass an ID that doesn't exist. This will get a JSONDecodeError,
    followed by a KeyError, which is automatically handled by the class.
    """
    _ = TimeCard(99999998)


def test_weekly(fake_times):
    """Can build a TimeCard and pull the report."""
    weekly = TimeCard(99999999)
    df = weekly.weekly_report()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    delete_charge("99999999")


def test_period(fake_times):
    """Can build a TimeCard and pull the report."""
    period = TimeCard(99999999)
    df = period.pay_period_report()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    delete_charge("99999999")


def test_monthly(fake_times):
    """Can build a TimeCard and pull the report."""
    monthly = TimeCard(99999999)
    df = monthly.monthly_report()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    delete_charge("99999999")


if __name__ == "__main__":  # pragma: no cover

    def make_times(
        start: dt.datetime = None,
        end: dt.datetime = None,
        name: str = "FakeCode",
        description: str = "These times are fake.",
        id: int = 99999999,
        n: int = 60,
        console: Console = None,
    ) -> None:
        """Temporary function for testing."""
        # Initialize default inputs
        if not end:
            end = dt.datetime.today()
        if not start:
            start = end - dt.timedelta(days=35)
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

        my_code = ChargeCode(name, description, id)

        my_code.times = tuple(zip(ins, outs))
        my_code.write_class()
        my_code.write_json()

    make_times(name="Project Alpha", description="Work on project Alpha.", id=103)
    make_times(name="Project Beta", description="Work on project Beta.", id=104)
    make_times(name="Project Gamma", description="Work on project Gamma.", id=105)
