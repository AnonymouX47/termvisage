"""TermVisage's CLI Implementation"""

from __future__ import annotations

import argparse
import logging as _logging
import os
import re
import sys
import warnings
from contextlib import suppress
from multiprocessing import Event as mp_Event, Queue as mp_Queue, Value
from operator import mul, setitem
from os.path import abspath, basename, exists, isdir, isfile, islink, realpath
from queue import Empty, Queue
from tempfile import mkdtemp
from threading import current_thread
from time import sleep
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Union,
)
from urllib.parse import urlparse

import requests
from PIL import Image, UnidentifiedImageError
from term_image import (
    AutoCellRatio,
    enable_win_size_swap,
    set_cell_ratio,
    set_query_timeout,
)
from term_image.exceptions import (
    StyleError,
    TermImageError,
    TermImageWarning,
    URLNotFoundError,
)
from term_image.image import BlockImage, ITerm2Image, KittyImage, Size, auto_image_class
from term_image.utils import get_terminal_name_version, get_terminal_size, write_tty

from . import logging, notify
from .config import config_options, init_config
from .ctlseqs import ERASE_IN_LINE_LEFT_b
from .exit_codes import FAILURE, INVALID_ARG, NO_VALID_SOURCE, SUCCESS
from .logging import LoggingThread, init_log, log, log_exception

try:
    import fcntl  # noqa: F401
except ImportError:
    OS_HAS_FCNTL = False
else:
    OS_HAS_FCNTL = True

if TYPE_CHECKING:
    from term_image.image import BaseImage


# Checks for CL arguments that have possible invalid values and don't have corresponding
# config options. See `check_arg()`.
ARG_CHECKS = (
    ("frame_duration", lambda x: x is None or x > 0.0, "less than or equal to zero"),
    ("max_depth", lambda x: x > 0, "less than or equal to zero"),
    (
        "max_depth",
        lambda x: (x + 50 > sys.getrecursionlimit() and sys.setrecursionlimit(x + 50)),
        "too deep",
        (RecursionError, OverflowError),
    ),
    ("repeat", lambda x: x != 0, "zero"),
    ("alpha", lambda x: 0.0 <= x < 1.0, "out of range"),
    (
        "alpha_bg",
        lambda x: not x or re.fullmatch("#([0-9a-fA-F]{6})?", "#" + x),
        "invalid hex color",
    ),
    ("h_allow", lambda x: x >= 0, "less than zero"),
    ("v_allow", lambda x: x >= 0, "less than zero"),
    ("width", lambda x: x is None or x > 0, "less than or equal to zero"),
    (
        "width",
        lambda x: (
            x is None
            or x <= (get_terminal_size().columns - args.h_allow)
            or args.oversize
        ),
        "greater than the available terminal width and `--oversize` is not specified",
    ),
    ("height", lambda x: x is None or x > 0, "less than or equal to zero"),
    (
        "height",
        lambda x: (
            x is None
            or x <= (get_terminal_size().lines - args.v_allow)
            or args.scroll
            or args.oversize
        ),
        "greater than the available terminal height and `--scroll` or `--oversize` is "
        "not specified",
    ),
    ("scale", lambda x: x is None or 0.0 < x <= 1.0, "out of range"),
    ("scale_x", lambda x: 0.0 < x <= 1.0, "out of range"),
    ("scale_y", lambda x: 0.0 < x <= 1.0, "out of range"),
    ("pad_width", lambda x: x is None or x > 0, "less than or equal to zero"),
    (
        "pad_width",
        lambda x: x is None or x <= (get_terminal_size().columns - args.h_allow),
        "greater than available terminal width",
    ),
    ("pad_height", lambda x: x is None or x > 0, "less than or equal to zero"),
)


