"""Thymed.

This file contains basic functions and classes
related to to time-keeping.
"""


from dataclasses import dataclass, field
import datetime as dt
from pathlib import Path
import toml
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
__DATA = __DIR / Path(__OPTIONS['data']['file'])



## Classes

@dataclass
class ChargeCode():
    """
    A ChargeCode represents a type of work to dedicate
    hours to.
    
    ChargeCodes have a name, description, 
    identification number, and optional limits on time
    per week and total time dedicated.
    """

    name: str
    description: str
    id: int

    times: List[Tuple] = field(default_factory=list)

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


if __name__ == '__main__':
    ## Scratchpad
    import time

    # Create a new charge_code
    my_code = ChargeCode('Testing Thyme', 'Testing charge code for Thyme.', 100)

    print(f'Charge code is currently in state: {my_code.is_active}')
    my_code.punch()

    print('Charge code times:')
    print(my_code.times)

    print('Sleeping on the job...')
    time.sleep(5)

    print(f'Charge code is currently in state: {my_code.is_active}')
    my_code.punch()
    print('Charge code times:')
    print(my_code.times)
    print(f'Charge code is currently in state: {my_code.is_active}')
