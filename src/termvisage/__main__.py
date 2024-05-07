"""Support for command-line execution using `python -m termvisage`"""

from __future__ import annotations

import logging as _logging
import multiprocessing
import sys
from threading import Thread, main_thread

from term_image.utils import write_tty

from .exit_codes import FAILURE, INTERRUPTED, codes


def main() -> int:
    """CLI execution entry-point"""
    from argcomplete import autocomplete

    from .parsers import parser

    autocomplete(parser)

    from . import cli, logging, notify, tui

    global MAIN_THREAD, interrupted

    def cleanup_temp_dir():
        if not TEMP_DIR:
            return

        from shutil import rmtree

        try:
            rmtree(TEMP_DIR)
        except OSError:
            logging.log_exception(
                f"Failed to delete the temporary data directory {TEMP_DIR!r}", logger
            )

    def finish_loading():
        if notify.loading_initialized:
            notify.end_loading()  # End the current phase (may be CLI or TUI)
            notify.loading_interrupted.set()
            if not tui.initialized:
                while notify.is_loading():  # Wait for the CLI phase to end
                    pass
                notify.end_loading()  # End the TUI phase
            notify.loading_indicator.join()  # Finally, wait for the thread to exit

    def finish_multi_logging():
        if logging.initialized and logging.MULTI:
            from .logging_multi import child_processes, log_queue, multi_logger

            if not interrupted:
                for process in child_processes:
                    process.join()

            log_queue.put((None,) * 2)  # End of logs
            multi_logger.join()

    # 1. `PIL.Image.open()` seems to cause forked child processes to block when called
    # in both the parent and the child.
    # 2. Unifies things across multiple platforms.
    multiprocessing.set_start_method("spawn")

    MAIN_THREAD = main_thread()

    logger = _logging.getLogger("termvisage")
    logger.setLevel(_logging.INFO)

    try:
        write_tty(b"\033[22;2t")  # Save window title
        write_tty(b"\033]2;TermVisage\033\\")  # Set window title
        exit_code = cli.main()
    except KeyboardInterrupt:
        interrupted = True
        finish_loading()
        finish_multi_logging()
        cleanup_temp_dir()
        logging.log(
            "Session interrupted",
            logger,
            _logging.CRITICAL,
            file=logging.initialized,
            # If the TUI was not initialized, write to console only if verbosity is
            # enabled
            direct=bool(
                tui.initialized or cli.args and (cli.args.verbose or cli.args.debug)
            ),
        )
        if cli.args and cli.args.debug:
            raise
        return INTERRUPTED
    except Exception as e:
        interrupted = True
        finish_loading()
        finish_multi_logging()
        cleanup_temp_dir()
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
        cleanup_temp_dir()
        logger.info(f"Session ended with return-code {exit_code} ({codes[exit_code]})")
        return exit_code
    finally:
        write_tty(b"\033[23;2t")  # Restore window title
        # Explicit cleanup is necessary since the top-level `Image` widgets
        # will still hold references to the `BaseImage` instances
        for _, image_w in cli.url_images:
            image_w._ti_image.close()


# Session-specific temporary data directory.
# Updated from `.cli.main()`.
TEMP_DIR: str | None = None

# The main thread of the main process.
# Set from `main()`.
MAIN_THREAD: Thread

# Process interruption flag.
interrupted: bool = False

if __name__ == "__main__":
    sys.exit(main())
