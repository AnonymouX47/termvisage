# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Uppercase letters in hex BG colors being flagged as invalid ([term-image@b4533d5]).
- Crash when `"log file"` or `--log-file` specifies a path with a non-stat-able directory ([term-image@8b0af4c]).
- [tui] Render style support when multiprocessing is enabled ([1637a38]).
- [tui] Erasure of the last column of images with *iterm2* render style ([5d828d1]).
- [tui] UI Foreground color for terminals with white background ([c1249ce]).

### Changed
- [config] Changed default value of "log file" config option to `"{$XDG_STATE_HOME}/termvisage/log"` ([ab971d6]).

### Added
- [tui] "About" section within the "Help" overlay ([19b6650]).
- [tui] File name labels to image grid cells ([e64edd4]).
- [tui] Support for terminal synchronized output ([ad059bb]).

### Removed
- As much private API usage across the CLI and TUI code ([term-image#70]).

[term-image#70]: https://github.com/AnonymouX47/term-image/pull/70
[term-image@b4533d5]: https://github.com/AnonymouX47/term-image/commit/b4533d5697d41fe0742c2ac895077da3b8d889dc
[term-image@8b0af4c]: https://github.com/AnonymouX47/term-image/pull/70/commits/8b0af4cd76c96187b95237e7bcd74ab5b16b2c82
[1637a38]: https://github.com/AnonymouX47/termvisage/commit/1637a388affef84735805ac105b995cb2f25c005
[19b6650]: https://github.com/AnonymouX47/termvisage/commit/19b66509666ae3860d07ff76bbd6c0b7be5663d4
[5d828d1]: https://github.com/AnonymouX47/termvisage/commit/5d828d1d1d3d2436c9b7802712cb42af05bc8be4
[c1249ce]: https://github.com/AnonymouX47/termvisage/commit/c1249ceb78272c33e347a4a48d786a71e2306f02
[e64edd4]: https://github.com/AnonymouX47/termvisage/commit/e64edd4017f98733a2d53d627b7481b5a209937b
[ad059bb]: https://github.com/AnonymouX47/termvisage/commit/ad059bbddc072ad641c4e7d524d2cb1edbf54dce
[ab971d6]: https://github.com/AnonymouX47/termvisage/commit/ab971d6766fe5fa260f9963fbffbca48e10b4d37


## Pre-0.1
See [term-image] up to [term-image v0.5.0].

[Unreleased]: https://github.com/AnonymouX47/termvisage/commits/main
[term-image v0.5.0]: https://github.com/AnonymouX47/term-image/blob/main/CHANGELOG.md#
[term-image]: https://github.com/AnonymouX47/term-image
