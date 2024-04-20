"""Event logging"""

from __future__ import annotations

import logging
import os
import sys
import warnings
from logging.handlers import RotatingFileHandler
from multiprocessing import Event as mp_Event
from threading import Thread
from typing import Optional

from term_image.widget import UrwidImageScreen

from . import cli, notify


def init_log(
    logfile: str,
    level: int,
    debug: bool,
    multi: bool,
    quiet: bool,
    verbose: bool,
    verbose_log: bool,
) -> None:
    """Initialize application event logging"""
    global DEBUG, MULTI, QUIET, VERBOSE, VERBOSE_LOG

    logfile = os.path.expanduser(logfile)
    os.makedirs(os.path.dirname(logfile) or ".", exist_ok=True)
    handler = RotatingFileHandler(
        logfile,
        maxBytes=2**20,  # 1 MiB
        backupCount=1,
    )
    handler.addFilter(_filter)

    QUIET, VERBOSE, VERBOSE_LOG = quiet, verbose or debug, verbose_log
    DEBUG = debug = debug or level == logging.DEBUG
    if debug:
        level = logging.DEBUG
    elif VERBOSE or VERBOSE_LOG:
        level = logging.INFO

    FORMAT = (
        "({process}) ({asctime}) [{levelname}] "
        + ("{processName}: {threadName}: " if debug else "")
        + "{name}: "
        + ("{funcName}: " if debug and stacklevel_is_available else "")
        + "{message}"
    )
    logging.basicConfig(
        handlers=(handler,),
        format=FORMAT,
        style="{",
        level=level,
    )

    if debug:
        _logger.setLevel(logging.DEBUG)

    _logger.info("Starting a new session")
    _logger.info(f"Logging level set to {logging.getLevelName(level)}")

    if debug and not stacklevel_is_available:
        warnings.warn(
            "Please upgrade to Python 3.8 or later to get more detailed logs."
        )

    if not QUIET:
        notify.loading_indicator = Thread(target=notify.load, name="LoadingIndicator")
        notify.loading_indicator.start()

    if (
        not multi
        or cli.args.cli
        or (os.cpu_count() or 0) <= 2  # Avoid affecting overall system performance
        or sys.platform in {"win32", "cygwin"}
    ):
        MULTI = False
    else:
        try:
            import multiprocessing.synchronize  # noqa: F401
        except ImportError:
            MULTI = False
        else:
            MULTI = True

    if MULTI:
        from .logging_multi import process_multi_logs

        process_multi_logs.started = mp_Event()
        Thread(target=process_multi_logs, name="MultiLogger").start()
        process_multi_logs.started.wait()
        del process_multi_logs.started

        # Inherited by instances of `.logging_multi.Process`
        cli.interrupted = mp_Event()


def log(
    msg: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    context: str = "",
    *,
    direct: bool = True,
    file: bool = True,
    verbose: bool = False,
    loading: bool = False,
) -> None:
    """Report events to various destinations"""
    if loading:
        msg += "..."

    if verbose:
        if VERBOSE:
            logger.log(level, msg, **_kwargs)
            notify.notify(
                msg,
                getattr(notify, logging.getLevelName(level)),
                context,
                loading=loading,
            )
        elif VERBOSE_LOG:
            logger.log(level, msg, **_kwargs)
    else:
        if file:
            logger.log(level, msg, **_kwargs)
        if direct:
            notify.notify(
                msg,
                getattr(notify, logging.getLevelName(level)),
                context,
                loading=loading,
            )


def log_exception(
    msg: str,
    logger: logging.Logger,
    context: str = "",
    *,
    direct: bool = False,
    fatal: bool = False,
) -> None:
    """Report an error with the exception responsible

    NOTE: Should be called from within an exception handler
    i.e from (also possibly in a nested context) within an except or finally clause.
    """
    if DEBUG:
        logger.exception(f"{msg} due to:", **_kwargs_exc)
    elif VERBOSE or VERBOSE_LOG:
        exc_type, exc, _ = sys.exc_info()
        logger.error(
            f"{msg} due to: ({exc_type.__module__}.{exc_type.__qualname__}) {exc}",
            **_kwargs,
        )
    else:
        logger.error(msg, **_kwargs)

    if VERBOSE and direct:
        notify.notify(msg, notify.CRITICAL if fatal else notify.ERROR, context)


# Not annotated because it's not directly used.
def _log_warning(msg, catg, fname, lineno, f=None, line=None):
    """Redirects warnings to the logging system.

    Intended to replace `warnings.showwarning()`.
    """
    _logger.warning(warnings.formatwarning(msg, catg, fname, lineno, line), **_kwargs)
    notify.notify(
        "Please view the logs for some warning(s).",
        level=notify.WARNING,
    )


def _filter(record: logging.LogRecord) -> None:
    return (
        record.name.partition(".")[0] not in _disallowed_modules
        # Workaround for urwid screen logs
        and not record.name.startswith(_urwid_screen_logger_name)
    )


class Thread(Thread):
    """A thread with integration into the logging system"""

    def __init__(self, *args, **kwargs):
        try:
            del kwargs["redirect_notifs"]
        except KeyError:
            pass
        super().__init__(*args, **kwargs)

    def run(self):
        _logger.debug("Starting")
        try:
            super().run()
        except Exception:
            log_exception("Aborted" if DEBUG else f"{self.name} was aborted", _logger)
        else:
            _logger.debug("Exiting")


# Writing to STDERR messes up output, especially with the TUI
warnings.showwarning = _log_warning

_logger = logging.getLogger("termvisage")
_disallowed_modules = frozenset({"PIL", "urllib3", "urwid"})
_urwid_screen_logger_name = f"{UrwidImageScreen.__module__}.UrwidImageScreen"

# the _stacklevel_ parameter was added in Python 3.8
stacklevel_is_available = sys.version_info[:3] >= (3, 8, 0)
if stacklevel_is_available:
    # > log > logger.log > _log
    _kwargs = {"stacklevel": 2}
    # > exception-handler > log_exception > logger.exception > _log
    _kwargs_exc = {"stacklevel": 3}
else:
    _kwargs = _kwargs_exc = {}

# The annotations below are put in comments for compatibility with Python 3.7
# as it doesn't allow names declared as `global` within functions to be annotated.

# Set from within `init_log()`
DEBUG = None  #: Optional[bool]
MULTI = None  #: Optional[bool]
QUIET = None  #: Optional[bool]
VERBOSE = None  #: Optional[bool]
VERBOSE_LOG = None  #: Optional[bool]
