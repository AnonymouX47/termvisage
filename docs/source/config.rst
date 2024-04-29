Configuration
=============

The configuration is divided into the following categories:

* Options (applies to both the CLI and the TUI :ref:`modes`)
* Keybindings (applies to only the TUI :ref:`mode <modes>`)

The configuration file is written in **JSON** format, using a *partial config* style
i.e only the fields to be modified need to be present in the config file.

By default, ``termvisage`` searches the following locations, **in the specified order**,
for ``$DIR/termvisage/termvisage.json`` (a file named ``termvisage.json`` within a
directory named ``termvisage``):

* All valid directories specified in the ``XDG_CONFIG_DIRS`` environment variable,
  **in reverse order** or ``/etc/xdg`` if not set.
* The directory specified by the ``XDG_CONFIG_HOME`` environment variable or ``~/.config``
  if not set (where ``~`` is the current user's home directory).

If multiple config files are found (i.e in different locations), they're applied on top of
one another **in the order in which they were found**. Hence, a field present in the
latter, if valid, will override the same field also present in the former.

An alternative config file can be specified per-session using :option:`--config`.

To use the default configuration and not load any config file, use :option:`--no-config`.

.. tip::
   ``termvisage`` performs [quite] thorough validation on the values specified in a config
   file and reports any errors. To see information about how the errors are resolved
   (if resolvable), use :option:`-v`.

`This <https://raw.githubusercontent.com/AnonymouX47/termvisage/main/default-termvisage.json>`_
is a sample config file with all options and keybindings at their defaults.
Note that **this is only for reference**, using any field within it as-is has no effect.


Options
-------

These are top-level fields whose values control various settings of the viewer.

.. confval:: anim cache
   :synopsis: The maximum frame count of an image for which frames will be cached during
     animation.
   :type: integer
   :valid: *x* > ``0``
   :default: ``100``

   .. note::
      Overridden by :option:`--anim-cache`, :option:`--cache-all-anim`
      and :option:`--cache-no-anim`.

.. confval:: cell ratio
   :synopsis: The :term:`cell ratio`.
   :type: null or float
   :valid: ``null`` or *x* > ``0.0``
   :default: ``null``

   If ``null``, the ratio is determined from the :term:`active terminal` such that the
   aspect ratio of any image is always preserved. If this is not supported in the
   :term:`active terminal` or on the platform, ``0.5`` is used instead.

   .. note:: Overridden by :option:`-C` and :option:`--auto-cell-ratio`.

.. confval:: cell width
   :synopsis: The initial width of (no of columns for) grid cells, in the TUI.
   :type: integer
   :valid: ``30`` <= *x* <= ``50`` and *x* is even
   :default: ``30``

.. confval:: checkers
   :synopsis: Maximum number of subprocesses for checking directory sources.
   :type: null or integer
   :valid: ``null`` or *x* >= ``0``
   :default: ``null``

   If ``null``, the number of subprocesses is automatically determined based on the amount of
   logical processors available. CPU affinity is also taken into account on supported platforms.

   If less than ``2``, directory sources are checked within the main process.

.. confval:: getters
   :synopsis: Number of threads for downloading images from URL sources.
   :type: integer
   :valid: *x* > ``0``
   :default: ``4``

.. confval:: grid renderers
   :synopsis: Number of subprocesses for rendering grid cells.
   :type: integer
   :valid: *x* >= ``0``
   :default: ``1``

   If ``0`` (zero), grid cells are rendered by a thread of the main process.

.. confval:: log file
   :synopsis: The file to which logs are written.
   :type: string
   :valid: A writable/creatable file path
   :default: ``"{$XDG_STATE_HOME}/termvisage/termvisage.log"``

   If the file:

   * doesn't exist, at least one of the parents must be a directory and be writable,
     so the file can be created.
   * exists, it is appended to, not overwritten.

   Supports tilde expansion i.e a leading ``~`` (tilde) character is expanded to the
   current user's home directory.

   The environment variable ``$XDG_STATE_HOME`` defaults to ``~/.local/state`` if undefined.

   .. warning::
      Relative paths are allowed but this will cause the log file to be written (or
      created) relative to the **current working directory** every time a session
      is started.

   .. note:: Overridden by :option:`-l`.

   .. seealso:: :ref:`logging`

.. confval:: max notifications
   :synopsis: The maximum number of TUI notifications that can be shown at a time.
   :type: integer
   :valid: *x* >= ``0``
   :default: ``2``

   Adjusts the height of the :ref:`notification bar <notif-bar>`.

.. confval:: max pixels
   :synopsis: The maximum amount of pixels in images to be displayed in the TUI.
   :type: integer
   :valid: *x* > ``0``
   :default: ``4194304`` (2 ** 22)

   Any image having more pixels than the specified value will be:

   * **skipped**, in CLI mode, if :option:`--max-pixels-cli` is specified.
   * **replaced**, in TUI mode, with a placeholder (filled with exclamation marks)
     but can be forced to display using the **"Force Render"** action in contexts
     with full-sized image views.

   .. note:: Overridden by :option:`--max-pixels`.

   .. important::

      Increasing this should have little to no effect on general
      performance (i.e navigation, etc) but the larger an image is, the more the
      time and memory it'll take to render it. Thus, a large image might delay the
      rendering of other images to be rendered immediately after it.

.. confval:: multi
   :synopsis: Enable (if supported) or disable multiprocessing.
   :type: boolean
   :valid: ``true``, ``false``
   :default: ``true``

   If ``false``, the :confval:`checkers` and :confval:`grid renderers` options have no
   effect.

   .. note:: Overridden by :option:`--multi` and :option:`--no-multi`.

.. confval:: query timeout
   :synopsis: Timeout (in seconds) for all terminal queries.
   :type: float
   :valid: *x* > ``0.0``
   :default: ``0.1``

   .. note:: Overridden by :option:`--query-timeout`.

.. confval:: style
   :synopsis: Image :term:`render style`.
   :type: string
   :valid: ``"auto"``, ``"block"``, ``"iterm2"``, ``"kitty"``
   :default: ``"auto"``

   If set to any value other than ``"auto"`` and is not overridden by
   :option:`-S`, the style is used regardless of whether it's supported or not.

   .. note:: Overridden by :option:`-S`.

.. confval:: swap win size
   :synopsis: A workaround for some terminal emulators (e.g older VTE-based ones) that
     wrongly report window dimensions swapped.
   :type: boolean
   :valid: ``true``, ``false``
   :default: ``false``

   If ``true``, the window dimensions reported by the terminal emulator are swapped.

   .. note::
      * Overridden by :option:`--swap-win-size` and :option:`--no-swap-win-size`.
      * Affects *auto* :term:`cell ratio` computation.

.. confval:: thumbnail
   :synopsis: Enable or disable thumbnailing for the image grid.
   :type: boolean
   :valid: ``true``, ``false``
   :default: ``true``

   If ``true``, thumbnails are generated for some images (based on their size), cached
   on disk and cleaned up upon exit. Otherwise, all images in the grid are rendered
   directly from the original image files.

   .. note::

      - Overridden by :option:`--thumbnail` and :option:`--no-thumbnail`.
      - Thumbnails are generated **on demand** i.e a thumbnail will be generated for
        an image only if its grid cell has come into view at least once.

.. confval:: thumbnail cache
   :synopsis: The maximum amount of thumbnails that can be cached per time.
   :type: integer
   :valid: *x* >= ``0``
   :default: ``0``

   If ``0``, the cache size is infinite i.e no eviction. Otherwise, older thumbnails
   will be evicted to accommodate newer ones when the cache is full (i.e the specified
   size limit is reached).

   .. note:: Unused if :confval:`thumbnail` is ``false`` or :option:`--no-thumbnail`
      is specified.

.. confval:: thumbnail size
   :synopsis: Maxiumum thumbnail dimension.
   :type: integer
   :valid: ``32`` <= *x* <= ``512``
   :default: ``256``

   Thumbnails generated will have a maximum of *x* pixels in the long dimension.

   .. note:: Unused if :confval:`thumbnail` is ``false`` or :option:`--no-thumbnail`
      is specified.


Keybindings
-----------

The key assigned to every :ref:`action <actions>` in the TUI can be modified in the config file.

Keybindings are set by the ``keys`` top-level field, the value of which is a mapping
containing fields each mapping a :ref:`context <contexts>` to a mapping of
:ref:`actions <actions>` and their respective properties.

The format of the ``keys`` field is thus::

   "keys": {
      "<context>": {
         "<action>": [ "<key>", "<symbol>" ],
         ...
      },
      ...
   }

- *context* is the name of a :ref:`context <contexts>` or ``navigation``.
- *action* is the name of an :ref:`action <actions>`.
- Both *key* and *symbol* may contain Unicode characters and Python unicode escape sequences
  (``\uXXXX`` and ``\UXXXXXXXX``).
- *'...' means continuous repetition of the format may occur.*

.. tip::

   If using a Unicode character that occupies multiple columns in *symbol*, you **might**
   have to add after it as many spaces as are required to cover-up for the extra columns.

.. note::

   The ``navigation`` field is not actually a :ref:`context <contexts>`. Instead, it's
   the universal navigation configuration from which navigation actions in actual
   contexts are derived.

   The base navigation actions are:

   * ``Left``
   * ``Up``
   * ``Right``
   * ``Down``
   * ``Page Up``
   * ``Page Down``
   * ``Home``
   * ``End``

.. attention::

   #. Keys used in the ``global`` context cannot be used in any other context
      (including ``navigation``).
   #. Keys used in the ``navigation`` "context" cannot be used in any other context.
   #. All keys in a context must be unique.
   #. If a key is invalid or already used, the former and default keys for that action are
      tried as a fallback but if that fails (because they're already used), all keybindings
      from that config file are considered invalid and any changes already made are
      reverted.

`Here <https://raw.githubusercontent.com/AnonymouX47/termvisage/main/vim_style-termvisage.json>`_
is a sample config file with Vim-style (majorly navigation) keybindings.

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
