import numpy as np

def derivfield(fld,x=None,axis=0,**kwargs):
    """
    Compute the derivative of a field along the dimension dim (first dimension is 0)
    using 2nd order finite differences
    .
    INPUT: 
        fld : multidimensional array with n dimensions.
        axis : index (starts from 0)
              of the dimension along which to perform the derivative: 0<= dim<= n-1.
          x : array, 1D
              grid coordinates along which the derivative is performed
     **kwargs: other arguments that may be specified (e.g. a cutoff frequency to be applied 
               during differentiation
    """
    

    out = np.zeros(np.shape(fld))
    
    if len(out.shape) == 1:
        dif = np.diff(fld)
        if x is None:
            out[1:-1] = (dif[:-1] + dif[1:])/2
            out[0] = dif[0]
            out[-1] = dif[-1]
        else:
            dx =np.diff(x)
            out[1:-1] = (dif[:-1]/dx[:-1] + dif[1:]/dx[1:])/2
            out[0] = dif[0]/dx[0]
            out[-1] = dif[-1]/dx[-1]
        return out
    else:
        dim=axis
        dims = np.arange(np.size(fld.shape))
        dims[-1] = dim
        dims[dim] = np.size(dims) -1
        out = fld.transpose(dims)
        #out = out.reshape((np.prod(fld.shape[:-1]),fld.shape[-1]))
        dif = np.diff(out,axis=-1)
        if x is None:
            out[:,1:-1] = (dif[:,:-1] + dif[:,1:])/2
            out[:,0] = dif[:,0]
            out[:,-1] = dif[:,-1]
        else:
            dx =np.diff(x)
            out[:,1:-1] = (dif[:,:-1]/dx[:-1] + dif[:,1:]/dx[1:])/2
            out[:,0] = dif[:,0]/dx[0]
            out[:,-1] = dif[:,-1]/dx[-1]
        return out.transpose(dims)
    