def check_dir(
    dir: str, prev_dir: str = "..", *, _links: List[Tuple[str]] = None
) -> Optional[Dict[str, Union[bool, Dict[str, Union[bool, dict]]]]]:
    """Scan *dir* (and sub-directories, if '--recursive' was specified)
    and build the tree of directories [recursively] containing readable images.

    Args:
        - dir: Path to directory to be scanned.
        - prev_dir: Path (absolute or relative to *dir*) to set as working directory
          after scanning *dir* (default:  parent directory of *dir*).
        - _links: Tracks all symlinks from a *source* up **till** a subdirectory.

    Returns:
        - `None` if *dir* contains no readable images [recursively].
        - A dict representing the resulting directory tree whose items are:
          - a "/" key mapped to a ``True``. if *dir* contains image files
          - a directory name mapped to a dict of the same structure, for each non-empty
            sub-directory of *dir*

    NOTE:
        - If '--hidden' was specified, hidden (.[!.]*) images and subdirectories are
          considered.
        - `_depth` should always be initialized, at the module level, before calling
          this function.
    """
    global _depth

    _depth += 1
    try:
        os.chdir(dir)
    except OSError:
        log_exception(
            f"Could not access '{abspath(dir)}{os.sep}'",
            logger,
            direct=True,
        )
        return

    # Some directories can be changed to but cannot be listed
    try:
        entries = os.scandir()
    except OSError:
        log_exception(
            f"Could not get the contents of '{abspath('.')}{os.sep}'",
            logger,
            direct=True,
        )
        os.chdir(prev_dir)
        return

    empty = True
    content = {}
    for entry in entries:
        if not SHOW_HIDDEN and entry.name.startswith("."):
            continue
        try:
            is_file = entry.is_file()
            is_dir = entry.is_dir()
        except OSError:
            continue

        if is_file:
            if empty:
                try:
                    Image.open(entry.name)
                    empty = False
                    if not RECURSIVE:
                        break
                except Exception:
                    pass
        elif RECURSIVE and is_dir:
            if _depth > MAX_DEPTH:
                if not empty:
                    break
                continue

            result = None
            try:
                if entry.is_symlink():
                    path = realpath(entry)

                    # Eliminate cyclic symlinks
                    if os.getcwd().startswith(path) or (
                        _links and any(link[0].startswith(path) for link in _links)
                    ):
                        continue

                    if _source and _free_checkers.value:
                        _dir_queue.put((_source, _links.copy(), abspath(entry), _depth))
                    else:
                        _links.append((abspath(entry), path))
                        del path
                        # Return to the link's parent rather than the linked directory's
                        # parent
                        result = check_dir(entry.name, os.getcwd(), _links=_links)
                        _links.pop()
                else:
                    if _source and _free_checkers.value:
                        _dir_queue.put((_source, _links.copy(), abspath(entry), _depth))
                    else:
                        result = check_dir(entry.name, _links=_links)
            except OSError:
                pass

            if result:
                content[entry.name] = result

    # '/' is an invalid file/directory name on major platforms.
    # On platforms with root directory '/', it can never be the content of a directory.
    if not empty:
        content["/"] = True

    os.chdir(prev_dir)
    _depth -= 1
    return content or None


def check_dirs(
    checker_no: int,
    content_queue: mp_Queue,
    content_updated: mp_Event,
    dir_queue: mp_Queue,
    progress_queue: mp_Queue,
    progress_updated: mp_Event,
    free_checkers: Value,
    globals_: Dict[str, Any],
) -> None:
    """Checks a directory source in a newly **spawned** child process.

    Intended as the *target* of a **spawned** process to parallelize directory checks.
    """
    global _depth, _source

    globals().update(globals_, _free_checkers=free_checkers, _dir_queue=dir_queue)

    NO_CHECK = (None,) * 3
    while True:
        try:
            source, links, subdir, _depth = dir_queue.get_nowait()
        except KeyboardInterrupt:
            progress_queue.put((checker_no, NO_CHECK))
            raise
        except Empty:
            progress_updated.wait()
            progress_queue.put((checker_no, NO_CHECK))
            with free_checkers:
                free_checkers.value += 1
            try:
                source, links, subdir, _depth = dir_queue.get()
            finally:
                with free_checkers:
                    free_checkers.value -= 1

        if not subdir:
            break

        _source = source or subdir
        if not source:
            log(f"Checking {subdir!r}", logger, verbose=True)

        content_path = get_content_path(source, links, subdir)
        if islink(subdir):
            links.append((subdir, realpath(subdir)))
        progress_updated.wait()
        progress_queue.put((checker_no, (source, content_path, _depth)))
        result = None
        try:
            result = check_dir(subdir, _links=links)
        except Exception:
            log_exception(f"Checking {content_path!r} failed", logger, direct=True)
        finally:
            content_updated.wait()
            content_queue.put((source, content_path, result))


