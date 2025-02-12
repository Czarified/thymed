"""Thymed.

This file contains basic functions and classes
related to to time-keeping.
"""

import datetime as dt
import json
from copy import copy
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import List
from typing import Tuple

import pandas as pd
import toml
from rich.console import Console
from rich.panel import Panel


# CONSTANTS

# For now, hardocde some files
# TODO: Make this config directory customizable?
__DIR = Path.home() / Path(".thymed")
__CONFIG = __DIR / Path("config.toml")

if not __DIR.exists():
    # This is the first time a user has run Thymed.
    __DIR.mkdir()
    __CONFIG.touch()
    PUNCHFILE = Path(__DIR / "thymed_punches.dat")
    CHARGEFILE = Path(__DIR / "thymed_codes.json")
    default_config = f"""
        title = "Thymed Config"

        [database]
        # Where all charging punches are recorded
        data = "{PUNCHFILE.as_posix()}"

        # Where all charge code objects are recorded
        charges = "{CHARGEFILE.as_posix()}"

        # The default charge code
        default = 0
    """
    parsed_toml = toml.loads(default_config)
    with open(__CONFIG, "w") as f:
        _ = toml.dump(parsed_toml, f)


with open(__CONFIG) as f:
    __OPTIONS = toml.load(f)

# The data file to store information.
# Controlled in the CONFIG file, and therefore customizable by user
_DATA = Path(__OPTIONS["database"]["data"])
_CHARGES = Path(__OPTIONS["database"]["charges"])

# If the datafiles don't exist, we need to make them
if not _DATA.exists():
    _DATA.touch()

if not _CHARGES.exists():
    _CHARGES.touch()


# Exceptions


class ThymedError(Exception):
    """A custome Exception for Thymed."""


# Classes


