"""Sphinx configuration."""
project = "Thymed"
author = "Benjamin Crews"
copyright = "2022, Benjamin Crews"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
