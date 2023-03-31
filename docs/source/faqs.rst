FAQs
====

What about Windows support?
   - Firstly, only the new `Windows Terminal <https://github.com/microsoft/terminal>`_ seems to have proper truecolor support and mordern terminal emulator features.
   - The CLI mode currently works (with a few quirks), i.e using ``cmd`` or ``powershell``, if the other requirements are satisfied but can't guarantee it'll always be so.

     - Drawing images and animations doesn't work completely well in ``cmd`` and ``powershell``.
       See the `library <https://github.com/AnonymouX47/term-image>`_\'s
       :external+term_image:doc:`issues` for details.

   - The TUI doesn't work due to the lack of `fcntl <https://docs.python.org/3/library/fcntl.html>`_ on Windows, which is used by `urwid <https://urwid.org>`_.
   - If stuck on Windows and want to use all features, you could use WSL + Windows Terminal.

Why are colours not properly reproduced?
   - Some terminals support truecolor escape sequences but have a **256-color pallete**. This limits color reproduction.

Why are images out of scale?
   - If *auto* :term:`cell ratio` is supported and enabled,

     - Use the ``swap win size`` :ref:`config option <swap-win-size-config>` or the ``--swap-win-size`` command-line option.
     - If the above doesn't work, then open a new issue `here <https://github.com/AnonymouX47/termvisage/issues/new/choose>`_ with adequate details.

   - Otherwise,

     - Adjust the :term:`cell ratio` using the :ref:`config option <cell-ratio-config>` or the ``-C | --cell-ratio`` command-line option.

Why is the TUI unresponsive or slow in drawing images?
   - Drawing (not rendering) speed is **entirely** dependent on the terminal emulator itself.
   - Some terminal emulators block upon input, so rapidly repeated input could cause the terminal to be unresponsive.
