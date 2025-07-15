# Sphinx configuration file for documentation build.
# For details, see: https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

project = "nyp-fyp-chatbot"

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "piccolo_theme"
html_static_path = ["_static"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "piccolo_theme",
    "sphinx.ext.autosummary",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "inherited-members": True,
}