@dataclass
class ChargeCode:
    """A ChargeCode represents a type of work to dedicate hours to.

    ChargeCodes have a name, description,
    identification number, and optional limits on time
    per week and total time dedicated.

    Attributes:
        times   :   times is the heart of the dataclass,
                    it contains all the time code data in
                    a list of tuples. For example:
                    ::python
                    [(Datetime, Datetime), ... (Datetime, Datetime)]
    """

    name: str
    description: str
    id: int

    times: List[Tuple[dt.datetime, dt.datetime]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Stuff to do right after instantiation.

        Upon instantiation, need to look for existing data, and read in
        the times. If existing data is in the record for this charge code
        id, the times array will be initialized as that complete array.
        """
        try:
            with open(_DATA) as infile:
                # Read the existing file and store it
                try:
                    existing = json.load(infile)
                    # Keys read from the JSON will be str. Convert to int
                    keys = [int(key) for key in existing.keys()]
                    # However, keys in the final are still str, so use an fstring
                    if self.id in keys:
                        str_times = existing[f"{self.id}"]
                        for entry in str_times:
                            self.times.append(
                                tuple(dt.datetime.fromisoformat(time) for time in entry)
                            )
                except json.JSONDecodeError:  # pragma: no cover
                    # If the file is completely blank, we will get an error
                    pass
        except Exception as e:  # pragma: no cover
            # Otherwise, let me know what went wrong
            raise e

    @property
    def is_active(self) -> Any:
        """The charge code is active if it has been activated, but not closed."""
        # If the last item in the times list has only 1 entry,
        # we assume the code is still active.
        if len(self.times) == 0:
            return None

        return True if len(self.times[-1]) == 1 else False

    def punch(self) -> None:
        """Punch in/out of chargeable time."""
        if self.is_active:
            # Close the code.
            self.times[-1] = (self.times[-1][0], dt.datetime.now())
        else:
            # Open the code.
            self.times.append((dt.datetime.now(),))

    def write_json(self, data: Path = _DATA, log: bool = False) -> None:
        """Write the times data to a json file.

        Read the file first, then append the times to their
        appropriate charge code number.
        """
        console = Console()
        _times = []
        for entry in self.times:
            # Open punches are of length 1
            # Closed punches are of length 2
            # Either way, append it as a tuple of isoformat
            _times.append(tuple(time.isoformat() for time in entry))

        # Need to attempt some tidy data handling
        try:
            with open(data) as infile:
                # Read the existing file and store it
                existing = json.load(infile)
                # # Make a copy, just for clarity
                # We need the copy to carry all the data which does not pertain
                # to the current specific ChargeCode.
                final_data = copy(existing)
                # We overwrite data directly here, because the post_init method
                # reads the same file.
                final_data[f"{self.id}"] = _times
        except json.JSONDecodeError:  # pragma: no cover
            # Unless we can't read the file
            console.log("[red]Got JSONDecodeError, assuming the file was blank...")
            final_data = {self.id: _times}

        # Serializing json
        if log:
            console.print("Serializing JSON-formatted time data...")
        json_object = json.dumps(final_data, indent=2)
        if log:
            console.print(json_object)

        # Write json
        with open(data, "w") as outfile:
            if log:
                console.print("Writing JSON data to file...")
            outfile.write(json_object)

    def write_class(self) -> None:
        """Write the class to the Charges json file."""
        out = copy(self.__dict__)
        out["__type__"] = "ChargeCode"
        del out["times"]

        # Read the stored data
        with open(_CHARGES) as f:
            try:
                codes = json.load(f)
            except json.JSONDecodeError:  # pragma: no cover
                # If the file is completely blank, we will get an error
                codes = dict()

        # We're going to write new data
        with open(_CHARGES, "w") as f:
            # If the current code is not in the keys
            if not str(self.id) in codes.keys():
                # We can create a new entry for it
                codes[self.id] = out
            else:
                # A ChargeCode with the id already exists
                # TODO: prompt user and ask for overwrite
                pass

            # Write the exact data to file
            _ = f.write(json.dumps(codes, indent=2))


@dataclass
class TimeCard:
    """A TimeCard collects work activity.

    TimeCards take a single ChargeCode and collect all punch data
    for them. This enables filtering, reporting, and exporting
    data, but only for a single ChargeCode.
    """

    id: int

    def __post_init__(self) -> None:
        """Grab the ChargeCode with the given id."""
        self.code = get_code(self.id)

    def general_report(self, start: dt.datetime, end: dt.datetime) -> pd.DataFrame:
        """A general method to pull times data.

        Specify a start and end date. This method will
        then form a pandas dataframe from the ChargeCode,
        and filter down for all times inclusively between
        the two dates.

        Start and End can theoretically be any datetime object.
        """
        try:
            df = pd.DataFrame(self.code.times, columns=["clock_in", "clock_out"])
        except ValueError as exc:
            # This happens when only a clock_in time is provided.
            # AKA the code was created, and initialized, but not punched out.
            raise ThymedError(
                "Looks like this code doesn't have clock_in and clock_out times!"
            ) from exc
        df["date"] = df.clock_in.dt.strftime("%d/%m/%Y")
        df["duration"] = df.clock_out - df.clock_in
        df["hours"] = df.duration.apply(
            lambda x: x.components.hours + round(x.components.minutes / 60, 1)
        )
        df["week"] = df.clock_in.dt.isocalendar().week
        # Day 0 corresponds to Monday, Day 6 = Sunday
        df["day"] = df.clock_in.dt.day_of_week
        df["weekday"] = df.clock_in.apply(lambda x: x.strftime("%A"))
        date_set = df.loc[df.clock_in <= end].loc[df.clock_in >= start].copy()

        return date_set

    def weekly_report(self) -> pd.DataFrame:
        """Generates a report of all activity.

        This method takes today's date, and returns a
        filtered set of punch data for the past 7 days.
        """
        today = dt.datetime.today()
        start = today - dt.timedelta(days=7)

        return self.general_report(start, today)

    def pay_period_report(self) -> pd.DataFrame:
        """Generates a report of all activity.

        This method takes today's date, and returns a
        filtered set of punch data for the past 14 days.
        """
        today = dt.datetime.today()
        start = today - dt.timedelta(days=14)

        return self.general_report(start, today)

    def monthly_report(self) -> pd.DataFrame:
        """Generates a report of all activity.

        This method takes today's date, and returns a
        filtered set of punch data for the past 4 weeks.
        """
        today = dt.datetime.today()
        start = today - dt.timedelta(weeks=4)

        return self.general_report(start, today)

    def to_excel(self, report: pd.DataFrame, folder: Path) -> Path:
        """This method just saves the report to the directory provided."""
        name = self.code.name.replace(" ", "_").replace("'", "")
        filepath = folder / Path(f"{name}_report.xlsx")
        report.to_excel(filepath)
        return filepath


# Functions


def object_decoder(obj) -> Any:
    """Decoder hook for the ChargeCode class."""
    if "__type__" in obj and obj["__type__"] == "ChargeCode":
        return ChargeCode(obj["name"], obj["description"], obj["id"])
    return obj


def get_code(id: int) -> Any:
    """Read stored data and return the ChargeCode specified."""
    assert type(id) is int, "ID must be an int!"
    console = Console()
    with open(_CHARGES) as f:
        try:
            codes = json.load(f, object_hook=object_decoder)
        except json.JSONDecodeError:  # pragma: no cover
            # If the Charges file is completely blank (fresh install),
            # It will read with a length of zero. We should skip this
            # to avoid testing or runtime errors. Notify the user and exit.
            console = Console()
            console.print(
                "Looks like you're trying to use a ChargeCode "
                "without first defining any codes! Try running `thymed create` "
                "first."
            )
            codes = dict()
    try:
        # We assert id is an int, so it's safe to convert into string.
        # Without asserting at the beginning, you could pass thru weird
        # keys that are plain strings, or even something malicious.
        code = codes[str(id)]
    except KeyError:
        text = (
            f"Cannot find the charge code with id: {id}\n"
            "Try viewing available charge codes with `thymed list` or "
            "try punching the default code with `thymed punch`"
        )
        console.print(
            Panel(
                text,
                title="[magenta]Code Not Found",
                width=100,
                style="spring_green1",
            )
        )
        code = None

    return code


def delete_charge(id: str = "99999999") -> None:
    """Cleanup the test ChargeCode and punch data.

    This function manually removes the data. There
    may be a better way to do this in the future...
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


# TODO: Function to update _DATA global variable.
#       This function should be available in the CLI,
#       prompt to make the new file if non-existent,
#       and update the config.toml to use the new file.
