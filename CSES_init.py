"""
initialization script of csespy package with variables pointing at the cses database
WARNING: this package is configured to work in the server at IAPS.
change variables accordingly should the path to cses database (fpath) change
"""

import csespy
from attrdict import AttrDict
import numpy as np
from .blombly import pylab as plt
plt.ion()
cses_inipar = AttrDict()
fpath = '/CSES_Data/CSES01/'
cses_path = fpath

cses_inipar.cses_path = fpath

