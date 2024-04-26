"""Definitions for deferred image rendering"""

from __future__ import annotations

import logging as _logging
from multiprocessing import Event as mp_Event, Queue as mp_Queue
from os import remove
from os.path import basename, split
from queue import Empty, Queue
from tempfile import mkdtemp, mkstemp
from threading import Event, Lock
from typing import Union

from term_image.image import Size

from .. import logging, notify
from ..logging_multi import Process
from ..utils import clear_queue


def delete_thumbnail(thumbnail: str) -> bool:
    try:
        remove(thumbnail)
    except OSError:  # On Windows, a file in use cannot be deleted
        logging.log_exception(f"Failed to delete thumbnail file {thumbnail!r}", logger)
        return False

    return True


def generate_grid_thumbnails(
    input: Queue | mp_Queue,
    output: Queue | mp_Queue,
    thumbnail_size: int,
    not_generating: Event | mp_Event,
) -> None:
    from os import fdopen, mkdir
    from shutil import rmtree

    from PIL.Image import Resampling, open as Image_open

    THUMBNAIL_FRAME_SIZE = (thumbnail_size,) * 2
    BOX = Resampling.BOX
    THUMBNAIL_MODES = {"RGB", "RGBA"}

    try:
        THUMBNAIL_DIR = (TEMP_DIR := mkdtemp(prefix="termvisage-")) + "/thumbnails"
        mkdir(THUMBNAIL_DIR)
    except OSError:
        logging.log_exception(
            "Failed to create thumbnail directory", logger, fatal=True
        )
        raise

    logging.log(
        f"Created thumbnail directory {THUMBNAIL_DIR!r}",
        logger,
        _logging.DEBUG,
        direct=False,
    )

    try:
        while True:
            not_generating.set()
            try:
                if not (source := input.get()):
                    break  # Quitting
            finally:
                not_generating.clear()

            # Make source image into a thumbnail
            try:
                img = Image_open(source)
                has_transparency = img.has_transparency_data
                img.thumbnail(THUMBNAIL_FRAME_SIZE, BOX)
                if img.mode not in THUMBNAIL_MODES:
                    with img:
                        img = img.convert("RGBA" if has_transparency else "RGB")
            except Exception:
                output.put((source, None))
                logging.log_exception(
                    f"Failed to generate thumbnail for {source!r}", logger
                )
                continue

            # Create thumbnail file
            try:
                thumbnail_fd, thumbnail = mkstemp(
                    "", f"{basename(source)}-", THUMBNAIL_DIR
                )
            except Exception:
                output.put((source, None))
                logging.log_exception(
                    f"Failed to create thumbnail file for {source!r}", logger
                )
                continue

            # Save thumbnail
            with img, fdopen(thumbnail_fd, "wb") as thumbnail_file:
                try:
                    img.save(thumbnail_file, "PNG")
                except Exception:
                    output.put((source, None))
                    thumbnail_file.close()  # Close before deleting the file
                    delete_thumbnail(thumbnail)
                    logging.log_exception(
                        f"Failed to save thumbnail for {source!r}", logger
                    )
                    continue

            output.put((source, thumbnail))
    finally:
        try:
            rmtree(TEMP_DIR, ignore_errors=True)
        except OSError:
            logging.log_exception(
                f"Failed to delete thumbnail directory {THUMBNAIL_DIR!r}", logger
            )

    clear_queue(output)


