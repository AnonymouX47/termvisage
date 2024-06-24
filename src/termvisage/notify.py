"""Issuing user notifications in the TUI and on STDOUT"""

from __future__ import annotations

import argparse
import logging as _logging
from queue import Queue
from sys import stderr, stdout
from threading import Event, current_thread
from typing import Any, Tuple, Union

import urwid

from . import __main__, logging, tui
from .config import config_options
from .ctlseqs import SGR_FG_BLUE, SGR_FG_DEFAULT, SGR_FG_RED, SGR_FG_YELLOW

DEBUG = INFO = 0
WARNING = 1
ERROR = 2
CRITICAL = 3


def add_notification(msg: Union[str, Tuple[str, str]]) -> None:
    """Adds a message to the TUI notification bar."""
    if _alarms.full():
        clear_notification(tui.main.loop, None)
    tui.widgets.notifications.contents.insert(
        0, (urwid.Filler(urwid.Text(msg, wrap="ellipsis")), ("given", 1))
    )
    _alarms.put(tui.main.loop.set_alarm_in(5, clear_notification))


def clear_notification(loop: urwid.MainLoop, data: Any) -> None:
    """Removes the oldest message in the TUI notification bar."""
    tui.widgets.notifications.contents.pop()
    loop.remove_alarm(_alarms.get())


def end_loading() -> None:
    """Signals the end of all progressive operations for the current mode."""
    global _n_loading

    if not QUIET:
        _n_loading = -1
        _loading.set()


def init_notify(args: argparse.Namespace) -> None:
    global QUIET, VERBOSE, initialized, loading_indicator

    QUIET, VERBOSE = args.quiet, args.verbose or args.debug

    if not QUIET:
        loading_indicator = logging.LoggingThread(target=load, name="LoadingIndicator")
        loading_indicator.start()

    initialized = True


def is_loading() -> bool:
    """Returns ``True`` if the loading indicator is active or ``False`` if not."""
    return _loading.is_set()


def load() -> None:
    """Displays a loading indicator.

    - elipsis-style for the CLI
    - braille-style for the TUI
    """
    global _n_loading

    stream = stdout if stdout.isatty() else stderr

    # CLI Phase

    _loading.wait()  # Wait for a loading operation

    while _n_loading > -1:  # CLI phase hasn't ended?
        while _n_loading > 0:  # Anything loading?
            # Animate the CLI loading indicator
            for stage in (".  ", ".. ", "..."):
                stream.write(stage + "\b" * 3)
                stream.flush()
                if _n_loading <= 0:  # Nothing loading or CLI phase ended?
                    break
                if loading_interrupted.wait(0.25):  # Delay interruptibly
                    loading_interrupted.clear()
                if _n_loading <= 0:  # Nothing loading or CLI phase ended?
                    break

        # Clear the CLI loading indicator
        stream.write(" " * 3 + "\b" * 3)
        stream.flush()

        if _n_loading > -1:  # Still in the CLI phase?
            _loading.clear()  # Signal "not loading"
            _loading.wait()  # Wait for a loading operation

    # TUI Phase

    _n_loading = 0
    _loading.clear()  # Signal "not loading"
    _loading.wait()  # Wait for a loading operation

    if _n_loading > -1:  # Not skipping TUI phase?
        from .tui.main import update_screen
        from .tui.widgets import loading

    while _n_loading > -1:  # TUI phase hasn't ended?
        while _n_loading > 0:  # Anything loading?
            # Animate the TUI loading indicator
            for stage in (
                "\u28bf",
                "\u28fb",
                "\u28fd",
                "\u28fe",
                "\u28f7",
                "\u28ef",
                "\u28df",
                "\u287f",
            ):
                loading.set_text(stage)
                update_screen()
                if _n_loading <= 0:  # Nothing loading or TUI phase ended?
                    break
                if loading_interrupted.wait(0.25):  # Delay interruptibly
                    loading_interrupted.clear()
                if _n_loading <= 0:  # Nothing loading or TUI phase ended?
                    break

        # Clear the TUI loading indicator
        loading.set_text("")
        update_screen()

        if _n_loading > -1:  # Still in the TUI phase?
            _loading.clear()  # Signal "not loading"
            _loading.wait()  # Wait for a loading operation

    _loading.clear()  # Signal "not loading"


def notify(
    msg: str,
    level: int = INFO,
    context: str = "",
    *,
    verbose: bool = False,
    loading: bool = False,
) -> None:
    """Displays a message in the TUI's notification bar or to STDOUT/STDERR."""
    if (
        (__main__.interrupted and current_thread() is not __main__.MAIN_THREAD)
        or (QUIET and level < CRITICAL)
        or (verbose and not VERBOSE)
    ):
        return

    if tui.active:
        if config_options.max_notifications:
            add_notification(
                [
                    ("notif context", f"{context}: " if context else ""),
                    # CRITICAL-level notifications should never be displayed in the TUI,
                    # since the program shouldn't recover from the cause.
                    (msg, ("warning", msg), ("error", msg))[level],
                ]
            )
    else:
        print(
            (f"{SGR_FG_BLUE}{context}:{SGR_FG_DEFAULT} " if context else "")
            + (
                f"{SGR_FG_RED}{msg}{SGR_FG_DEFAULT}"
                if level >= ERROR
                else f"{SGR_FG_YELLOW}{msg}{SGR_FG_DEFAULT}"
                if level == WARNING
                else msg  # fmt: skip
            ),
            file=stderr if level >= WARNING else stdout,
        )

    if loading:
        start_loading()


def start_loading() -> None:
    """Signals the start of a progressive operation."""
    global _n_loading

    if not (QUIET or __main__.interrupted or tui.quitting):
        _n_loading += 1
        _loading.set()


def stop_loading() -> None:
    """Signals the end of a progressive operation."""
    global _n_loading

    if not QUIET:
        _n_loading -= 1


logger = _logging.getLogger(__name__)

_alarms = Queue(5)  # Max value for "max notifications" is 5

_loading = Event()
_n_loading = 0
initialized = False
# Used to implement an interruptible loading mechanism.
loading_interrupted = Event()

# Set from `init_notify()`.
loading_indicator: logging.LoggingThread

# Set from `init_notify()`.
QUIET: bool
VERBOSE: bool
