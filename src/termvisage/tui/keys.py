"""Definitions of key functions"""

from __future__ import annotations

import logging as _logging
import os
from os.path import abspath, basename
from time import sleep
from types import FunctionType
from typing import Any, Tuple

import urwid
from term_image import get_cell_ratio
from term_image.image import GraphicsImage
from term_image.utils import get_cell_size, get_terminal_size

from .. import __version__, logging, tui
from ..config import config_options, context_keys, expand_key
from . import main
from .render import resync_grid_rendering
from .widgets import (
    Image,
    ImageCanvas,
    action_bar,
    confirmation,
    confirmation_overlay,
    expand,
    footer,
    image_box,
    image_grid,
    image_grid_box,
    main as main_widget,
    menu,
    menu_box,
    overlay,
    pile,
    placeholder,
    view,
    viewer,
)

# Action Status Modification


def disable_actions(context: str, *actions: str) -> None:
    keyset = context_keys[context]
    for action in actions:
        keyset[action][4] = False
        keys[context][keyset[action][0]][1] = False
    if context == main.get_context() or context == "global":
        action_bar.update(context)


def enable_actions(context: str, *actions: str) -> None:
    keyset = context_keys[context]
    for action in actions:
        keyset[action][4] = True
        keys[context][keyset[action][0]][1] = True
    if context == main.get_context() or context == "global":
        action_bar.update(context)


def hide_actions(context: str, *actions: str) -> None:
    keyset = context_keys[context]
    for action in actions:
        keyset[action][3] = False
    disable_actions(context, *actions)


def show_actions(context: str, *actions: str) -> None:
    keyset = context_keys[context]
    for action in actions:
        keyset[action][3] = True
    enable_actions(context, *actions)


# Main


def change_key(context: str, old: str, new: str) -> None:
    """Changes the key for a registered action from *old* to *new*.

    Raises:
        KeyError: *old* was not registered.
    """
    keys[context][new] = keys[context].pop(old)


def display_context_help(context: str) -> None:
    """Displays the help menu for a particular context, showing all visible actions
    and their descriptions.
    """
    global _prev_view_widget

    actions = (
        *context_keys[context].items(),
        *(() if context in no_globals else context_keys["global"].items()),
    )

    separator = (1, urwid.Filler(urwid.Text("\u2502" * 3)))
    contents = [
        (
            3,
            urwid.Columns(
                [
                    (
                        "weight",
                        3,
                        urwid.Filler(
                            urwid.Text(("default bold", f"{action}"), "center")
                        ),
                    ),
                    separator,
                    (
                        "weight",
                        2,
                        urwid.Filler(
                            urwid.Text(("default bold", f"{symbol} ({key})"), "center")
                        ),
                    ),
                    separator,
                    (
                        "weight",
                        5,
                        urwid.Filler(
                            urwid.Text(("default bold", f"{description}"), "center")
                        ),
                    ),
                ],
                min_width=5,
            ),
        )
        for action, (key, symbol, description, visible, _) in actions
        if visible
    ]

    line = urwid.SolidFill("\u2500")
    divider = urwid.Columns(
        [
            ("weight", 3, line),
            (1, urwid.Filler(urwid.Text("\u253c"))),
            ("weight", 2, line),
            (1, urwid.Filler(urwid.Text("\u253c"))),
            ("weight", 5, line),
        ],
        min_width=5,
    )
    for index in range(1, (len(contents) - 1) * 2, 2):
        contents.insert(index, (1, divider))

    contents.insert(
        0,
        (
            1,
            urwid.Columns(
                [
                    ("weight", 3, line),
                    (1, urwid.Filler(urwid.Text("\u252c"))),
                    ("weight", 2, line),
                    (1, urwid.Filler(urwid.Text("\u252c"))),
                    ("weight", 5, line),
                ],
                min_width=5,
            ),
        ),
    )

    contents.extend(
        [
            (
                1,
                urwid.Columns(
                    [
                        ("weight", 3, line),
                        (1, urwid.Filler(urwid.Text("\u2534"))),
                        ("weight", 2, line),
                        (1, urwid.Filler(urwid.Text("\u2534"))),
                        ("weight", 5, line),
                    ],
                    min_width=5,
                ),
            ),
            (
                "pack",
                urwid.LineBox(
                    urwid.Text(
                        [
                            ("default bold", f"TermVisage v{__version__}\n"),
                            "\n",
                            ("default bold", "Homepage: "),
                            "https://github.com/AnonymouX47/termvisage\n",
                            ("default bold", "Docs: "),
                            "https://termvisage.readthedocs.io\n",
                            ("default bold", "Issue Tracker: "),
                            "https://github.com/AnonymouX47/termvisage/issues\n",
                            ("default bold", "Changelog: "),
                            "https://github.com/AnonymouX47/termvisage/blob/main/"
                            "CHANGELOG.md\n",
                            ("default bold", "License: "),
                            "https://github.com/AnonymouX47/termvisage/blob/main/"
                            "LICENSE\n",
                            "\n",
                            ("default bold", "Copyright (c) 2023 Toluwaleke Ogundipe"),
                        ],
                        "center",
                    ),
                    "About",
                    "center",
                    "default bold",
                ),
            ),
        ]
    )

    overlay.top_w.original_widget.body[0] = urwid.Pile(contents)
    overlay.bottom_w = view if main.get_context() == "full-image" else pile
    main_widget.contents[0] = (overlay, ("weight", 1))
    main.set_context("overlay")

    # `Image` widgets don't support overlay.
    # Always reset by "overlay::Close"
    _prev_view_widget = view.original_widget
    view.original_widget = urwid.LineBox(
        placeholder, _prev_view_widget.title_widget.text.strip(" "), "left"
    )