def manage_anim_renders() -> None:
    from .main import ImageClass, update_screen
    from .widgets import ImageCanvas, image_box

    def next_frame() -> bool:
        frame, repeat, frame_no, size, rendered_size = frame_render_out.get()
        if not_skip() and (not forced or image_w._ti_force_render):
            if frame:
                canv = ImageCanvas(frame.encode().split(b"\n"), size, rendered_size)
                image_w._ti_image.seek(frame_no)
                image_w._ti_frame = (canv, repeat, frame_no)
            else:
                image_w._ti_anim_finished = True
                image_w._ti_image.seek(0)
        # If this image is the one currently displayed, it's either:
        # - forced but size changed -> End animation; Remove attributes
        # - a size change -> Continue animation; Do not remove attributes
        # - a restart (moved to another entry and back) -> Animation will be ended at
        #   restart; attributes already removed in `.main.animate_image()`
        elif image_w is not image_box.original_widget or forced:
            frame_render_in.put((..., None, None))
            clear_queue(frame_render_out)  # In case output is full
            frame = None

        if not frame:
            try:
                # If one fails, the rest shouldn't exist (removed in `animate_image()`)
                del image_w._ti_anim_ongoing
                del image_w._ti_frame
                if forced:
                    # See "Forced render" section of `.widgets.Image.render()`
                    del image_w._ti_force_render
                    del image_w._ti_forced_anim_size_hash
            except AttributeError:
                pass

        update_screen()
        return bool(frame)

    def not_skip():
        return image_w is image_box.original_widget and anim_render_queue.empty()

    frame_render_in = (mp_Queue if logging.MULTI else Queue)()
    frame_render_out = (mp_Queue if logging.MULTI else Queue)(20)
    ready = (mp_Event if logging.MULTI else Event)()
    renderer = (Process if logging.MULTI else logging.Thread)(
        target=render_frames,
        args=(
            frame_render_in,
            frame_render_out,
            ready,
            ImageClass,
            anim_style_specs.get(ImageClass.style, ""),
            REPEAT,
            ANIM_CACHED,
        ),
        name="FrameRenderer",
        redirect_notifs=True,
    )
    renderer.start()

    frame_duration = None
    image_w = None  # Silence flake8's F821

    try:
        while True:
            try:
                data, size, forced = anim_render_queue.get(timeout=frame_duration)
            except Empty:
                if not next_frame():
                    frame_duration = None
            else:
                if not data:
                    break

                notify.start_loading()

                if anim_render_queue.empty():
                    ready.clear()
                    frame_render_in.put((..., None, None))
                    clear_queue(frame_render_out)  # In case output is full
                    ready.wait()
                    # multiprocessing queues are not so reliable
                    clear_queue(frame_render_out)

                if isinstance(data, tuple):
                    if not_skip():
                        frame_render_in.put((data, size, image_w._ti_alpha))
                        if not next_frame():
                            frame_duration = None
                    elif image_w is not image_box.original_widget:
                        # The next item in the queue is NOT a size change
                        frame_duration = None
                else:
                    # Safe, since the next item in the queue cannot be a size change
                    # cos no animation is ongoing
                    frame_duration = None

                    image_w = data
                    if not_skip():
                        frame_render_in.put(
                            (image_w._ti_image._source, size, image_w._ti_alpha)
                        )
                        # Ensures successful deletion if the displayed image has
                        # changed before the first frame is ready
                        image_w._ti_frame = None

                        if next_frame():
                            frame_duration = (
                                FRAME_DURATION or image_w._ti_image.frame_duration
                            )

                notify.stop_loading()
    finally:
        clear_queue(frame_render_in)
        frame_render_in.put((None,) * 3)
        clear_queue(frame_render_out)  # In case the renderer is blocking on `put()`
        renderer.join()
        clear_queue(anim_render_queue)


def manage_image_renders():
    from .main import ImageClass, update_screen
    from .widgets import Image, ImageCanvas, image_box

    def not_skip():
        # If this image is the one currently displayed but the queue is non empty,
        # it means some "forth and back" has occurred.
        # Skipping this render avoids the possibility of wasting time with this render
        # in the case where the image size has changed.
        return image_w is image_box.original_widget and image_render_queue.empty()

    multi = logging.MULTI
    image_render_in = (mp_Queue if multi else Queue)()
    image_render_out = (mp_Queue if multi else Queue)()
    renderer = (Process if multi else logging.Thread)(
        target=render_images,
        args=(
            image_render_in,
            image_render_out,
            ImageClass,
            image_style_specs.get(ImageClass.style, ""),
        ),
        name="ImageRenderer",
        redirect_notifs=True,
    )
    renderer.start()

    faulty_image = Image._ti_faulty_image
    last_image_w = image_box.original_widget
    # To prevent an `AttributeError` with the first deletion, while avoiding `hasattr()`
    last_image_w._ti_canv = None

    try:
        while True:
            # A redraw is necessary even when the render is skipped, in case the skipped
            # render is of the currently displayed image.
            # So that a new render can be sent in (after `._ti_rendering` is unset).
            # Otherwise, the image will remain unrendered until a redraw.
            update_screen()

            image_w, size, alpha = image_render_queue.get()
            if not image_w:
                break

            if not not_skip():
                del image_w._ti_rendering
                continue

            image_render_in.put(
                (
                    image_w._ti_image._source,
                    size,
                    alpha,
                    image_w._ti_faulty,
                )
            )
            notify.start_loading()
            render, rendered_size = image_render_out.get()

            if not_skip():
                del last_image_w._ti_canv
                if render:
                    image_w._ti_canv = ImageCanvas(
                        render.encode().split(b"\n"), size, rendered_size
                    )
                else:
                    image_w._ti_canv = faulty_image.render(size)
                    # Ensures a fault is logged only once per `Image` instance
                    if not image_w._ti_faulty:
                        image_w._ti_faulty = True
                last_image_w = image_w

            del image_w._ti_rendering
            notify.stop_loading()
    finally:
        clear_queue(image_render_in)
        image_render_in.put((None,) * 4)
        renderer.join()
        clear_queue(image_render_queue)


