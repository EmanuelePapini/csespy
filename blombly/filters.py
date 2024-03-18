from numba import jit
import numpy as np

#HAMPEL FILTER
@jit(nopython=True)
def hampel_filter_forloop_numba(input_series, window_size, n_sigmas=3):
    """
    Apply the Hampel filter to a 1D input time series.
    
    Parameters:
    -----------
    input_series : 1D array-type
        input time series
    window_size : int
        half-size (radius) of the sliding window. Given a point
        input_series[i], the median and MAD are computed on a stencil
        i-window_size:i+window_size
    
    
    N.B. probably needs to be numba-optimized
    """
    n = len(input_series)
    new_series = np.copy(input_series)

    k = 1.4826 # scale factor for Gaussian distribution
    indices = []
    
    for i in range((window_size),(n - window_size)):
        x0 = np.nanmedian(input_series[(i - window_size):(i + window_size + 1)])
        S0 = k * np.nanmedian(np.abs(input_series[(i - window_size):(i + window_size + 1)] - x0))
        if (np.abs(input_series[i] - x0) > n_sigmas * S0):
            new_series[i] = x0
            indices.append(i)
    
    return new_series, indices

def hampel_filter(input_series, window_size, n_sigmas=3, use_mean = False):
    
    n = len(input_series)
    new_series = input_series.copy()
    k = 1.4826 # scale factor for Gaussian distribution
    indices = []
    
    for i in range((window_size),(n - window_size)):
        x0 = np.nanmedian(input_series[(i - window_size):(i + window_size + 1)])
        S0 = k * np.nanmedian(np.abs(input_series[(i - window_size):(i + window_size + 1)] - x0))
        if (np.abs(input_series[i] - x0) > n_sigmas * S0):
            if use_mean:
                new_series[i] = (np.sum(input_series[(i - window_size):i])+\
                np.sum(input_series[i+1:i + window_size + 1]))/(2*window_size)
            else:
                new_series[i] = x0
            indices.append(i)
    
    return new_series, indices

def highpass_filt(fld, icut, kind='circle', method='fft'):
    """
    high pass filtering function for a N-dimensional scalar field fld
    INPUT:
        fld : np.ndarray of dimension N
        icut: int
            integer wavenumber defining the radius of the filter (in units of the smallest contained wavenumber)
    OPTIONAL:
        kind : str (DEFAULT 'circle')
            defines the shape of the filtering interval ("circle" = hypersphere, "square" = hypercube)
            only circle has been implemented so far

    NOTES:
        the version actually implemented is very much memory consuming. This should not be an issue until the "fld" array
        is a small fraction of the total memory
    """

    import numpy as np

    ndim=len(fld.shape)
    kk = [np.fft.fftfreq(i,d=1/i)**2 for i in fld.shape]
    
    kk = np.meshgrid(*kk)
    #isotropizing
    kr = np.zeros(fld.shape)

    for ik in kk:
        kr = kr + ik
    kr = np.sqrt(kr)

    fat = np.fft.ifftn(fld)
    fat[kr<icut] = 0.    

    return np.fft.fftn(fat)

def lowpass_filt(fld, icut, kind='circle', method='fft'):
    """
    low-pass filtering function for a N-dimensional scalar field fld
    INPUT:
        fld : np.ndarray of dimension N
        icut: int
            integer wavenumber defining the radius of the filter (in units of the smallest contained wavenumber)
    OPTIONAL:
        type : str (DEFAULT 'circle')
            defines the shape of the filtering interval ("circle" = hypersphere, "square" = hypercube)
            only circle has been implemented so far

    NOTES:
        the version actually implemented is very much memory consuming. This should not be an issue until the "fld" array
        is a small fraction of the total memory
    """

    import numpy as np

    ndim=len(fld.shape)
    if kind == 'circle':
        kk = [np.fft.fftfreq(i,d=1/i)**2 for i in fld.shape]
    
        kk = np.meshgrid(*kk)
        #isotropizing
        kr = np.zeros(fld.shape)

        for ik in kk:
            kr = kr + ik
        kr = np.sqrt(kr)
        mask = kr>icut
    elif kind == 'square':
        kk = [np.fft.fftfreq(i,d=1/i)**2>icut**2 for i in fld.shape]
        mask = np.sum(kk,axis=0,dtype=bool)
    
    fat = np.fft.ifftn(fld)
    fat[mask] = 0.    

    return np.fft.fftn(fat)


