"""Support for command-line execution using `python -m termvisage`"""

from __future__ import annotations

import logging as _logging
import multiprocessing
import sys
from threading import Event

from term_image.utils import write_tty

from .exit_codes import FAILURE, INTERRUPTED, codes


def main() -> int:
    """CLI execution entry-point"""
    from argcomplete import autocomplete

    from .parsers import parser

    autocomplete(parser)

    from . import cli, logging, notify
    from .tui import main

    def finish_loading():
        if not logging.QUIET and notify.loading_indicator:
            notify.end_loading()
            if not main.loop:  # TUI was not launched
                while notify.is_loading():
                    pass
                notify.end_loading()
            notify.loading_indicator.join()

    def finish_multi_logging():
        if logging.initialized and logging.MULTI:
            from .logging_multi import child_processes, log_queue

            for process in child_processes:
                process.join()
            log_queue.put((None,) * 2)  # End of logs
            log_queue.join()

    # 1. `PIL.Image.open()` seems to cause forked child processes to block when called
    # in both the parent and the child.
    # 2. Unifies things across multiple platforms.
    multiprocessing.set_start_method("spawn")

    logger = _logging.getLogger("termvisage")
    logger.setLevel(_logging.INFO)

    cli.interrupted = Event()
    try:
        write_tty(b"\033[22;2t")  # Save window title
        write_tty(b"\033]2;TermVisage\033\\")  # Set window title
        exit_code = cli.main()
    except KeyboardInterrupt:
        cli.interrupted.set()  # Signal interruption to subprocesses and other threads.
        finish_loading()
        finish_multi_logging()
        logging.log(
            "Session interrupted",
            logger,
            _logging.CRITICAL,
            file=logging.initialized,
            # If the TUI was not launched, only print to console if verbosity is enabled
            direct=bool(main.loop or cli.args and (cli.args.verbose or cli.args.debug)),
        )
        if cli.args and cli.args.debug:
            raise
        return INTERRUPTED
    except Exception as e:
        cli.interrupted.set()  # Signal interruption to subprocesses and other threads.
        finish_loading()
        finish_multi_logging()
        if logging.initialized:
            logger.exception("Session terminated due to:")
        logging.log(
            "Session not ended successfully: "
            f"({type(e).__module__}.{type(e).__qualname__}) {e}",
            logger,
            _logging.CRITICAL,
            file=logging.initialized,
        )
        if cli.args and cli.args.debug:
            raise
        return FAILURE
    else:
        finish_loading()
        finish_multi_logging()
        logger.info(f"Session ended with return-code {exit_code} ({codes[exit_code]})")
        return exit_code
    finally:
        write_tty(b"\033[23;2t")  # Restore window title
        # Explicit cleanup is necessary since the top-level `Image` widgets
        # will still hold references to the `BaseImage` instances
        for _, image_w in cli.url_images:
            image_w._ti_image.close()


if __name__ == "__main__":
    sys.exit(main())
