
from pylab import *
#import matplotlib as mpl
#
#cm = mpl.cm
#plt.style.use('classic')
#plt.tick_params(axis='both',which='both',direction='in',bottom=True, top=True, left=True, right=True)

mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['ytick.direction'] = 'in'
mpl.rcParams['xtick.top'] = True
mpl.rcParams['ytick.right'] = True
mpl.rcParams['xtick.minor.top'] = True
mpl.rcParams['ytick.minor.right'] = True
mpl.rcParams['xtick.minor.visible'] = True
mpl.rcParams['ytick.minor.visible'] = True


mpl.rcParams['font.size'] = 12
mpl.rcParams['font.family'] = 'STIXGeneral'

#mpl.rcParams['mathtext.fontset'] = 'cm'
mpl.rcParams['mathtext.fontset'] = 'stix' #custom
mpl.rcParams['mathtext.bf'] = 'STIXGeneral:bold:italic'
mpl.rcParams['mathtext.it'] = 'STIXGeneral:italic'
mpl.rcParams['mathtext.rm'] = 'STIXGeneral'


import __main__
if hasattr(__main__,"use_amsmath"):
    use_amsmath=__main__.use_amsmath
else:
    use_amsmath=False 


if use_amsmath:
    mpl.rcParams['text.usetex'] = True
    plt.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}']


#mpl.rcParams['font.family'] = 'Dejavu Sans'
#mpl.rcParams['font.serif'] = 'Times New Roman'
#print(len(plt.style.available))
#pst=plt.style.available[22]
#plt.style.use(pst) #6 is default
#print(pst)
#from scipy.io import readsav
#import numpy as np
plt.tick_params(axis='both',which='both',direction='in',bottom=True, top=True, left=True, right=True)

def get_figure(fig=None,ax=None):
    if fig is None:
        return subplots()
    if ax is None:
        ax = fig.add_subplot()
        return fig,ax
    return fig,ax