def get_content_path(source: str, links: List[Tuple[str]], subdir: str) -> str:
    """Returns the original path from *source* to *subdir*, collapsing all symlinks
    in-between.
    """
    if not (source and links):
        return subdir

    links = iter(links)
    absolute, prev_real = next(links)
    path = source + absolute[len(source) :]
    for absolute, real in links:
        path += absolute[len(prev_real) :]
        prev_real = real
    path += subdir[len(prev_real) :]

    return path


def get_links(source: str, subdir: str) -> List[Tuple[str, str]]:
    """Returns a list of all symlinks (and the directories they point to) between
    *source* and *subdir*.
    """
    if not source:
        return [(subdir, realpath(subdir))] if islink(subdir) else []

    links = [(source, realpath(source))] if islink(source) else []
    # Strips off the basename in case it's a link
    path = os.path.dirname(subdir[len(source) + 1 :])
    if path:
        cwd = os.getcwd()
        os.chdir(source)
        for dir in path.split(os.sep):
            if islink(dir):
                links.append((abspath(dir), realpath(dir)))
            os.chdir(dir)
        os.chdir(cwd)

    return links


def manage_checkers(
    n_checkers: int,
    dir_queue: Union[Queue, mp_Queue],
    contents: Dict[str, Union[bool, Dict]],
    images: List[Tuple[str, Generator]],
) -> None:
    """Manages the processing of directory sources in parallel using multiple processes.

    If multiprocessing is not supported on the host platform, the sources are processed
    serially in the current thread of execution, after all file sources have been
    processed.
    """
    from .logging_multi import LoggingProcess

    global _depth

    def process_result(
        source: str,
        subdir: str,
        result: Union[None, bool, Dict[str, Union[bool, Dict]]],
        n: int = -1,
    ) -> None:
        if n > -1:
            exitcode = -checkers[n].exitcode
            log(
                f"Checker-{n} was terminated "
                + (f"by signal {exitcode} " if exitcode else "")
                + (f"while checking {subdir!r}" if subdir else ""),
                logger,
                _logging.ERROR,
                direct=False,
            )
            if subdir:
                dir_queue.put(
                    (
                        source,
                        get_links(source, subdir),
                        os.path.join(
                            realpath(os.path.dirname(subdir)), basename(subdir)
                        ),
                        result,
                    )
                )
            return

        if result:
            if source not in contents:
                contents[source] = {}
            update_contents(source, contents[source], subdir, result)
        elif not source and subdir not in contents:
            # Marks a potentially empty source
            # If the source is actually empty the dict stays empty
            contents[subdir] = {}

    if logging.MULTI and n_checkers > 1:
        content_queue = mp_Queue()
        content_updated = mp_Event()
        progress_queue = mp_Queue()
        progress_updated = mp_Event()
        free_checkers = Value("i")
        globals_ = {
            name: globals()[name] for name in ("MAX_DEPTH", "RECURSIVE", "SHOW_HIDDEN")
        }

        checkers = [
            LoggingProcess(
                name=f"Checker-{n}",
                target=check_dirs,
                args=(
                    n,
                    content_queue,
                    content_updated,
                    dir_queue,
                    progress_queue,
                    progress_updated,
                    free_checkers,
                    globals_,
                ),
                daemon=True,
            )
            for n in range(n_checkers)
        ]

        for checker in checkers:
            checker.start()

        NO_CHECK = (None,) * 3
        try:
            contents[""] = contents
            content_updated.set()
            checks_in_progress = [NO_CHECK] * n_checkers
            progress_updated.set()

            # Wait until at least one checker starts processing a directory
            setitem(checks_in_progress, *progress_queue.get())

            while not (
                not any(checks_in_progress)  # All checkers are dead
                # All checks are done
                or (
                    # No check in progress
                    all(not check or check == NO_CHECK for check in checks_in_progress)
                    # All sources have been passed in
                    and dir_queue.sources_finished
                    # All sources and branched-off subdirectories have been processed
                    and dir_queue.empty()
                    # All progress updates have been processed
                    and progress_queue.empty()
                    # All results have been processed
                    and content_queue.empty()
                )
            ):
                content_updated.clear()
                while not content_queue.empty():
                    process_result(*content_queue.get())
                content_updated.set()

                progress_updated.clear()
                while not progress_queue.empty():
                    setitem(checks_in_progress, *progress_queue.get())
                progress_updated.set()

                for n, checker in enumerate(checkers):
                    if checks_in_progress[n] and not checker.is_alive():
                        # Ensure it's actually the last source processed by the dead
                        # process that's taken into account.
                        progress_updated.clear()
                        while not progress_queue.empty():
                            setitem(checks_in_progress, *progress_queue.get())
                        progress_updated.set()

                        if checks_in_progress[n]:  # Externally terminated
                            process_result(*checks_in_progress[n], n)
                            checks_in_progress[n] = None

                sleep(0.01)  # Allow queue sizes to be updated
        finally:
            if not any(checks_in_progress):
                log(
                    "All checkers were terminated, checking directory sources failed!",
                    logger,
                    _logging.ERROR,
                )
                contents.clear()
                return

            for check in checks_in_progress:
                if check:
                    dir_queue.put((None,) * 4)
            for checker in checkers:
                checker.join()
            del contents[""]
            for source, result in tuple(contents.items()):
                if result:
                    images.append((source, ...))
                else:
                    del contents[source]
                    log(f"{source!r} is empty", logger, verbose=True)
    else:
        current_thread.name = "Checker"

        _, links, source, _depth = dir_queue.get()
        while source:
            log(f"Checking {source!r}", logger, verbose=True)
            if islink(source):
                links.append((source, realpath(source)))
            try:
                result = check_dir(source, os.getcwd(), _links=links)
            except Exception:
                log_exception(f"Checking {source!r} failed", logger, direct=True)
            else:
                if result:
                    source = abspath(source)
                    contents[source] = result
                    images.append((source, ...))
                else:
                    log(f"{source!r} is empty", logger, verbose=True)
            _, links, source, _depth = dir_queue.get()


