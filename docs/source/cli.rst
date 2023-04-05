Command-Line Interface
======================

Usage
-----

Run ``termvisage --help`` to see the usage info and help text.

.. note::
   Some options are only applicable in a specific :ref:`mode <modes>`.
   If used with the other mode, they're simply ignored.

.. tip::
   Some options have a ``[N]`` (where *N* is a number) after their description,
   it indicates that the option has a footnote.
   The footnotes are at the bottom of the help text.


Options and Arguments
---------------------

.. autoprogram:: termvisage.parsers:parser
   :groups:

|

.. rubric:: Footnotes

.. [#] In CLI mode, only image sources are used, directory sources are skipped.
   Animated images are displayed only when animation is disabled (with ``--no-anim``),
   when there's only one image source or when using native animation of some render
   styles.

.. [#]  Frames will not be cached for any animation with more frames than this value.
   Memory usage depends on the frame count **per image**, not this maximum count.

.. [#] The size is multiplied by the scale on respective axes when an image is rendered.
   A scale value must be such that 0.0 < value <= 1.0.

.. [#] Width and height are in units of columns and lines repectively.

   By default (i.e if none of the sizing options is specified), the equivalent of
   ``--original-size`` is used if not larger than the :term:`available size`, else
   ``--fit``.

.. [#] Any image having more pixels than the specified maximum will be:

   - skipped, in CLI mode, if ``--max-pixels-cli`` is specified.
   - replaced, in TUI mode, with a placeholder when displayed but can still be
     explicitly made to display.

   Note that increasing this should not have any effect on general performance
   (i.e navigation, etc) but the larger an image is, the more the time and memory
   it'll take to render it. Thus, a large image might delay the rendering of other
   images to be rendered immediately after it.

.. [#] Any event with a level lower than the specified one is not reported.

.. [#] 0 -> worst quality; smallest data size, 95 -> best quality; largest data size.

   By default (i.e when disabled), PNG format is used for re-encoding images,
   which has less compression with better quality. JPEG encoding:

   - reduces render time & image data size and increases drawing speed on the
     terminal's end but at the cost of image quality and color reproduction.
   - is useful for animations with high resolution and/or sparse color distribution.
   - only applies when an image is re-encoded and not read directly from file
     (see ``--iterm2-no-read-from-file``).
   - can only be used for non-transparent images but the transparency status
     of some images can not be correctly determined in an efficient way at render time.

     Thus, to ensure the JPEG format is always used for re-encoded images, disable
     transparency (``--no-alpha``) or set a background color (``-b | --alpha-bg``).

.. [#] By default, image data is used directly from file when no image manipulation is
   required. Otherwise, it's re-encoded in PNG (or JPEG, if enabled) format.

   The optimization significantly reduces render time when applicable but does not apply
   to animations, native or not.
