from setuptools import setup

classifiers = [
    "Environment :: Console",
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: End Users/Desktop",
    "Operating System :: POSIX :: Linux",
    "Operating System :: MacOS",
    "Operating System :: Android",
    "Operating System :: Microsoft :: Windows :: Windows 10",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Utilities",
    "Topic :: Multimedia :: Graphics :: Viewers",
]

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(
    name="termvisage",
    version="0.2.0-dev",
    author="Toluwaleke Ogundipe",
    author_email="anonymoux47@gmail.com",
    url="https://github.com/AnonymouX47/termvisage",
    description="Display and browse images in the terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    classifiers=classifiers,
    python_requires=">=3.8",
    install_requires=[
        "argcomplete>=2,<4",
        "Pillow>=10.1,<11",
        "term-image>=0.6,<0.7",
        "urwid>=2.1,<3",
    ],
    entry_points={
        "console_scripts": ["termvisage=termvisage.__main__:main"],
    },
    project_urls={
        "Changelog": (
            "https://github.com/AnonymouX47/termvisage/blob/main/CHANGELOG.md"
        ),
        "Documentation": "https://termvisage.readthedocs.io/",
        "Funding": "https://github.com/AnonymouX47/termvisage#donate",
        "Source": "https://github.com/AnonymouX47/termvisage",
        "Tracker": "https://github.com/AnonymouX47/termvisage/issues",
    },
    keywords=[
        "image",
        "terminal",
        "viewer",
        "PIL",
        "Pillow",
        "console",
        "xterm",
        "cli",
        "tui",
        "ANSI",
        "ASCII-Art",
        "kitty",
        "iterm2",
        "sixel",
        "graphics",
    ],
)