def update_contents(
    dir: str,
    contents: Dict[str, Union[bool, Dict]],
    subdir: str,
    subcontents: Dict[str, Union[bool, Dict]],
):
    """Updates a directory's content tree with the content tree of a subdirectory."""

    def update_dict(base: dict, update: dict):
        for key in update:
            # "/" can be in *base* if the directory's parent was re-checked
            if key in base and key != "/":
                update_dict(base[key], update[key])
            else:
                base[key] = update[key]

    path = subdir[len(dir) + 1 :].split(os.sep) if dir else [subdir]
    target = path.pop()

    path_iter = iter(path)
    for branch in path_iter:
        try:
            contents = contents[branch]
        except KeyError:
            contents[branch] = {}
            contents = contents[branch]
            break
    for branch in path_iter:
        contents[branch] = {}
        contents = contents[branch]
    if target in contents:
        update_dict(contents[target], subcontents)
    else:
        contents[target] = subcontents


def get_urls(
    url_queue: Queue,
    images: list[tuple[str, BaseImage]],
    ImageClass: type,
) -> None:
    """Processes URL sources from a/some separate thread(s)"""
    source = url_queue.get()
    while source:
        log(f"Getting image from {source!r}", logger, verbose=True)
        try:
            images.append((basename(source), ImageClass.from_url(source)))
        # Also handles `ConnectionTimeout`
        except requests.exceptions.ConnectionError:
            log(f"Unable to get {source!r}", logger, _logging.ERROR)
        except URLNotFoundError as e:
            log(str(e), logger, _logging.ERROR)
        except UnidentifiedImageError as e:
            log(str(e), logger, _logging.ERROR)
        except Exception:
            log_exception(f"Getting {source!r} failed", logger, direct=True)
        else:
            log(f"Done getting {source!r}", logger, verbose=True)
        source = url_queue.get()


def open_files(
    file_queue: Queue,
    images: list[tuple[str, BaseImage]],
    ImageClass: type,
) -> None:
    source = file_queue.get()
    while source:
        log(f"Opening {source!r}", logger, verbose=True)
        try:
            images.append((source, ImageClass.from_file(source)))
        except UnidentifiedImageError as e:
            log(str(e), logger, _logging.ERROR)
        except OSError as e:
            log(f"Could not read {source!r}: {e}", logger, _logging.ERROR)
        except Exception:
            log_exception(f"Opening {source!r} failed", logger, direct=True)
        source = file_queue.get()


