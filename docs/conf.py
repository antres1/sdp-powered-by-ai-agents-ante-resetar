"""Sphinx configuration file for Trading Card Game Kata documentation."""

# -- Project information -----------------------------------------------------

project = "Trading Card Game Kata"
copyright = "2026, Ante Resetar"
author = "Ante Resetar"
release = "1.0.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx_wagtail_theme",
    "myst_parser",
    "sphinx_new_tab_link",
]

new_tab_link_show_external_link_icon = True

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_wagtail_theme"

html_theme_options = {
    "project_name": "Trading Card Game Kata",
    "github_url": "https://github.com/antres1/sdp-powered-by-ai-agents-ante-resetar",
    "footer_links": "",
}

html_show_copyright = True
html_last_updated_fmt = "%b %d, %Y"
html_show_sphinx = False

# -- MyST Parser configuration -----------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
]
