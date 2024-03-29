"""Custom widget definitions and UI components assembly"""

from __future__ import annotations

import logging as _logging
from math import ceil
from operator import floordiv, mul, sub
from os.path import basename
from typing import List, Optional, Tuple

import urwid
from term_image.image import BaseImage, Size
from term_image.utils import get_terminal_name_version, get_terminal_size

from .. import logging
from ..config import config_options, expand_key, navi
from ..utils import KITTY_DELETE_CURSOR_IMAGES_b
from . import keys, main as tui_main
from .render import anim_render_queue, grid_render_queue, image_render_queue

# NOTE: Any new "private" attribute set on any subclass or instance of an urwid class
# should be prepended with "_ti" to prevent clashes with names used by urwid itself.


class GridListBox(urwid.ListBox):
    def __init__(self, grid: urwid.GridFlow):
        self._ti_grid = grid
        self._ti_ncell = 1
        self._ti_cell_width = grid.cell_width
        self._ti_grid_path = None
        self._ti_ncontent = 0
        self._ti_page_ncell = 1  # Used by GridScanner
        self._ti_topmost = None
        self._ti_top_trim = 0
        self._ti_next_index = 0

        return super().__init__([urwid.Divider()])

    def rows(self, size: Tuple[int, int], focus: bool = False) -> int:
        return self._ti_grid.rows(size[:1], focus)

    def keypress(self, size: Tuple[int, int], key: str) -> Optional[str]:
        if not size[1]:
            size = (size[0], 1)
        return super().keypress(size, key)

    def render(self, size: Tuple[int, int], focus: bool = False) -> urwid.Canvas:
        # 0, if maxcol < cell_width (maxcol = size[0]).
        # Otherwise, number of cells per row.
        ncell = sum(
            map(
                floordiv,
                # No of whole (cell_width + h_sep), columns left after last h_sep
                divmod(size[0], self._ti_grid.cell_width + self._ti_grid.h_sep),
                # if one cell_width can fit into the remaining space
                (1, self._ti_grid.cell_width),
            )
        )

        # The path takes care of "same directory"
        # The number of cells takes care of deletions in that directory.
        grid_path = tui_main.grid_path
        ncontent = len(self._ti_grid.contents)

        _row_pos = self.focus_position
        transfer_col_pos = False

        visible = self.calculate_visible(size)
        if visible[0]:
            (_, middle, *_), (top_trim, top), _ = visible
            topmost = top[-1][0] if top else middle
        else:
            topmost = top_trim = None

        if self._ti_grid_path == grid_path and not (
            self._ti_topmost is topmost and self._ti_top_trim == top_trim
        ):
            getattr(
                tui_main.ImageClass, "clear", lambda: True
            )() or ImageCanvas.change()

        self._ti_topmost = topmost
        self._ti_top_trim = top_trim

        if (
            self._ti_grid_path != grid_path  # Different grids
            or self._ti_ncontent != ncontent  # Different no of cells
            or not (ncell or self._ti_ncell)  # maxcol is and was < cell_width
            or ncell != self._ti_ncell  # Number of cells per row changed
            or self._ti_cell_width != self._ti_grid.cell_width  # cell_width changed
        ):
            # When maxcol < cell_width, the grid contents are not `Columns` widgets.
            # Instead, they're what would normally be the contents of the `Columns`.
            # If the grid is empty, then the `GridListBox` only contains a `Divider`

            # Old and new grids are both non-empty
            both_non_empty = self._ti_ncontent and ncontent
            # Conditions for transferring GridListBox's focus position
            transfer_row_pos = self._ti_grid_path == grid_path and both_non_empty

            if transfer_row_pos:
                # Conditions for transferring column focus position
                transfer_col_pos = ncell and self._ti_ncell
                # The 0-based index of the focused cell if the grid were laid out flat
                cell_index = (
                    # The GridListBox also contains dividers between columns
                    # i.e Column - Divider - Column - DIvider - Column - ...
                    # Hence the `// 2`
                    (self.focus_position // 2) * (self._ti_ncell or 1)
                    + (self._ti_ncell and self.focus.focus_position)
                )

            self._update_grid_contents(
                size[:1],
                ncell or 1,
                new=(
                    self._ti_grid_path != grid_path  # Different grids
                    or not (ncell or self._ti_ncell)  # maxcol is and was < cell_width
                    or ncell != self._ti_ncell  # Number of cells per row changed
                    # cell_width changed
                    or self._ti_cell_width != self._ti_grid.cell_width
                ),
            )

            if transfer_row_pos:
                # Ensure focus-position is not out-of-bounds
                # For the `* 2`, see the comments on cell_index calculation above
                self.focus_position = min(
                    len(self.body) - 1, cell_index // (ncell or 1) * 2
                )
            else:
                self.focus_position = 0

            if transfer_col_pos:
                # Ensure focus-position is not out-of-bounds
                col_pos = self.focus.focus_position = min(
                    len(self.focus.contents) - 1, cell_index % ncell
                )
            elif ncontent and ncell:
                self.focus.focus_position = 0

            if grid_path != self._ti_grid_path:
                # Maximum number of cells per grid page. Used by GridScanner
                self._ti_page_ncell = ncell * ceil(
                    size[1] / (ceil(self._ti_grid.cell_width / 2) + self._ti_grid.v_sep)
                )

            self._ti_grid_path = grid_path
            self._ti_ncontent = ncontent
            self._ti_ncell = ncell
            self._ti_cell_width = self._ti_grid.cell_width

        canv = super().render(size, focus)

        # For some reason, `GridListBox.render()` resets the focused column's
        # focus_position to 0 whenever its (the GridListBox's) own focus_position is
        # manually changed to a different position
        # So, the focus_position of the newly focused column has be set again after
        # `render()` and another render set in place
        if transfer_col_pos and _row_pos != self.focus_position:
            self.focus.focus_position = col_pos
            tui_main.update_screen()

        return canv

    def _update_grid_contents(
        self, size: Tuple[int, int], ncell: int, new: bool = True
    ) -> None:
        # The display widget is a `Divider` when the grid is empty
        if not self._ti_grid.contents:
            self._ti_next_index = 0
            self.body[:] = [urwid.Divider()]
            return

        if new:
            self._ti_next_index = 0
            self.body.clear()
        else:
            if self._ti_next_index:
                # Remove all cells after the previous *next_index* cos they are
                # officially just being added.
                # For the `* 2`, see the comments on cell_index calculation in
                # `render()` above.
                self.body[(self._ti_next_index // ncell) * 2 - 1 :] = [urwid.Divider()]
            else:
                self.body.clear()  # Remove the empty-grid Divider

        original = self._ti_grid._contents
        next_index = (len(original) // ncell) * ncell

        # Must include incomplete rows becaused the cells might've been counted with
        # *ncontent*.
        # They'll be removed before the next re-population if the grid wasn't complete
        # yet when *ncontent* was computed.
        # This way, the population can never be behind *ncontent*, ensuring the listbox
        # is always complete when the grid is complete.
        dummy = original[self._ti_next_index :]
        if not dummy:
            if not self._ti_next_index:
                # Would've been cleared earlier
                self.body[:] = [urwid.Divider()]
            return

        # Does not affect GridScanner as it uses a direct reference to the grid's
        # original contents list
        self._ti_grid._contents = urwid.MonitoredFocusList(dummy)

        self.body.extend(
            [
                content[0] if isinstance(content[0], urwid.Divider)
                # `.original_widget` gets rid of an unnecessary padding
                else content[0].original_widget
                for content in self._ti_grid.generate_display_widget(size).contents
            ]
        )

        self._ti_grid._contents = original
        self._ti_next_index = next_index


class Image(urwid.Widget):
    _sizing = frozenset(["box"])
    _selectable = True
    no_cache = ["render", "rows"]

    _ti_faulty_image = urwid.SolidFill("?")
    _ti_large_image = urwid.SolidFill("!")
    _ti_placeholder = urwid.SolidFill(".")

    _ti_force_render = False
    _ti_force_render_contexts = {"image", "full-image", "full-grid-image"}
    _ti_forced_anim_size_hash = None

    _ti_frame = None
    _ti_anim_ongoing = _ti_anim_finished = False

    _ti_faulty = False
    _ti_canv = None
    _ti_rendering = False

    _ti_grid_cache = {}

    # Set from `.tui.init()`
    _ti_alpha = ""
    _ti_grid_style_spec = ""

    def __init__(self, image: BaseImage):
        self._ti_image = image

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        return key

    def rows(self, size: Tuple[int, int], focus: bool = False) -> int:
        # Incompetent implementation due to the lack of *maxrows*
        return self._ti_image._valid_size(
            size[0],
            None,
            maxsize=get_terminal_size(),  # Omit 2-line allowance
        )[1]

    def render(self, size: Tuple[int, int], focus: bool = False) -> urwid.Canvas:
        context = tui_main.get_context()
        image = self._ti_image
        image.set_size(Size.AUTO, maxsize=size)

        # Forced render

        if mul(*image.original_size) > tui_main.MAX_PIXELS and not (
            self._ti_canv
            and (
                # will be resized later @ Rendering.
                self._ti_canv._ti_image_size == image.size
                # can either be SolidCanvas (faulty) or ImageCanvas
                if isinstance(self._ti_canv, ImageCanvas)
                # but faulty shouldn't be resized to allow re-rendering after resize
                else self._ti_canv.size == size
            )
            or self._ti_rendering
        ):
            if self._ti_force_render:
                # AnimRendermanager or `.tui.main.animate_image()` deletes
                # `_force_render` when the animation is done to avoid attribute
                # creation and deletion per frame
                if image.is_animated and not tui_main.NO_ANIMATION:
                    if not (self._ti_frame or self._ti_anim_finished):
                        self._ti_forced_anim_size_hash = hash(image.size)
                    elif hash(image.size) != self._ti_forced_anim_size_hash:
                        self._ti_force_render = False
                        if context in self._ti_force_render_contexts:
                            keys.enable_actions(context, "Force Render")
                        return __class__._ti_large_image.render(size, focus)
                else:
                    del self._ti_force_render
            else:
                if context in self._ti_force_render_contexts:
                    keys.enable_actions(context, "Force Render")
                return __class__._ti_large_image.render(size, focus)

        if context in self._ti_force_render_contexts:
            keys.disable_actions(context, "Force Render")

        # Grid cells

        if (
            view.original_widget is image_grid_box
            and context != "full-grid-image"
            # Grid render cell width adjusts when _maxcols_ < _cell_width_
            # `+2` cos `LineSquare` subtracts the columns for surrounding lines
            and size[0] + 2 == image_grid.cell_width
        ):
            canv = __class__._ti_grid_cache.get(basename(image._source))
            if not canv:
                grid_render_queue.put((image._source, size, self._ti_alpha))
                __class__._ti_grid_cache[basename(image._source)] = ...
                canv = __class__._ti_placeholder.render(size, focus)
            elif canv is ...:
                canv = __class__._ti_placeholder.render(size, focus)
            return canv

        # Rendering

        if view.original_widget is image_grid_box and context != "full-grid-image":
            # When the grid render cell width adjusts; when _maxcols_ < _cell_width_
            try:
                canv = ImageCanvas(
                    f"{image:1.1{self._ti_alpha}{self._ti_grid_style_spec}}"
                    .encode().split(b"\n"),  # fmt: skip
                    size,
                    image.rendered_size,
                )
            except Exception:
                canv = __class__._ti_faulty_image.render(size, focus)
        elif self._ti_frame:
            canv, repeat, frame_no = self._ti_frame
            if canv._ti_image_size != image.size:  # The canvas is always an ImageCanvas
                canv = (
                    placeholder
                    if (
                        # Workaround to erase text on wezterm without glitchy animation
                        tui_main.ImageClass.style == "iterm2"
                        and get_terminal_name_version()[0] == "wezterm"
                    )
                    else __class__._ti_placeholder
                ).render(size)
                anim_render_queue.put(((repeat, frame_no), size, self._ti_force_render))
                self._ti_frame = None  # Avoid resending
                getattr(tui_main.ImageClass, "clear", lambda: True)()
            else:
                canv.size = size
        elif self._ti_canv and (
            self._ti_canv._ti_image_size == image.size
            # Can either be SolidCanvas (faulty) or ImageCanvas
            if isinstance(self._ti_canv, ImageCanvas)
            # but faulty shouldn't be resized to allow re-rendering after resize
            else self._ti_canv.size == size
        ):
            self._ti_canv.size = size
            canv = self._ti_canv
        else:
            if (
                image.is_animated
                and not tui_main.NO_ANIMATION
                and not self._ti_anim_finished
            ):
                if not self._ti_anim_ongoing:
                    anim_render_queue.put((self, size, self._ti_force_render))
                    self._ti_anim_ongoing = True
            elif not self._ti_rendering:
                self._ti_rendering = True
                image_render_queue.put((self, size, self._ti_alpha))
            canv = (
                placeholder
                if (
                    # Workaround to erase text on wezterm without glitchy animation
                    image.is_animated
                    and not tui_main.NO_ANIMATION
                    and tui_main.ImageClass.style == "iterm2"
                    and get_terminal_name_version()[0] == "wezterm"
                )
                else __class__._ti_placeholder
            ).render(size)

        return canv


class ImageCanvas(urwid.Canvas):
    cacheable = False
    _ti_change_state = 0

    def __init__(
        self, lines: List[bytes], size: Tuple[int, int], image_size: Tuple[int, int]
    ):
        super().__init__()
        self.size = size
        self.lines = lines
        self._ti_image_size = image_size

    def cols(self) -> int:
        return self.size[0]

    def rows(self) -> int:
        return self.size[1]

    def content(self, trim_left=0, trim_top=0, cols=None, rows=None, attr_map=None):
        # In all our use cases, the canvas is never trimmed horizontally
        cols = self.cols()
        rows = rows or self.rows()  # Visible rows of the widget
        trim_bottom = self.rows() - trim_top - rows

        diff_x, diff_y = map(sub, self.size, self._ti_image_size)
        pad_up = diff_y // 2
        pad_down = diff_y - pad_up
        pad_left = diff_x // 2
        pad_right = diff_x - pad_left

        # If negative, they imply the number of lines to be trimmed off the image on
        # respective sides
        pad_up -= trim_top
        pad_down -= trim_bottom

        fill = (None, "U", b" " * cols)
        fill_left = (None, "U", b" " * pad_left)
        fill_right = (None, "U", b" " * pad_right)

        terminal_name = get_terminal_name_version()[0]
        style = tui_main.ImageClass.style
        disguise = (
            b"\b "
            * self._ti_change_state
            * (style == "kitty" or style == "iterm2" and terminal_name == "konsole")
        )
        disguise = (None, "U", disguise)
        delete = (
            ((None, "U", KITTY_DELETE_CURSOR_IMAGES_b),)
            if style == "kitty" == terminal_name
            else ()
        )

        # Visible padding may be larger than the visible rows
        for _ in range(min(rows, pad_up)):
            yield [fill]

        # See the description of `pad_up` and `pad_down` above
        for line in self.lines[-min(0, pad_up) : min(0, pad_down) or len(self.lines)]:
            yield [
                fill_left,
                *(delete * line.startswith(b"\033_G")),
                (None, "U", line),
                fill_right,
                disguise,
            ]

        # Visible padding may be larger than the visible rows
        for _ in range(min(rows, pad_down)):
            yield [fill]

    @classmethod
    def change(cls):
        """Causes the canvas to embed or not embed some hidden text on every line of
        the image, such that every line of the image is seen as different in each state.

        ``urwid`` will not redraw lines that have not changed since the last redaw.
        So this is to trick ``urwid`` into taking every line containing a part of an
        image as different in each state.

        This is used to force redraws of all images on screen, particularly when their
        positions do not change much e.g when images need to be cleared in kitty.
        """
        cls._ti_change_state = (cls._ti_change_state + 1) % 3


class LineSquare(urwid.LineBox):
    no_cache = ["render", "rows"]

    def __init__(self, widget, title=""):
        super().__init__(widget, title, "left", "default")

        # Prevents `Image.rows()` from being called,
        # in order to get the correct no of rows for a `<LinesSquare <Image>>` widget
        original_middle = self._w.contents[1]
        new_middle = LineSquareMiddleColumns(
            [x[0] for x in original_middle[0].contents],
            box_columns=(0, 2),
            focus_column=original_middle[0].focus_position,
        )
        new_middle.contents[0] = (new_middle.contents[0][0], ("given", 1, True))
        new_middle.contents[2] = (new_middle.contents[2][0], ("given", 1, True))
        self._w.contents[1] = (new_middle, original_middle[1])
        self.title_widget.set_wrap_mode("ellipsis")

    def rows(self, size: Tuple[int, int], focus: bool = False) -> int:
        return ceil(size[0] / 2)

    def render(self, size: Tuple[int, int], focus: bool = False) -> urwid.Canvas:
        return super().render((size[0], ceil(size[0] / 2)), focus)


# To prevent `Image.rows()` from being called,
# in order to get the correct no of rows for a `<LinesSquare <Image>>` widget
class LineSquareMiddleColumns(urwid.Columns):
    no_cache = ["render", "rows"]

    def rows(self, size: Tuple[int, int], focus: bool = False) -> int:
        return ceil(size[0] / 2) - 2


class MenuEntry(urwid.Text):
    _selectable = True

    def __init__(self, name: str) -> None:
        super().__init__(name, "left", "ellipsis")

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        return key


class MenuListBox(urwid.ListBox):
    def keypress(self, size: Tuple[int, int], key: str) -> Optional[str]:
        if not size[1]:
            size = (size[0], 1)
        ret = super().keypress(size, key)
        return key if key in navi else ret

    def render(self, size: Tuple[int, int], focus: bool = False):
        self._ti_height = size[1]  # Used by MenuScanner
        return super().render(size, focus)


class NoSwitchColumns(urwid.Columns):
    _command_map = urwid.command_map.copy()
    _command_map._command.clear()


class PlaceHolder(urwid.SolidFill):
    _selectable = True  # Prevents _image_box_ from being completely un-selectable

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        return key


logger = _logging.getLogger(__name__)

placeholder = PlaceHolder(" ")
menu = MenuListBox(urwid.SimpleFocusListWalker([]))
menu_box = urwid.LineBox(menu, "List", "left")
image_grid = urwid.GridFlow([placeholder], config_options.cell_width, 2, 1, "left")
image_box = urwid.LineBox(placeholder, "Image", "left")
image_grid_box = urwid.LineBox(urwid.Padding(GridListBox(image_grid)), "Image", "left")
view = urwid.AttrMap(image_box, "unfocused box", "focused box")
viewer = NoSwitchColumns(
    [(20, urwid.AttrMap(menu_box, "unfocused box", "focused box")), view]
)
loading = urwid.Text("", "center")
notifications = urwid.Pile([])
notif_bar = urwid.Columns([(3, urwid.Filler(loading)), urwid.Filler(notifications)])
pile = urwid.Pile([viewer])

info_bar = urwid.Text("")

key_bar = urwid.Filler(urwid.Text(""))
expand = urwid.Filler(urwid.Text(f"\u25B2 [{expand_key[1]}]", align="right"), "middle")
bottom_bar = urwid.Columns([key_bar, (len(expand.original_widget.text), expand)], 2)

main = urwid.Pile([pile, (1, bottom_bar)], 0)

confirmation = urwid.Text("", "center")
confirmation_overlay = urwid.Overlay(
    urwid.LineBox(
        urwid.Filler(confirmation),
        "",
        "center",
        None,
        "\u2554",
        "\u2550",
        "\u2551",
        "\u2557",
        "\u255a",
        "\u2551",
        "\u2550",
        "\u255d",
    ),
    placeholder,
    "center",
    ("relative", 25),
    "middle",
    ("relative", 25),
    50,
    3,
)

overlay = urwid.Overlay(
    urwid.LineBox(
        urwid.ListBox([placeholder]),
        "Help",
        "center",
        "default bold",
        "\u2554",
        "\u2550",
        "\u2551",
        "\u2557",
        "\u255a",
        "\u2551",
        "\u2550",
        "\u255d",
    ),
    placeholder,
    "center",
    ("relative", 50),
    "middle",
    ("relative", 75),
    100,
    4,
)
