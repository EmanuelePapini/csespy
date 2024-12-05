import numpy as np
def running_mean1D(f,n,bc_type = 'None',meantype = 'standard'):
    """
    Compute the walking mean of f in n steps
    
    Parameters
    ----------
        bc_type : str, optional
            boundary condition to use (default 'None')
            {'None','periodic'}
    
        meantype : str, optional
            'standard': standard running average
            'neighbor': calculate the average using the neighbor points only
                        not the ith point, i.e.
                        mean[i] = sum_{k=i-n/2}^{i+n/2}(1-d_ij)*f[k] / (n-1)
    """

    ntot = np.size(f)

    n2 = int(n/2)

    y = np.ndarray(ntot)

    #boundary points
    if bc_type.lower() == 'none' :
        for i in range(n2):
            y[i]  = np.mean(f[0:2*i+1])
            y[-i-1] = np.mean(f[-(2*i+1):])

    if bc_type.lower() == 'periodic':

        for i in range(n2):
            y[i] = np.mean(np.roll(f, n2-i)[0:2*n2+1])
            y[-i-1] = np.mean(np.roll(f,-n2+i)[-(2*n2+1):])


    for i in range(n2,ntot-n2,1):
        y[i] = np.mean(f[i-n2:i+n2+1])

    if meantype == 'neighbor':
        y = (y*(2*n2+1) - f)/(2*n2)

    return y

