Installation
============

Requirements
------------

* Operating System: Unix / Linux / MacOS X / Windows (limited support, see the :doc:`faqs`)
* `Python <https://www.python.org/>`_ >= 3.7
* A terminal emulator with **any** of the following:
  
  * support for the `Kitty graphics protocol <https://sw.kovidgoyal.net/kitty/graphics-protocol/>`_.
  * support for the `iTerm2 inline image protocol <https://iterm2.com/documentation-images.html>`_.
  * full Unicode support and truecolor support

  **Plans to support a wider variety of terminal emulators are in motion**
  (see the `library <https://github.com/AnonymouX47/term-image>`_\'s
  :external+term_image:doc:`planned`).


Steps
-----

The latest version can be installed from `PyPI <https://pypi.org/project/termvisage>`_ using `pipx <https://pypa.github.io/pipx/>`_ with:

.. code-block:: shell

   pipx install termvisage

and upgraded with:

.. code-block:: shell

   pipx upgrade termvisage

.. note:: `pip <https://pip.pypa.io/en/stable/>`_ can also be used but ``pipx`` is recommended.


Supported Terminal Emulators
----------------------------

Some terminals emulators that have been tested to meet the requirements for at least one render style include:

- **libvte**-based terminal emulators such as:

  - Gnome Terminal
  - Terminator
  - Tilix

- Kitty
- Konsole
- iTerm2
- WezTerm
- Alacritty
- Windows Terminal
- MinTTY (on Windows)
- Termux (on Android)

For render style-specific support, see :ref:`render-styles`.

.. note::
   Some terminal emulators support truecolor escape sequences but have a
   256-color palette. This will limit color reproduction.