def check_arg(
    name: str,
    check: Callable[[Any], Any],
    msg: str,
    exceptions: Tuple[Exception] = None,
    *,
    fatal: bool = True,
) -> bool:
    """Performs generic argument value checks and outputs the given message if the
    argument value is invalid.

    Returns:
        ``True`` if valid, otherwise ``False``.

    If *exceptions* is :
      - not given or ``None``, the argument is invalid only if ``check(arg)``
        returns a falsy value.
      - given, the argument is invalid if ``check(arg)`` raises one of the given
        exceptions. It's also invalid if it raises any other exception but the
        error message is different.
    """
    value = getattr(args, name)
    if exceptions:
        valid = False
        try:
            check(value)
            valid = True
        except exceptions:
            pass
        except Exception:
            log_exception(
                "Invalid! See the logs",
                logger,
                f"--{name.replace('_', '-')}",
                direct=True,
                fatal=fatal,
            )
    else:
        valid = check(value)

    if not valid:
        notify.notify(
            f"{msg} (got: {value!r})",
            notify.CRITICAL if fatal else notify.ERROR,
            f"--{name.replace('_', '-')}",
        )

    return bool(valid)


def main() -> None:
    """CLI execution sub-entry-point"""
    # Importing these (in isort order) at module-level results in circular imports
    # # Prevents circular import for program execution
    from . import __main__, config

    # # Prevents circular import for docs `autoprogram` (isort order or not)
    from .parsers import parser, style_parsers

    global args, MAX_DEPTH, RECURSIVE, SHOW_HIDDEN

    warnings.filterwarnings("error", "", TermImageWarning, "term_image.image.iterm2")

    args = parser.parse_args()
    MAX_DEPTH = args.max_depth
    RECURSIVE = args.recursive
    SHOW_HIDDEN = args.all

    force_cli_mode = not sys.stdout.isatty() and not args.cli
    if force_cli_mode:
        args.cli = True

    notify.init_notify(args)

    config.user_config_file = args.config
    if args.no_config:
        config.xdg_config_file = None
    init_config()

    init_log(args)  # `check_arg()` requires logging

    for arg_details in ARG_CHECKS:
        if not check_arg(*arg_details):
            return INVALID_ARG

    for name, option in config_options.items():
        var_name = name.replace(" ", "_")
        try:
            arg_value = getattr(args, var_name)
        # Not all config options have corresponding command-line arguments
        except AttributeError:
            continue

        if arg_value is None:
            setattr(args, var_name, option.value)
        elif not option.is_valid(arg_value):
            arg_name = f"--{name.replace(' ', '-')}"
            notify.notify(
                f"{option.error_msg} (got: {arg_value!r})",
                notify.ERROR,
                arg_name,
            )
            option_repr = "null" if option.value is None else repr(option.value)
            notify.notify(
                f"Using config value: {option_repr}",
                context=arg_name,
                verbose=True,
            )
            setattr(args, var_name, option.value)

    try:
        __main__.TEMP_DIR = mkdtemp(prefix="termvisage-")
    except OSError:
        log_exception("Failed to create the temporary data directory", logger)
    else:
        logger.debug(f"Created the temporary data directory {__main__.TEMP_DIR!r}")

    set_query_timeout(args.query_timeout)
    if args.swap_win_size:
        enable_win_size_swap()

    if args.auto_cell_ratio:
        args.cell_ratio = None
    try:
        set_cell_ratio(args.cell_ratio or AutoCellRatio.DYNAMIC)
    except TermImageError:
        notify.notify(
            "Auto cell ratio is not supported in the active terminal or on this "
            "platform, using 0.5. It can be set otherwise using `-C | --cell-ratio`.",
            notify.WARNING,
        )
        args.cell_ratio = 0.5

    ImageClass = {
        "auto": None,
        "kitty": KittyImage,
        "iterm2": ITerm2Image,
        "block": BlockImage,
    }[args.style]
    if not ImageClass:
        ImageClass = auto_image_class()

    if args.force_style or args.style is config_options.style != "auto":
        ImageClass.is_supported()  # Some classes need to set some attributes
        ImageClass.forced_support = True
    else:
        try:
            ImageClass(None)
        except StyleError:  # Instantiation isn't permitted
            write_tty(ERASE_IN_LINE_LEFT_b + b"\r")  # Erase any emitted APCs
            log(
                f"The '{ImageClass}' render style is not supported in the current "
                "terminal! To use it anyways, add '--force-style'.",
                logger,
                _logging.CRITICAL,
            )
            return FAILURE
        except TypeError:  # Instantiation is permitted
            if not ImageClass.is_supported():
                log(
                    f"The '{ImageClass}' render style might not be fully supported in "
                    "the current terminal... using it anyways.",
                    logger,
                    _logging.WARNING,
                )

    # Some APCs (e.g kitty's) used for render style support detection get emitted on
    # some non-supporting terminal emulators
    write_tty(ERASE_IN_LINE_LEFT_b + b"\r")  # Erase any emitted APCs

    log(f"Using '{ImageClass}' render style", logger, verbose=True)
    style_parser = style_parsers.get(ImageClass.style)
    style_args = vars(style_parser.parse_known_args()[0]) if style_parser else {}

    if ImageClass.style == "iterm2":
        ITerm2Image.jpeg_quality = style_args.pop("jpeg_quality")
        ITerm2Image.native_anim_max_bytes = style_args.pop("native_max_bytes")
        ITerm2Image.read_from_file = style_args.pop("read_from_file")

    if ImageClass.style in {"kitty", "iterm2"} and not 0 <= style_args["compress"] <= 9:
        notify.notify(
            "Compression level must be between 0 and 9, both inclusive "
            f"(got: {style_args['compress']})",
            notify.CRITICAL,
        )
        return INVALID_ARG

    # Remove style-specific args with default values
    for arg_name, value in tuple(style_args.items()):
        if value == style_parser.get_default(arg_name):
            del style_args[arg_name]

    if force_cli_mode:
        log(
            "Output is not a terminal, forcing CLI mode!",
            logger,
            _logging.WARNING,
        )

    log("Processing sources...", logger, verbose=True)
    notify.start_loading()

    file_images, dir_images = [], []
    contents = {}
    sources = [
        abspath(source) if exists(source) else source for source in args.sources or "."
    ]
    unique_sources: dict[str, int] = {}

    url_queue = Queue()
    getters = [
        LoggingThread(
            target=get_urls,
            args=(url_queue, url_images, ImageClass),
            name=f"Getter-{n}",
            daemon=True,
        )
        for n in range(1, config_options.getters + 1)
    ]
    getters_started = False

    file_queue = Queue()
    opener = LoggingThread(
        target=open_files,
        args=(file_queue, file_images, ImageClass),
        name="Opener",
        daemon=True,
    )
    opener_started = False

    if OS_HAS_FCNTL and not args.cli:
        n_checkers = config_options.checkers
        if n_checkers is None:
            n_checkers = max(
                (
                    len(os.sched_getaffinity(0))
                    if hasattr(os, "sched_getaffinity")
                    else os.cpu_count() or 0
                )
                - 1,
                2,
            )
        dir_queue = mp_Queue() if logging.MULTI and n_checkers > 1 else Queue()
        dir_queue.sources_finished = False
        check_manager = LoggingThread(
            target=manage_checkers,
            args=(n_checkers, dir_queue, contents, dir_images),
            name="CheckManager",
            daemon=True,
        )
    checkers_started = False

    for source_index, source in enumerate(sources):
        if source in unique_sources:
            log(f"Source repeated: {source!r}", logger, verbose=True)
            continue
        unique_sources[source] = source_index

        if all(urlparse(source)[:3]):  # Is valid URL
            if not getters_started:
                for getter in getters:
                    getter.start()
                getters_started = True
            url_queue.put(source)
        elif isfile(source):
            if not opener_started:
                opener.start()
                opener_started = True
            file_queue.put(source)
        elif isdir(source):
            if args.cli:
                log(f"Skipping directory {source!r}", logger, verbose=True)
                continue
            if not OS_HAS_FCNTL:
                dir_images = True
                continue
            if not checkers_started:
                check_manager.start()
                checkers_started = True
            dir_queue.put(("", [], source, 0))
        else:
            log(f"{source!r} is invalid or does not exist", logger, _logging.ERROR)

    # Signal end of sources
    if getters_started:
        for _ in range(config_options.getters):
            url_queue.put(None)
    if opener_started:
        file_queue.put(None)
    if checkers_started:
        if logging.MULTI and n_checkers > 1:
            dir_queue.sources_finished = True
        else:
            dir_queue.put((None,) * 4)

    if getters_started:
        for getter in getters:
            getter.join()
    if opener_started:
        opener.join()
    if checkers_started:
        check_manager.join()

    notify.stop_loading()
    notify.loading_interrupted.set()
    while notify.is_loading():
        pass

    if not OS_HAS_FCNTL and dir_images:
        log(
            "Directory sources skipped, not supported on Windows!",
            logger,
            _logging.ERROR,
        )
        dir_images = []

    log("... Done!", logger, verbose=True)

    images = file_images + url_images + dir_images
    if not images:
        log("No valid source!", logger)
        return NO_VALID_SOURCE
    # Sort entries by order on the command line
    images.sort(key=lambda x: unique_sources[x[0] if x[1] is ... else x[1].source])

    if args.cli or not args.tui and len(images) == 1 and images[0][1] is not ...:
        log("Running in CLI mode", logger, direct=False)

        if style_args.get("native") and len(images) > 1:
            style_args["stall_native"] = False

        show_name = len(args.sources) > 1
        for entry in images:
            image = entry[1]
            if 0 < args.max_pixels < mul(*image._original_size):
                log(
                    f"Has more than the maximum pixel-count, skipping: {entry[0]!r}",
                    logger,
                    _logging.WARNING,
                    verbose=True,
                )
                continue

            if (
                not args.no_anim
                and image.is_animated
                and not style_args.get("native")
                and len(images) > 1
            ):
                log(f"Skipping animated image: {entry[0]!r}", logger, verbose=True)
                continue

            if show_name:
                notify.notify("\n" + basename(entry[0]) + ":")
            try:
                if args.width is None is args.height:
                    args.width = args.auto_size or Size.AUTO
                image.set_size(
                    args.width,
                    args.height,
                    args.h_allow,
                    args.v_allow,
                )
                image.scale = (
                    (args.scale_x, args.scale_y) if args.scale is None else args.scale
                )
                if args.frame_duration:
                    image.frame_duration = args.frame_duration

                if ImageClass.style == "kitty":
                    image.set_render_method(
                        "lines"
                        if (
                            get_terminal_name_version()[0] == "kitty"
                            and image.is_animated
                            and not args.no_anim
                        )
                        else "whole"
                    )
                elif ImageClass.style == "iterm2":
                    image.set_render_method(
                        "whole"
                        if (
                            get_terminal_name_version()[0] == "konsole"
                            # Always applies to non-native animations also
                            or image.rendered_height <= get_terminal_size().lines
                        )
                        else "lines"
                    )

                image.draw(
                    *(
                        (None, 1, None, 1)
                        if args.no_align
                        else (
                            args.h_align,
                            args.pad_width,
                            args.v_align,
                            args.pad_height or 1,
                        )
                    ),
                    (
                        None
                        if args.no_alpha
                        else (
                            args.alpha if args.alpha_bg is None else "#" + args.alpha_bg
                        )
                    ),
                    scroll=args.scroll,
                    animate=not args.no_anim,
                    repeat=args.repeat,
                    cached=(
                        not args.cache_no_anim
                        and (args.cache_all_anim or args.anim_cache)
                    ),
                    check_size=not args.oversize,
                    **style_args,
                )

            # Handles `ValueError` and `.exceptions.InvalidSizeError`
            # raised by `BaseImage.set_size()`, scaling value checks
            # or padding width/height checks.
            except (ValueError, StyleError, TermImageWarning) as e:
                notify.notify(str(e), notify.ERROR)
            except BrokenPipeError:
                # Prevent ignored exception message at interpreter shutdown
                with suppress(BrokenPipeError):
                    sys.stdout.close()
                break
    elif OS_HAS_FCNTL:
        from . import tui

        tui.init(args, style_args, images, contents, ImageClass)
    else:
        log(
            "The TUI is not supported on Windows! Try with `--cli`.",
            logger,
            _logging.CRITICAL,
        )
        return FAILURE

    return SUCCESS


logger = _logging.getLogger(__name__)

# Used by `check_dir()`
_depth: int

# Set from within `check_dirs()`; Hence, only set in "Checker-?" processes
_dir_queue: Queue | mp_Queue
_free_checkers: Value
_source: str | None = None

# Set from within `main()`
MAX_DEPTH: int
RECURSIVE: bool
SHOW_HIDDEN: bool
# # Used in other modules
args: argparse.Namespace | None = None
url_images: list[tuple[str, BaseImage]] = []