def manage_grid_renders(n_renderers: int):
    """Manages grid cell rendering.

    Intended to be executed in a separate thread of the main process.

    If multiprocessing is enabled and *n_renderers* > 0, it spawns *n_renderers*
    subprocesses to render the cells and handles their proper termination.
    Otherwise, it starts a single new thread to render the cells.
    """
    from . import main
    from .main import ImageClass, grid_active, quitting, update_screen
    from .widgets import Image, ImageCanvas, image_grid

    # NOTE:
    # Always keep in mind that every directory entry is rendered only once per grid
    # since results are cached, at least for now.

    def mark_thumbnail_rendered(source: str, thumbnail: str) -> None:
        with thumbnail_render_lock:
            """
            # Better than `e[k] or d.pop(k, None)`.
            thumbnail = (
                thumbnail_cache[source]
                if source in thumbnail_cache
                # Safe to pop since every source is rendered only once per grid.
                # Need to pop because after this point, there's no efficient way
                # to tie `thumbnail` to `source`.
                else extra_thumbnail_cache.pop(source)
            )
            """
            if source in extra_thumbnail_cache:
                del extra_thumbnail_cache[source]
            thumbnails_being_rendered.remove(thumbnail)

    multi = logging.MULTI and n_renderers > 0
    grid_render_in = (mp_Queue if multi else Queue)()
    grid_render_out = (mp_Queue if multi else Queue)()
    renderers = [
        (Process if multi else logging.Thread)(
            target=render_grid_images,
            args=(
                grid_render_in,
                grid_render_out,
                ImageClass,
                grid_style_specs.get(ImageClass.style, ""),
            ),
            name="GridRenderer" + f"-{n}" * multi,
            redirect_notifs=True,
        )
        for n in range(n_renderers if multi else 1)
    ]
    for renderer in renderers:
        renderer.start()

    cell_width = grid_path = None  # Silence flake8's F821
    faulty_image = Image._ti_faulty_image
    delimited = False
    grid_cache = Image._ti_grid_cache
    in_sync = grid_renderer_in_sync

    try:
        while True:
            while not (
                grid_active.wait(0.1)
                or quitting.is_set()
                or not grid_render_out.empty()
            ):
                pass
            if quitting.is_set():
                break

            if delimited or not in_sync.is_set():
                grid_cache.clear()
                in_sync.set()

                # Purge the in and out queues and update the loading indicator counter
                for q in (grid_render_in, grid_render_out):
                    while True:
                        try:
                            q.get(timeout=0.005)
                        except Empty:
                            break
                        else:
                            notify.stop_loading()

                if not delimited:
                    # Purge all items until the grid delimeter
                    while grid_render_queue.get():
                        pass
                else:
                    delimited = False

                cell_width = image_grid.cell_width
                grid_path = main.grid_path

            if not in_sync.is_set():
                continue

            if grid_active.is_set():
                try:
                    image_info = grid_render_queue.get(timeout=0.02)
                except Empty:
                    pass
                else:
                    if not image_info:
                        delimited = True
                        continue
                    grid_render_in.put(image_info)
                    notify.start_loading()

            if not in_sync.is_set():
                continue

            try:
                source, thumbnail, render, size, rendered_size = grid_render_out.get(
                    timeout=0.02
                )
            except Empty:
                pass
            else:
                source_dirname, source_basename = split(source)
                # The directory and cell-width checks are to filter out any remnants
                # that were still being rendered at the other end
                if (
                    in_sync.is_set()
                    and source_dirname == grid_path
                    and size[0] + 2 == cell_width
                ):
                    grid_cache[source_basename] = (
                        ImageCanvas(render.encode().split(b"\n"), size, rendered_size)
                        if render
                        else faulty_image.render(size)
                    )
                    if grid_active.is_set():
                        update_screen()
                    if THUMBNAIL_CACHE_SIZE and thumbnail:
                        mark_thumbnail_rendered(source, thumbnail)
                notify.stop_loading()
    finally:
        clear_queue(grid_render_in)
        for renderer in renderers:
            grid_render_in.put((None,) * 4)
        for renderer in renderers:
            renderer.join()
        clear_queue(grid_render_queue)