def threshold_denoise(fld, factor = 1 ,sigmalogn= True, verbose = False):
    """
    Denoise a field by removing the small scale noise assuming it follows a gaussian statistics
    """

    import numpy as np

    fld = np.array(fld) #if not hasattr(fld,'dtype') else fld
    fac = factor
    #calculating guessed treshold eps_0
    eps_i = np.sqrt(2*np.log(np.size(fld)))*np.std(fld)*fac


    if fld.dtype == np.complex:
        sig_r = threshold_denoise(np.real(fld),factor)
        sig_i = threshold_denoise(np.imag(fld),factor)
        return sig_r +1j*sig_i
    
    k= np.abs(fld) <= eps_i
    
    if not k.any() :
    	return fld
    	
    nn=fld.size 
    i=0
    while nn != np.sum(k) :
        nn=np.sum(k) 

        eps_i = fld[k].std() *np.sqrt(2*np.log(nn))*fac if sigmalogn else fld[k].std() *fac
        
        k = np.abs(fld) <= eps_i
        i+=1

    if verbose:
        print('# iterations: %d, final treshold: %f'%(i, eps_i))
        print('# noise coefficients: %d %f%%'%(nn,float(nn)/fld.size*100.))

    signal=np.copy(fld) ; signal[k]=0
    
    return signal
    

def fft_denoise(fld,**kwargs):
    from numpy.fft import fftn,ifftn 
    from numpy import real
    sig=threshold_denoise(fftn(fld),**kwargs)
    return real(ifftn(sig))

#def threshold_meanplussigma_filter(fld,factor = 2, verbose = False,binarize = False):
#    """
#    Filter out a field by setting to nan the grid points below the mean plus two sigma the final iteration
#    """
#
#    import numpy as np
#
#    fld = np.array(fld) #if not hasattr(fld,'dtype') else fld
#    fac = factor
#    mean = fld.mean()
#    std = np.std(fld)
#    #calculating guessed treshold eps_0
#    eps_i = np.std(fld)*fac + mean
#
#    k= fld <= eps_i
#    
#    if not k.any() :
#    	return fld 
#    	
#    nn=fld.size 
#    i=0
#    while nn != np.sum(k) :
#        nn=np.sum(k) 
#
#        eps_i = fld[k].std() *fac +fld[k].mean()        
#        
#        k = fld <= eps_i
#        i+=1
#
#    if verbose:
#        print('# iterations: %d, final treshold: %f, mean: %f'%(i, eps_i,mean))
#        print('# noise coefficients: %d %f%%'%(nn,float(nn)/fld.size*100.))
#
#    signal=np.copy(fld)+ mean ; signal[k]=np.nan
#    if binarize:
#        signal[np.isfinite(signal)] = 1
#        signal[~np.isfinite(signal)] = 0
#    return signal

def threshold_meanplussigma_filter(fld,factor = 2, verbose = False,binarize = False,\
        plot = True,return_threshold=False):
    """
    Filter out a field by setting to nan the grid points below the mean plus two sigma the final iteration
    """

    import numpy as np

    fld = np.array(fld) #if not hasattr(fld,'dtype') else fld
    
    fac = factor
    mean = fld.mean()
    std = np.std(fld)
    #calculating guessed treshold eps_0
    eps_i = std*fac + mean

    k= fld <= eps_i
   
    kfld = fld[k]
    if kfld.size == fld.size :
    	return fld 
    
    eps = [eps_i]
    nn=fld.size 
    i=0
    while nn != kfld.size :
        nn=kfld.size 

        mean = kfld.mean()
        std = kfld.std()
        eps_i = std *fac + mean
        
        k = kfld <= eps_i
        i+=1
        eps.append(eps_i)
        kfld = kfld[k]
              
    if verbose:
        print('# iterations: %d, final treshold: %f, mean: %f'%(i, eps_i,mean))
        print('# noise coefficients: %d %f%%'%(nn,float(nn)/fld.size*100.))
    
    if plot:
        import pylab as plt
        plt.ion()
        plt.plot(eps,'bo')
        plt.axhline(eps_i)

    signal=np.copy(fld) ; signal[signal<=eps_i]=np.nan
    if binarize:
        signal[np.isfinite(signal)] = 1
        signal[~np.isfinite(signal)] = 0
    return signal if not return_threshold else signal, eps_i


