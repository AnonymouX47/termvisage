General Concepts
================

The image viewer is started from the command line using the ``termvisage`` command.

.. _image-sources:

Image Sources
-------------

The viewer accepts the following kinds of :term:`sources <source>`:

* A path to an image file on a local filesystem.
* A path to a directory on a local filesystem.
* An Image URL.

Any thing else given as a source is reported as invalid. If no valid source is given,
the process exits with code ``NO_VALID_SOURCE`` (see :ref:`exit-codes`).


.. _modes:

Modes
-----

The viewer can be used in two modes:

1. **CLI mode**

   In this mode, images are directly printed to standard output. It is used when
   
   * output is not a terminal (even if ``--tui`` is specified)
   * there is only a single image source
   * the ``--cli`` option is specified

2. **TUI mode**

   In this mode, a Terminal/Text-based User Interface is launched, within which images
   and directories can be browsed and viewed in different ways. It is used when

   * there is at least one non-empty directory source
   * there are multiple image sources
   * the ``--tui`` option is specified


.. _render-styles:

Render Styles
-------------

See :term:`render style`.

By default, the best style supported by the :term:`active terminal` is automatically detected.
A particular render style can be specified using :confval:`style` or the ``-S | --style``
command-line option.

If the specified render style is:

* **graphics-based** and not supported, an error notification is emitted and the process
  exits with code ``FAILURE`` (see :ref:`exit-codes`).
* **text-based** and not [fully] supported, a warning notification is emitted but
  execution still proceeds with the style.

The ``--force-style`` command-line option can be used to bypass style support checks and
force the usage of any render style whether it's supported or not.


.. _cell-ratio:

Cell Ratio
----------

The :term:`cell ratio` is taken into consideration when setting image sizes for
**text-based** render styles, in order to preserve the aspect ratio of images drawn to
the terminal.

This value is determined by :confval:`cell ratio` OR either of the command-line options
``-C | --cell-ratio`` or ``--auto-cell-ratio``.
The command-line options are mutually exclusive and override the config option.

By default (i.e without changing the config option value or specifying either
command-line option), ``termvisage`` tries to determine the value from the
:term:`active terminal` which works on most mordern terminal emulators (currently
supported on UNIX-like platforms only).
This is probably the best choice, except the terminal emulator or platform doesn't
support this feature.

If ``termvisage`` is unable to determine this value automatically, it falls back to
``0.5``, which is a reasonable value in most cases.

In case *auto* cell ratio is not supported and the fallback value does not give expected
results, a different value can be specified using the config or command-line option.

.. attention::
   If using *auto* cell ratio and the :term:`active terminal` is not the controlling
   terminal of the ``termvisage`` process (e.g output is redirected to another terminal),
   ensure no process that might read input (e.g a shell) is currently running in the
   active terminal, as such a process might interfere with determining the cell ratio on
   some terminal emulators (e.g VTE-based ones).

   For instance, the ``sleep`` command can be executed if a shell is currently running in the active terminal.


Notifications
-------------

Notifications are event reports meant to be brought to the immediate knowledge of the user.

Notifications have two possible destinations:

* Standard output/error stream: This is used while the TUI is **not** launched.
* TUI :ref:`notification bar <notif-bar>`: This is used while the TUI is launched.

  * Notifications sent here automatically disappear after 5 seconds.

.. _logging:

Logging
-------

Logs are more detailed event reports meant for troubleshooting and debugging purporses.

Logs are written to a file on a local filesystem. The default log file is ``~/.termvisage/termvisage.log`` but a different file can be specified:

* for all sessions, using :confval:`log file`
* per session, using the ``--log-file`` command-line option

A log entry has the following format:

.. code-block:: none

   (<pid>) (<date> <time>) <process>: <thread>: [<level>] <module>: <function>: <message>

* *pid*: The process ID of the session.
* *date* and *time*: Current system date and time in the format ``%Y-%m-%d %H:%M:%S,<ms>``, where ``<ms>`` is in milliseconds.
* *process* and *thread*: The names of the python process and thread that produced the log record.

  * Only present when the *logging level* is set to ``DEBUG`` (either by ``--debug`` or ``--log-level=DEBUG``).

* *level*: The level of the log entry, this indicates it's importance.
* *module*: The package sub-module from which it originated.
* *function*: The function from which it originated.

  * Only present when running on **Python 3.8+** and *logging level* is set to ``DEBUG`` (either by ``--debug`` or ``--log-level=DEBUG``).

* *message*: The actual report describing the event that occured.


.. note::

   * Certain logs and some extra info are only provided when *logging level* is set to ``DEBUG``.
   * Log files are **appended to**, so it's safe use the same file for multiple sessions.
   * Log files are rotated upon reaching a size of **1MiB**.

     * Only the current and immediate previous log file are kept.

   * The Process ID of the each session preceeds its log entries, so this can be used to distinguish between logs from different sessions running simultaneously while using the same log file.


.. _exit-codes:

Exit Codes
----------
``termvisage`` returns the following exit codes with the specified meanings:

* ``0`` (SUCCESS): Exited normally and successfully.
* ``1`` (FAILURE): Exited due to an unhandled exception or a non-specific error.
* ``2`` (INVALID_ARG): Exited due to an invalid command-line argument value or option combination.
* ``3`` (INTERRUPTED): The program recieved an interrupt signal i.e ``SIGINT``.
* ``4`` (NO_VALID_SOURCE): Exited due to lack of any valid source.
