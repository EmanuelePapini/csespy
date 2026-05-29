# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'csespy'
copyright = '2026, E. Papini, F. M. Follega'
author = 'E. Papini, F. M. Follega'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

from pathlib import Path
import sys
import types

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# RTD checks out the repository under a generic folder name (not necessarily
# ``csespy``). The project source is a flat package at repository root, so we
# register a lightweight package shim named ``csespy`` for autodoc imports.
if 'csespy' not in sys.modules:
    csespy_pkg = types.ModuleType('csespy')
    csespy_pkg.__file__ = str(REPO_ROOT / '__init__.py')
    csespy_pkg.__path__ = [str(REPO_ROOT)]
    sys.modules['csespy'] = csespy_pkg

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Mock imports that are optional or not available in the docs environment
# (prevents autodoc import errors for heavy third-party packages)
autodoc_mock_imports = [
    'hdf5storage',
    'flammkuchen',
    'numpy',
    'scipy',
    'pandas',
    'h5py',
    'matplotlib',
    'cartopy',
    'aacgmv2',
    'skimage',
    'termcolor',
    'numba',
    'csespy.blombly.pylab',
    'blombly.pylab',
]

# Napoleon settings: prefer numpy-style docstrings which this project uses
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

# Generate autosummary pages where requested
autosummary_generate = True

# Enable matplotlib's plot directive only when matplotlib is available.
try:
    import matplotlib  # noqa: F401
except ModuleNotFoundError:
    pass
else:
    extensions += [
        "matplotlib.sphinxext.plot_directive",
    ]

# Register lightweight dummy roles for matplotlib-specific interpreted text
from docutils import nodes
from docutils.parsers.rst.roles import register_local_role

def _dummy_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    return [nodes.inline(text, text)], []

register_local_role('mpltype', _dummy_role)
register_local_role('rc', _dummy_role)



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
# html_theme = 'alabaster'
html_static_path = ['_static']
