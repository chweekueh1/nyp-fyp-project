# Configuration file for the Sphinx documentation builder.
"""
Sphinx configuration for NYP FYP CNC Chatbot documentation.

This file sets up paths, extensions, and build options for generating the project documentation.
"""
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
print(f"[conf.py] sys.path for Sphinx: {sys.path}")

# -- Project information -----------------------------------------------------
project = "NYP FYP CNC Chatbot"
copyright = "2024, bladeacer, chweekueh1"
author = "bladeacer, chweekueh1"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.githubpages",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.napoleon",  # For Google-style docstrings
]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
    "inherited-members": True,
    "private-members": False,
    "show-source": True,
    "imported-members": True,
    "ignore-module-all": True,
    "no-index": False,  # Allow indexing of duplicate objects
}

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/.ruff_cache",
    "**/__pycache__",
    "**/*.pyc",
    "**/.git",
    "**/venv",
    "**/.env",
]

# -- Options for HTML output -------------------------------------------------
html_theme = "piccolo_theme"
html_static_path = ["_static"]

# Set light theme as default
html_theme_options = {
    # "color_scheme": "light",  # Removed: unsupported by piccolo_theme
}

# Suppress warnings
suppress_warnings = [
    "autosectionlabel.*",
    "toc.not_readable",
    "ref.python",
    "docutils",
    "autodoc.*",
    "intersphinx.*",
    "ref.ref",
    "ref.confval",
]

# -- Options for autodoc ----------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
    "inherited-members": True,
    "private-members": False,
    "show-source": True,
    "imported-members": True,
    "ignore-module-all": True,
    "no-index": False,  # Allow indexing of duplicate objects
}

# -- Options for intersphinx -------------------------------------------------
# Disable external inventories that are failing to speed up build
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}

# -- Options for todo -------------------------------------------------------
todo_include_todos = True


# -- Options for viewcode ---------------------------------------------------
viewcode_follow_imports = True

# -- Options for autodoc type hints -----------------------------------------
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
autodoc_typehints_format = "short"
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"
autodoc_default_flags = ["members", "undoc-members", "show-inheritance"]
autodoc_docstring_signature = True
autodoc_preserve_defaults = True
autodoc_inherit_docstrings = True
autodoc_show_inheritance = True
autodoc_show_sourcelink = True

# Handle duplicate object descriptions
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
    "inherited-members": True,
    "private-members": False,
    "show-source": True,
    "imported-members": True,
    "ignore-module-all": True,
    "no-index": False,  # Allow indexing of duplicate objects
}

# -- Options for Napoleon (Google-style docstrings) -------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True  # Enable NumPy style as well
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_preprocess_types = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Options for docstring parsing ------------------------------------------
# Enable parsing of both Google and Sphinx style docstrings
autodoc_docstring_signature = True
autodoc_preserve_defaults = True
autodoc_inherit_docstrings = True
autodoc_show_inheritance = True
autodoc_show_sourcelink = True

# Configure docstring parsing to handle both styles
autodoc_default_options.update(
    {
        "docstring-options": "google,sphinx",
        "docstring-signature": True,
    }
)
autodoc_mock_imports = [
    "gradio",
    "langchain",
    "langchain_openai",
    "langchain_core",
    "langgraph",
    "openai",
    "numpy",
    "pandas",
    "PIL",
    "pydub",
    "pytz",
    "nltk",
    "sklearn",
    "chromadb",
    "sentence_transformers",
]
