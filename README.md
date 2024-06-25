<div align="center">

<h1><b>TermVisage</b></h1>

<p>
<img src="https://raw.githubusercontent.com/AnonymouX47/termvisage/23b8b4612e0ac4a167fa92630be63766f7f56e29/docs/source/resources/logo.png" height="200">
</p>

<p>
<b>Browse and view images in the terminal</b>
</p>

<p>
   &#128214; <a href='https://termvisage.readthedocs.io'>Manual</a>
    &#9553; 
   &#128444; <a href='https://termvisage.readthedocs.io/en/latest/gallery.html'>Gallery</a>
</p>

<p>
   <a href='https://pypi.org/project/termvisage/'>
      <img src='https://img.shields.io/pypi/v/termvisage.svg'/>
   </a>
   <a href='https://pepy.tech/project/termvisage'>
      <img src="https://pepy.tech/badge/termvisage/month">
   </a>
   <a href='https://pypi.org/project/termvisage/'>
      <img src='https://img.shields.io/pypi/pyversions/termvisage.svg'/>
   </a>
   <a href='https://github.com/psf/black'>
      <img src='https://img.shields.io/badge/code%20style-black-000000.svg'/>
   </a>
   <a href='https://termvisage.readthedocs.io/en/latest/?badge=latest'>
      <img src='https://readthedocs.org/projects/termvisage/badge/?version=latest' alt='Documentation Status'/>
   </a>
   <img src="https://img.shields.io/github/last-commit/AnonymouX47/termvisage"/>
   <a href="https://twitter.com/intent/tweet?text=Browse%20and%20view%20images%20in%20the%20terminal&url=https://github.com/AnonymouX47/termvisage&hashtags=developers,images,terminal,python">
      <img src="https://img.shields.io/twitter/url/http/shields.io.svg?style=social"/>
   </a>
</p>

</div>


