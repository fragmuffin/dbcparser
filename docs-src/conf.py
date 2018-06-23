# -*- coding: utf-8 -*-
#
# dbcparser documentation build configuration file, created by
# sphinx-quickstart on Thu Nov 16 13:21:56 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from distutils.version import LooseVersion
import re

sys.path.insert(0, os.path.abspath(os.path.join('..', 'src')))

# --- Import documented libs
import dbcparser


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx.ext.githubpages',
    'sphinx.ext.mathjax',  # examples to get started: https://en.wikipedia.org/wiki/Help:Displaying_a_formula#Examples_of_implemented_TeX_formulas
    'sphinx.ext.todo',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = dbcparser.__title__
copyright = re.sub(r'^copyright\s*', '', dbcparser.__copyright__, flags=re.I)
author = dbcparser.__author__

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The full version, including alpha/beta/rc tags.
release = unicode(dbcparser.__version__)
# The short X.Y version.
version = u'.'.join(str(i) for i in LooseVersion(release).version[:2])

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'classic'
html_theme = 'sphinx_rtd_theme'  # same as cadquery

# Logo
#html_logo = "_static/logos/dbcparser/light.svg"
#html_logo = "_static/logos/dbcparser/dark.svg"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'dbcparserdoc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'dbcparser.tex', u'dbcparser Documentation',
     u'Peter Boin', 'manual'),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'dbcparser', u'dbcparser Documentation',
     [author], 1)
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'dbcparser', u'dbcparser Documentation',
     author, 'dbcparser', 'Controller Area Network (CAN) DBC file parser for Python',
     'Miscellaneous'),
]



# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/', None),
}

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# TODO: show todo lists
todo_include_todos = True


def custom_noskip():
    NOSKIP = {
        'instancemethod': (
            '__init__',
            '__add__', '__sub__',
            '__mul__', '__div__',
            '__call__',
        ),
    }

    def callback(app, what, name, obj, skip, options):
        if name in NOSKIP.get(type(obj).__name__, []) and obj.__doc__:
            return False
        return None

    return callback


def setup(app):
    # Custom Style-sheet (effectively inherits from theme, andn overrides it)
    app.add_stylesheet('css/custom.css')

    # Custom skip mapping
    app.connect("autodoc-skip-member", custom_noskip())
