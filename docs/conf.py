import importlib.metadata
import os

project = "SonicModbus"
author = "tim-oe"
copyright = "2026, tim-oe"
release = importlib.metadata.version("sonic-modbus")

extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx.ext.viewcode",
    "sphinx_markdown_builder",
]

# MyST-parser
myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
    "deflist",
]
myst_heading_anchors = 3

# autodoc2 — scans source tree directly (no import needed)
autodoc2_packages = [
    "../sonic_modbus",
]
autodoc2_render_plugin = "myst"
# Override default template (it advertised sphinx-autodoc2 and overwrote apidocs/index.rst each build).
autodoc2_index_template = """\
Module index
============

Public modules and submodules:

.. toctree::
   :titlesonly:
{% for package in top_level %}
   {{ package }}
{%- endfor %}

"""

# Source file handling
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Build output tuned for GitHub wiki markdown export
templates_path = ["_templates"]
html_theme = "alabaster"
html_static_path = ["_static"]

# sphinx-markdown-builder — wiki / GFM output (see sync-wiki.sh)
markdown_flavor = "github"
# Absolute links for GitHub wiki (``markdown_http_base`` on
# https://pypi.org/project/sphinx-markdown-builder/ ). Uses Sphinx docnames (with ``/``).
# ``scripts/sync-wiki.sh`` rewrites those URLs to GitHub wiki slugs (leaf name only).
markdown_http_base = os.environ.get(
    "SONICMODBUS_WIKI_BASE", "https://github.com/tim-oe/SonicModBus/wiki"
)
markdown_uri_doc_suffix = ""
