#This files contains simple but useful functions that can be handy (e.g. raised cosines and so on)

import numpy as np



def logn(number,base):
    return np.log(number)/np.log(base)

def raised_cosine(n, endpoint = False):
    """
    returns an array of size n containing a raised cosine from 0 to 1.
    If endpoint == True, then out[n] = 1,
    """
    x=np.arange(float(n))/(n-1) if endpoint else np.arange(float(n))/n
    x = x*np.pi
    return (-np.cos(x) +1)/2
