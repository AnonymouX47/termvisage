"""Event logging"""

from __future__ import annotations

import logging
import os
import sys
import warnings
from logging.handlers import RotatingFileHandler
from threading import Event, Thread, current_thread
from typing import TYPE_CHECKING, Optional

from term_image.widget import UrwidImageScreen

from . import __main__, notify

if TYPE_CHECKING:
    import argparse


def init_log(args: argparse.Namespace) -> None:
    """Initialize application event logging"""
    from .config import config_options

    global DEBUG, MULTI, QUIET, VERBOSE, VERBOSE_LOG, initialized

    log_file = os.path.expanduser(
        args.log_file
        # If the argument is invalid, the error will be emitted by the CLI.
        if args.log_file and config_options["log file"].is_valid(args.log_file)
        else config_options.log_file
    )
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=2**20,  # 1 MiB
        backupCount=1,
    )
    handler.addFilter(_filter)

    level = getattr(logging, args.log_level)
    DEBUG = args.debug or level == logging.DEBUG
    QUIET = args.quiet
    VERBOSE = args.verbose or args.debug
    VERBOSE_LOG = args.verbose_log

    if DEBUG:
        level = logging.DEBUG
    elif VERBOSE or VERBOSE_LOG:
        level = logging.INFO

    if (
        not (config_options.multi if args.multi is None else args.multi)
        or args.cli
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

    FORMAT = (
        "({process}) ({asctime}) [{levelname}] "
        + ("{processName}: " if DEBUG and MULTI else "")
        + ("{threadName}: " if DEBUG else "")
        + "{name}: "
        + ("{funcName}: " if DEBUG else "")
        + "{message}"
    )

    logging.basicConfig(
        handlers=(handler,),
        format=FORMAT,
        style="{",
        level=level,
    )

    if DEBUG:
        _logger.setLevel(logging.DEBUG)

    _logger.info("Starting a new session")
    _logger.info(f"Logging level set to {logging.getLevelName(level)}")

    if MULTI:
        from . import logging_multi
        from .logging_multi import process_multi_logs

        process_multi_logs.started = Event()
        logging_multi.multi_logger = LoggingThread(
            target=process_multi_logs, name="MultiLogger"
        )
        logging_multi.multi_logger.start()
        process_multi_logs.started.wait()
        del process_multi_logs.started

    initialized = True


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
            logger.log(level, msg, **_log_kwargs)
            notify.notify(
                msg,
                getattr(notify, logging.getLevelName(level)),
                context,
                loading=loading,
            )
        elif VERBOSE_LOG:
            logger.log(level, msg, **_log_kwargs)
    else:
        if file:
            logger.log(level, msg, **_log_kwargs)
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
        logger.exception(f"{msg} due to:", **_log_exc_kwargs)
    elif VERBOSE or VERBOSE_LOG:
        exc_type, exc, _ = sys.exc_info()
        logger.error(
            f"{msg} due to: ({exc_type.__module__}.{exc_type.__qualname__}) {exc}",
            **_log_kwargs,
        )
    else:
        logger.error(msg, **_log_kwargs)

    if VERBOSE and direct:
        notify.notify(msg, notify.CRITICAL if fatal else notify.ERROR, context)


# Not annotated because it's not directly used.
def _log_warning(msg, catg, fname, lineno, f=None, line=None):
    """Redirects warnings to the logging system.

    Intended to replace `warnings.showwarning()`.
    """
    _logger.warning(
        warnings.formatwarning(msg, catg, fname, lineno, line), **_log_kwargs
    )
    notify.notify(
        "Please view the logs for some warning(s).",
        level=notify.WARNING,
    )


def _filter(record: logging.LogRecord) -> None:
    return (
        (not __main__.interrupted or current_thread() is __main__.MAIN_THREAD)
        and record.name.partition(".")[0] not in _disallowed_modules
        # Workaround for urwid screen logs
        and not record.name.startswith(_urwid_screen_logger_name)
    )


class LoggingThread(Thread):
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

initialized = False
# > log > logger.log > _log
_log_kwargs = {"stacklevel": 2}
# > exception-handler > log_exception > logger.exception > _log
_log_exc_kwargs = {"stacklevel": 3}

# Set from within `init_log()`
DEBUG: bool
MULTI: bool
QUIET: bool
VERBOSE: bool
VERBOSE_LOG: bool
