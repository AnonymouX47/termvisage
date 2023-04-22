<div align="center">

<h1><b>TermVisage</b></h1>

<p>
<img src="https://user-images.githubusercontent.com/61663146/233754936-87265eef-f6be-4046-98c5-44b778470b29.png">
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
   <img src="https://static.pepy.tech/badge/termvisage"/>
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
   <a href="https://twitter.com/intent/tweet?text=Display%20and%20browse%20images%20in%20the%20the%20terminal&url=https://github.com/AnonymouX47/termvisage&hashtags=developers,images,terminal,python">
      <img src="https://img.shields.io/twitter/url/http/shields.io.svg?style=social"/>
   </a>
</p>

</div>


> # 🚧 WIP 🚧
>
> In the mean time, install with:
> ```shell
> pipx install "term-image==0.5.*"
> ```


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
- Operating System: Unix / Linux / Mac OS X / Windows (limited support, see the [FAQs](https://termvisage.readthedocs.io/en/latest/faqs.html))
- [Python](https://www.python.org/) >= 3.7
- A terminal emulator with **any** of the following:
  
  - support for the [Kitty graphics protocol](https://sw.kovidgoyal.net/kitty/graphics-protocol/).
  - support for the [iTerm2 inline image protocol](https://iterm2.com/documentation-images.html).
  - full Unicode support and ANSI 24-bit color support

  **Plans to support a wider variety of terminal emulators are in motion** (see the [library][term-image]'s planned features).

### Steps
The latest version can be installed from [PyPI](https://pypi.org/project/termvisage) with:

```shell
pipx install termvisage
```

and upgraded with:

```shell
pipx upgrade termvisage
```

**NOTE:** `pip` can also be used but `pipx` is recommended.


## Features

### CLI/TUI features
- Almost everything the [term-image] library supports
- Display individual images
- Browse multiple images and directories (recursively)
- Adjustable image grids
- Context-based controls
- Customizable controls and configuration options
- Smooth and performant experience
- and more... 😁


## Demo

<video autoplay loop poster="https://user-images.githubusercontent.com/61663146/233754936-87265eef-f6be-4046-98c5-44b778470b29.png" src="https://user-images.githubusercontent.com/61663146/233754941-7d5e5205-6a4e-4743-9518-6ac4c6b3fb92.mp4" width="100%">TUI Demo Video</video>

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
Run `termvisage --help` to see the full usage info and list of options.

See the [CLI manual](https://termvisage.readthedocs.io/en/latest/cli.html).

### TUI (Terminal User Interface)
The controls are **context-based** and always displayed at the bottom of the screen.
Pressing the `F1` key (in most contexts) brings up a **help** menu describing the available controls (called *actions*) in that context.

The TUI can be configured using a config file. See the [Configuration](https://termvisage.readthedocs.io/en/latest/config.html) section of the docs.

[Here](https://github.com/AnonymouX47/termvisage/blob/main/vim-style_config.json) is a config file with Vim-style key-bindings (majorly navigation).

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

- [term-image]
- [Urwid](https://urwid.org)

Thanks to [**@digitallyserviced**](https://github.com/digitallyserviced) for the project name. (Yeah, I totally suck at naming things 🥲)

## Donate

Your donation will go a long way in aiding the progress and development of this project.

```
USDT Address: TKP6d3hLcs7i5R18WRFxLe3zsPQcCBS1Ro
Network: TRC20
```
I'm sincerly sorry for any inconviences that may result from the means of donation.

Please bare with me, as usual means of accepting donations are not available in the region of the world where I reside.

Thank you! 💓


[term-image]: https://github.com/AnonymouX47/term-image
