"""
termvisage

Display and browse images in the terminal

Provides:
    1. A CLI to display images from a local filesystem or URLs.
    2. A TUI to browse through images and directories on a local filesystem
       or from URLS.

AUTHOR: Toluwaleke Ogundipe <anonymoux47@gmail.com>
Copyright (c) 2023
"""

__author__ = "Toluwaleke Ogundipe"

version_info = (0, 2, 0)

# Follows https://semver.org/spec/v2.0.0.html
__version__ = ".".join(map(str, version_info[:3]))
if version_info[3:]:
    __version__ += "-" + ".".join(map(str, version_info[3:]))
