"""Main UI"""

from __future__ import annotations

import logging as _logging
import os
from enum import Enum, auto
from operator import mul
from os.path import abspath, basename, isfile, islink
from pathlib import Path
from queue import Queue
from threading import Event
from typing import Callable, Dict, Generator, Iterable, List, Optional, Tuple, Union

import PIL
import urwid
from term_image.image import BaseImage
from term_image.utils import write_tty

from .. import logging, notify
from ..config import context_keys, expand_key
from ..ctlseqs import BEL_b
from .keys import (
    disable_actions,
    enable_actions,
    keys,
    no_globals,
    set_image_grid_actions,
    set_image_view_actions,
    set_menu_actions,
    set_menu_count,
)
from .render import resync_grid_rendering
from .widgets import (
    Image,
    ImageCanvas,
    LineSquare,
    MenuEntry,
    action_bar,
    image_box,
    image_grid,
    image_grid_box,
    info_bar,
    menu,
    placeholder,
    view,
    viewer,
)


class EntryKind(Enum):
    """Kinds of directory entries as used by ``scan_dir*()``."""

    UNKNOWN = auto()
    HIDDEN = auto()
    UNREADABLE = auto()
    IMAGE = auto()
    DIR = auto()


class MenuAction(Enum):
    """Some actions of the menu context implemented via ``display_images()``."""

    OPEN = auto()
    BACK = auto()
    DELETE = auto()


def animate_image(image_w: Image, forced_render: bool = False) -> None:
    """Initializes an animation."""
    if not NO_ANIMATION and (
        mul(*image_w._ti_image.original_size) <= MAX_PIXELS or forced_render
    ):
        try:
            del image_w._ti_anim_finished
        except AttributeError:
            try:
                del image_w._ti_anim_ongoing
            except AttributeError:
                pass
        else:
            if image_w._ti_canv:  # Hasn't been removed
                image_w._ti_canv = None  # Deleting will break `ImageRenderManager`

        # Switched from this animated image earlier, to another animated image while
        # AnimRenderManager was waiting on a frame's duration
        # i.e the attributes didn't get to be removed by AnimRenderManager
        try:
            # If one fails, the rest shouldn't exist (removed by AnimRenderManager)
            del image_w._ti_frame
            del image_w._ti_force_render
            del image_w._ti_forced_anim_size_hash
        except AttributeError:
            pass

        # Only needs to be set once for an animation, not per frame
        if forced_render:
            image_w._ti_force_render = True


