<div align="center">
<h1><b>Term-Image-Viewer</b></h1>
<b>Browse and view images in the terminal</b>
<br>
<img src="https://raw.githubusercontent.com/AnonymouX47/term-image-viewer/main/docs/source/resources/tui.png">

<p align="center">
   <a href='https://pypi.org/project/term-image-viewer/'>
      <img src='https://img.shields.io/pypi/v/term-image-viewer.svg'>
   </a>
   <img src="https://static.pepy.tech/badge/term-image-viewer">
   <a href='https://pypi.org/project/term-image-viewer/'>
      <img src='https://img.shields.io/pypi/pyversions/term-image-viewer.svg'>
   </a>
   <a href='https://github.com/psf/black'>
      <img src='https://img.shields.io/badge/code%20style-black-000000.svg'>
   </a>
   <a href='https://term-image-viewer.readthedocs.io/en/latest/?badge=latest'>
      <img src='https://readthedocs.org/projects/term-image-viewer/badge/?version=latest' alt='Documentation Status' />
   </a>
   <img src="https://img.shields.io/github/last-commit/AnonymouX47/term-image-viewer">
   <a href="https://twitter.com/intent/tweet?text=Display%20and%20browse%20images%20in%20the%20the%20terminal&url=https://github.com/AnonymouX47/term-image-viewer&hashtags=developers,images,terminal,python">
      <img src="https://img.shields.io/twitter/url/http/shields.io.svg?style=social">
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
- [Donate](#donate)


## Installation

### Requirements
- Operating System: Unix / Linux / Mac OS X / Windows (limited support, see the [FAQs](https://term-image-viewer.readthedocs.io/en/latest/faqs.html))
- [Python](https://www.python.org/) >= 3.7
- A terminal emulator with **any** of the following:
  
  - support for the [Kitty graphics protocol](https://sw.kovidgoyal.net/kitty/graphics-protocol/).
  - support for the [iTerm2 inline image protocol](https://iterm2.com/documentation-images.html).
  - full Unicode support and ANSI 24-bit color support

  **Plans to support a wider variety of terminal emulators are in motion** (see [Planned Features](#planned-features)).

### Steps
The latest **stable** version can be installed from [PyPI](https://pypi.python.org/pypi/term-image-viewer) using `pip`:

```shell
pip install term-image-viewer
```

The **development** version can be installed thus:

**NOTE:** it's recommended to install in an isolated virtual environment which can be created by any means.

Clone this repository from within a terminal
```shell
git clone https://github.com/AnonymouX47/term-image-viewer.git
```

then navigate into the local repository
```shell
cd term-image-viewer
```

and run
```shell
pip install .
```


## Features

### CLI/TUI features
- Almost everything the [term-image] library supports
- Display individual images
- Browse multiple images and directories (recursively)
- Adjustable image grids
- Context-based controls
- Customizable controls and configuration options
- Smooth and performant experience
- and more... :grin:


## Demo

Check out the [gallery](https://term-image-viewer.readthedocs.io/en/latest/gallery.html).

[TUI Demo Video](https://user-images.githubusercontent.com/61663146/163809903-e8fb254b-a0aa-4d0d-9fc9-dd676c10b735.mp4)

_\*The video was recorded at normal speed and not sped up._


## Quick Start

With a local image file
```shell
term-image path/to/image.png
```

With an image URL
```shell
term-image https://www.example.com/image.png
```

With a directory, recursively (not currently supported on Windows)
```shell
term-image -r path/to/dir/
```

If a single source is given and it's animated (GIF, APNG, Animated WebP), the animation is infinitely looped by **default** and can be stopped with `Ctrl-C` (`SIGINT`).

By **default**, if multiple sources or at least one directory source is given, the TUI (Terminal User Interface) is launched to navigate through the images and/or directories.


## Usage

<p align="center"><b>
   :construction: Under Construction - There might be incompatible changes between minor versions of <a href='https://semver.org/spec/v2.0.0.html#spec-item-4'>version zero</a>!
</b></p>

### CLI (Command-Line Interface)
Run `term-image --help` to see the full usage info and list of options.

### TUI (Terminal User Interface)
The controls are **context-based** and always displayed at the bottom of the screen.
Pressing the `F1` key (in most contexts) brings up a **help** menu describing the available controls (called *actions*) in that context.

The TUI can be configured using a config file. See the [Configuration](https://term-image-viewer.readthedocs.io/en/latest/config.html) section of the docs.

[Here](https://github.com/AnonymouX47/term-image-viewer/blob/main/vim-style_config.json) is a config file with Vim-style key-bindings (majorly navigation).


## Contribution

If you've found any bug or want to suggest a new feature, please open a new [issue](https://github.com/AnonymouX47/term-image-viewer/issues) with proper description, after browsing/searching through the existing issues and making sure you won't create a duplicate.

For code contributions, please read through the [guidelines](https://github.com/AnonymouX47/term-image-viewer/blob/main/CONTRIBUTING.md).

Also, check out the [Planned Features](#planned-features) section below.
If you wish to work on any of the listed tasks, please click on the linked issue or go through the [issues](https://github.com/AnonymouX47/term-image-viewer/issues) tab and join in on an ongoing discussion about the task or create a new issue if one hasn't been created yet, so that the implementation can be discussed.

Hint: You can filter issues by *label* or simply *search* using the task's name or description.

For anything other than the above (such as questions or anything that would fit under the term "discussion"), please open a new [discussion](https://github.com/AnonymouX47/term-image-viewer/discussions) instead.

Thanks! :heart:


## Planned Features

See [here](https://term-image-viewer.readthedocs.io/en/latest/planned.html).

## Known Issues

See [here](https://term-image-viewer.readthedocs.io/en/latest/issues.html).

## FAQs

See the [FAQs](https://term-image-viewer.readthedocs.io/en/latest/faqs.html) section of the docs.

## Credits

The following projects have been (and are still) crucial to the development of this project:

- [term-image]
- [Urwid](https://urwid.org)

## Donate

Your donation will go a long way in aiding the progress and development of this project.

```
USDT Address: TKP6d3hLcs7i5R18WRFxLe3zsPQcCBS1Ro
Network: TRC20
```
I'm sincerly sorry for any inconviences that may result from the means of donation.

Please bare with me, as usual means of accepting donations are not available in the region of the world where I reside.

Thank you! :heart:


[term-image]: https://github.com/AnonymouX47/term-image