def register_key(*args: Tuple[str, str]) -> FunctionType:
    """Returns a decorator to register a function to some context action(s).

    Args: `(context, action)` tuple(s), each specifying an *action* and it's *context*.

    Each *context* and *action* must be valid.
    If no argument is given, the wrapper simply does nothing.
    """

    def register(func: FunctionType) -> None:
        """Registers *func* to the key corresponding to each ``(context, action)`` pair
        received by the call to ``register_key()`` that defines it.
        """
        for context, action in args:
            # All actions are enabled by default
            keys[context][context_keys[context][action][0]] = [func, True]

        return func

    return register


def set_confirmation(
    msg: str,
    bottom_widget: urwid.widget,
    confirm: FunctionType,
    cancel: FunctionType,
    confirm_args: tuple = (),
    cancel_args: tuple = (),
) -> None:
    """Setup a confirmation dialog

    Args:
      - msg: The message to be displayed in the dialog.
      - bottom_widget: The widget on which the confirmation dialog will be overlaid.
      - confirm: A function to be called for the "Confirm" action of the
        confirmation context.
      - cancel: A function to be called for the "Cancel" action of the
        confirmation context.
      - confirm_args: Optional positional arguments to be passed to _confirm_.
      - cancel_args: Optional positional arguments to be passed to _cancel_.

    This function must be called by any context action using the confirmation dialog.
    """
    global _confirm, _cancel, _prev_view_widget

    _confirm = (confirm, confirm_args)
    _cancel = (cancel, cancel_args)
    confirmation.set_text(msg)
    main.set_context("confirmation")

    # `Image` widgets don't support overlay.
    # Always reset by "confirmation::Confirm" or "confirmation::Cancel"
    # but *confirm* must reset `view.original_widget` on it's own.
    _prev_view_widget = view.original_widget
    view.original_widget = urwid.LineBox(
        placeholder, _prev_view_widget.title_widget.text.strip(" "), "left"
    )

    confirmation_overlay.bottom_w = bottom_widget
    main_widget.contents[0] = (confirmation_overlay, ("weight", 1))

    getattr(main.ImageClass, "clear", lambda: True)()


def update_footer_expand_collapse_icon():
    if not config_options.show_footer:
        return

    expand.set_text(
        [
            "\u25B2" if action_bar._ti_collapsed else "\u25BC",
            " ",
            ("key", f" {expand_key[1]} "),
        ]
    )


# Context Actions

# {<context>: {<key>: [<func>, <state>], ...}, ...}
keys = {context: {} for context in context_keys}


# global
@register_key(("global", "Quit"))
def quit():
    tui.quitting = True
    raise urwid.ExitMainLoop()