def display_images(
    dir: str,
    items: List[Tuple[str, Union[Image, type(...)]]],
    contents: Dict[str, Union[bool, Dict[str, Union[bool, dict]]]],
    prev_dir: str = "..",
    *,
    top_level: bool = False,
) -> Generator[None, Union[int, MenuAction], bool]:
    """Displays images in _dir_ (and sub-directories, if '--recursive' is set)
    as yielded by ``scan_dir(dir)``.

    Args:
        - dir: Path to directory containing images.
        - items: An iterable of ``(entry, value)`` pairs, such as yielded by
          ``scan_dir(dir)`` i.e:

          - ``(str, Image)`` for images in *dir*, and
          - ``(str, Ellipsis)`` for sub-directories of *dir*

        - contents: Tree of directories containing readable images
          (such as returned by `check_dir(dir)`)
        - prev_dir: Path to set as working directory after displaying images in *dir*
          (default:  parent directory of *dir*)
        - top_level: Specifies if *dir* is the top level (For internal use only)

    Returns:
        The empty status of the (current) directory being exited i.e ``True`` if empty,
        otherwise ``False``.

    Receives:
        Via .send(), either:
          - a menu item position (-1 and above)
          - an enumerator denoting a certain action
    """
    global _grid_list, grid_path, last_non_empty_grid_path

    os.chdir(dir)

    # For `.tui.keys.set_menu_actions()`, called by `update_menu()`
    menu_is_complete = top_level or grid_scan_done.is_set()
    menu_scan_done.set() if menu_is_complete else menu_scan_done.clear()

    update_menu(items, top_level)
    next_menu.put((items, contents, menu_is_complete))

    entry = prev_pos = value = None  # Silence linter's `F821`
    pos = 0 if top_level else -1

    while True:
        if pos == -1:  # Cursor on top menu item ("..")
            if top_level:
                if items:
                    # Ensure ".." is not selectable at top level
                    # Possible when "Home" action is invoked
                    pos = 0
                    menu.focus_position = 1
                    continue
                else:
                    set_context("global")
            grid_active.clear()
            image_box._w.contents[1][0].contents[1] = (
                placeholder,
                ("weight", 1, False),
            )
            image_box.original_widget = placeholder  # halt image and anim rendering
            image_box.set_title("Image")
            view.original_widget = image_box
            getattr(ImageClass, "clear", lambda: True)()

        # Implements "menu::Open" action (for non-image entries)
        elif pos == MenuAction.OPEN:
            if prev_pos == -1:
                # prev_pos can never be -1 at top level (See `pos == -1` branch above),
                # and even if it could, `pos == MenuAction.BACK` still guards against it
                pos = MenuAction.BACK
                continue

            # Ensure menu scanning is halted before WD is changed to prevent
            # `FileNotFoundError`s
            if not menu_scan_done.is_set():
                menu_acknowledge.clear()
                menu_change.set()
                menu_acknowledge.wait()
                menu_change.clear()

            # Ensure grid scanning is halted to avoid updating `_grid_list` which is
            # used as the next `menu_list` as is and to prevent `FileNotFoundError`s
            if not grid_scan_done.is_set():
                grid_acknowledge.clear()
                grid_active.clear()
                grid_acknowledge.wait()

            # To restore the menu on the way back
            menu_is_complete = menu_scan_done.is_set()

            logger.debug(f"Going into {abspath(entry)}/")
            empty = yield from display_images(
                entry,
                _grid_list,
                contents[entry],
                # Return to Top-Level Directory, OR
                # to the link's parent instead of the linked directory's parent
                os.getcwd() if top_level or islink(entry) else "..",
            )
            # Menu change already signaled by menu::Back from the exited directory

            # For `.tui.keys.set_menu_actions()`, called by `update_menu()`
            menu_scan_done.set() if menu_is_complete else menu_scan_done.clear()

            if empty:  # All entries in the exited directory have been deleted
                del items[prev_pos]
                del contents[entry]
                pos = min(prev_pos, len(items) - 1)
                # Restore the menu and view pane for the previous (this) directory,
                # while removing the empty directory entry.
                update_menu(items, top_level, pos)
                logger.debug(f"Removed empty directory entry '{entry}/' from the menu")
                notify.notify(f"Removed empty directory entry '{entry}/' from the menu")
            else:
                # Restore the menu and view pane for the previous (this) directory
                update_menu(items, top_level, prev_pos)
                pos = prev_pos

            next_menu.put((items, contents, menu_is_complete))
            continue  # Skip `yield`

        elif pos == MenuAction.BACK:  # Implements "menu::Back" action
            if not top_level:
                # Ensure menu scanning is halted before WD is changed to prevent
                # `FileNotFoundError`s
                if not menu_scan_done.is_set():
                    menu_acknowledge.clear()
                    menu_change.set()
                    menu_acknowledge.wait()
                    menu_change.clear()

                # Ensure grid scanning is halted before WD is changed to prevent
                # `FileNotFoundError`s
                if grid_active.is_set() and not grid_scan_done.is_set():
                    grid_acknowledge.clear()
                    grid_active.clear()
                    grid_acknowledge.wait()

                break

            # Since the execution context is not exited at the top-level, ensure pos
            # (and indirectly, prev_pos) always corresponds to a valid menu position.
            # By implication, this prevents an `IndexError` or rendering the wrong image
            # when coming out of a directory that was entered when prev_pos < -1.
            pos = prev_pos

        elif pos == MenuAction.DELETE:
            del items[prev_pos]
            pos = min(prev_pos, len(items) - 1)
            update_menu(items, top_level, pos)
            yield  # Displaying next image immediately will mess up confirmation overlay
            if DEBUG:
                info_bar.set_text(f"delete_pos={pos} {info_bar.text}")
            continue

        else:
            entry, value = items[pos]
            if isinstance(value, Image):
                grid_active.clear()
                image_box._w.contents[1][0].contents[1] = (value, ("weight", 1, False))
                image_box.set_title(entry)
                view.original_widget = image_box
                image_box.original_widget = value
                if value._ti_image.is_animated:
                    animate_image(value)
            else:  # Directory
                grid_acknowledge.clear()
                grid_active.set()

                next_grid.put((entry, contents[entry]))
                # No need to wait for acknowledgement since this is a new list instance
                _grid_list = []
                # Absolute paths work fine with symlinked images and directories,
                # as opposed to real paths, especially in path comparisons
                # e.g in `.tui.render.manage_grid_renders()`.
                grid_path = abspath(entry)

                if contents[entry].get("/") and grid_path != last_non_empty_grid_path:
                    resync_grid_rendering()
                    last_non_empty_grid_path = grid_path

                image_box.original_widget = placeholder  # halt image and anim rendering
                image_grid_box.set_title(grid_path + "/")
                view.original_widget = image_grid_box
                image_grid_box.base_widget._invalidate()

                if contents[entry].get("/"):
                    enable_actions("menu", "Switch Pane")
                else:
                    disable_actions("menu", "Switch Pane")

                # Wait for GridScanner to clear grid contents.
                # Not waiting could result in an `IndexError` raised by
                # `GridFlow.focus_position` in `GridFlow.generate_display_widget()`
                # when it meets the grid non-empty but it's then cleared by
                # GridScanner in the course of generating the display widget.
                grid_acknowledge.wait()

            getattr(ImageClass, "clear", lambda: True)() or ImageCanvas.change()

        prev_pos = pos
        pos = yield
        while pos == prev_pos:
            pos = yield
        if DEBUG:
            info_bar.set_text(f"pos={pos} {info_bar.text}")

    if not top_level:
        logger.debug(f"Going back to {abspath(prev_dir)}/")
        os.chdir(prev_dir)

    return menu_scan_done.is_set() and not items