def manage_grid_thumbnails(thumbnail_size: int) -> None:
    from .main import grid_active, quitting

    # NOTE:
    # Always keep in mind that every directory entry is rendered only once per grid
    # since results are cached, at least for now.

    def cache_thumbnail(source: str, thumbnail: str) -> None:
        # Eviction, for finite cache size
        if THUMBNAIL_CACHE_SIZE and len(thumbnail_cache) == THUMBNAIL_CACHE_SIZE:
            # Evict and delete the first cached thumbnail not in the render pipeline
            for other_source, other_thumbnail in thumbnail_cache.items():
                # `thumbnail_render_lock` is unnecessary here since it's just a
                # membership test; the outcome is the same as when the lock is
                # used but more efficient.
                if other_thumbnail not in thumbnails_being_rendered:
                    delete_thumbnail(other_thumbnail)
                    del thumbnail_cache[other_source]
                    break
            # If all are being rendered, evict the oldest and queue it up to be
            # deleted later.
            else:
                with thumbnail_render_lock:
                    other_source = next(iter(thumbnail_cache))  # oldest entry
                    other_thumbnail = thumbnail_cache.pop(other_source)
                    extra_thumbnail_cache[other_source] = other_thumbnail
                thumbnails_to_be_deleted.add(other_thumbnail)

        thumbnail_cache[source] = thumbnail  # Cache the new thumbnail.

    multi = logging.MULTI
    thumbnail_in = (mp_Queue if multi else Queue)()
    thumbnail_out = (mp_Queue if multi else Queue)()
    not_generating = (mp_Event if multi else Event)()
    generator = (Process if multi else logging.Thread)(
        target=generate_grid_thumbnails,
        args=(thumbnail_in, thumbnail_out, thumbnail_size, not_generating),
        name="GridThumbnailer",
        redirect_notifs=True,
    )
    generator.start()
    not_generating.set()

    delimited = False
    in_sync = grid_thumbnailer_in_sync
    renderer_in_sync = grid_renderer_in_sync
    thumbnails_to_be_deleted: set[str] = set()
    # Stores `(size, alpha)`s (to be passed on to the renderer) in the same order in
    # which `source`s are sent to the generator.
    size_alpha_s: Queue[tuple[tuple[int, int], str | float | None]] = Queue()

    try:
        while True:
            while not (
                grid_active.wait(0.1)
                or quitting.is_set()
                or not thumbnail_out.empty()
                or thumbnails_to_be_deleted
            ):
                pass
            if quitting.is_set():
                break

            if delimited or not in_sync.is_set():
                in_sync.set()
                renderer_in_sync.wait()

                if THUMBNAIL_CACHE_SIZE:
                    with thumbnail_render_lock:
                        extra_thumbnail_cache.clear()
                        thumbnails_being_rendered.clear()

                    for thumbnail in thumbnails_to_be_deleted:
                        delete_thumbnail(thumbnail)
                    thumbnails_to_be_deleted.clear()

                # Purge the in queue and update the loading indicator counter
                while True:
                    try:
                        thumbnail_in.get(timeout=0.005)
                    except Empty:
                        break
                    else:
                        notify.stop_loading()

                # Wait for the thumbnail being generated, if any
                not_generating.wait()

                # Cache or delete already generated thumbnails in the out queue
                # and update the loading indicator counter
                while True:
                    try:
                        source, thumbnail = thumbnail_out.get(timeout=0.005)
                    except Empty:
                        break
                    else:
                        if (
                            THUMBNAIL_CACHE_SIZE
                            and len(thumbnail_cache) == THUMBNAIL_CACHE_SIZE
                        ):
                            # Quicker than the eviction process
                            delete_thumbnail(thumbnail)
                        else:
                            cache_thumbnail(source, thumbnail)
                        notify.stop_loading()

                # It's okay since we've taken care of all thumbnails that were being
                # generated.
                clear_queue(size_alpha_s)

                if not delimited:
                    while grid_thumbnail_queue.get():
                        pass
                else:
                    delimited = False

            if not in_sync.is_set():
                continue

            if THUMBNAIL_CACHE_SIZE:
                for thumbnail in thumbnails_to_be_deleted - thumbnails_being_rendered:
                    delete_thumbnail(thumbnail)
                    thumbnails_to_be_deleted.remove(thumbnail)

            if not in_sync.is_set():
                continue

            if grid_active.is_set():
                try:
                    image_info = grid_thumbnail_queue.get(timeout=0.02)
                except Empty:
                    pass
                else:
                    if not image_info:
                        delimited = True
                        continue
                    if thumbnail := thumbnail_cache.get(source := image_info[0]):
                        grid_render_queue.put((source, thumbnail, *image_info[2:]))
                        if THUMBNAIL_CACHE_SIZE:
                            with thumbnail_render_lock:
                                thumbnails_being_rendered.add(thumbnail)
                    else:
                        thumbnail_in.put(source)
                        size_alpha_s.put(image_info[2:])
                        notify.start_loading()

            if not in_sync.is_set():
                continue

            try:
                source, thumbnail = thumbnail_out.get(timeout=0.02)
            except Empty:
                pass
            else:
                size_alpha = size_alpha_s.get()
                if in_sync.is_set():
                    grid_render_queue.put((source, thumbnail, *size_alpha))
                    if THUMBNAIL_CACHE_SIZE and thumbnail:
                        with thumbnail_render_lock:
                            thumbnails_being_rendered.add(thumbnail)
                if thumbnail:
                    cache_thumbnail(source, thumbnail)
                notify.stop_loading()
    finally:
        clear_queue(thumbnail_in)
        thumbnail_in.put(None)
        generator.join()
        clear_queue(grid_thumbnail_queue)