@register_key(("global", "Expand/Collapse Footer"))
def expand_collapse_keys():
    if expand._ti_shown:
        if action_bar._ti_collapsed and action_bar_rows() > 1:
            update_footer_expand_collapse_icon()
            main_widget.contents[-1] = (footer, ("given", action_bar_rows()))
            action_bar._ti_collapsed = False
            getattr(main.ImageClass, "clear", lambda: True)() or ImageCanvas.change()
        elif not action_bar._ti_collapsed:
            update_footer_expand_collapse_icon()
            main_widget.contents[-1] = (footer, ("given", 1))
            action_bar._ti_collapsed = True
            getattr(main.ImageClass, "clear", lambda: True)() or ImageCanvas.change()


@register_key(("global", "Help"))
def help():
    display_context_help(main.get_context())
    getattr(main.ImageClass, "clear", lambda: True)()


def adjust_footer():
    if not config_options.show_footer:
        return

    needed_rows = action_bar.rows((get_terminal_size()[0],))
    if expand._ti_shown:
        if needed_rows == 1:
            footer.contents.pop()
            expand._ti_shown = False
    elif needed_rows > 1:
        footer.contents.append((expand, ("pack", None, False)))
        expand._ti_shown = True

    if not action_bar._ti_collapsed:
        if main_widget.contents[-1][1][1] != (rows := action_bar_rows()):
            main_widget.contents[-1] = (footer, ("given", rows))
            getattr(main.ImageClass, "clear", lambda: True)()


def action_bar_cols():
    # Consider columns occupied by the expand key and the divider
    return get_terminal_size()[0] - (expand.pack()[0] + 2) * expand._ti_shown


def action_bar_rows():
    return action_bar.rows((action_bar_cols(),))


def resize():
    global _prev_cell_ratio, _prev_cell_size

    if issubclass(main.ImageClass, GraphicsImage):
        cell_size = get_cell_size()
        # `get_cell_size()` may sometimes return `None` on terminals that don't
        # implement the `TIOCSWINSZ` ioctl command. Hence, the `cell_size and`.
        if cell_size and cell_size != _prev_cell_size:
            _prev_cell_size = cell_size
            if main.THUMBNAIL:
                Image._ti_update_grid_thumbnailing_threshold(cell_size)
            if main.grid_active.is_set():
                resync_grid_rendering()
    else:
        cell_ratio = get_cell_ratio()
        if cell_ratio != _prev_cell_ratio:
            _prev_cell_ratio = cell_ratio
            if main.grid_active.is_set():
                resync_grid_rendering()

    adjust_footer()
    getattr(main.ImageClass, "clear", lambda: True)() or ImageCanvas.change()


keys["global"].update({"resized": [resize, True]})


# menu
@register_key(
    ("menu", "Prev"),
    ("menu", "Next"),
    ("menu", "Page Up"),
    ("menu", "Page Down"),
    ("menu", "Top"),
    ("menu", "Bottom"),
)
def menu_nav():
    main.displayer.send(menu.focus_position - 1)
    if not main.at_top_level or main.menu_list:
        set_menu_actions()
        set_menu_count()


def set_menu_actions():
    pos = menu.focus_position - 1
    if pos == -1:
        disable_actions("menu", "Switch Pane", "Delete", "Prev", "Page Up", "Top")
    elif main.menu_list[pos][1] is ...:
        disable_actions("menu", "Delete")
        enable_actions("menu", "Prev", "Page Up", "Top")
    else:
        enable_actions("menu", "Switch Pane", "Delete", "Prev", "Page Up", "Top")

    if main.at_top_level:
        if pos == 0:
            # "Top" is not disabled to ensure ".." is never selected
            # See `pos == -1` in `.main.display_images()`
            disable_actions("menu", "Prev", "Page Up")
        disable_actions("menu", "Back")
    else:
        enable_actions("menu", "Back")

    if main.menu_scan_done.is_set() and pos == len(main.menu_list) - 1:
        disable_actions("menu", "Next", "Page Down", "Bottom")
    else:
        enable_actions("menu", "Next", "Page Down", "Bottom")


def set_menu_count():
    length = len(main.menu_list) if main.menu_scan_done.is_set() else "..."
    menu_box.set_title(f"{menu.focus_position} of {length}")


@register_key(("menu", "Open"))
def open():
    if menu.focus_position == 0 or main.menu_list[menu.focus_position - 1][1] is ...:
        main.displayer.send(main.MenuAction.OPEN)
    else:
        main.set_context("full-image")
        main_widget.contents[0] = (view, ("weight", 1))
        set_image_view_actions()

    getattr(main.ImageClass, "clear", lambda: True)()