def get_context() -> None:
    """Returns the current context"""
    return _context


def get_prev_context(n: int = 1) -> None:
    """Return the nth previous context (1 <= n <= 3)"""
    return _prev_contexts[n - 1]


def process_input(key: str) -> bool:
    if DEBUG:
        info_bar.set_text(f"{key!r} {info_bar.text}")

    found = False
    if key in keys["global"]:
        if (
            _context not in no_globals
            or _context == "global"
            or key in {"resized", expand_key[0]}
        ):
            func, state = keys["global"][key]
            func() if state else write_tty(BEL_b)
            found = True

    elif key[0] == "mouse press":  # strings also support subscription
        # change context if the pane in focus changed.
        if _context in {"image", "image-grid"} and viewer.focus_position == 0:
            set_context("menu")
            found = True
        elif _context == "menu" and viewer.focus_position == 1:
            if not context_keys["menu"]["Switch Pane"][4]:
                # Set focus back to the menu if "menu::Switch Pane" is disabled
                viewer.focus_position = 0
            else:
                if view.original_widget is image_box:
                    set_context("image")
                    set_image_view_actions()
                else:
                    set_context("image-grid")
                    set_image_grid_actions()
            found = True

    else:
        func, state = keys[_context].get(key, (None, None))
        if state:
            func()
        elif state is False:
            write_tty(BEL_b)
        found = state is not None

    return bool(found)


def scan_dir(
    dir: str,
    contents: Dict[str, Union[bool, Dict[str, Union[bool, dict]]]],
    last_entry: Optional[str] = None,
    sort_key: Optional[Callable] = None,
    *,
    notify_errors: bool = False,
) -> Generator[Tuple[EntryKind, Tuple[str, Union[Image, type(...)]]], None, int]:
    """Scans *dir* for readable images (and sub-directories containing such,
    if '--recursive' was set).

    Args:
        - dir: Path to directory to be scanned.
        - contents: Tree of directories containing readable images
          (as produced by ``.cli.check_dir(dir)``).
        - last_entry: The entry after which scanning should start, if ``None`` or
          not found, all entries in the directory are scanned.
        - sort_key: A callable to generate values to be used in sorting the directory
          entries.
        - notify_errors: If True, a notification showing the number of unreadable
          files will be displayed.

    Yields:
        A tuple ``(kind, (entry, value))``, where
          - *kind* is the entry's kind,
          - *entry* is the entry's name,
          - and *value* is either:

            - an image widget, for images in *dir*, or
            - ``Ellipsis``, for sub-directories of *dir* (if '--recursive' is set).

    Returns:
        The number of unreadable files in *dir*.

    - If '--all' was set, hidden (.*) images and subdirectories are included.
    - Items are grouped into images and directories, sorted lexicographically and
      case-insensitively. Any preceding '.'s (dots) are ignored when sorting.
    - If a dotted entry has the same main-name as another entry, the dotted one comes
      first.
    """
    _entries = sorted(os.scandir(dir), key=sort_key or sort_key_lexi)
    entries = iter(_entries)
    if last_entry:
        for entry in entries:
            if entry.name == last_entry:
                break
        else:  # Start from the beginning if *last_entry* isn't found
            entries = _entries

    errors = 0
    for entry in entries:
        kind = scan_dir_entry(entry, contents)
        if kind is EntryKind.UNREADABLE:
            errors += 1
        yield kind, (
            entry.name,
            (
                Image(ImageClass.from_file(entry.path))
                if kind is EntryKind.IMAGE
                else ... if kind is EntryKind.DIR else None
            ),
        )

    if notify_errors and errors:
        notify.notify(
            f"{errors} file(s) could not be read in {abspath(dir)!r}! Check the logs.",
            level=notify.ERROR,
        )

    return errors