## Contents
- [Installation](#installation)
- [Features](#features)
- [Demo](#demo)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Contribution](#contribution)
- [Planned Features](#planned-features)
- [Known Issues](#known-issues)
- [FAQs](#faqs)
- [Credits](#credits)
- [Sponsor This Project](#sponsor-this-project)


## Installation

### Requirements
- Operating System: Unix / Linux / Mac OS X / Windows (limited support, see the [FAQs](https://termvisage.readthedocs.io/en/latest/faqs.html))
- [Python](https://www.python.org/) >= 3.8
- A terminal emulator with **any** of the following:
  
  - support for the [Kitty graphics protocol](https://sw.kovidgoyal.net/kitty/graphics-protocol/)
  - support for the [iTerm2 inline image protocol](https://iterm2.com/documentation-images.html)
  - Unicode and direct-color (truecolor) support

  **Plans to support a wider variety of terminal emulators are in motion** (see the [library][term-image]'s planned features).

### Steps
The latest version can be installed from [PyPI](https://pypi.org/project/termvisage) using [`pipx`](https://pypa.github.io/pipx/) with:

```shell
pipx install termvisage
```

and upgraded with:

```shell
pipx upgrade termvisage
```

**NOTE:** [`pip`](https://pip.pypa.io/en/stable/) can also be used but `pipx` is recommended.

See the [installation docs](https://termvisage.readthedocs.io/en/stable/installation.html) for info about optional features and more.


## Features

- Almost everything the [term-image] library supports
- Display individual images
- Browse multiple images and directories (recursively)
- Efficient and configurable thumbnailing
- Adjustable image grids
- Context-based controls
- Customizable controls and configuration options
- Smooth and performant experience
- Shell completion for command-line arguments
- and more... 😁


## Demo

![Demo Image](https://github.com/AnonymouX47/termvisage/assets/61663146/beff58d9-fcff-4326-af1f-703e86041402)

### Multiple Render Styles
| block | iterm2 | kitty |
|:-----:|:------:|:-----:|
| ![block style](https://user-images.githubusercontent.com/61663146/233488229-d4d0258c-2567-4b2a-ba38-8546b886fba3.png) | ![iterm2 style](https://user-images.githubusercontent.com/61663146/233488248-8c5750d2-9281-4a96-b0f4-32d61c29b02c.png) | ![kitty style](https://user-images.githubusercontent.com/61663146/233488260-6e7ce3fe-7561-44f7-aafe-d7a708e14758.png) |

### High-Resolution Images
| ![high_res_1](https://github.com/AnonymouX47/termvisage/assets/61663146/acb754f1-30d7-4477-85f3-9688d2aae5da) | ![high_res_2](https://github.com/AnonymouX47/termvisage/assets/61663146/938ccc20-39d4-4f15-8f3e-1960543fd895) |
|:---:|:---:|

### Video Demo
[Demo Video](https://user-images.githubusercontent.com/61663146/235648854-dcccd260-c463-4692-bd01-f51c099613cf.mp4)

### Gallery
Check out the [Gallery](https://termvisage.readthedocs.io/en/latest/gallery.html) for more.


## Quick Start

With a file path:
```shell
termvisage path/to/image.png
```

With a URL:
```shell
termvisage https://www.example.com/image.png
```

With a directory, recursively (not currently supported on Windows):
```shell
termvisage -r path/to/dir/
```

If a single source is given and it's animated (GIF, APNG, Animated WebP), the animation is infinitely looped by **default** and can be stopped with `Ctrl-C` (`SIGINT`).

By **default**, if multiple sources or at least one directory source is given, the TUI (Terminal User Interface) is launched to navigate through the images and/or directories.


## Usage

### CLI (Command-Line Interface)
Run ``termvisage --help`` to see the basic help message or ``termvisage --long-help`` for the full help message.

See the [CLI manual](https://termvisage.readthedocs.io/en/latest/cli.html).

### TUI (Terminal User Interface)
The controls are **context-based** and always displayed at the bottom of the screen.
Pressing the `F1` key (in most contexts) brings up a **help** menu describing the available controls (called *actions*) in that context.

The TUI can be configured using a config file. See the [Configuration](https://termvisage.readthedocs.io/en/latest/config.html) section of the docs.

[Here](https://github.com/AnonymouX47/termvisage/blob/main/vim_style-termvisage.json) is a config file with Vim-style key-bindings (majorly navigation).

See the [TUI manual](https://termvisage.readthedocs.io/en/latest/tui.html).


## Contribution

If you've found any bug or want to suggest a new feature, please open a new [issue](https://github.com/AnonymouX47/termvisage/issues) with proper description, after browsing/searching through the existing issues and making sure you won't create a duplicate.

For code contributions, please read through the [guidelines](https://github.com/AnonymouX47/termvisage/blob/main/CONTRIBUTING.md).

Also, check out the [Planned Features](#planned-features) section below.
If you wish to work on any of the listed tasks, please click on the linked issue or go through the [issues](https://github.com/AnonymouX47/termvisage/issues) tab and join in on an ongoing discussion about the task or create a new issue if one hasn't been created yet, so that the implementation can be discussed.

Hint: You can filter issues by *label* or simply *search* using the task's name or description.

For anything other than the above (such as questions or anything that would fit under the term "discussion"), please open a new [discussion](https://github.com/AnonymouX47/termvisage/discussions) instead.

Thanks! 💓


## Planned Features

See [here](https://termvisage.readthedocs.io/en/latest/planned.html).

## Known Issues

See [here](https://termvisage.readthedocs.io/en/latest/issues.html).

## FAQs

See the [FAQs](https://termvisage.readthedocs.io/en/latest/faqs.html) section of the docs.

## Credits

The following projects have been (and are still) crucial to the development of this project:
- [term-image] by [@AnonymouX47](https://github.com/AnonymouX47)
- [Pillow](https://python-pillow.org) by [Fredrik Lundh, Jeffrey A. Clark (Alex) and contributors](https://github.com/python-pillow/Pillow/graphs/contributors)
- [Urwid](https://urwid.org) by [Ian Ward et al](https://github.com/urwid/urwid/graphs/contributors)
- [argcomplete](https://github.com/kislyuk/argcomplete) by [Andrey Kislyuk](https://github.com/kislyuk)

The logo was composed using resource(s) from the following source(s):
- [Gallery icons created by Andrean Prabowo - Flaticon](https://www.flaticon.com/free-icons/gallery)

Thanks to [@digitallyserviced](https://github.com/digitallyserviced) for the project name and logo concept.

## Sponsor This Project

<a href="https://www.buymeacoffee.com/anonymoux47" target="_blank">
   <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

Any amount will go a long way in aiding the progress and development of this project.
Thank you! 💓


[term-image]: https://github.com/AnonymouX47/term-image
