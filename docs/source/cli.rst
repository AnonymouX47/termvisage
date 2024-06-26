Command-Line Interface
======================

Run ``termvisage --help`` to see the basic help message or ``termvisage --long-help``
for the full help message.

.. note::
   Some options are only applicable in a specific :ref:`mode <modes>`.
   If used with the other mode, they're simply ignored.


Shell Completion
----------------

Run ``termvisage --completions`` for instructions on enabling tab completion for options
and arguments of ``termvisage`` in your preferred shell.


Options and Arguments
---------------------

.. autoprogram:: termvisage.parsers:parser
   :groups:

|

.. rubric:: Footnotes

.. [#] See :ref:`render-styles`.

.. [#] In CLI mode, only image sources are used, directory sources are skipped.
   Animated images are displayed only when animation is disabled (with
   :option:`--no-anim`), when there's only one image source or when using native
   animation of some render styles.

.. [#]  Frames will not be cached for any animation with more frames than this value.
   Memory usage depends on the frame count **per image**, not this maximum count.

.. [#] The size is multiplied by the scale on respective axes when an image is rendered.
   A scale value must be such that 0.0 < value <= 1.0.

.. [#] Width and height are in units of columns and lines respectively.

   By default (i.e if none of the sizing options is specified), the equivalent of
   :option:`--original-size` is used if not larger than the :term:`available size`,
   else :option:`--fit`.

.. [#] Any event with a level lower than the specified one is not reported.

.. [#] 0 -> worst quality; smallest data size, 95 -> best quality; largest data size.

   By default (i.e when disabled), PNG format is used for re-encoding images,
   which has less compression with better quality. JPEG encoding:

   - reduces render time & image data size and increases drawing speed on the
     terminal's end but at the cost of image quality and color reproduction.
   - is useful for animations with high resolution and/or sparse color distribution.
   - only applies when an image is re-encoded and not read directly from file
     (see :option:`--itnrff`).
   - can only be used for non-transparent images but the transparency status
     of some images can not be correctly determined in an efficient way at render time.

     Thus, to ensure the JPEG format is always used for re-encoded images, disable
     transparency (:option:`--no-alpha`) or set a background color (:option:`-b`).

.. [#] By default, image data is used directly from file when no image manipulation is
   required. Otherwise, it's re-encoded in PNG (or JPEG, if enabled) format.

   The optimization significantly reduces render time when applicable but does not apply
   to animations, native or not.