@register_key(("menu", "Back"))
def back():
    main.displayer.send(main.MenuAction.BACK)
    getattr(main.ImageClass, "clear", lambda: True)()


# image
@register_key(("image", "Maximize"))
def maximize():
    main.set_context("full-image")
    main_widget.contents[0] = (view, ("weight", 1))
    set_image_view_actions()

    getattr(main.ImageClass, "clear", lambda: True)()


# image-grid
@register_key(("image-grid", "Size-"))
def cell_width_dec():
    if image_grid.cell_width == 50:
        main.enable_actions("image-grid", "Size+")

    if image_grid.cell_width > 10:
        image_grid.cell_width -= 2
        resync_grid_rendering()
        getattr(main.ImageClass, "clear", lambda: True)()

        if image_grid.cell_width == 10:
            main.disable_actions("image-grid", "Size-")

    if main.THUMBNAIL:
        Image._ti_update_grid_thumbnailing_threshold(_prev_cell_size)


@register_key(("image-grid", "Size+"))
def cell_width_inc():
    if image_grid.cell_width == 10:
        main.enable_actions("image-grid", "Size-")

    if image_grid.cell_width < 50:
        image_grid.cell_width += 2
        resync_grid_rendering()
        getattr(main.ImageClass, "clear", lambda: True)()

        if image_grid.cell_width == 50:
            main.disable_actions("image-grid", "Size+")

    if main.THUMBNAIL:
        Image._ti_update_grid_thumbnailing_threshold(_prev_cell_size)


@register_key(("image-grid", "Open"))
def maximize_cell():
    main.set_context("full-grid-image")
    row = image_grid_box.base_widget.focus
    image_w = (
        row.focus
        if isinstance(row, urwid.Columns)  # when maxcol >= cell_width
        else row
    ).original_widget.original_widget  # The Image is in a LineSquare in an AttrMap

    image_box._w.contents[1][0].contents[1] = (image_w, ("weight", 1, True))
    image_box.set_title(basename(image_w._ti_image._source))
    main_widget.contents[0] = (image_box, ("weight", 1))

    image_box.original_widget = image_w
    if image_w._ti_image.is_animated:
        main.animate_image(image_w)

    getattr(main.ImageClass, "clear", lambda: True)()


def set_image_grid_actions():
    # The grid for a non-empty directory might be empty at the start of scanning
    if image_grid.contents:
        enable_actions("image-grid", "Open", "Size-", "Size+")
    else:
        disable_actions("image-grid", "Open", "Size-", "Size+")


# full-image, full-grid-image
@register_key(("full-image", "Restore"), ("full-grid-image", "Back"))
def restore():
    if main.get_context() == "full-grid-image":
        image_box.original_widget = placeholder  # halt image and anim rendering

    main.set_prev_context()
    main_widget.contents[0] = (pile, ("weight", 1))
    if main.get_context() == "menu":
        set_menu_actions()
    elif main.get_context() == "image":
        set_image_view_actions()

    getattr(main.ImageClass, "clear", lambda: True)()


# image, full-image
@register_key(("image", "Prev"), ("full-image", "Prev"))
def prev_image():
    if (
        menu.focus_position > 1
        # Don't scroll through directory items in image views
        and main.menu_list[menu.focus_position - 2][1] is not ...  # Previous item
    ):
        menu.focus_position -= 1
        main.displayer.send(menu.focus_position - 1)

    set_image_view_actions()
    set_menu_count()


@register_key(("image", "Next"), ("full-image", "Next"))
def next_image():
    # `menu_list` is one item less than `menu` (at it's beginning), hence no `len - 1`
    if menu.focus_position < len(main.menu_list):
        menu.focus_position += 1
        main.displayer.send(menu.focus_position - 1)

    set_image_view_actions()
    set_menu_count()


@register_key(
    ("menu", "Force Render"), ("image", "Force Render"), ("full-image", "Force Render")
)
def force_render():
    # Will re-render immediately after processing input, since caching has been disabled
    # for `Image` widgets.
    image_w = main.menu_list[menu.focus_position - 1][1]
    if image_w._ti_image.is_animated:
        main.animate_image(image_w, True)
    else:
        image_w._ti_force_render = True


