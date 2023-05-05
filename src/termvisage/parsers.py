"""CLI argument parsers"""

import re
import sys
from argparse import Action, ArgumentParser, RawDescriptionHelpFormatter, _ArgumentGroup

from term_image.image import ITerm2Image, Size

from . import cli  # noqa: F401; prevents circular import of `.config` (below)
from . import __version__
from .config import config_options


def rst_role_repl(match):
    if match.group(1) == "option":
        return f"`{match.group(2)}`"
    return match.group(2)


def strip_markup(string: str) -> str:
    """Strip selected reST markup from the *string*."""
    if string:
        string = string.replace("``", "`")
        string = string.replace("\\", "")
        for pattern, repl in (
            (r":(\w+):`(.+?)( <.+>)?`", rst_role_repl),
            (r"\*\*(.+)\*\*", r"\1"),
            (r"\*(.+)\*", r"\1"),
            (r" \[.+\]_", ""),
        ):
            string = re.sub(pattern, repl, string)

    return string


# Parser epilog, group descriptions and argument help may contain reStructuredText
# markup.
# Ensure any markup used is stripped by `strip_markup()`.

parser = ArgumentParser(
    prog="termvisage",
    formatter_class=RawDescriptionHelpFormatter,
    description="Display/Browse images in a terminal",
    epilog=""" \

``--`` should be used to separate positional arguments that begin with an ``-`` \
from options/flags, to avoid ambiguity.
For example, ``$ termvisage [options] -- -image.jpg --image.png``.

See https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html for \
supported image formats.

See https://termvisage.readthedocs.io/en/stable/cli.html for the complete CLI \
description.
""",
    add_help=False,  # `-h` is used for HEIGHT
)

# Positional
positional_args = parser.add_argument_group("Positional Arguments")
positional_args.add_argument(
    "sources",
    nargs="*",
    metavar="source",
    help=(
        "Image file path(s), directory path(s) and/or image URL(s). "
        "If no source is provided, the current working directory is used."
    ),
)

# General
general = parser.add_argument_group("General Options")
general.add_argument(
    "--help",
    action="help",
    help="Show this help message and exit",
)
general.add_argument(
    "--version",
    action="version",
    version=__version__,
    help="Show the program version and exit",
)
general.add_argument(
    "--query-timeout",
    type=float,
    metavar="N",
    help=(
        "Timeout (in seconds) for all terminal queries "
        f"(default: {config_options.query_timeout})"
    ),
)
general.add_argument(
    "-S",
    "--style",
    choices=("auto", "block", "iterm2", "kitty"),
    help=f"Image :term:`render style` (default: {config_options.style}) [#]_",
)
general.add_argument(
    "--force-style",
    action="store_true",
    help=(
        "Use the specified :term:`render style` even if it's reported as unsupported "
        "by the :term:`active terminal`"
    ),
)

cell_ratio_options = general.add_mutually_exclusive_group()
cell_ratio_options.add_argument(
    "-C",
    "--cell-ratio",
    type=float,
    metavar="N",
    help=(
        "The :term:`cell ratio` (width-to-height ratio of a character cell) in the "
        "terminal; to preserve image aspect ratio (default: auto)"
    ),
)
cell_ratio_options.add_argument(
    "--auto-cell-ratio",
    action="store_true",
    help=(
        "Determine the :term:`cell ratio` from the terminal emulator, if possible "
        "(default)"
    ),
)

win_size_options = general.add_mutually_exclusive_group()
win_size_options.add_argument(
    "--swap-win-size",
    action="store_true",
    default=None,
    help=(
        "A workaround for *auto* :term:`cell ratio` on some terminal emulators "
        "(e.g older VTE-based ones) that wrongly report window dimensions swapped"
    ),
)
win_size_options.add_argument(
    "--no-swap-win-size",
    action="store_false",
    default=None,
    dest="swap_win_size",
    help=(
        "Unlike :option:`--swap-win-size`, use the reported window size as-is (default)"
    ),
)

mode_options = general.add_mutually_exclusive_group()
mode_options.add_argument(
    "--cli",
    action="store_true",
    help=(
        "Do not launch the TUI. Instead, draw all image sources "
        "to the terminal directly [#]_"
    ),
)
mode_options.add_argument(
    "--tui",
    action="store_true",
    help="Launch the TUI, even for a single image",
)

