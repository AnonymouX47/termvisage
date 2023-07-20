"""TermVisage's Terminal User Interface"""

from __future__ import annotations

import argparse
import logging as _logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Tuple, Union

import urwid
from term_image.utils import lock_tty, write_tty
from term_image.widget import UrwidImageScreen

from .. import logging
from ..config import config_options
from ..utils import CSI
from . import main, render
from .keys import adjust_bottom_bar
from .main import process_input, scan_dir_grid, scan_dir_menu, sort_key_lexi
from .widgets import Image, info_bar, main as main_widget


def init(
    args: argparse.Namespace,
    style_args: Dict[str, Any],
    images: Iterable[Tuple[str, Union[Image, Iterator]]],
    contents: dict,
    ImageClass: type,
) -> None:
    """Initializes the TUI"""
    global is_launched

    if args.debug:
        main_widget.contents.insert(
            -1, (urwid.AttrMap(urwid.Filler(info_bar), "reverse"), ("given", 1))
        )

    main.DEBUG = args.debug
    main.MAX_PIXELS = args.max_pixels
    main.NO_ANIMATION = args.no_anim
    main.RECURSIVE = args.recursive
    main.SHOW_HIDDEN = args.all
    main.ImageClass = ImageClass
    main.loop = Loop(
        main_widget, palette, UrwidImageScreen(), unhandled_input=process_input
    )
    main.update_pipe = main.loop.watch_pipe(lambda _: None)

    render.ANIM_CACHED = not args.cache_no_anim and (
        args.cache_all_anim or args.anim_cache
    )
    render.FRAME_DURATION = args.frame_duration
    render.REPEAT = args.repeat

    images.sort(
        key=lambda x: sort_key_lexi(
            Path(x[0] if x[1] is ... else x[1]._ti_image._source)
        )
    )
    main.displayer = main.display_images(".", images, contents, top_level=True)

    if "compress" in style_args:
        for name in ("anim", "grid", "image"):
            specs = getattr(render, f"{name}_style_specs")
            specs[ImageClass.style] += f"c{style_args['compress']}"

    Image._ti_alpha = (
        "#"
        if args.no_alpha
        else (
            "#" + f"{args.alpha:f}"[1:]
            if args.alpha_bg is None
            else "#" + (args.alpha_bg or "#")
        )
    )
    Image._ti_grid_style_spec = render.grid_style_specs.get(ImageClass.style, "")

    # daemon, to avoid having to check if the main process has been interrupted
    menu_scanner = logging.Thread(target=scan_dir_menu, name="MenuScanner", daemon=True)
    grid_scanner = logging.Thread(target=scan_dir_grid, name="GridScanner", daemon=True)
    grid_render_manager = logging.Thread(
        target=render.manage_grid_renders,
        args=(config_options.grid_renderers,),
        name="GridRenderManager",
        daemon=True,
    )
    image_render_manager = logging.Thread(
        target=render.manage_image_renders,
        name="ImageRenderManager",
        daemon=True,
    )
    anim_render_manager = logging.Thread(
        target=render.manage_anim_renders,
        name="AnimRenderManager",
        daemon=True,
    )

    UrwidImageScreen.draw_screen = lock_tty(UrwidImageScreen.draw_screen)
    main.loop.screen.clear()
    main.loop.screen.set_terminal_properties(2**24)

    logger = _logging.getLogger(__name__)
    logging.log("Launching TUI", logger, direct=False)
    main.set_context("menu")
    is_launched = True
    menu_scanner.start()
    grid_scanner.start()
    grid_render_manager.start()
    image_render_manager.start()
    anim_render_manager.start()

    try:
        write_tty(f"{CSI}?1049h".encode())  # Switch to the alternate buffer
        next(main.displayer)
        main.loop.run()
        grid_render_manager.join()
        render.image_render_queue.put((None,) * 3)
        image_render_manager.join()
        render.anim_render_queue.put((None,) * 3)
        anim_render_manager.join()
        logging.log("Exited TUI normally", logger, direct=False)
    except Exception:
        main.quitting.set()
        render.image_render_queue.put((None,) * 3)
        image_render_manager.join()
        render.anim_render_queue.put((None,) * 3)
        anim_render_manager.join()
        raise
    finally:
        # urwid fails to restore the normal buffer on some terminals
        write_tty(f"{CSI}?1049l".encode())  # Switch back to the normal buffer
        main.displayer.close()
        is_launched = False
        os.close(main.update_pipe)


class Loop(urwid.MainLoop):
    def start(self):
        adjust_bottom_bar()  # Properly set expand key visibility at initialization
        return super().start()

    def process_input(self, keys):
        if "window resize" in keys:
            # "window resize" never reaches `.unhandled_input()`.
            # Adjust the bottom bar and clear grid cache.
            keys.append("resized")
        return super().process_input(keys)


is_launched = False

palette = [
    ("default", "", "", "", "", ""),
    ("default bold", "", "", "", "bold", ""),
    ("reverse", "", "", "", "standout", ""),
    ("reverse bold", "", "", "", "standout,bold", ""),
    ("inactive", "", "", "", "#7f7f7f", ""),
    ("white on black", "", "", "", "#ffffff", "#000000"),
    ("black on white", "", "", "", "#000000", "#ffffff"),
    ("focused entry", "", "", "", "standout", ""),
    ("unfocused box", "", "", "", "#7f7f7f", ""),
    ("focused box", "default"),
    ("green fg", "", "", "", "#00ff00", ""),
    ("key", "", "", "", "", "#5588ff"),
    ("disabled key", "", "", "", "#7f7f7f", "#5588ff"),
    ("error", "", "", "", "bold", "#ff0000"),
    ("warning", "", "", "", "#ff0000,bold", ""),
    ("notif context", "", "", "", "#0000ff,bold", ""),
]
