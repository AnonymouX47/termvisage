Configuration
=============

The configuration is divided into the following categories:

* Options
* Keybindings

A configuration file is written in JSON format, using a *partial config* style i.e only
the fields to be modified need to be present in the config file.

By default, ``termvisage`` searches the following locations, in the specified order,
for ``$DIR/termvisage/config.json`` (a file named ``config.json`` within a ``termvisage``
directory).

* All valid directories specified in the ``XDG_CONFIG_DIRS`` enviroment variable,
  **in reverse order** or ``/etc/xdg`` if not set.
* The directory specified in the ``XDG_CONFIG_HOME`` enviroment variable or ``~/.config``
  if not set (where ``~`` is the current user's home directory).

If multiple config files are found (i.e in different locations), they're applied on top of
one another **in the order in which they were found**. Hence, a field present in the
latter, if valid, will override the same field also present in the former.

An alternative config file can be specified per-session using the ``--config`` command-line
option.

To use the default configuration and not load any config file, use the ``--no-config``
command-line option.

.. hint::
   ``termvisage`` performs [quite] thorough validation on the values specified in a config
   file and reports any errors. To see information about how the errors are resolved
   (if resolvable), use the ``-v/--verbose`` command-line option.

`This <https://raw.githubusercontent.com/AnonymouX47/termvisage/main/default_config.json>`_
is a sample config file with all options and keybindings at their defaults. Note that **this is only for reference**, using any field within it as-is has no effect.

Config Options
--------------

| These are fields whose values control various behaviours of the viewer.
| Any option with a "[\*]" after its description will be used only when a corresponding
  command-line option is either not specified or has an invalid value.

They are as follows:

.. confval:: anim cache
   :synopsis: The maximum frame count of an image for which frames will be cached during
     animation [\*]
   :type: integer
   :valid: x > ``0``
   :default: ``100``

.. _cell-ratio-config:

.. confval:: cell ratio
   :synopsis: The :term:`cell ratio` [\*]
   :type: null or float
   :valid: ``null`` or x > ``0.0``
   :default: ``null``

   If ``null``, the ratio is determined from the :term:`active terminal` such that the
   aspect ratio of any image is always preserved. If this is not supported in the
   :term:`active terminal` or on the platform, ``0.5`` is used instead.

.. confval:: cell width
   :synopsis: The initial width of (no of columns for) grid cells, in the TUI.
   :type: integer
   :valid: ``30`` <= x <= ``50`` and x is even
   :default: ``30``

.. confval:: checkers
   :synopsis: Maximum number of subprocesses for checking directory sources. [\*]
   :type: null or integer
   :valid: ``null`` or x >= ``0``
   :default: ``null``

   | If ``null``, the number of subprocesses is automatically determined based on the amount of
     logical processors available. CPU affinity is also taken into account on supported platforms.
   | If less than ``2``, directory sources are checked within the main process.

.. confval:: getters
   :synopsis: Number of threads for downloading images from URL sources. [\*]
   :type: integer
   :valid: x > ``0``
   :default: ``4``

.. confval:: grid renderers
   :synopsis: Number of subprocesses for rendering grid cells. [\*]
   :type: integer
   :valid: x >= ``0``
   :default: ``1``

   If ``0`` (zero), grid cells are rendered by a thread of the main process.

.. _log-file-config:

.. confval:: log file
   :synopsis: The file to which logs are written. [\*]
   :type: string
   :valid: An absolute path to a writable file.
   :default: ``"~/.termvisage/termvisage.log"``

   | If the file doesn't exist, at least one of the parents must be a directory and be
     writable, so the file can created.
   | If the file exists, it is appended to, not overwritten.
   | Supports tilde expansion i.e a leading ``~`` (tilde) character is expanded to the
     current user's home directory.
   | See :ref:`logging`.

   .. warning::
      Relative paths are allowed but this will cause the log file to be written (or
      created) relative to the **current working directory** every time the process
      is started.

.. confval:: max notifications
   :synopsis: The maximum number of TUI notifications that can be shown at a time.
   :type: integer
   :valid: x >= ``0``
   :default: ``2``

   | Adjusts the height of the :ref:`notification bar <notif-bar>`.

.. confval:: max pixels
   :synopsis: The maximum amount of pixels in images to be displayed in the TUI. [\*]
   :type: integer
   :valid: x > ``0``
   :default: ``4194304`` (2 ** 22)

   Any image having more pixels than the specified value will be:

   * skipped, in CLI mode, if ``--max-pixels-cli`` is specified.
   * replaced, in TUI mode, with a placeholder when displayed but can still be forced
     to display or viewed externally.

   Note that increasing this should not have any effect on general performance (i.e
   navigation, etc) but the larger an image is, the more the time and memory it'll take
   to render it. Thus, a large image might delay the rendering of other images to be
   rendered immediately after it.

.. confval:: multi
   :synopsis: Enable or disable multiprocessing. [\*]
   :type: boolean
   :valid: ``true``, ``false``
   :default: ``true``

   If ``false``, the ``checkers`` and ``grid renderers`` options have no effect.

.. confval:: query timeout
   :synopsis: Timeout (in seconds) for all terminal queries. [\*]
   :type: float
   :valid: x > ``0.0``
   :default: ``0.1``

.. _style-config:

.. confval:: style
   :synopsis: Image :term:`render style`. [\*]
   :type: string
   :valid: ``"auto"``, ``"block"``, ``"iterm2"``, ``"kitty"``
   :default: ``"auto"``

   If set to any value other than ``"auto"`` and is not overriden by the ``-S | --style``
   command-line option, the style is used regardless of whether it's supported or not.

.. _swap-win-size-config:

.. confval:: swap win size
   :synopsis: A workaround for some terminal emulators (e.g older VTE-based ones) that wrongly
     report window dimensions swapped. [\*]
   :type: boolean
   :valid: ``true``, ``false``
   :default: ``false``

   | If ``true``, the dimensions reported by the terminal emulator are swapped.
   | This setting affects *auto* :term:`cell ratio` computation.


Keybindings
-----------

The key assigned to every :ref:`action <actions>` can be modified in the config file.

The ``"keys"`` field in the config holds a mapping containing fields each mapping a
:ref:`context <contexts>` to a mapping of :ref:`actions <actions>` to their properties.

The format of the ``"keys"`` mapping is thus::

   {
      "<context>": {
         "<action>": [
            "<key>",
            "<symbol>"
         ],

         ...
      },

      ...
   }

*'...' means continuous repetition of the format **may** occur.*

| *action* is the name of an action.
| Both *key* and *symbol* must be valid Python strings, hence Unicode characters and
  escape sequences (``\uXXXX`` and ``\UXXXXXXXX``) are supported.

.. hint::

   If using a Unicode character that occupies multiple columns in *symbol*, then add spaces
   after it as required to cover-up for the extra columns.

.. note::

   The ``navigation`` field is not actually a *context*, instead it's the universal
   navigation controls configuration from which navigation *actions* in actual *contexts*
   are updated.

.. attention::

   1. Keys used in ``global`` context cannot be used in any other context (including ``navigation``).
   1. Keys used in ``navigation`` context cannot be used in any other context.
   2. All keys in a context must be unique.

   3. If a key is invalid or already used, the former and default keys for that action are
      tried as a fallback but if that fails (because they're already used), all keybindings
      from that config file are considered invalid and any changes already made are
      reverted.

| `Here <https://raw.githubusercontent.com/AnonymouX47/termvisage/main/vim-style_config.json>`_
  is a config with Vim-style (majorly navigation) keybindings.
| Remember to rename the file to ``config.json`` if placing it in any of the XDG Base Directories.

Below is a list of all **valid** values for *key*::

    " "
    "!"
    """
    "#"
    "$"
    "%"
    "&"
    "'"
    "("
    ")"
    "*"
    "+"
    ","
    "-"
    "."
    "/"
    "0"
    "1"
    "2"
    "3"
    "4"
    "5"
    "6"
    "7"
    "8"
    "9"
    ":"
    ";"
    "<"
    "="
    ">"
    "?"
    "@"
    "["
    "\\"
    "]"
    "^"
    "_"
    "`"
    "A"
    "a"
    "ctrl a"
    "B"
    "b"
    "ctrl b"
    "C"
    "c"
    "D"
    "d"
    "ctrl d"
    "E"
    "e"
    "ctrl e"
    "F"
    "f"
    "ctrl f"
    "G"
    "g"
    "ctrl g"
    "H"
    "h"
    "ctrl h"
    "I"
    "i"
    "ctrl i"
    "J"
    "j"
    "ctrl j"
    "K"
    "k"
    "ctrl k"
    "L"
    "l"
    "ctrl l"
    "M"
    "m"
    "ctrl m"
    "N"
    "n"
    "ctrl n"
    "O"
    "o"
    "ctrl o"
    "P"
    "p"
    "ctrl p"
    "Q"
    "q"
    "ctrl q"
    "R"
    "r"
    "ctrl r"
    "S"
    "s"
    "ctrl s"
    "T"
    "t"
    "ctrl t"
    "U"
    "u"
    "ctrl u"
    "V"
    "v"
    "ctrl v"
    "W"
    "w"
    "ctrl w"
    "X"
    "x"
    "ctrl x"
    "Y"
    "y"
    "ctrl y"
    "Z"
    "z"
    "{"
    "|"
    "}"
    "~"
    "f1"
    "ctrl f1"
    "shift f1"
    "shift ctrl f1"
    "f2"
    "ctrl f2"
    "shift f2"
    "shift ctrl f2"
    "f3"
    "ctrl f3"
    "shift f3"
    "shift ctrl f3"
    "f4"
    "ctrl f4"
    "shift f4"
    "shift ctrl f4"
    "f5"
    "ctrl f5"
    "shift f5"
    "shift ctrl f5"
    "f6"
    "ctrl f6"
    "shift f6"
    "shift ctrl f6"
    "f7"
    "ctrl f7"
    "shift f7"
    "shift ctrl f7"
    "f8"
    "ctrl f8"
    "shift f8"
    "shift ctrl f8"
    "f9"
    "ctrl f9"
    "shift f9"
    "shift ctrl f9"
    "up"
    "ctrl up"
    "shift up"
    "shift ctrl up"
    "end"
    "ctrl end"
    "shift end"
    "shift ctrl end"
    "esc"
    "f10"
    "ctrl f10"
    "shift f10"
    "shift ctrl f10"
    "f11"
    "ctrl f11"
    "shift f11"
    "shift ctrl f11"
    "f12"
    "ctrl f12"
    "shift f12"
    "shift ctrl f12"
    "tab"
    "down"
    "ctrl down"
    "shift down"
    "shift ctrl down"
    "home"
    "ctrl home"
    "shift home"
    "shift ctrl home"
    "left"
    "ctrl left"
    "shift left"
    "shift ctrl left"
    "enter"
    "right"
    "ctrl right"
    "shift right"
    "shift ctrl right"
    "delete"
    "ctrl delete"
    "shift delete"
    "shift ctrl delete"
    "insert"
    "backspace"
    "page up"
    "ctrl page up"
    "page down"
    "ctrl page down"

Any value other than these will be flagged as invalid.
