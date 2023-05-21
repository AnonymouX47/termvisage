# Configuration file for the Sphinx documentation builder.
#
# For the full list of configuration options, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import argparse

from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx_toolbox import confval
from sphinxcontrib import autoprogram, video

# Sets the attributes removed in the CLI Parser section below
from termvisage import parsers  # noqa: F401
from termvisage import __version__

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
project = "TermVisage"
copyright = "2023, Toluwaleke Ogundipe"
author = "Toluwaleke Ogundipe"
release = __version__

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_toolbox.confval",
    "sphinxcontrib.autoprogram",
    "sphinxcontrib.video",
]

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_logo = "resources/logo.png"
html_favicon = "resources/logo.ico"

# -- Options for extensions ----------------------------------------------

# # -- sphinx-intersphinx ----------------------------------------------
intersphinx_mapping = {
    "term_image": ("https://term-image.readthedocs.io/en/stable/", None),
}
intersphinx_disabled_reftypes = ["*"]

# -- Extras -----------------------------------------------------------------

# # -- Custom `confval` ------------------------------------------------------


class ConfigValueSibling(confval.ConfigurationValue.__base__):
    def run(self):
        content = list(self.content)

        # First 5 items for a raw latex directive, next 2 for the synopsis, ...
        content[5:5] = (self.options["synopsis"], "")
        if "valid" in self.options:
            # "default" is always inserted last
            index = (
                7
                + len(self.options.keys() - {"synopsis", "valid"})
                - ("default" in self.options)  # insert before "default" if present
            )
            content[index:index] = (f"| **Valid values:** {self.options['valid']}",)

        self.content = StringList(content)

        return super().run()


class ConfigValue(confval.ConfigurationValue, ConfigValueSibling):
    option_spec = {
        "synopsis": directives.unchanged_required,
        "valid": directives.unchanged_required,
        **confval.ConfigurationValue.option_spec,
    }


confval.ConfigurationValue = ConfigValue

# # -- Custom `video` ------------------------------------------------------


class Video(video.Video):
    def run(self):
        node = super().run()[0]
        node["width"] = "100%"

        return [node]


video.Video = Video

# # -- CLI Parser -----------------------------------------------------------

# Do not strip reST markup
del argparse.ArgumentParser.epilog
del argparse.Action.help
del argparse._ArgumentGroup.description


# Omit `program` directive for shorter references.
# Also, omit program title and description.
def render_rst(title, options, is_program, *args, **kwargs):
    render = _render_rst(title, options, is_program, *args, **kwargs)

    if is_program:
        for _ in range(6):
            next(render)
        while next(render):
            pass
        yield ""

    yield from render


_render_rst = autoprogram.render_rst
autoprogram.render_rst = render_rst
