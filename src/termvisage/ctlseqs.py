"""Control Sequences

See https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
"""

from __future__ import annotations

__all__: list[str] = []  # Updated later on

# Parameters
# ======================================================================================

C = "%c"
Ps = "%d"
Pt = "%s"


# ============================ START OF CONTROL SEQUENCES ==============================

_START = None  # Marks the beginning control sequence definitions


# C0
# ======================================================================================

BEL = "\x07"
ESC = "\x1b"

BEL_b: bytes
ESC_b: bytes

# C1
# ======================================================================================

APC = f"{ESC}_"
CSI = f"{ESC}["
OSC = f"{ESC}]"
ST = f"{ESC}\\"

APC_b: bytes
CSI_b: bytes
OSC_b: bytes
ST_b: bytes

# Functions Beginning With CSI
# ======================================================================================

ERASE_IN_LINE_LEFT = f"{CSI}1K"
RESTORE_WINDOW_TITLE = f"{CSI}23;2t"
SAVE_WINDOW_TITLE = f"{CSI}22;2t"

ERASE_IN_LINE_LEFT_b: bytes
RESTORE_WINDOW_TITLE_b: bytes
SAVE_WINDOW_TITLE_b: bytes

# # Select Graphic Rendition
# # ====================================================================================

SGR = f"{CSI}{Pt}m"
SGR_FG_8 = SGR % f"3{Ps}"
SGR_SHORT = SGR % Ps

SGR_b: bytes
SGR_FG_8_b: bytes
SGR_SHORT_b: bytes

SGR_BLUE = SGR_FG_8 % 4
SGR_BOLD = SGR_SHORT % 1
SGR_DEFAULT = SGR % ""
SGR_ITALIC = SGR_SHORT % 3
SGR_NOT_BOLD_FAINT = SGR_SHORT % 22
SGR_NOT_ITALIC = SGR_SHORT % 23
SGR_RED = SGR_FG_8 % 1
SGR_YELLOW = SGR_FG_8 % 3

SGR_BLUE_b: bytes
SGR_BOLD_b: bytes
SGR_DEFAULT_b: bytes
SGR_ITALIC_b: bytes
SGR_NOT_BOLD_FAINT_b: bytes
SGR_NOT_ITALIC_b: bytes
SGR_RED_b: bytes
SGR_YELLOW_b: bytes

# Operating System Commands
# ======================================================================================

TEXT_PARAM_SET = f"{OSC}{Ps};{Pt}{ST}"

TEXT_PARAM_SET_b: bytes

SET_WINDOW_TITLE = TEXT_PARAM_SET % (2, Pt)

SET_WINDOW_TITLE_b: bytes

# Kitty Graphics Protocol
# See https://sw.kovidgoyal.net/kitty/graphics-protocol/
# ======================================================================================

KITTY_START = f"{APC}G"
KITTY_DELETE_CURSOR_IMAGES = f"{KITTY_START}a=d,d=C;{ST}"

KITTY_START_b: bytes
KITTY_DELETE_CURSOR_IMAGES_b: bytes


# `bytes` Versions of Control Sequences
# ======================================================================================

module_items = tuple(globals().items())
for name, value in module_items[module_items.index(("_START", None)) + 1 :]:
    globals()[f"{name}_b"] = value.encode()
    __all__.extend((name, f"{name}_b"))

del _START, module_items
