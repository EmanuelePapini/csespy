# -*- coding: utf-8 -*-
"""
Created on Wed May 11 12:01:41 2016

@author: Emanuele Papini

This module contains all basic tools (functions /class) I developed
    
"""

import numpy as np



def make_periodic(sig, npoints, window_function = 'raised cosine'):
    """
    """
    
    nn = np.size(sig)
    
    if type(npoints) is int:
        
        if npoints > nn//2: 
            raise ValueError('Error! the number of points used for the periodicization exceeds %d\n'%(nn//2,))
        
        rs = raised_cosine(npoints)
        rs = np.concatenate([rs, np.ones(nn-2*npoints), np.flip(rs)])
    mean = np.mean(sig)
    return (sig - mean) * rs + mean



def raised_cosine(n, endpoint = False):
    """
    returns an array of size n containing a raised cosine from 0 to 1.
    If endpoint == True, then out[n] = 1,
    """
    x=np.arange(float(n))/(n-1) if endpoint else np.arange(float(n))/n
    x = x*np.pi
    return (-np.cos(x) +1)/2


def extend_signal(sig,npad, mode = 'asymw-periodic',npad_raisedcos = None,**kwargs):

    """
    wrapper for numpy.pad

    provides aliases for some modes:

    Parameters
    ----------
    
    npad : int or sequence of ints
        number of points (left and right) to use for the extension

    mode : str (default is 'constant')
        method of extension/padding.
        the modes are the same of numpy.pad.
        additional modes provided by this wrapper are

        'asymw' : correspond to mode = 'reflect', reflect_type='odd'
        'symw'  : correspond to mode = 'reflect', reflect_type='even'
        'asymw-periodic': correspond to 'asymw', but the padded region is multiplied by 
            a raised cosine (plus the mean) to make the signal periodic.
        example:
        >>>a=np.arange(10)
        array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        >>>wextend(a,4,mode = 'symw')
        array([4, 3, 2, 1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5])
        >>>wextend(a,4,mode = 'asymw')
        array([-4, -3, -2, -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12,13])
    
    npad_raisedcos : int or sequence of ints or None
        number of points (from left and right boundary) where to apply the raised cosine.
        If None, then npad = npad_raisedcos 
    """

    npad_rs = npad_raisedcos if npad_raisedcos is not None else npad

    if mode.lower() == 'symw':
        
        return np.pad(sig, npad, mode = 'reflect', reflect_type='even',**kwargs)
    
    if mode.lower() == 'asymw':
        
        return np.pad(sig, npad, mode = 'reflect', reflect_type='odd',**kwargs)

    if mode == 'asymw-periodic':
        
        shape = np.shape(sig)
        new_sig = np.pad(sig, npad, mode = 'reflect', reflect_type='odd',**kwargs) 
        newshape=new_sig.shape
        if len(shape) == 1:
            mean = np.mean(new_sig)
        
            rs = raised_cosine(npad_rs,endpoint=True)
        
            new_sig[0:npad_rs] = (new_sig[0:npad_rs] - mean)*rs +mean
            new_sig[-npad_rs:] = (new_sig[-npad_rs:] - mean)*np.flip(rs) + mean
       
        else:
            new_sig=new_sig.reshape( (np.prod(newshape[0:-1]),newshape[-1]) )
            
            mean = np.mean(new_sig,axis=-1) 
            
            rsl = raised_cosine(npad_rs[-1][0])
            rsr = np.flip(raised_cosine(npad_rs[-1][-1]))
            
            for i in range(new_sig.shape[0]): 
                new_sig[i,0:npad_rs[-1][0]] = (new_sig[i,0:npad_rs[-1][0]] \
                                                - mean[i])*rsl +mean[i]
                new_sig[i,-npad_rs[-1][-1]:] = (new_sig[i,-npad_rs[-1][-1]:] \
                                                - mean[i])*rsr + mean[i]

            new_sig.reshape(newshape)

       
        return new_sig
    
    return np.pad(sig, npad, mode = mode,**kwargs)

def minmax(a):
    return [np.min(a),np.max(a)]


#******************************************************************************
#*******************ARRAYS MANIPULATION TOOLS**********************************
#******************************************************************************


def start_end(x,nparts,use='index'):
    """
    given an array x, it returns a list [np,2] containing the ranges
    over which x can be subdivided in nparts chunks,
    method of subdivision:
        use = 'index' :(default)
            x is divided according to its index, i.e., the output chunks
            have the same size
        use = 'value'
            x is divided according to its value (only for monotonic arrays)
            e.g. if x is a time series, then each chunk will have 
            the same lenght in time but not the same size

    N.B. in the python spirit, [ip,1] == [ip+1,0], since in python x[a:b] 
         contains the indexes from a to b-1
         
    examples of application include dividing a dataset for parallel computing        

    """

    stend =np.zeros([nparts,2],dtype=int)

    nout = len(x)

    if use == 'index':

        stend[:,0]  = np.round(nout/nparts)*np.arange(nparts,dtype=int)
        stend[:,1]  = stend[:,0]+ np.round(nout/nparts)
        stend[-1,-1] = nout

    if use == 'value':

        stend_v = np.zeros([nparts,2],dtype=float)
       
        dt = (x[-1]-x[0])/np.float(nparts)

        for i in range(nparts):
            stend[i,0] = np.where(x >= x[0]+ i*dt)[0][0]
            stend[i,1] = np.where(x >= x[0]+ (i+1)*dt)[0][0]

        stend[-1,-1] = nout
    return stend

def start_end_ND(xyz,nparts,input_type = 'arrays', use='index'):
    """
    given a tuple of len() == N of arrays x,y,z,..., or ranges([xmax,x0,x1],[ymax,y0,y1],...)
    it returns a list of tuples [np,N] containing the ranges
    over which xyz can be subdivided in nparts chunks,
    method of subdivision:
        use = 'index' :(default)
            x is divided according to its index, i.e., the output chunks
            have the same size
        ///use = 'value' NOT IMPLEMENTED FOR ND VERSION
        ///    x is divided according to its value (only for monotonic arrays)
        ///    e.g. if x is a time series, then each chunk will have 
        ///    the same lenght in time but not the same size

    N.B. in the python spirit, [ip,1] == [ip+1,0], since in python x[a:b] 
         contains the indexes from a to b-1
    
    examples of application include dividing a dataset for parallel computing        

    parameters
    ----------
    xyz : tuple of arrays or list
        if input_type == 'arrays' then each tuple element is one array of,e.g. ranges
        if input_type == 'ranges' then each element is a list of 3 elements [xmax,xstart,xend]
        where xmax is the maximum of the range, xstart and xend are the extrema of the (sub)range.

    nparts : int
        number of chunks
    input_type : str
        'arrays' : input are the arrays to be chunked (by index or value)
        'ranges' : input are the ranges to be chunked (by index only)
    use : str
        'index' (implemented) or value (not implemented)

    """

    if input_type == 'arrays':
        if type(xyz) is not tuple: raise ValueError('input must be a tuple of arrays')
        
        ndim = len(xyz)
        shapes = [np.size(xyz[i]) for i in range(ndim)] 
        nout = np.prod(shapes)
        partsize = nout//nparts
        offset_start = 0
    elif input_type == 'ranges':

        ndim = len(xyz)
        shapes = tuple([i[0] for i in xyz])
        offset_start = \
            np.sum([ixyz[1]*np.prod([i[0] for i in xyz[j+1:]]) for j,ixyz in enumerate(xyz[:-1])]) \
            + xyz[-1][1]
        nout = np.prod([i[0] for i in xyz]) - offset_start
        partsize = nout//nparts
        
    stend_multi =np.zeros([nparts,ndim,2],dtype=int)
    stend = np.zeros([nparts,2],dtype=int)

    istart = np.zeros(ndim)
    iend = np.zeros(ndim)
    if use == 'index':
            
        stend[:,0]  = np.round(nout/nparts)*np.arange(nparts,dtype=int)
        stend[:,1]  = stend[:,0]+ np.round(nout/nparts)
        stend[-1,-1] = nout
        stend += offset_start

        dummy =np.copy(stend)
       
        for i in range(ndim-1):
            stend_multi[:,i,:] = dummy//np.prod(shapes[i+1:])
            dummy = dummy%np.prod(shapes[i+1:])
            stend_multi[:,i+1,:] = dummy 




    return stend_multi

def wextend(sig, npad, mode = 'constant', **kwargs):
    """
    wrapper for numpy.pad

    provides aliases for some modes:

    Parameters
    ----------

    mode : str (default is 'constant')
        method of extension/padding.
        the modes are the same of numpy.pad.
        additional modes provided by this wrapper are

        'asymw' : correspond to mode = 'reflect', reflect_type='odd'
        'symw'  : correspond to mode = 'reflect', reflect_type='even'

        example:
        >>>a=np.arange(10)
        array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        >>>wextend(a,4,mode = 'symw')
        array([4, 3, 2, 1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5])
        >>>wextend(a,4,mode = 'asymw')
        array([-4, -3, -2, -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12,13])
    """

    if mode.lower() == 'symw':
        return np.pad(sig, npad, mode = 'reflect', reflect_type='even',**kwargs)
    if mode.lower() == 'asymw':
        return np.pad(sig, npad, mode = 'reflect', reflect_type='odd',**kwargs)

    return np.pad(sig, npad, mode = mode,**kwargs)

def interp1(x,xp,fp,fill_value='extrapolate',**kwargs):
    from scipy.interpolate import interp1d 

    finterp=interp1d(xp,fp,fill_value=fill_value,**kwargs)
    return finterp(x)

def interp1_jumps(xint,x,y,interval):
    """
    interpolate y defined on x to y defined on xint
    if y is a function defined in an domain with interval [a,b] (e.g. from -180 to 180)
    and x is such that y is discontinous (e.g. arcsin), the function removes the jumps 
    before interpolating and restores them afterwards.
    """

    #from numpy import interp as interp1


    yper = y.flatten()

    dy = np.diff(yper)

    intdif = interval[1]-interval[0]

    dymed = np.median(np.abs(dy))
    mask = (dy>dymed)* (dy>intdif*0.51)
    #print(np.sum(mask))
    if np.sum(mask) >0:
        for i in np.where(mask)[0]:
            yper[i+1:] -= np.sign(dy[i])*intdif
            
        return np.mod(interp1(xint,x,yper) - interval[0],intdif) + interval[0]
    else:
        return interp1(xint,x,yper)
        
def remove_jumps(y,interval):
    """
    if y is a function defined in an domain with interval [a,b] (e.g. from -180 to 180)
    and y is discontinous , the function removes the jumps 
    """

    #from numpy import interp as interp1


    yper = y.flatten()

    dy = np.abs(np.diff(yper))

    intdif = interval[1]-interval[0]

    dymed = np.median(np.abs(dy))
    mask = (dy>dymed)* (dy>intdif*0.51)
    dy=np.diff(yper)
    #print(np.sum(mask))
    if np.sum(mask) >0:
        for i in np.where(mask)[0]:
            yper[i+1:] -= np.sign(dy[i])*intdif
            
    return yper 


def add_jumps(y,interval):
    """
    given an input array y, return the array defined in a domain 
    with interval [a,b] (e.g. from -180 to 180)
    by adding jumps that bring y in mod(y-a,b-a)+a.
    i.e. make y leave in a modular set (useful, e.g., to deal with 
    longitude coordinates jumps between +180 and -180 )
    """

    intdif = interval[1]-interval[0]
    
    return np.mod(y - interval[0],intdif) + interval[0]

def find_jumps(y,jump):
    """
    it returns the indices where a 1d array has jumps exceeding the absolute jump value
    parameters:
    -----------
    y : 1D array-like
        the input array
    jump: float
        threshold absolute value of the jump
    """

    return np.where(np.abs(np.diff(y))>jump)

def unfold_periodic(y,interval,*args):

    """
    given an input array y, which is assumed to be periodic in the
    input interval (y in [a,b]), it returns the unfolded array in the interval
    [a-b,a+b], together with the indices to unfold related arrays.

    e.g. assume y is a longitude coordinate defined in [-180,180] and you need
    to unfold it in [-360,360]. This routine does that and return the unfolded
    1D arrays in *args that are assumed to be defined on the support described  
    by the y coordinates.
    N.B. It assumes that y covers the full interval!
    
    """
    yper = y.flatten()

    dy = np.abs(np.diff(yper))

    intdif = interval[1]-interval[0]

    dymed = np.median(np.abs(dy))
    mask = (dy>dymed)* (dy>intdif*0.51)
    ijump = np.arange(np.size(yper)-1)[mask]    

    yper = np.roll(yper,-ijump-1)

    yout = np.concatenate([yper-intdif,yper,yper+intdif])

    if len(args):
        argout = []
        for iarg in args:
            iarg = np.roll(iarg.flatten(),-ijump-1)
            argout.append(np.concatenate([iarg,iarg,iarg]))
        return yout,*tuple(argout)
    return yout



