import os
import sys
import re
import subprocess

sys.path.insert(0, os.path.abspath("../"))

subprocess.call(["pip", "install", "."], cwd="../")

project = "Kvsqlite"
copyright = "2023, AYMEN Mohammed"
author = "AYMEN Mohammed"

with open("../kvsqlite/__init__.py", "r") as f:
    version = re.findall(r"__version__ = \"(.+)\"", f.read())[0]

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_design",
    "sphinx_copybutton",
]

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

napoleon_use_rtype = False
napoleon_use_param = False

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    # "modules.rst",
    # "kvsqlite.rst",
]
templates_path = ["_templates"]

master_doc = "index"
source_suffix = ".rst"
autodoc_member_order = "bysource"

html_title = "Kvsqlite"
html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_show_sourcelink = True
html_show_copyright = True
html_copy_source = False

autoclass_content = "init"
html_theme_options = {
    "github_url": "https://github.com/AYMENJD/Kvsqlite",
    "header_links_before_dropdown": 4,
    "show_toc_level": 2,
    "show_nav_level": 2,
    # "navbar_align": "left",  # [left, content, right]
    "navbar_center": ["version-switcher", "navbar-nav"],
    "collapse_navigation": True,
    "footer_items": ["copyright"],
    # "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "navbar_persistent": ["search-button"],
    "external_links": [
        {"name": "API", "url": "API.html"},
        {"name": "PyPI", "url": "https://pypi.org/project/kvsqlite"},
    ],
}

html_context = {"default_mode": "auto"}
