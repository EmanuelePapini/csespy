"""
initialization script of csespy package with variables pointing at the cses database
WARNING: this package is configured to worki with CSES data located in fpath.
change variables accordingly should the path to cses data (fpath) change
"""

fpath = '/CSES_Data/CSES01/'

import csespy
from .blombly.tools.objects import AttrDict
import numpy as np
from .blombly import pylab as plt
plt.ion()
cses_inipar = AttrDict()
cses_path = fpath

cses_inipar.cses_path = fpath

