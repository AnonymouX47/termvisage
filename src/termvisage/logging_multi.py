"""Extension of `.logging` for multiprocessing support"""

from __future__ import annotations

import logging as _logging
import os
from multiprocessing import JoinableQueue, Process
from traceback import format_exception

from term_image import (
    AutoCellRatio,
    enable_win_size_swap,
    set_cell_ratio,
    set_query_timeout,
)

from . import cli, logging, notify, tui


def process_multi_logs() -> None:
    """Emits logs and notifications redirected from subprocesses.

    Intended to be executed in a separate thread of the main process.
    """
    global log_queue

    PID = os.getpid()
    log_queue = JoinableQueue()
    process_multi_logs.started.set()

    log_type, data = log_queue.get()
    while data:
        if log_type == LOG:
            data["process"] = PID
            _logger.handle(_logging.makeLogRecord(data))
        else:
            notify.notify(*data[0], **data[1])
        log_queue.task_done()
        log_type, data = log_queue.get()
    log_queue.task_done()


class Process(Process):
    """A process with integration into the logging system

    Sets up the logging system to redirect all logs (and optionally notifications)
    in the subprocess, to the main process to be emitted.

    NOTE:
        - Only TUI notifications need to be redirected.
        - The redirected logs and notifications are automatically handled by
          `process_multi_logs()`, running in the MultiLogger thread of the main process.
    """

    def __init__(self, *args, redirect_notifs: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_queue = log_queue
        self._logging_details = {
            "constants": {
                name: value for name, value in vars(logging).items() if name.isupper()
            },
            "logging_level": _logging.getLogger().getEffectiveLevel(),
            "redirect_notifs": redirect_notifs,
        }
        self._main_process_interrupted = cli.interrupted
        self._ImageClass = tui.main.ImageClass
        if self._ImageClass:  # if the TUI is initialized
            self._supported = self._ImageClass._supported
            self._forced_support = self._ImageClass.forced_support
            self._cell_ratio = cli.args.cell_ratio
            self._query_timeout = cli.args.query_timeout
            self._swap_win_size = cli.args.swap_win_size
            self._style_attrs = [
                (attr, getattr(self._ImageClass, attr))
                for attr in exported_style_attrs.get(self._ImageClass.style, ())
            ]
        child_processes.append(self)

    def run(self):
        self._redirect_logs()
        _logger.debug("Starting")

        try:
            if self._ImageClass:  # if the TUI is initialized
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
            # Log only if the main process was not interrupted
            if not self._main_process_interrupted.wait(0.1):
                logging.log(
                    "Interrupted" if logging.DEBUG else f"{self.name} was interrupted",
                    _logger,
                    _logging.ERROR,
                    direct=False,
                )
        except Exception:
            logging.log_exception(
                "Aborted" if logging.DEBUG else f"{self.name} was aborted", _logger
            )
        else:
            _logger.debug("Exiting")

    def _notif_redirector(self, *args, loading: bool = False, **kwargs):
        self._log_queue.put((NOTIF, (args, kwargs)))

    def _redirect_logs(self) -> None:
        # Logs
        vars(logging).update(self._logging_details["constants"])
        logger = _logging.getLogger()
        logger.setLevel(self._logging_details["logging_level"])
        logger.addHandler(RedirectHandler(self._log_queue))
        logger.handlers[0].addFilter(logging.filter_)

        # # Warnings and session-level logs
        _logger.setLevel(min(self._logging_details["logging_level"], _logging.INFO))

        # Notifications
        if self._logging_details["redirect_notifs"] and not logging.QUIET:
            notify.notify = self._notif_redirector


class RedirectHandler(_logging.Handler):
    """Puts the attribute dict of log records into *log_queue*.

    The records can be recreated with `logging.makeLogRecord()` and emitted with the
    `handle()` method of a logger with a different handler.
    """

    def __init__(self, log_queue: JoinableQueue, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._log_queue = log_queue

    def handle(self, record: _logging.LogRecord):
        attrdict = vars(record)
        exc_info = attrdict["exc_info"]
        if exc_info:
            # traceback objects cannot be pickled
            attrdict["msg"] = "\n".join(
                (attrdict["msg"], "".join(format_exception(*exc_info)))
            ).rstrip()
            attrdict["exc_info"] = None
        self._log_queue.put((LOG, attrdict))


_logger = _logging.getLogger("termvisage")

LOG = 0
NOTIF = 1
child_processes = []
exported_style_attrs = {
    "iterm2": ("_TERM", "_TERM_VERSION", "jpeg_quality", "read_from_file"),
    "kitty": ("_TERM", "_TERM_VERSION", "_KITTY_VERSION"),
}

# The annotations below are put in comments for compatibility with Python 3.7
# as it doesn't allow names declared as `global` within functions to be annotated.

# Set from `process_multi_logs()` in the MultiLogger thread, only in the main process
log_queue = None  #: Optional[JoinableQueue]
