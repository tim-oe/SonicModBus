import importlib.metadata

project = "SonicModbus"
author = "tim-oe"
copyright = "2026, tim-oe"
release = importlib.metadata.version("sonic-modbus")

extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx.ext.viewcode",
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
