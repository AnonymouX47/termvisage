# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Uppercase letters in hex BG colors being flagged as invalid ([term-image@b4533d5])
- Crash when `"log file"` or `--log-file` specifies a path with a non-stat-able directory ([term-image@8b0af4c]).
- Render style support when multiprocessing is enabled ([1637a38]).

### Removed
- As much private API usage across the CLI and TUI code ([term-image#70]).

[term-image#70]: https://github.com/AnonymouX47/term-image/pull/70
[term-image@b4533d5]: https://github.com/AnonymouX47/term-image/commit/b4533d5697d41fe0742c2ac895077da3b8d889dc
[term-image@8b0af4c]: https://github.com/AnonymouX47/term-image/pull/70/commits/8b0af4cd76c96187b95237e7bcd74ab5b16b2c82
[1637a38]: https://github.com/AnonymouX47/termvisage/commit/1637a388affef84735805ac105b995cb2f25c005


## Pre-0.1
See [term-image] up to [term-image v0.5.0].

[Unreleased]: https://github.com/AnonymouX47/termvisage/commits/main
[term-image v0.5.0]: https://github.com/AnonymouX47/term-image/blob/main/CHANGELOG.md#
[term-image]: https://github.com/AnonymouX47/term-image