def set_image_view_actions(context: str = None):
    context = context or main.get_context()
    if (
        menu.focus_position < 2
        # Previous item is a directory
        or main.menu_list[menu.focus_position - 2][1] is ...
    ):
        disable_actions(context, "Prev")
    else:
        enable_actions(context, "Prev")

    if (
        # Last item
        main.menu_scan_done.is_set()
        and menu.focus_position == len(main.menu_list)
    ):
        disable_actions(context, "Next")
    else:
        enable_actions(context, "Next")


# menu, image, full-image
@register_key(
    ("menu", "Delete"),
    ("image", "Delete"),
    ("full-image", "Delete"),
)
def delete():
    entry = main.menu_list[menu.focus_position - 1][0]
    set_confirmation(
        ("warning", "Permanently delete this image?"),
        view if main.get_context() == "full-image" else pile,
        _confirm_delete,
        _cancel_delete,
        (entry,),
    )


def _confirm_delete(entry):
    try:
        os.remove(entry)
    except OSError:
        successful = False
        logging.log_exception(f"Unable to delete {abspath(entry)!r}", logger)
        confirmation.set_text(("warning", "Unable to delete! Check the logs for info."))
    else:
        successful = True
        main.displayer.send(main.MenuAction.DELETE)
        confirmation.set_text(f"Successfully deleted {abspath(entry)}")
        confirmation.set_text(("green fg", "Successfully deleted!"))
    main.loop.draw_screen()
    sleep(1)

    if successful:
        next(main.displayer)  # Render next image view
        if not main.menu_list or main.menu_list[menu.focus_position - 1][1] is ...:
            # All menu entries have been deleted OR selected menu item is a directory
            main_widget.contents[0] = (pile, ("weight", 1))
            viewer.focus_position = 0
            # "confirmation:Confirm" calls `set_prev_context()`
            main._prev_contexts[0] = (
                "global" if main.at_top_level and not main.menu_list else "menu"
            )
        else:
            _cancel_delete()
    else:
        view.original_widget = _prev_view_widget
        _cancel_delete()


def _cancel_delete():
    main_widget.contents[0] = (
        view if main.get_prev_context() == "full-image" else pile,
        ("weight", 1),
    )
    if main.get_prev_context() in {"image", "full-image"}:
        set_image_view_actions(main.get_prev_context())


# menu, image, image-grid
@register_key(
    ("menu", "Switch Pane"),
    ("image", "Switch Pane"),
    ("image-grid", "Switch Pane"),
)
def switch_pane():
    if main.get_context() != "menu":
        main.set_context("menu")
        viewer.focus_position = 0
        set_menu_actions()
    else:
        viewer.focus_position = 1
        if view.original_widget is image_box:
            main.set_context("image")
            set_image_view_actions()
        else:
            main.set_context("image-grid")
            set_image_grid_actions()


# confirmation
@register_key(("confirmation", "Confirm"))
def confirm():
    # `_confirm()` must [re]set `view.original_widget`
    _confirm[0](*_confirm[1])
    main.set_prev_context()


@register_key(("confirmation", "Cancel"))
def cancel():
    _cancel[0](*_cancel[1])
    view.original_widget = _prev_view_widget
    main.set_prev_context()


# overlay
@register_key(("overlay", "Close"))
def close():
    main_widget.contents[0] = (
        view if main.get_prev_context() == "full-image" else pile,
        ("weight", 1),
    )
    view.original_widget = _prev_view_widget
    main.set_prev_context()


logger = _logging.getLogger(__name__)
no_globals = {"global", "confirmation", "full-grid-image", "overlay"}
action_bar._ti_collapsed = True
expand._ti_shown = True

# Used in the "confirmation" context.
#
# Updated by `set_confirmation()`.
_confirm: tuple[FunctionType, tuple[Any, ...]] | None = None
_cancel: tuple[FunctionType, tuple[Any, ...]] | None = None

# Used for overlays
_prev_view_widget: urwid.Widget | None = None

# Used to guard grid render refresh upon terminal resize, for text-based styles.
#
# Updated from `resize()`.
_prev_cell_ratio: float = 0.0

# Used to [re]compute the grid thumbnailing threshold.
# Also used to guard grid render refresh on terminal resize, for graphics-based styles.
#
# The default value is for text-based styles, for which this variable is never updated.
# Updated from `.tui.init()` and `resize()`, for graphics-based styles.
_prev_cell_size: tuple[int, int] = (1, 2)
