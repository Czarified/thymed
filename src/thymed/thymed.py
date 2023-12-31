"""The main Thymed Textual App.

This module contains the code for the Textual TUI of the main Textual 
app. The Textual app has a simple interface with a dynamic applet, 
surrounded by a header and footer. Most of the functionality comes with 
the dynamic sidebar of functions.
"""

from importlib.metadata import version
from pathlib import Path

from rich import box
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Static,
    Switch,
    Placeholder
)

SIDEBAR_INFO = """
There are multiple tools available in Thymed. To use one, select it or hit the keybinding. The main area will be updated with the 'applet' along with some more information. :smiley:
"""

LINKS = """
Here are some links, you can click these!

[@click="app.open_link('https://github.com/czarified/thymed')"]Thymed GitHub[/]
[@click="app.open_link('https://https://thymed.readthedocs.io/en/latest/')"]:books:Thymed Docs[/]
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
            Placeholder("Option 1", classes="option"),
            Placeholder("Option 2", classes="option"),
            Placeholder("Option 3", classes="option"),
            Placeholder("Option 4", classes="option"),
            Placeholder("Option 5", classes="option"),
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
    # Info is basically the same as the docstring, 
    # just with all the line breaks removed. This is because I need it
    # to render properly with text wrapping.
    info = "Punch a ChargeCode.\nThis tool presents a 'login screen' to punch a ChargeCode. Type in the ChargeCode ID number, then press enter or select the Punch button. The provided ID will change state ('out' to 'in' or vice versa)."

    def compose(self) -> ComposeResult:
        yield Static("ChargeCode ID:", classes="label")
        yield Input(placeholder="123456")
        yield Static()
        yield Button("Punch", variant="primary", id="punch")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        _button_id = event.button.id
        field = self.query_one(Input)
        field.value = ""
        field.action_submit()
        


class Body(Container):
    """The Body is a container in the app that has dynamic widgets inside.
    
    The information pane displays text with instructions about the current
    active applet.

    The applet is the functional tool of the application. There are multiple
    applets available and which one is shown here is toggled via
    the sidebar menu.
    """
    applet = reactive(Placeholder(classes="applet"))

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
        ("f5", "launch_settings", "Settings"),
        Binding("escape", "app.quit", "Quit", show=True)
    ]

    show_sidebar = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Sidebar(classes="-hidden"),
            Body()
        )
        yield Footer()

    def action_launch_punch(self) -> None:
        """This method 'launches' the punch applet."""
        body = self.query_one(Body)
        body.applet = PunchForm(classes="applet")
        self.query_one(InfoPane).info = body.applet.info
        

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser

        webbrowser.open(link)


if __name__ == '__main__':
    app = ThymedApp()
    app.run()