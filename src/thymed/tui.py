"""This module contains the TUI code.

The Text User Interface is all created, managed,
and tested with Textual.
"""
from typing import Any, Coroutine
from textual import events
import thymed
import json
from time import monotonic

from rich.text import Text

from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Button, Header, Footer, Static, DataTable, Rule


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

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update the time to the current time."""
        self.time = self.total + monotonic() - self.start_time

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def start(self) -> None:
        """Method to start (or resume) time updating."""
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
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay()


class Thingy(Static):
    """This thingy has a couple buttons to add and remove stopwatches."""
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler for app-level actions based on buttons."""
        button_id = event.button.id
        if button_id == "add":
            new_stopwatch = Stopwatch()
            self.app.query_one("#timers").mount(new_stopwatch)
            new_stopwatch.scroll_visible()
        elif button_id == "remove":
            timers = self.app.query("Stopwatch")
            if timers:
                timers.last().remove()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Add", id="add", variant="success")
        yield Button("Remove", id="remove", variant="error")


class HomePane(Container):
    """A view of Thymed ChargeCodes, and buttons to add timers."""

    def compose(self) -> ComposeResult:
        self.name_widget = Static("Thymed.\n")
        self.table_title_widget = Static("ChargeCodes in Current Database:")
        yield self.name_widget
        yield self.table_title_widget
        yield DataTable()
        yield Thingy()
        

    def on_mount(self) -> None:
        self.name_widget.styles.color = "springgreen"
        self.table_title_widget.styles.color = "springgreen"
        self.table_title_widget.styles.content_align = ("center", "top")


class Thymed(App):
    """A Textual app to manage Thymed!"""

    CSS_PATH = "thymed.tcss"
    BINDINGS = [
        ("escape", "exit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode")
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Footer()
        yield HomePane()
        yield Rule()
        yield ScrollableContainer(Stopwatch(), Stopwatch(), id="timers")

    def on_mount(self) -> None:
        self.title = "Thymed"
        table = self.query_one(DataTable)
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])
        table.cursor_type = "row"

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """Grab the selected ChargeCode."""
        cursor_row = event.cursor_row
        assert cursor_row == 0


    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_exit(self) -> None:
        """Exits the app."""
        self.exit()


if __name__ == "__main__":      # pragma: no cover
    app = Thymed()
    app.run()