# # Animation
anim_options = parser.add_argument_group("Animation Options (General)")
anim_options.add_argument(
    "-f",
    "--frame-duration",
    type=float,
    metavar="N",
    help=(
        "The time (in seconds) between frames for all :term:`animated` images "
        "(default: determined per image from the metadata OR 0.1)"
    ),
)
anim_options.add_argument(
    "-R",
    "--repeat",
    type=int,
    default=-1,
    metavar="N",
    help=(
        "Number of times to repeat all frames of an :term:`animated` image; "
        "A negative count implies an infinite loop (default: -1)"
    ),
)

anim_cache_options = anim_options.add_mutually_exclusive_group()
anim_cache_options.add_argument(
    "--anim-cache",
    type=int,
    metavar="N",
    help=(
        "Maximum frame count for animation frames to be cached (Better performance "
        f"at the cost of memory) (default: {config_options.anim_cache}) [#]_"
    ),
)
anim_cache_options.add_argument(
    "--cache-all-anim",
    action="store_true",
    help=(
        "Cache frames for all animations (**beware**, the higher the frame count "
        "**per image**, the higher the memory usage)"
    ),
)
anim_cache_options.add_argument(
    "--cache-no-anim",
    action="store_true",
    help="Disable frame caching (Less memory usage but reduces performance)",
)

anim_options.add_argument(
    "--no-anim",
    action="store_true",
    help=(
        "Disable image animation. Animated images are displayed as just their "
        "first frame."
    ),
)

# # Transparency
_alpha_options = parser.add_argument_group(
    "Transparency Options (General)",
    "**NOTE:** These are mutually exclusive",
)
alpha_options = _alpha_options.add_mutually_exclusive_group()
alpha_options.add_argument(
    "--no-alpha",
    action="store_true",
    help="Disable image transparency (alpha channel is removed)",
)
alpha_options.add_argument(
    "-A",
    "--alpha",
    type=float,
    metavar="N",
    default=40 / 255,
    help=(
        "Alpha ratio above which pixels are taken as opaque (0 <= x < 1), "
        f"for text-based :term:`render styles` (default: {40 / 255:f})"
    ),
)
alpha_options.add_argument(
    "-b",
    "--alpha-bg",
    nargs="?",
    const="",
    metavar="COLOR",
    help=(
        "Hex color (without ``#``) to replace transparent backgrounds with "
        "(omit *COLOR* to use the :term:`active terminal`\\'s default BG color)"
    ),
)

# CLI-only
cli_options = parser.add_argument_group(
    "CLI-only Options",
    "These options apply only when there is only one valid image source or "
    ":option:`--cli` is specified",
)
cli_options.add_argument(
    "--h-allow",
    type=int,
    default=0,
    metavar="N",
    help=(
        ":term:`Horizontal allowance` i.e minimum number of columns to leave unused "
        "(default: 0)"
    ),
)
cli_options.add_argument(
    "--v-allow",
    type=int,
    default=2,
    metavar="N",
    help=(
        ":term:`Vertical allowance` i.e minimum number of lines to leave unused "
        "(default: 2)"
    ),
)
cli_options.add_argument(
    "--scroll",
    action="store_true",
    help=(
        "Allow an image's height to be greater than the :term:`terminal height`. "
        "Not needed when :option:`--fit-to-width` is specified."
    ),
)
cli_options.add_argument(
    "-O",
    "--oversize",
    action="store_true",
    help=(
        "Allow an image's size to be greater than the :term:`terminal size` "
        "(To be used with :option:`-w` or :option:`--original-size`)"
    ),
)

# Sizing
_sizing_options = parser.add_argument_group(
    "Sizing Options (CLI-only)",
    "These apply to all images and are mutually exclusive [#]_",
)
sizing_options = _sizing_options.add_mutually_exclusive_group()
sizing_options.add_argument(
    "-w",
    "--width",
    type=int,
    metavar="N",
    help="Image width",
)
sizing_options.add_argument(
    "-h",
    "--height",
    type=int,
    metavar="N",
    help="Image height",
)
sizing_options.add_argument(
    "--fit",
    action="store_const",
    const=Size.FIT,
    dest="auto_size",
    help=(
        "Fit each image optimally within the :term:`available <available size>` "
        ":term:`terminal size`"
    ),
)
sizing_options.add_argument(
    "--fit-to-width",
    action="store_const",
    const=Size.FIT_TO_WIDTH,
    dest="auto_size",
    help=(
        "Fit each image to the :term:`available <available size>` :term:`terminal "
        "width`, :option:`--v-allow` has no effect i.e :term:`vertical allowance` "
        "is ignored"
    ),
)
sizing_options.add_argument(
    "--original-size",
    action="store_const",
    const=Size.ORIGINAL,
    dest="auto_size",
    help=(
        "Render each image using its original size "
        "(See :option:`-O`, **USE WITH CAUTION!**)"
    ),
)
sizing_options.add_argument(
    "-s",
    "--scale",
    type=float,
    metavar="N",
    help="Image :term:`scale` (overrides :option:`-x` and :option:`-y`) [#]_",
)
sizing_options.add_argument(
    "-x",
    "--scale-x",
    type=float,
    metavar="N",
    default=1.0,
    help="Image horizontal :term:`scale` (overriden by :option:`-s`) (default: 1.0)",
)
sizing_options.add_argument(
    "-y",
    "--scale-y",
    type=float,
    metavar="N",
    default=1.0,
    help="Image vertical :term:`scale` (overriden by :option:`-s`) (default: 1.0)",
)

