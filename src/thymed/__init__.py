"""Thymed.

This file contains basic functions and classes
related to to time-keeping.
"""


from collections import defaultdict
from dataclasses import dataclass, field
import datetime as dt
from pathlib import Path
import toml
import json
from copy import copy
from typing import List, Tuple

## CONSTANTS

# For now, hardocde some files
# TODO: Look up the directory location for .thyme
#       to be similar to .jupyter or .cookiecutter
__DIR = Path(Path(__file__).parent) / Path('.thyme')
__CONFIG = __DIR / Path('config.toml')

with open(__CONFIG, 'r') as f:
    __OPTIONS = toml.load(f)

# The data file to store information.
# Controlled in the CONFIG file, and therefore customizable by user
_DATA = __DIR / Path(__OPTIONS['database']['file'])



## Classes

@dataclass
class ChargeCode():
    """
    A ChargeCode represents a type of work to dedicate
    hours to.
    
    ChargeCodes have a name, description, 
    identification number, and optional limits on time
    per week and total time dedicated.

    Attributes:
        times   :   times is the heart of the dataclass, 
                    it contains all the time code data in 
                    a list of tuples. For example:
                    ```python
                        [(Datetime, Datetime), ... (Datetime, Datetime)]
                    ```
    """

    name: str
    description: str
    id: int

    times: List[Tuple] = field(default_factory=list)

    def __post_init__(self):
        """
        Upon instantiation, need to look for existing data, and read in 
        the times. If existing data is in the record for this charge code
        id, the times array will be initialized as that complete array.
        """
        try:
            with open(_DATA, "r") as infile:
                # Read the existing file and store it
                existing = json.load(infile)
                # Keys read from the JSON will be str. Convert to int
                keys = [int(key) for key in existing.keys()]
                # However, keys in the final are still str, so use an fstring
                if self.id in keys:
                    str_times = existing[f'{self.id}']
                    for entry in str_times:
                        self.times.append(
                            tuple(
                                dt.datetime.fromisoformat(time) for time in entry
                            )
                        )
        except Exception as e:
            raise e


    @property
    def is_active(self) -> bool:
        """The charge code is active if it has been initalized, but not closed."""
        # If the last item in the times list has only 1 entry,
        # we assume the code is still active.
        if len(self.times) == 0:
            return None

        return True if len(self.times[-1]) == 1 else False
    

    def punch(self):
        """Punch in/out of chargeable time."""
        if self.is_active:
            # Close the code.
            self.times[-1] = (self.times[-1][0], dt.datetime.now())
        else:
            # Open the code.
            self.times.append((dt.datetime.now(),))

    
    def write_json(self, DATA=_DATA, log:bool=False):
        """
        Write the times data to a json file. Read the file first,
        and append the times to their appropriate charge code number.
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
            with open(DATA, "r") as infile:
                # Read the existing file and store it
                existing = json.load(infile)
                # # Make a copy, just for clarity
                final_data = copy(existing)
                # # Keys read from the JSON will be str. Convert to int
                # keys = [int(key) for key in existing.keys()]
                # # However, keys in the final are still str, so use an fstring
                # if self.id in keys:
                #     final_data[f'{self.id}'].extend(_times)
                # else:
                #     final_data[f'{self.id}'] = _times
                final_data[f'{self.id}'] = _times
        except json.JSONDecodeError:
            # Unless we can't read the file
            console.log('[red]Got JSONDecodeError, assuming the file was blank...')
            final_data = _times

        # Serializing json
        if log:
            console.print("Serializing JSON-formatted time data...")
        json_object = json.dumps(final_data, indent = 2)
        if log:
            console.print(json_object)
        
        # Write json
        with open(DATA, 'w') as outfile:
            if log:
                console.print("Writing JSON data to file...")
            outfile.write(json_object)


@dataclass
class TimeCard():
    """
    A TimeCard collects work activity.
    """

    pass


    def weekly_report(self):
        """Generates a report of all activity
        on the timecard for the previous week.
        """
        pass


## Functions

def new_charge_code(name, description, id):
    """
    Defines a new ChargeCode object.
    """
    new = ChargeCode(name, description, id)



# TODO: Function to update _DATA global variable.
#       This function should be available in the CLI,
#       prompt to make the new file if non-existent, 
#       and update the config.toml to use the new file.



if __name__ == '__main__':
    ## Scratchpad
    import time
    from random import randint
    from copy import copy
    from rich.console import Console
    console = Console(record=True)
    # Create a new charge_code
    my_code = ChargeCode('Testing Thyme', 'Testing charge code for Thyme.', 100)
    your_code = ChargeCode('Running Thyme', 'Run run run.', 200)
    data = {}

    def test_run(my_code:ChargeCode):
        for i in range(randint(2,4)):
            console.log(f"Sprint {i}:")
            console.print(my_code)
            console.log(f"   Charge code is currently in state: {my_code.is_active}")
            console.log(f"      [green italic]Clocking in...")
            my_code.punch()
            console.log(f"   Charge code is currently in state: {my_code.is_active}")
            t = randint(1,7)
            console.log(f"   Working for {t}...")
            time.sleep(t)
            my_code.punch()
            console.log(f"      [green italic]Clocking out...")
            console.log(f"   Charge code is currently in state: {my_code.is_active}")
            console.log(f"   Charge code times:")
            console.log(my_code.times)

    
    my_code.punch()
    
    my_code.write_json()

    console.print("[red on white]   J O B    D O N E !! !!   ",justify='center')