def render_frames(
    input: Union[Queue, mp_Queue],
    output: Union[Queue, mp_Queue],
    ready: Union[Event, mp_Event],
    ImageClass: type,
    style_spec: str,
    repeat: int,
    cached: Union[bool, int],
):
    """Renders animation frames.

    Intended to be executed in a subprocess or thread.
    """
    from term_image.image import ImageIterator

    image = animator = None  # Silence flake8's F821
    block = True
    while True:
        try:
            data, size, alpha = input.get(block)
        except Empty:
            try:
                output.put(
                    (
                        next(animator),
                        animator.loop_no,
                        image.tell(),
                        size,
                        image.rendered_size,
                    )
                )
            except StopIteration:
                output.put((None,) * 5)
                block = True
            except Exception as e:
                output.put((None,) * 5)
                logging.log_exception(
                    (
                        f"Failed to render frame {image.tell()} of {image._source!r}"
                        + (f" during loop {animator.loop_no}" if repeat != -1 else "")
                    ),
                    logger,
                )
                notify.notify(str(e), level=notify.ERROR)
                block = True
        else:
            if not data:
                break

            if data is ...:
                try:
                    animator.close()
                except AttributeError:  # First time
                    pass
                clear_queue(output)
                ready.set()
                block = True
            elif isinstance(data, tuple):
                new_repeat, frame_no = data
                animator = ImageIterator(
                    image, new_repeat, f"1.1{alpha}{style_spec}", cached
                )
                next(animator)
                animator.seek(frame_no)
                image.set_size(Size.AUTO, maxsize=size)
                block = False
            else:
                # A new image is always created to ensure:
                # 1. the seek position of the image
                #    in MainProcess::MainThread is always correct, since frames should
                #    be rendered ahead.
                # 2. the image size is not changed from another thread in the course of
                #    animation (could occur when an animated image is opened from a
                #    grid wherein its cell is yet to be rendered, since GridRenderer
                #    will continue rendering cells alongside the animation).
                image = ImageClass.from_file(data)
                animator = ImageIterator(
                    image, repeat, f"1.1{alpha}{style_spec}", cached
                )
                image.set_size(Size.AUTO, maxsize=size)
                block = False

    clear_queue(output)


