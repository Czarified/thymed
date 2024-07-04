"""This module contains the TUI code.

The Text User Interface is all created, managed,
and tested with Textual.
"""

import json
from time import monotonic

# from rich.text import Text
# from textual import events
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Container
from textual.containers import ScrollableContainer
from textual.reactive import reactive

# from textual.reactive import var
from textual.widget import Widget
from textual.widgets import Button
from textual.widgets import DataTable
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Rule
from textual.widgets import Static

import thymed


# from typing import Any
# from typing import Coroutine


ROWS = [("ID", "NAME", "DESCRIPTION", "ACTIVE")]
with open(thymed._CHARGES) as f:
    try:
        codes = json.load(f, object_hook=thymed.object_decoder)

        # Sort the codes dictionary by key (code id)
        sorted_codes = sorted(codes.items(), key=lambda kv: int(kv[0]))
        codes = [x[1] for x in sorted_codes]
    except json.JSONDecodeError:  # pragma: no cover
        codes = dict()

for code in codes:
    ROWS.append((str(code.id), code.name, code.description, str(code.is_active)))


class TimeDisplay(Static):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)
    name = reactive("name")

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update the time to the current time."""
        self.time = self.total + monotonic() - self.start_time

    def watch_time(self, time: float) -> None:
        """Called when the attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{self.name}\n{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def start(self) -> None:
        """Method to resume time updating."""
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self) -> None:
        """Method to stop the time display updating."""
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total

    def reset(self) -> None:
        """Method to reset the time display to zero."""
        self.total = 0
        self.time = 0


class Stopwatch(Static):
    """A stopwatch widget."""

    name = reactive("name")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)
        if button_id == "start":
            time_display.start()
            self.add_class("started")
        elif button_id == "stop":
            time_display.stop()
            self.remove_class("started")
        elif button_id == "reset":
            time_display.reset()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        display = TimeDisplay()
        display.name = self.name
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield display


class ReactiveTitle(Widget):
    """A Reactive Title that changes based on the selected DataTable row."""

    name: reactive[str | None] = reactive("This is a title.")
    sub: reactive[str | None] = reactive("Description.")

    def render(self) -> str:
        return f"{self.name}\n{self.sub}"


class Thingy(Static):
    """This thingy has a couple buttons to add and remove stopwatches."""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler for app-level actions based on buttons."""
        button_id = event.button.id
        if button_id == "add":
            name = self.query_one(ReactiveTitle).name
            new_stopwatch = Stopwatch()
            new_stopwatch.name = name
            self.app.query_one("#timers").mount(new_stopwatch)
            new_stopwatch.scroll_visible()
        elif button_id == "remove":
            timers = self.app.query("Stopwatch")
            if timers:
                timers.last().remove()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Add", id="add", variant="success")
        yield ReactiveTitle(id="hometitle", classes="title")
        yield Button("Remove", id="remove", variant="error")


class HomePane(Container):
    """A view of Thymed ChargeCodes, and buttons to add timers."""

    def compose(self) -> ComposeResult:
        """Compose."""
        self.name_widget = Static("Thymed.\n")
        self.table_title_widget = Static(
            "ChargeCodes in Current Database:", classes="title"
        )
        yield self.name_widget
        yield self.table_title_widget
        yield DataTable()
        yield Thingy()

    def on_mount(self) -> None:
        """What to do on mount."""
        self.name_widget.styles.color = "springgreen"


class Thymer(App):
    """A Textual app to manage timers!!"""

    CSS_PATH = "thymer.tcss"
    BINDINGS = [("escape", "exit", "Quit"), ("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Footer()
        yield HomePane()
        yield Rule()
        yield ScrollableContainer(Stopwatch(), Stopwatch(), id="timers")

    def on_mount(self) -> None:
        """What to do on mount."""
        self.title = "Thymed"
        table = self.query_one(DataTable)
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])
        table.cursor_type = "row"

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """Grab the selected ChargeCode."""
        data = event.data_table.get_row(event.row_key)
        self.query_one("#hometitle", ReactiveTitle).name = str(data[1])
        self.query_one("#hometitle", ReactiveTitle).sub = str(data[2])

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_exit(self) -> None:
        """Exits the app."""
        self.exit()


if __name__ == "__main__":  # pragma: no cover
    app = Thymer()
    app.run()
