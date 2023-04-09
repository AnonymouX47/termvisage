Glossary
========

Below are definitions of terms used in the CLI help text, info/warning/error messages and the documentation.

.. note::

   For contributors, some of these terms are also used in the source code, as variable names, in comments, docstrings, etc.

.. glossary::
   :sorted:

   active terminal
      The terminal emulator connected to the first TTY device discovered at startup.

      At times, this may also be used to refer to the TTY device itself.

   alignment
      The position of a primary :term:`render` output within its :term:`padding`.

   horizontal alignment
      The horizontal position of a primary :term:`render` output within its :term:`padding width`.

      .. seealso:: :option:`--h-align`

   vertical alignment
      The vertical position of a primary :term:`render` output within its :term:`padding height`.

      .. seealso:: :option:`--v-align`

   allowance
      The amount of space to be left unused on the terminal screen.

   horizontal allowance
      The amount of **columns** to be left unused on the terminal screen.

      .. seealso:: :option:`--h-allow`

   vertical allowance
      The amount of **lines** to be left unused on the terminal screen.

      .. seealso:: :option:`--v-allow`

   alpha threshold
      Alpha ratio/value above which a pixel is taken as **opaque** (applies only to text-based render styles).

      .. seealso:: :option:`-A`

   animated
      Having multiple frames.
      
      The frames of an animated image are generally meant to be displayed in rapid succession, to give the effect of animation.

   available size
      The remainder after :term:`allowances <allowance>` are subtracted from the maximum frame size.

   available width
      The remainder after horizontal allowance is subtracted from the maximum amount of columns.

   available height
      The remainder after vertical allowance is subtracted from the maximum amount of lines.

   cell ratio
      The **aspect ratio** (i.e the ratio of **width to height**) of a **character cell** on a terminal screen.

      .. seealso:: :ref:`cell-ratio`

   render
   rendered
   rendering
      The process of encoding pixel data into a byte/character **string** (possibly including escape sequences to reproduce colour and transparency).

      This string is also called the **primary** render output and **excludes** :term:`padding`.

   rendered size
      The amount of space (columns and lines) that'll be occupied by a primary :term:`render` output **when drawn (written) onto a terminal screen**.

   rendered width
      The amount of **columns** that'll be occupied by a primary :term:`render` output **when drawn (written) onto a terminal screen**.

   rendered height
      The amount of **lines** that'll be occupied by a primary :term:`render` output **when drawn (written) onto a terminal screen**.

   padding
      Amount of lines and columns within which to fit a primary :term:`render` output.

   padding width
      Amount of **columns** within which to fit a primary :term:`render` output.

      Excess columns on either or both sides of the render output (depending on the :term:`horizontal alignment`) will be filled with spaces.

      .. seealso:: :option:`--pad-width`

   padding height
      Amount of **lines** within which to fit a primary :term:`render` output.

      Excess lines on either or both sides of the render output (depending on the :term:`vertical alignment`) will be filled with spaces.

      .. seealso:: :option:`--pad-height`

   render style
   render styles
   style
   styles
      A specific technique for rendering or displaying pixel data (including images)
      in a terminal emulator. 

      .. seealso:: :ref:`render-styles`

   scale
      The fraction/ratio of an image's size that'll actually be used to :term:`render` it.
      
   source
      The resource from which an image instance is initialized.

      .. seealso:: :ref:`image-sources`

   terminal size
      The amount of columns and lines on a terminal screen at a time i.e without scrolling.

   terminal width
      The amount of columns on a terminal screen at a time.

   terminal height
      The amount of lines on a terminal screen at a time i.e without scrolling.