# # Alignment
align_options = parser.add_argument_group(
    "Alignment Options (CLI-only)",
    "These apply to all images",
)
align_options.add_argument(
    "--no-align",
    action="store_true",
    help=(
        "Output image without :term:`alignment` or :term:`padding`. "
        "Overrides all other alignment options."
    ),
)
align_options.add_argument(
    "-H",
    "--h-align",
    choices=("left", "center", "right"),
    help=":term:`Horizontal alignment` (default: center)",
)
align_options.add_argument(
    "--pad-width",
    metavar="N",
    type=int,
    help=(
        "Number of columns within which to align each image "
        "(default: :term:`terminal width`, minus :term:`horizontal allowance`)"
    ),
)
align_options.add_argument(
    "-V",
    "--v-align",
    choices=("top", "middle", "bottom"),
    help=":term:`Vertical alignment` (default: middle)",
)
align_options.add_argument(
    "--pad-height",
    metavar="N",
    type=int,
    help="Number of lines within which to align each image (default: none)",
)

# TUI-only
tui_options = parser.add_argument_group(
    "TUI-only Options",
    "These options apply only when there is at least one valid directory source, "
    "multiple valid sources or :option:`--tui` is specified",
)

tui_options.add_argument(
    "-a",
    "--all",
    action="store_true",
    help="Inlcude hidden file and directories",
)
tui_options.add_argument(
    "-r",
    "--recursive",
    action="store_true",
    help="Scan for local images recursively",
)
tui_options.add_argument(
    "-d",
    "--max-depth",
    type=int,
    metavar="N",
    default=sys.getrecursionlimit() - 50,
    help=f"Maximum recursion depth (default: {sys.getrecursionlimit() - 50})",
)

# Performance
perf_options = parser.add_argument_group("Performance Options")
perf_options.add_argument(
    "--max-pixels",
    type=int,
    metavar="N",
    help=(
        "Maximum amount of pixels in images to be displayed "
        f"(default: {config_options.max_pixels}) [#]_"
    ),
)
perf_options.add_argument(
    "--max-pixels-cli",
    action="store_true",
    help="Apply :option:`--max-pixels` in CLI mode",
)
perf_options.add_argument(
    "--checkers",
    type=int,
    metavar="N",
    help=(
        "Maximum number of subprocesses for checking directory sources (default: auto)"
    ),
)
perf_options.add_argument(
    "--getters",
    type=int,
    metavar="N",
    help=(
        "Number of threads for downloading images from URL sources "
        f"(default: {config_options.getters})"
    ),
)
perf_options.add_argument(
    "--grid-renderers",
    type=int,
    metavar="N",
    help=(
        "Number of subprocesses for rendering grid cells in the TUI "
        f"(default: {config_options.grid_renderers})"
    ),
)

multi_options = perf_options.add_mutually_exclusive_group()
multi_options.add_argument(
    "--multi",
    action="store_true",
    default=None,
    help="Enable multiprocessing, if supported (default)",
)
multi_options.add_argument(
    "--no-multi",
    action="store_false",
    default=None,
    dest="multi",
    help="Disable multiprocessing",
)

# Config
config_options__ = parser.add_argument_group(
    "Config Options",
    "**NOTE:** These are mutually exclusive",
)
config_options_ = config_options__.add_mutually_exclusive_group()

config_options_.add_argument(
    "--config",
    metavar="FILE",
    help="The config file to use for this session (default: Searches XDG Base Dirs)",
)
config_options_.add_argument(
    "--no-config",
    action="store_true",
    help="Use the default configuration",
)

