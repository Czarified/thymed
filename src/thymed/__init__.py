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
                except json.JSONDecodeError:
                    # If the file is completely blank, we will get an error
                    pass
        except Exception as e:
            # Otherwise, let me know what went wrong
            raise e

    @property
    def is_active(self) -> Any:
        """The charge code is active if it has been initalized, but not closed."""
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
        except json.JSONDecodeError:
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
            except json.JSONDecodeError:
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


    def weekly_report(self) -> None:
        """Generates a report of all activity."""
        ...


# Functions


def object_decoder(obj) -> Any:
    """Decoder hook for the ChargeCode class."""
    if "__type__" in obj and obj["__type__"] == "ChargeCode":
        return ChargeCode(obj["name"], obj["description"], obj["id"])
    return obj


def get_code(id: int) -> Any:
    """Read stored data and return the ChargeCode specified."""
    assert type(id) is int, 'ID must be an int!'
    console = Console()
    with open(_CHARGES) as f:
        try:
            codes = json.load(f, object_hook=object_decoder)
        except json.JSONDecodeError:
            # If the file is completely blank, we will get an error
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

# TODO: Function to update _DATA global variable.
#       This function should be available in the CLI,
#       prompt to make the new file if non-existent,
#       and update the config.toml to use the new file.


if __name__ == "__main__":  # pragma: no cover
    # # Scratchpad
    console = Console(record=True)
    
    import pandas as pd
    import random

    def build_fake_timesheet():
        """Temporary function for testing."""
        start = dt.datetime(2020,1,1)
        end = dt.datetime(2020,12,31)
        # Max number of days our worker will work in this time period
        n = 251
        name = 'Julia Farmer'
        description = "Working on the farm in 2020."
        id = 23

        # Initialize the output variables
        ins = []
        outs = []
        # Iteration variable. We don't want to repeat days or "work" them out of order.
        iter_start = start
        for i in range(n):
            # Pick a random timestamp in the time range
            date = dt.timedelta(days=random.randint(0,5)) + iter_start
            iter_start = date
            # Check if we should stop here (beyond the end date)
            if (iter_start >= end) or (date > end):
                break
            
            # Generate the timedelta for punch in/out on that day
            in_delta = random.randint(-120,750)
            out_delta = random.randint(-200,350)
            
            # Add the deltas for in/out
            in_punch = dt.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour = 7
            ) + dt.timedelta(seconds=in_delta)
            ins.append(in_punch)

            out_punch = dt.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour = 17
            ) + dt.timedelta(seconds=out_delta)
            outs.append(out_punch)

        df = pd.DataFrame()
        df['in_punch'] = ins
        df['out_punch'] = outs

        console.print(df)

        my_code = ChargeCode(name, description, id)
        console.print(my_code)

        my_code.times = tuple(zip(ins,outs))
        my_code.write_class()
        my_code.write_json()