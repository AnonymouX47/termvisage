# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import argparse

from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx_toolbox import confval

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

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_toolbox.confval",
    "sphinxcontrib.autoprogram",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = []

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []


# -- Options for extensions ----------------------------------------------

# # -- sphinx-intersphinx ----------------------------------------------
intersphinx_mapping = {
    "term_image": ("https://term-image.readthedocs.io/en/v0.6.0/", None),
}
intersphinx_disabled_reftypes = ["*"]


# -- Others options ----------------------------------------------------------
toc_object_entries = False


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

# # -- CLI Parser (do not strip reST markup) -------------------------------------
del argparse.ArgumentParser.epilog
del argparse.Action.help
del argparse._ArgumentGroup.description
