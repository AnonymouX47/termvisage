"""Extension of `.logging` for multiprocessing support"""

from __future__ import annotations

import logging as _logging
import os
from multiprocessing import Process, Queue as mp_Queue
from traceback import format_exception

from term_image import (
    AutoCellRatio,
    enable_win_size_swap,
    set_cell_ratio,
    set_query_timeout,
)

from . import logging, notify


def process_multi_logs() -> None:
    """Emits logs and notifications redirected from subprocesses.

    Intended to be executed in a separate thread of the main process.
    """
    global log_queue

    PID = os.getpid()
    log_queue = mp_Queue()
    process_multi_logs.started.set()  # See `.logging.init_log()`

    record_type, record = log_queue.get()
    while record:
        if record_type == LOG:
            record.process = PID
            _logger.handle(record)
        else:
            notify.notify(*record[0], **record[1])
        record_type, record = log_queue.get()


class LoggingProcess(Process):
    """A process with integration into the logging system

    Sets up the logging system to redirect all logs (and optionally notifications)
    in the subprocess, to the main process to be emitted.

    NOTE:
        - Only TUI notifications need to be redirected.
        - The redirected logs and notifications are automatically handled by
          `process_multi_logs()`, running in the MultiLogger thread of the main process.
    """

    def __init__(self, *args, redirect_notifs: bool = False, **kwargs):
        from . import tui
        from .cli import args as cli_args

        super().__init__(*args, **kwargs)

        self._log_queue = log_queue
        self._logging_details = {
            "constants": {
                name: value for name, value in vars(logging).items() if name.isupper()
            },
            "logging_level": _logging.getLogger().getEffectiveLevel(),
            "redirect_notifs": redirect_notifs,
        }
        self._tui_is_initialized = tui.initialized

        if self._tui_is_initialized:
            self._ImageClass = tui.main.ImageClass
            self._supported = self._ImageClass._supported
            self._forced_support = self._ImageClass.forced_support
            self._cell_ratio = cli_args.cell_ratio
            self._query_timeout = cli_args.query_timeout
            self._swap_win_size = cli_args.swap_win_size
            self._style_attrs = [
                (attr, getattr(self._ImageClass, attr))
                for attr in exported_style_attrs.get(self._ImageClass.style, ())
            ]

        child_processes.append(self)

    def run(self):
        self._redirect_logs()
        _logger.debug("Starting")

        try:
            if self._tui_is_initialized:
                # The unpickled class object is in the originally defined state
                self._ImageClass._supported = self._supported  # Avoid support check
                self._ImageClass.forced_support = self._forced_support
                for item in self._style_attrs:
                    setattr(self._ImageClass, *item)

                set_query_timeout(self._query_timeout)
                if self._swap_win_size:
                    enable_win_size_swap()

                if not self._cell_ratio:
                    # Avoid an error in case the terminal wouldn`t respond on time
                    AutoCellRatio.is_supported = True
                set_cell_ratio(self._cell_ratio or AutoCellRatio.DYNAMIC)

            super().run()
        except KeyboardInterrupt:
            _logger.error(
                "Interrupted" if logging.DEBUG else f"{self.name} was interrupted"
            )
        except Exception:
            logging.log_exception(
                "Aborted" if logging.DEBUG else f"{self.name} was aborted", _logger
            )
        else:
            _logger.debug("Exiting")

    def _redirect_notif(
        self,
        msg: str,
        # Cannot access `notify.INFO` as `.notify` would/might be partially initialized.
        level: int | None = None,
        *args,
        verbose: bool = False,
        loading: bool = False,  # Not passed across
        **kwargs,
    ):
        if level is None:
            level = notify.INFO

        if notify.QUIET and level < notify.CRITICAL or verbose and not notify.VERBOSE:
            return

        self._log_queue.put(
            (NOTIF, ((msg, level, *args), {"verbose": verbose, **kwargs}))
        )

    def _redirect_logs(self) -> None:
        # Logs
        vars(logging).update(self._logging_details["constants"])
        logger = _logging.getLogger()
        logger.setLevel(self._logging_details["logging_level"])
        logger.addHandler(RedirectHandler(self._log_queue))
        logger.handlers[0].addFilter(logging._filter)

        # # Warnings and session-level logs
        _logger.setLevel(min(self._logging_details["logging_level"], _logging.INFO))

        logging.initialized = True

        # Notifications
        notify.QUIET = logging.QUIET
        notify.VERBOSE = logging.VERBOSE
        if self._logging_details["redirect_notifs"] and not notify.QUIET:
            notify.notify = self._redirect_notif
        notify.initialized = True


class RedirectHandler(_logging.Handler):
    """Puts the attribute dict of log records into *log_queue*.

    The records can be recreated with `logging.makeLogRecord()` and emitted with the
    `handle()` method of a logger with a different handler.
    """

    def __init__(self, log_queue: mp_Queue, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._log_queue = log_queue

    def handle(self, record: _logging.LogRecord):
        if exc_info := record.exc_info:
            # traceback objects cannot be pickled
            record.msg = "\n".join(
                (record.msg, "".join(format_exception(*exc_info)))
            ).rstrip()
            record.exc_info = None
        self._log_queue.put((LOG, record))


_logger = _logging.getLogger("termvisage")

LOG = 0
NOTIF = 1
child_processes = []
exported_style_attrs = {
    "iterm2": ("_TERM", "_TERM_VERSION", "jpeg_quality", "read_from_file"),
    "kitty": ("_TERM", "_TERM_VERSION", "_KITTY_VERSION"),
}

# Set from `process_multi_logs()` in the MultiLogger thread, only in the main process
log_queue: mp_Queue

# Set from `.logging.init_log()`.
multi_logger: logging.LoggingThread
