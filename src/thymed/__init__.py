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
    """A TimeCard collects work activity."""

    pass

    def weekly_report(self) -> None:
        """Generates a report of all activity."""
        pass


# Functions


def object_decoder(obj) -> Any:
    """Decoder hook for the ChargeCode class."""
    if "__type__" in obj and obj["__type__"] == "ChargeCode":
        return ChargeCode(obj["name"], obj["description"], obj["id"])
    return obj


# TODO: Function to update _DATA global variable.
#       This function should be available in the CLI,
#       prompt to make the new file if non-existent,
#       and update the config.toml to use the new file.


if __name__ == "__main__":
    # # Scratchpad
    console = Console(record=True)
    # Create a new charge_code
    # my_code = ChargeCode("Testing Thyme", "Testing charge code for Thyme.", 100)
    with open(_CHARGES) as f:
        codes = json.load(f, object_hook=object_decoder)

    my_code = codes["100"]
    print(my_code)

    # my_code.write_class()
    your_code = ChargeCode("Running Thyme", "Run run run.", 200)
    your_code.write_class()

    my_code.write_class()
    my_code.punch()

    my_code.write_json()

    console.print("[red on white]   J O B    D O N E !! !!   ", justify="center")
