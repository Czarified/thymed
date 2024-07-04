"""Command-line interface."""

import json
from importlib.metadata import version
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.prompt import IntPrompt
from rich.prompt import Prompt
from rich.table import Table
from rich.traceback import install

import thymed
from thymed.tui import ThymedApp


install()


__version__ = version("thymed")


@click.group()
@click.version_option()
def main() -> None:  # pragma: no cover
    """Thymed.

    This command serves as the main entrypoint into
    the Thymed CLI. Subcommands exist for each specific action.

    For more information, try: thymed hello
    """
    pass


@main.command()
def hello():
    """See information about Thymed."""
    console = Console()
    console.print("Hello World!\n")
    console.print(
        "I am [spring_green3 italic]Thymed.[/] " "Simple command-line time-tracking."
    )
    console.print(f"Current Version: {__version__}\n")


def default_code() -> Any:
    """This function returns the default ChargeCode.

    The default ChargeCode is defined in the Thymed config file.
    If no default id is defined, raises a warning.
    """
    try:
        default_id = thymed.__OPTIONS["database"]["default"]
        return thymed.get_code(default_id)
    except KeyError:
        # KeyError means default code isn't set. We should notify user,
        # and exit.
        console = Console()
        text = (
            "Looks like you haven't set a default ChargeCode, "
            "or the code provided isn't in the database somehow. "
            "Try providing the specific code you want to punch in, "
            "or set the default code for future with: `thymed set default <id>`"
        )
        console.print(
            Panel(
                text,
                title="[magenta]No Default Found",
                width=100,
                style="spring_green1",
            )
        )


@main.command()
@click.argument("id", nargs=-1)
def punch(id) -> None:
    """Punch a ChargeCode.

    Punch the ChargeCode id provided.

    If no id provided, grab the default code,
    and call its `punch` method.

    Punches the current time. Write the data and the code,
    then exit.
    """
    # Manually check some argument variables...
    if len(id) > 1:  # pragma: no cover
        raise NotImplementedError
    elif len(id) == 1:
        id = id[0]

    console = Console()
    console.print("[spring_green3 italic]Thymed.[/]\n")
    if not id:
        code = default_code()
    else:
        code = thymed.get_code(int(id))
    if code is None:
        # code is None if the default code was not found, nor was it provided
        console.print("No code to punch, so exiting...")
        return None

    console.print(f"Punching Charge Code: [medium_spring_green]{code.name}")
    code.punch()
    code.write_class()
    code.write_json()
    console.print("[spring_green3 italic]   ...Done!")


@main.command()
def create():
    """Create a new ChargeCode.

    Create a new ChargeCode object with the given id.
    """
    console = Console()
    name = Prompt.ask("Enter a name for the ChargeCode")
    description = Prompt.ask("Description for this ChargeCode")
    id = IntPrompt.ask("A unique identifier for this code (integer value)")

    new_code = thymed.ChargeCode(name, description, id)
    console.print(new_code)
    confirmed = Confirm.ask(
        "Confirm ChargeCode data? (If no, you will exit with no changes)"
    )

    if confirmed:
        new_code.write_class()
        # TODO: Make this prettier
        console.print("Wrote ChargeCode data to the Thymed Charges file!")
    else:  # pragma: no cover
        # TODO: Make this prettier
        console.print("Exiting without writing new ChargeCode...Try again.")


@main.command()
def list():
    """List out all the available charge codes."""
    with open(thymed._CHARGES) as f:
        try:
            codes = json.load(f, object_hook=thymed.object_decoder)

            # Sort the codes dictionary by key (code id)
            sorted_codes = sorted(codes.items(), key=lambda kv: int(kv[0]))
            codes = [x[1] for x in sorted_codes]
        except json.JSONDecodeError:  # pragma: no cover
            print("Got JSON Error")
            # If the file is completely blank, we will get an error
            codes = dict()

    console = Console()
    table = Table(title="ChargeCodes in Current Database", style="spring_green2")
    table.add_column("ID", justify="right", style="green", no_wrap=True)
    table.add_column("NAME", style="spring_green3 italic")
    table.add_column("DESCRIPTION", style="spring_green4")
    table.add_column("ACTIVE", style="green")

    for code in codes:
        table.add_row(str(code.id), code.name, code.description, str(code.is_active))

    console.print(table)


@main.command()
def tui():
    """Launch the TUI.

    This command launches the Text User Interface (TUI).
    While the commandline functions are quite efficient,
    many users may prefer or need the TUI for interacting
    with Thymed. It's quite robust and polished! Give it a try!
    """
    app = ThymedApp()
    app.run()


if __name__ == "__main__":
    main(prog_name="thymed")  # pragma: no cover
