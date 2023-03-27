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
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Utilities",
    "Topic :: Multimedia :: Graphics :: Viewers",
]

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(
    name="term-image-viewer",
    version="0.1.0-dev",
    author="Toluwaleke Ogundipe",
    author_email="anonymoux47@gmail.com",
    url="https://github.com/AnonymouX47/term-image-viewer",
    description="Display and browse images in the terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    classifiers=classifiers,
    python_requires=">=3.7",
    install_requires=["term-image>=0.5,<0.6", "urwid>=2.1,<3.0"],
    entry_points={
        "console_scripts": ["term-image=term_image_viewer.__main__:main"],
    },
    project_urls={
        "Changelog": (
            "https://github.com/AnonymouX47/term-image-viewer/blob/main/CHANGELOG.md"
        ),
        "Documentation": "https://term-image-viewer.readthedocs.io/",
        "Funding": "https://github.com/AnonymouX47/term-image-viewer#donate",
        "Source": "https://github.com/AnonymouX47/term-image-viewer",
        "Tracker": "https://github.com/AnonymouX47/term-image-viewer/issues",
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