def fif_lowfilter(f,M,tol = 1e-18, preprocess='extend-periodic', \
    verbose = False,MaxInner=200,delta=0.001,BCmode='clip',\
    wshrink=0,npad_raisedcos = None):
    
    from numpy import linalg as LA
    from .prefixed_double_filter import MM
    def get_mask_v1_1(y, k,verbose,tol):
        """
        Rescale the mask y so that its length becomes 2*k+1.
        k could be either an integer or a float.
        y is the area under the curve for each bar
        
        wrapped from FIF_v2_13.m
        
        """
        n = np.size(y)
        m = (n-1)//2
        k = int(k)
    
        if k<=m:
    
            if np.mod(k,1) == 0:
                
                a = np.zeros(2*k+1)
                
                for i in range(1, 2*k+2):
                    s = (i-1)*(2*m+1)/(2*k+1)+1
                    t = i*(2*m+1)/(2*k+1)
    
                    s2 = np.ceil(s) - s
    
                    t1 = t - np.floor(t)
    
                    if np.floor(t)<1:
                        print('Ops')
    
                    a[i-1] = np.sum(y[int(np.ceil(s))-1:int(np.floor(t))]) +\
                             s2*y[int(np.ceil(s))-1] + t1*y[int(np.floor(t))-1]
            else:
                new_k = int(np.floor(k))
                extra = k - new_k
                c = (2*m+1)/(2*new_k+1+2*extra)
    
                a = np.zeros(2*new_k+3)
    
                t = extra*c + 1
                t1 = t - np.floor(t)
    
                if k<0:
                    print('Ops')
                    a = []
                    return a
    
                a[0] = np.sum(y[:int(np.floor(t))]) + t1*y[int(np.floor(t))-1]
    
                for i in range(2, 2*new_k+3):
                    s = extra*c + (i-2)*c+1
                    t = extra*c + (i-1)*c
                    s2 = np.ceil(s) - s
                    t1 = t - np.floor(t)
    
                    a[i-1] = np.sum(y[int(np.ceil(s))-1:int(np.floor(t))]) +\
                             s2*y[int(np.ceil(s))-1] + t1*y[int(np.floor(t))-1]
                t2 = np.ceil(t) - t
    
                a[2*new_k+2] = np.sum(y[int(np.ceil(t))-1:n]) + t2*y[int(np.ceil(t))-1]
    
        else: # We need a filter with more points than MM, we use interpolation
            dx = 0.01
            # we assume that MM has a dx = 0.01, if m = 6200 it correspond to a
            # filter of length 62*2 in the physical space
            f = y/dx
            dy = m*dx/k
            # b = np.interp(list(range(1,int(m+1),m/k)), list(range(0,int(m+1))), f[m:2*m+1])
            b = np.interp(np.linspace(0,m,int(np.ceil(k+1))), np.linspace(0,m,m+1), f[m:2*m+1])
    
            a = np.concatenate((np.flipud(b[1:]), b))*dy
    
            if abs(LA.norm(a,1)-1)>tol:
                if verbose:
                    print('\n\n Warning!\n\n')
                    print(' Area under the mask equals %2.20f\n'%(LA.norm(a,1),))
                    print(' it should be equal to 1\n We rescale it using its norm 1\n\n')
                a = a/LA.norm(a,1)
            
        return a


    def compute_imf_fft(f,a):
        """
        Extracts the imf from the signal f using the window function (mask) a,
        according to the settings specified in the options dict
        
        N.B. This calculation is done via convolution of f with a in Fourier space,
        using scipy.signal.fftconvolve
        
        mandatory keyword in options:
        'delta' : minimum difference in the 2norm between the two iterations
        'MaxInner': maximum number of iterations
        'verbose' : verbosity level 
        """

        from scipy.signal import fftconvolve

        h = np.array(f)
        h_ave = np.zeros(len(h))

        kernel = a
        BCmod = BCmode

        inStepN = 0
        SD = 1.

        Nh = len(h)
        while SD>delta and inStepN<MaxInner:
            inStepN += 1
            if BCmod == 'wrap':
                h_ave = fftconvolve1D(h,kernel)
            else:
                h_ave = fftconvolve(h,kernel,mode='same')
            #computing norm
            SD = LA.norm(h_ave)**2/LA.norm(h)**2
            h[:] = h[:] - h_ave[:]
            h_ave[:] = 0
            if verbose:
                print('(fft): %2.0d      %1.40f          %2.0d\n' % (inStepN, SD, np.size(a)))



        if verbose:
            print('(fft): %2.0d      %1.40f          %2.0d\n' % (inStepN, SD, np.size(a)))

        return h,inStepN,SD


    in_f = f
    wsh = 0
    if preprocess == 'make-periodic':
        print('\nmaking input signal periodic...')
        from .tools.arrays import make_periodic

        if wshrink == 0 : wshrink = in_f.size//4

        in_f = make_periodic(in_f,wshrink)

        wsh = 0
    elif preprocess == 'extend-periodic':
        print('\nextending input signal (asymmetric-periodic)...')

        from .tools.arrays import extend_signal

        if wshrink == 0 : wshrink = in_f.shape[-1]//2

        in_f = extend_signal(in_f,wshrink,npad_raisedcos = npad_raisedcos)
        
        wsh = wshrink



    a = get_mask_v1_1(MM, M,verbose,tol)

    h,inStepN,SD = compute_imf_fft(in_f,a)

    if wsh == 0:
        return in_f - h 
    else:
        return (in_f-h)[wsh:-wsh]

def fftconvolve1D(f,ker):#, mode = 'same', BCmode = 'wrap'):
    """

    Compute the 1D convolution between f and ker, using fft.

    It assumes that the field is periodic

    This function is used when the option "extend-periodic" is selected


    parameters
    ----------
    f : 1D-like array
        input array
    ker : 1D-like array
        kernel of the convolution filter

    """
    if f.shape[0] <ker.shape[0]:
        print('error, kernel shape cannot be larger than 1D array shape')
        return None

    m = ker.shape[0]//2
    kpad = np.pad(ker,((0,f.shape[0]-ker.shape[0])))
    kpad = np.roll(kpad,-m)
    return np.fft.irfft(np.fft.rfft(f)*np.fft.rfft(kpad),n=f.shape[0])