def scan_dir_entry(
    entry: Union[os.DirEntry, Path],
    contents: Dict[str, Union[bool, Dict[str, Union[bool, dict]]]],
    entry_path: Optional[str] = None,
) -> EntryKind:
    """Scans a single directory entry and returns its kind."""
    if not SHOW_HIDDEN and entry.name.startswith("."):
        return EntryKind.HIDDEN
    if contents.get("/") and entry.is_file():
        try:
            PIL.Image.open(abspath(entry))
        except PIL.UnidentifiedImageError:
            # Reporting will apply to every non-image file :(
            return EntryKind.UNKNOWN
        except Exception:
            logging.log_exception(f"{abspath(entry)!r} could not be read", logger)
            return EntryKind.UNREADABLE
        else:
            return EntryKind.IMAGE
    if RECURSIVE and entry.name in contents:
        # `.cli.check_dir()` already eliminated bad symlinks
        return EntryKind.DIR

    return EntryKind.UNKNOWN


def scan_dir_grid() -> None:
    """Updates the image grid using ``scan_dir()``.

    This is designed to be executed in a separate thread, while certain grid details
    are passed in using the ``next_grid`` queue.

    For each valid entry, a tuple ``(entry, value)``, like in ``scan_dir()``,
    is appended to ``.tui.main._grid_list`` and adds the *value* to the
    grid widget (for image entries only), then updates the screen.
    """
    grid_contents = image_grid.contents
    while True:
        dir, contents = next_grid.get()
        grid_list = _grid_list
        grid_contents.clear()
        grid_acknowledge.set()  # Cleared grid contents
        grid_scan_done.clear()
        page_not_complete = True
        notify.start_loading()

        for kind, item in scan_dir(dir, contents):
            if kind is EntryKind.IMAGE:
                grid_list.append(item)
                image_w = item[1]
                image = image_w._ti_image
                border_attr = (
                    "high-res"
                    if 0 < MAX_PIXELS < mul(*image.original_size)
                    else "focused box"
                )
                grid_contents.append(
                    (
                        urwid.AttrMap(
                            LineSquare(image_w, basename(image.source), border_attr),
                            "unfocused box",
                            border_attr,
                        ),
                        image_grid.options(),
                    )
                )
                image_grid_box.base_widget._invalidate()
                if page_not_complete:
                    if len(grid_contents) <= image_grid_box.base_widget._ti_page_ncell:
                        update_screen()
                    else:
                        page_not_complete = False
            elif kind is EntryKind.DIR:
                grid_list.append(item)

            if not next_grid.empty():
                break
            if not grid_active.is_set():
                grid_acknowledge.set()
                break
        else:
            grid_scan_done.set()
            update_screen()
            # There is a possibility that `grid_scan_done` is read as "cleared"
            # in-between the end of the last iteration an here :)
            if not grid_active.is_set():
                grid_acknowledge.set()
        notify.stop_loading()


def scan_dir_menu() -> None:
    """Updates the menu list using ``scan_dir()``.

    This is designed to be executed in a separate thread, while certain menu details
    are passed in using the ``next_menu`` queue.

    For each valid entry, a tuple ``(entry, value)``, like in ``scan_dir()``,
    is appended to ``.tui.main.menu_list`` and appends a ``MenuEntry`` widget to the
    menu widget, then updates the screen.
    """
    menu_body = menu.body
    while True:
        items, contents, menu_is_complete = next_menu.get()
        if menu_is_complete:
            continue
        page_not_complete = True
        notify.start_loading()

        for kind, item in scan_dir(
            ".", contents, items[-1][0] if items else None, notify_errors=True
        ):
            if kind is EntryKind.IMAGE:
                items.append(item)
                menu_body.append(
                    urwid.AttrMap(MenuEntry(item[0]), "default", "focused entry")
                )
                if page_not_complete:
                    if len(items) <= menu._ti_height:
                        update_screen()
                    else:
                        page_not_complete = False
            elif kind is EntryKind.DIR:
                items.append(item)
                menu_body.append(
                    urwid.AttrMap(MenuEntry(item[0] + "/"), "default", "focused entry")
                )
                if page_not_complete:
                    if len(items) <= menu._ti_height:
                        update_screen()
                    else:
                        page_not_complete = False

            if menu_change.is_set():
                menu_acknowledge.set()
                break
        else:
            menu_scan_done.set()
            set_menu_count()
            update_screen()
            # There is a possibility that `menu_scan_done` is read as "cleared"
            # in-between the end of the last iteration an here :)
            if menu_change.is_set():
                menu_acknowledge.set()
        notify.stop_loading()


