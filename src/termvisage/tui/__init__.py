"""TermVisage's Terminal User Interface"""

from __future__ import annotations

import logging as _logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    import argparse

    from term_image.image import BaseImage


def init(
    args: argparse.Namespace,
    style_args: Dict[str, Any],
    images: list[tuple[str, BaseImage | Ellipsis]],
    contents: dict,
    ImageClass: type,
) -> None:
    """Initializes the TUI"""

    import urwid
    from term_image.image import GraphicsImage
    from term_image.utils import get_cell_size, lock_tty
    from term_image.widget import UrwidImageScreen

    from .. import notify
    from ..__main__ import TEMP_DIR
    from ..config import _context_keys, config_options, reconfigure_tui
    from ..logging import LoggingThread, log
    from . import main  # Loaded before `.tui.keys` to prevent circular import
    from . import keys, render
    from .keys import adjust_footer, update_footer_expand_collapse_icon
    from .main import process_input, scan_dir_grid, scan_dir_menu, sort_key_lexi
    from .widgets import Image, info_bar, main as main_widget

    global active, initialized, quitting

    class Loop(urwid.MainLoop):
        def start(self):
            update_footer_expand_collapse_icon()
            adjust_footer()
            return super().start()

        def process_input(self, keys):
            if "window resize" in keys:
                # "window resize" never reaches `.unhandled_input()`.
                # Adjust the footer and clear grid cache.
                keys.append("resized")
            return super().process_input(keys)

    reconfigure_tui(_context_keys)

    if args.debug:
        main_widget.contents.insert(
            1, (urwid.AttrMap(urwid.Filler(info_bar), "reverse"), ("given", 1))
        )

    main.DEBUG = args.debug
    main.MAX_PIXELS = args.max_pixels
    main.NO_ANIMATION = args.no_anim
    main.RECURSIVE = args.recursive
    main.SHOW_HIDDEN = args.all
    main.THUMBNAIL = args.thumbnail and TEMP_DIR
    main.THUMBNAIL_SIZE_PRODUCT = config_options.thumbnail_size**2
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
    render.THUMBNAIL_CACHE_SIZE = config_options.thumbnail_cache

    images = [
        entry if entry[1] is ... else (entry[0], Image(entry[1])) for entry in images
    ]
    images.sort(
        key=lambda x: sort_key_lexi(
            Path(x[0] if x[1] is ... else x[1]._ti_image.source),
            # For the sake of URL-sourced images
            x[0] if x[1] is ... else x[1]._ti_image._source,
        )
    )
    main.displayer = main.display_images(".", images, contents, top_level=True)

    if "compress" in style_args:
        for name in ("anim", "grid", "image"):
            specs = getattr(render, f"{name}_style_specs")
            specs[ImageClass.style] += f"c{style_args['compress']}"

    if issubclass(ImageClass, GraphicsImage):
        # `get_cell_size()` may sometimes return `None` on terminals that don't
        # implement the `TIOCSWINSZ` ioctl command. Hence, the `or (1, 2)`.
        keys._prev_cell_size = get_cell_size() or (1, 2)

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
    if main.THUMBNAIL:
        Image._ti_update_grid_thumbnailing_threshold(keys._prev_cell_size)

    # daemon, to avoid blocking exit upon interruption of the main process or having
    # to check, in each thread, if the main process has been interrupted.
    menu_scanner = LoggingThread(target=scan_dir_menu, name="MenuScanner", daemon=True)
    grid_scanner = LoggingThread(target=scan_dir_grid, name="GridScanner", daemon=True)
    grid_render_manager = LoggingThread(
        target=render.manage_grid_renders,
        args=(config_options.grid_renderers,),
        name="GridRenderManager",
        daemon=True,
    )
    if main.THUMBNAIL:
        grid_thumbnail_manager = LoggingThread(
            target=render.manage_grid_thumbnails,
            args=(config_options.thumbnail_size,),
            name="GridThumbnailManager",
            daemon=True,
        )
    image_render_manager = LoggingThread(
        target=render.manage_image_renders,
        name="ImageRenderManager",
        daemon=True,
    )
    anim_render_manager = LoggingThread(
        target=render.manage_anim_renders,
        name="AnimRenderManager",
        daemon=True,
    )

    UrwidImageScreen.draw_screen = lock_tty(UrwidImageScreen.draw_screen)
    main.loop.screen.clear()
    main.loop.screen.set_terminal_properties(2**24)

    logger = _logging.getLogger(__name__)
    log("Launching the TUI", logger, direct=False)
    main.set_context("menu")

    # End the CLI phase of loading indication and enter the TUI phase.
    #
    # NOTE: `finish_loading()` in `.__main__.main()` excpects loading indication to be
    # in the TUI phase if the TUI has been initialized.
    #
    # - It does no harm if loading indication is in the TUI phase but the TUI is not
    #   yet initialized.
    # - It will result in a deadlock if the TUI has been initialized but loading
    #   indication hasn't entered the TUI phase.
    notify.end_loading()

    active = initialized = True

    menu_scanner.start()
    grid_scanner.start()
    if main.THUMBNAIL:
        grid_thumbnail_manager.start()
    grid_render_manager.start()
    image_render_manager.start()
    anim_render_manager.start()

    try:
        next(main.displayer)
        main.loop.run()
        if main.THUMBNAIL:
            grid_thumbnail_manager.join()
        grid_render_manager.join()
        render.image_render_queue.put((None,) * 3)
        image_render_manager.join()
        render.anim_render_queue.put((None,) * 3)
        anim_render_manager.join()
        log("Exited TUI normally", logger, direct=False)
    except Exception:
        quitting = True
        render.image_render_queue.put((None,) * 3)
        image_render_manager.join()
        render.anim_render_queue.put((None,) * 3)
        anim_render_manager.join()
        raise
    finally:
        main.displayer.close()
        active = False
        os.close(main.update_pipe)


active = initialized = quitting = False
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
    ("key", "reverse bold"),
    ("action", "default"),
    ("disabled key", "", "", "", "#8f8f8f,italics,standout", ""),
    ("disabled action", "", "", "", "#8f8f8f,italics", ""),
    ("error", "", "", "", "bold", "#ff0000"),
    ("warning", "", "", "", "#ff0000,bold", ""),
    ("notif context", "", "", "", "#0000ff,bold", ""),
    ("high-res", "", "", "", "#a07f00", ""),
]
