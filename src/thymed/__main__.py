"""Command-line interface."""
import thymed
import click
import json

from rich.console import Console


@click.command()
@click.version_option()
def main() -> None:
    """Thymed.
    
    This function will be used to execute the TUI.
    For now, it's just a placeholder.
    """
    console = Console()
    console.print("Hello World!\n")
    console.print(
        "I am [spring_green3 italic]Thymed.[/] "
        "Simple command-line time-tracking."
    )
    console.print(f"Current Version: 0.0.1\n")
    console.print(
        "Currently, this is a placeholder tool. "
        "Functionality exists in the API, but "
        "is not exteded to CLI yet.\n"
    )


def default_code() -> thymed.ChargeCode:
    '''This function returns the default ChargeCode.
    
    The default ChargeCode is defined in the Thymed config file.
    If no default id is defined, raises an error.
    '''
    with open(thymed._CHARGES) as f:
        codes = json.load(f, object_hook=thymed.object_decoder)

    default_id = thymed.__OPTIONS['database']['default']

    return codes[str(default_id)]
    

@click.command()
def punch_default() -> None:
    """Punch the default ChargeCode.

    Grab the default code, and call its `punch` method.
    Punches the current time. Write the data and the code,
    then exit.
    """
    code = default_code()
    code.punch()
    code.write_class()
    code.write_json()


if __name__ == "__main__":
    main(prog_name="thymed")  # pragma: no cover