def render_grid_images(
    input: Queue | mp_Queue,
    output: Queue | mp_Queue,
    ImageClass: type,
    style_spec: str,
):
    """Renders images for the grid.

    Intended to be executed in a subprocess or thread.
    """
    while True:
        source, thumbnail, size, alpha = input.get()

        if not source:  # Quitting
            break

        # Using `BaseImage` for padding will use more memory since all the
        # spaces will be in the render output string, and theoretically more time
        # with all the checks and string splitting & joining.
        # While `ImageCanvas` is better since it only stores the main image render
        # string (as a list though) then generates and yields the complete lines
        # **as needed**. Trimmed padding lines are never generated at all.
        try:
            image = ImageClass.from_file(thumbnail or source)
            image.set_size(Size.FIT if thumbnail else Size.AUTO, maxsize=size)
            output.put(
                (
                    source,
                    thumbnail,
                    f"{image:1.1{alpha}{style_spec}}",
                    size,
                    image.rendered_size,
                )
            )
        except Exception:
            output.put((source, thumbnail, None, size, None))

    clear_queue(output)


def render_images(
    input: Queue | mp_Queue,
    output: Queue | mp_Queue,
    ImageClass: type,
    style_spec: str,
):
    """Renders images.

    Intended to be executed in a subprocess or thread.
    """
    while True:
        source, size, alpha, faulty = input.get()

        if not source:  # Quitting
            break

        # Using `BaseImage` for padding will use more memory since all the
        # spaces will be in the render output string, and theoretically more time
        # with all the checks and string splitting & joining.
        # While `ImageCanvas` is better since it only stores the main image render
        # string (as a list though) then generates and yields the complete lines
        # **as needed**. Trimmed padding lines are never generated at all.
        try:
            image = ImageClass.from_file(source)
            image.set_size(Size.AUTO, maxsize=size)
            output.put((f"{image:1.1{alpha}{style_spec}}", image.rendered_size))
        except Exception as e:
            output.put((None, None))
            # `faulty` ensures a fault is logged only once per `Image` instance
            if not faulty:
                logging.log_exception(f"Failed to load or render {source!r}", logger)
            notify.notify(str(e), level=notify.ERROR)

    clear_queue(output)


logger = _logging.getLogger(__name__)
anim_render_queue = Queue()
grid_render_queue = Queue()
grid_thumbnail_queue = Queue()
image_render_queue = Queue()
grid_renderer_in_sync = Event()
grid_thumbnailer_in_sync = Event()
thumbnails_being_rendered: set[str] = set()
thumbnail_render_lock = Lock()
# Main thumbnail cache
thumbnail_cache: dict[str, str] = {}
# For evicted thumbnails still being rendered
extra_thumbnail_cache: dict[str, str] = {}

# `GridRenderManager` is actually "in sync" initially.
#
# Removing these may result in ocassional deadlocks because at init, the thread
# may detect "out of sync" and try to prep for a new grid but **without a grid
# delimeter**.
# The deadlock is unpredictable and timing-dependent, as it only happens when
# `main.display_images()` signals "out of sync" **after** the thread has responded to
# the false initial "out of sync". Hence, the thread blocks on trying to get a grid
# delimeter.
# When another "out of sync" is signaled (with a grid delimeter), the thread takes
# the delimeter as for the previous "out of sync" and comes back around to block
# again since the event will be unset after consuming the delimeter.
grid_renderer_in_sync.set()
grid_thumbnailer_in_sync.set()

# Updated from `.tui.init()`
anim_style_specs = {"kitty": "+W", "iterm2": "+Wm1"}
grid_style_specs = {"kitty": "+L", "iterm2": "+L"}
image_style_specs = {"kitty": "+W", "iterm2": "+W"}

# Set from `.tui.init()`
# # Corresponding to command-line args and/or config options
ANIM_CACHED: bool | int
FRAME_DURATION: float
REPEAT: int
THUMBNAIL_CACHE_SIZE: int