# Logging
log_options_ = parser.add_argument_group(
    "Logging Options",
    "**NOTE:** All these, except :option:`-l`, are mutually exclusive",
)
log_options = log_options_.add_mutually_exclusive_group()

log_options_.add_argument(
    "-l",
    "--log-file",
    metavar="FILE",
    help=f"The file to write logs to (default: {config_options.log_file})",
)
log_options.add_argument(
    "--log-level",
    choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    default="WARNING",
    help="Logging level for the session (default: WARNING) [#]_",
)
log_options.add_argument(
    "-q",
    "--quiet",
    action="store_true",
    help="No notifications, except fatal errors",
)
log_options.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="More detailed event reporting. Also sets logging level to INFO",
)
log_options.add_argument(
    "--verbose-log",
    action="store_true",
    help="Like :option:`-v` but only applies to the log file",
)
log_options.add_argument(
    "--debug",
    action="store_true",
    help="Implies :option:`--log-level=DEBUG` with verbosity",
)


# Style-specific Parsers

kitty_parser = ArgumentParser(add_help=False)
kitty_options = kitty_parser.add_argument_group(
    "Kitty Style Options",
    "These options apply only when the *kitty* :term:`render style` is used",
)
kitty_options.add_argument(
    "--kz",
    "--kitty-z-index",
    metavar="N",
    dest="z_index",
    default=0,
    type=int,
    help=(
        "Image stacking order [CLI-only]; ``>= 0`` -> above text, ``< 0`` -> below "
        "text, ``< -(2**31)/2`` -> below cells with non-default background "
        "(default: 0)"
    ),
)
kitty_options.add_argument(
    "--kc",
    "--kitty-compress",
    metavar="N",
    dest="compress",
    default=4,
    type=int,
    help=(
        "ZLIB compression level; 0 -> no compression, 1 -> best speed, "
        "9 -> best compression (default: 4)"
    ),
)

iterm2_parser = ArgumentParser(add_help=False)
iterm2_options = iterm2_parser.add_argument_group(
    "iTerm2 Style Options",
    "These options apply only when the *iterm2* :term:`render style` is used",
)
iterm2_options.add_argument(
    "--itn",
    "--iterm2-native",
    action="store_true",
    dest="native",
    help=(
        "Use the protocol's animation support; animations will not be skipped "
        "[CLI-only]"
    ),
)
iterm2_options.add_argument(
    "--itnmb",
    "--iterm2-native-max-bytes",
    metavar="N",
    dest="native_max_bytes",
    default=ITerm2Image.native_anim_max_bytes,
    type=int,
    help=(
        "Maximum size (in bytes) of image data for native animation [CLI-only] "
        f"(default: {ITerm2Image.native_anim_max_bytes})"
    ),
)
iterm2_options.add_argument(
    "--itc",
    "--iterm2-compress",
    metavar="N",
    dest="compress",
    default=4,
    type=int,
    help=(
        "ZLIB compression level, for images re-encoded in PNG format "
        "0 -> no compression, 1 -> best speed, 9 -> best compression (default: 4)"
    ),
)
iterm2_options.add_argument(
    "--itjq",
    "--iterm2-jpeg-quality",
    metavar="N",
    dest="jpeg_quality",
    default=ITerm2Image.jpeg_quality,
    type=int,
    help=(
        "JPEG compression status and quality; ``< 0`` -> disabled, ``0 <= x <= 95`` -> "
        f"quality (default: {ITerm2Image.jpeg_quality}) [#]_"
    ),
)
iterm2_options.add_argument(
    "--itnrff",
    "--iterm2-no-read-from-file",
    action="store_false",
    dest="read_from_file",
    help="Never use image data directly from file; always re-encode images [#]_",
)

style_parsers = {"kitty": kitty_parser, "iterm2": iterm2_parser}

for style_parser in style_parsers.values():
    parser._actions.extend(style_parser._actions)
    parser._option_string_actions.update(style_parser._option_string_actions)
    parser._action_groups.extend(style_parser._action_groups)
    parser._mutually_exclusive_groups.extend(style_parser._mutually_exclusive_groups)

# Setup reST markup to be Striped from epilog, group descriptions and argument help.
# Anything patched here must be unpatched in the docs config script.
ArgumentParser.epilog = property(lambda self: strip_markup(vars(self)["epilog"]))
Action.help = property(lambda self: strip_markup(vars(self)["help"]))
_ArgumentGroup.description = property(
    lambda self: strip_markup(vars(self)["description"])
)
