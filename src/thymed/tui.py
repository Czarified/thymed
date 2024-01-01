"""The main Thymed Textual App.

This module contains the code for the Textual TUI of the main Textual
app. The Textual app has a simple interface with a dynamic applet,
surrounded by a header and footer. Most of the functionality comes with
the dynamic sidebar of functions.
"""

import json
from importlib.metadata import version
from pathlib import Path

from rich.console import RenderableType
from rich.table import Table
from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.containers import ScrollableContainer
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button
from textual.widgets import DataTable
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Input
from textual.widgets import Placeholder
from textual.widgets import Static
from textual.widgets import Switch

import thymed


SIDEBAR_INFO = """
There are multiple tools available in Thymed. To use one, select it or hit the keybinding. The main area will be updated with the 'applet' along with some more information. :smiley:
"""

LINKS = """
Here are some links, you can click these!

[@click="app.open_link('https://github.com/czarified/thymed')"]Thymed GitHub[/]
[@click="app.open_link('https://thymed.readthedocs.io/en/latest/')"]:books:Thymed Docs[/]
[@click="app.open_link('https://github.com/czarified/thymed/issues')"]:hammer_and_wrench: Contact the Dev[/]
[@click="app.open_link('https://github.com/czarified/thymed/blob/master/CONTRIBUTING.md')"]:heart: Contribute![/]
"""


class Title(Static):
    pass


class OptionGroup(ScrollableContainer):
    pass


class Version(Static):
    def render(self) -> RenderableType:
        return f"[b]Thymed v{version('thymed')}"


class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Title("Menu")
        yield Static(SIDEBAR_INFO)
        yield OptionGroup(
            Placeholder("Punch Screen", classes="option"),
            Placeholder("ChargeCode Manager", classes="option"),
            Placeholder("Reporting", classes="option"),
            Placeholder("Admin Tools", classes="option"),
            Placeholder("Settings", classes="option"),
        )
        yield Static(LINKS)
        yield Version()


class InfoPane(Widget):
    info = reactive("Placeholder Information")

    def render(self) -> str:
        return f"{self.info}"


class PunchForm(Container):
    """Punch a ChargeCode.

    This tool presents a 'login screen' to punch a ChargeCode. Type in the
    ChargeCode ID number, then press enter or select the Punch button. The
    provided ID will change state ('out' to 'in' or vice versa).
    """

    # Info is just a formatted version of the docstring.
    info = (
        __doc__.split("\n")[0]
        + "\n"
        + " ".join([line.strip() for line in __doc__.split("\n")[1:]])
    )

    def compose(self) -> ComposeResult:
        yield Static("ChargeCode ID:", classes="label")
        yield Input(placeholder="123456", id="chargecode")
        yield Static()
        yield Button("Punch", variant="primary", id="punch")


class ChargeManager(ScrollableContainer):
    """Manage the available ChargeCodes in the Database.

    This tool presents a tabular list of ChargeCodes, along with
    buttons to add and remove items from the database.
    """

    # Info is just a formatted version of the docstring.
    info = (
        __doc__.split("\n")[0]
        + "\n"
        + " ".join([line.strip() for line in __doc__.split("\n")[1:]])
    )

    data = reactive(Table())

    def get_data(self) -> Table:
        """Function to retrieve Thymed data."""
        with open(thymed._CHARGES) as f:
            try:
                codes = json.load(f, object_hook=thymed.object_decoder)

                # Sort the codes dictionary by key (code id)
                sorted_codes = sorted(codes.items(), key=lambda kv: int(kv[0]))
                codes = [x[1] for x in sorted_codes]
            except json.JSONDecodeError:  # pragma: no cover
                self.notify("Got JSON Error", severity="error")
                # If the file is completely blank, we will get an error
                codes = dict()

        table = Table(style="spring_green2")
        table.add_column("ID", justify="right", style="green", no_wrap=True)
        table.add_column("NAME", style="spring_green3 italic")
        table.add_column("DESCRIPTION", style="spring_green4")
        table.add_column("ACTIVE", style="green")

        for code in codes:
            table.add_row(
                str(code.id), code.name, code.description, str(code.is_active)
            )

        return table

    def compose(self) -> ComposeResult:
        yield Title("ChargeCodes in Current Database")
        self.data = self.get_data()
        yield Static(self.data, classes="data")
        yield Container(
            Button("Add", variant="success", classes="add"),
            Button("Remove", variant="error", classes="remove"),
            classes="controls",
        )


class Body(Container):
    """The Body is a container in the app that has dynamic widgets inside.

    The information pane displays text with instructions about the current
    active applet.

    The applet is the functional tool of the application. There are multiple
    applets available and which one is shown here is toggled via
    the sidebar menu or keybindings.
    """

    applet = reactive(Placeholder(id="applet"))

    def compose(self) -> ComposeResult:
        yield InfoPane(id="info")
        yield self.applet


class ThymedApp(App[None]):
    CSS_PATH = "thymed.tcss"
    TITLE = "Thymed App"
    BINDINGS = [
        ("m", "toggle_sidebar", "Menu"),
        ("f1", "launch_punch", "Punch Screen"),
        ("f2", "launch_chargecode", "ChargeCode Manager"),
        ("f3", "launch_reporting", "Reporting"),
        ("f4", "launch_admin", "Admin Tools"),
        ("f12", "launch_settings", "Settings"),
        Binding("escape", "app.quit", "Quit", show=True),
    ]

    show_sidebar = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(Sidebar(classes="-hidden"), Body())
        yield Footer()

    def action_launch_punch(self) -> None:
        """This method 'launches' the punch form applet."""
        self.query_one("#applet").remove()
        new = PunchForm(id="applet")
        self.query_one(InfoPane).info = new.info
        self.query_one(Body).mount(new)

    def action_launch_chargecode(self) -> None:
        """This method 'launches' the chargecode manager applet."""
        self.query_one("#applet").remove()
        new = ChargeManager(id="applet")
        self.query_one(InfoPane).info = new.info
        self.query_one(Body).mount(new)

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def punch(self, id: int):
        """Method to do the chargecode punching."""
        title = "Punch"
        try:
            # To do the Thymed stuff for punching
            code = thymed.get_code(int(id))
            if not code:
                # The get_code function handles KeyErrors for the CLI.
                # It returns a None value in this case only.
                raise KeyError
            status_pre = "Active" if code.is_active else "Inactive"
            code.punch()
            code.write_class()
            code.write_json()
            status_post = "Active" if code.is_active else "Inactive"
            message = f"Punching Charge: {id}, {code.name}.\nFrom {status_pre} to {status_post}"
            severity = "information"
        except KeyError as error:
            # If things don't work notify the user to try again.
            message = f"Cannot find the charge code with id: {id}"
            severity = "error"

        self.notify(message, title=title, severity=severity)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Event handler called when Input is submitted."""
        field = event.input
        if field.id == "chargecode":
            id = event.value
            field.value = ""
            self.punch(id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when Buttons are pressed."""
        if event.button.id == "punch":
            field = self.query_one("#chargecode")
            id = field.value
            field.value = ""
            self.punch(id)

    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser

        webbrowser.open(link)


if __name__ == "__main__":
    app = ThymedApp()
    app.run()