def set_context(new_context) -> None:
    """Sets the current context and updates the Key/Action bar"""
    global _context

    if DEBUG:
        info_bar.set_text(f"{_prev_contexts} {info_bar.text}")
    _prev_contexts[1:] = _prev_contexts[:2]  # Right-shift older contexts
    _prev_contexts[0] = _context
    _context = new_context
    action_bar.update(new_context)
    if DEBUG:
        info_bar.set_text(f"{new_context!r} {_prev_contexts} {info_bar.text}")


def set_prev_context(n: int = 1) -> None:
    """Set the nth previous context as the current context (1 <= n <= 3)"""
    global _context

    if DEBUG:
        info_bar.set_text(f"{_prev_contexts} {info_bar.text}")
    _context = _prev_contexts[n - 1]
    action_bar.update(_context)
    _prev_contexts[:n] = []
    _prev_contexts.extend(["menu"] * n)
    if DEBUG:
        info_bar.set_text(f"{_prev_contexts} {info_bar.text}")


def sort_key_lexi(entry: os.DirEntry | Path, actual_path: str = ""):
    """Lexicographic ordering key function.

    Compatible with ``list.sort()``, ``sorted()``, etc.
    """
    name = entry.name
    return (
        # group directories before files
        chr(isfile(actual_path) if actual_path else entry.is_file())
        # sort within each group, ignoring visibility and case
        + name.lstrip(".").casefold()
        # hidden before non-hidden of the same name; '\0' makes the key for the
        # non-hidden longer without affecting it's order relative to other entries
        + "\0" * (not name.startswith("."))
    )


def update_menu(
    items: Iterable[Tuple[str, Union[Image, type(...)]]],
    top_level: bool = False,
    pos: int = -1,
) -> None:
    global menu_list, at_top_level
    menu_list, at_top_level = items, top_level

    menu.body[:] = [
        (
            urwid.Text(("inactive", ".."))
            if top_level
            else urwid.AttrMap(MenuEntry(".."), "default", "focused entry")
        )
    ]
    menu.body += [
        urwid.AttrMap(
            MenuEntry(
                (basename(entry) if at_top_level else entry) + "/" * (value is ...)
            ),
            "default",
            "focused entry",
        )
        for entry, value in items
    ]
    menu.focus_position = pos + 1 + (at_top_level and pos == -1)
    set_menu_actions()
    set_menu_count()


def update_screen():
    """Triggers a screen redraw.

    Meant to be called from threads other than the thread in which the MainLoop is
    running.
    """
    try:
        os.write(update_pipe, b" ")
    except OSError as e:
        if e.errno != 9:
            logging.log_exception("Screen update failed", logger)


logger = _logging.getLogger(__name__)

# For grid scanning/display
grid_acknowledge = Event()
grid_active = Event()
grid_scan_done = Event()
next_grid = Queue(1)

# # Set from within `display_images()`
_grid_list: list | None = None
grid_path: str | None = None
last_non_empty_grid_path: str | None = None

# For menu scanning/listing
menu_acknowledge = Event()
menu_change = Event()
menu_scan_done = Event()
next_menu = Queue(1)

# For Context Management
_prev_contexts = ["menu"] * 3
_context = "menu"  # To avoid a NameError the first time set_context() is called.

# Set by `update_menu()`
menu_list: list
at_top_level: bool

# Set from `.tui.init()`
ImageClass: BaseImage
displayer: Generator[None, int, bool]
loop: urwid.MainLoop
update_pipe: int

# # Corresponding to (or derived directly from) command-line args and/or config options
DEBUG: bool
MAX_PIXELS: int
NO_ANIMATION: bool
RECURSIVE: bool
SHOW_HIDDEN: bool
THUMBNAIL: bool
THUMBNAIL_SIZE_PRODUCT: int
