# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Removed
- Support for Python 3.8. ([a49f442])

[a49f442]: https://github.com/AnonymouX47/term-image/commit/a49f442edef26f97252f610eb4a7b0e5acc6b2b3


## [0.2.0] - 2024-06-25
### Fixed
- tui: Crash on image grid view ([c64f195]).
- cli,tui: Sorting of top-level (command line) entries ([9ea0572]).
- Deadlock upon interruption of the main process when multiprocessing is enabled ([b90ceef]).

### Added
- tui: Thumbnail generation (with deduplication) and caching for the image grid ([#13], [#16]).
  - config: `thumbnail`, `thumbnail cache` and `thumbnail size` config options.
  - args: `--thumbnail/--no-thumbnail` command-line option.
- tui: `Force Render` action to the `menu` context ([#13]).
- tui: Mouse scroll event handling for the image list (menu) ([2354639]).
- tui: Left mouse click handling for non-navigation actions (in the footer) ([#19]).
- tui,config: `show footer` config option to control the TUI footer visibility ([#19]).
- `completions` package installation extra, to install `argcomplete` for shell completions ([1890ab8]).

### Changed
- config,tui: Revamped the *max pixels* setting ([#13]).
  - It is now **opt-in** i.e by default, all images are now rendered regardless of resolution.
  - config: Changed the default value of the `max pixels` config option to `0` (disabled).
  - tui: It no longer applies in the `full-grid-image` context.
  - tui: In the `image-grid` context, images with more pixels than *max pixels* (**if non-zero**) are now distinguished by a yellow title and border.
- tui: Improved grid image rendering performance ([#13], [#16]).
- tui: Improved image grid cell size adjustment ([#15]).
- Exit properly and faster upon interruption ([b90ceef]).
- tui: Redesigned the footer, action bar and actions ([#19]).
- tui: Changed the default symbol for `esc` key from `⎋` (U+238B) to `ESC` ([21b16f3]).
- args: Disallowed abbreviation of CLI long options ([95e77a3]).
- Made the `argcomplete` dependency optional ([1890ab8]).
- logging: Process name is now excluded from log records when multiprocessing is disabled ([b2ccfa7]).

### Removed
- args: `--max-pixels-cli` command-line option ([#13]).

[#13]: https://github.com/AnonymouX47/termvisage/pull/13
[#15]: https://github.com/AnonymouX47/termvisage/pull/15
[#16]: https://github.com/AnonymouX47/termvisage/pull/16
[#19]: https://github.com/AnonymouX47/termvisage/pull/19
[c64f195]: https://github.com/AnonymouX47/termvisage/commit/c64f195a79557fdf5a9323db907a5716a12d6440
[9ea0572]: https://github.com/AnonymouX47/termvisage/commit/9ea0572e6db35984a4ae0af1691edfd179e5d393
[b90ceef]: https://github.com/AnonymouX47/termvisage/commit/b90ceefdd35a23eacb0e7199ea018776e79d7a14
[2354639]: https://github.com/AnonymouX47/termvisage/commit/235463981bad139ae93eeeec1079449d7d40dacf
[21b16f3]: https://github.com/AnonymouX47/termvisage/commit/21b16f3278b912765fb80d729a1f197b82517b9f
[95e77a3]: https://github.com/AnonymouX47/termvisage/commit/95e77a37881565c551dc75697544a4f97fc55b27
[1890ab8]: https://github.com/AnonymouX47/termvisage/commit/1890ab839e36d6fcc55dc1a19c3d1b02b25a7851
[b2ccfa7]: https://github.com/AnonymouX47/termvisage/commit/b2ccfa76f99f4bb9b7ec4aeab05b516286d60991


## [0.1.0] - 2023-06-03
### Fixed
- Uppercase letters in hex BG colors being flagged as invalid ([term-image@b4533d5]).
- Crash when `"log file"` or `--log-file` specifies a path with a non-stat-able directory ([term-image@8b0af4c]).
- [tui] Render style support when multiprocessing is enabled ([1637a38]).
- [tui] Erasure of the last column of images with *iterm2* render style ([5d828d1]).
- [tui] UI Foreground color for terminals with white background ([c1249ce]).
- [tui] Notification bar not hidden when `--quiet` is specified ([1692d6c]).

### Added
- [tui] "About" section within the "Help" overlay ([19b6650]).
- [tui] File name labels to image grid cells ([e64edd4]).
- [tui] Support for terminal synchronized output ([ad059bb]).
- [cli] `--long-help` command-line option for full help message ([d5852e6]).
- [cli] Support for shell completions ([#4]).
  - [argcomplete](https://github.com/kislyuk/argcomplete)>=2,<4 dependency
  - `--completions` command-line option

### Changed
- [config] Changed default value of "log file" config option to `"{$XDG_STATE_HOME}/termvisage/termvisage.log"` ([ab971d6], [cbbd162]).
- [tui] Grid cells are now re-rendered upon window resize ([a244048]).
- [cli] Shortened the output of `--help` command-line option ([d5852e6]).
- [config] Renamed config files from "config.json" to "termvisage.json" ([a23f2fe]).
- Improved startup time when `--quiet` is not specified ([aa05a76]).

### Removed
- As much usage of [term-image] private API ([term-image#70]).
- `--checkers`, `--getters` and `--grid-renderers` command-line options ([#5]).

[term-image#70]: https://github.com/AnonymouX47/term-image/pull/70
[#4]: https://github.com/AnonymouX47/termvisage/pull/4
[#5]: https://github.com/AnonymouX47/termvisage/pull/5
[term-image@b4533d5]: https://github.com/AnonymouX47/term-image/commit/b4533d5697d41fe0742c2ac895077da3b8d889dc
[term-image@8b0af4c]: https://github.com/AnonymouX47/term-image/pull/70/commits/8b0af4cd76c96187b95237e7bcd74ab5b16b2c82
[1637a38]: https://github.com/AnonymouX47/termvisage/commit/1637a388affef84735805ac105b995cb2f25c005
[19b6650]: https://github.com/AnonymouX47/termvisage/commit/19b66509666ae3860d07ff76bbd6c0b7be5663d4
[5d828d1]: https://github.com/AnonymouX47/termvisage/commit/5d828d1d1d3d2436c9b7802712cb42af05bc8be4
[c1249ce]: https://github.com/AnonymouX47/termvisage/commit/c1249ceb78272c33e347a4a48d786a71e2306f02
[e64edd4]: https://github.com/AnonymouX47/termvisage/commit/e64edd4017f98733a2d53d627b7481b5a209937b
[ad059bb]: https://github.com/AnonymouX47/termvisage/commit/ad059bbddc072ad641c4e7d524d2cb1edbf54dce
[ab971d6]: https://github.com/AnonymouX47/termvisage/commit/ab971d6766fe5fa260f9963fbffbca48e10b4d37
[1692d6c]: https://github.com/AnonymouX47/termvisage/commit/1692d6cf453ebeb9629713aaf85b231c4492b9a0
[a244048]: https://github.com/AnonymouX47/termvisage/commit/a2440484b36621138cda853cdcce9faf0ac569e1
[d5852e6]: https://github.com/AnonymouX47/termvisage/commit/d5852e6e5db48d34bc0ea119c54b510924501318
[a23f2fe]: https://github.com/AnonymouX47/termvisage/commit/a23f2fe5d7e2d53d1847dc2bcf2552718c22e7fd
[aa05a76]: https://github.com/AnonymouX47/termvisage/commit/aa05a76c7fff0ad79d9e0ee72e00cef88396163e
[cbbd162]: https://github.com/AnonymouX47/termvisage/commit/cbbd16227eef8a0aefafae908dc8de615f218750


## Pre-0.1
See [term-image] up to [term-image v0.5.0].


[term-image v0.5.0]: https://github.com/AnonymouX47/term-image/blob/main/CHANGELOG.md#050---2023-01-09
[term-image]: https://github.com/AnonymouX47/term-image


[Unreleased]: https://github.com/AnonymouX47/termvisage/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/AnonymouX47/termvisage/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AnonymouX47/termvisage/releases/tag/v0.1.0
