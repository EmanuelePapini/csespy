import numpy as np

#def stft(y,fs,window='hann',nperseg=256):
#    """
#    Calculates the STFT of a signal. No overlap is made.
#
#    The output is such that the POWER contained in the signal is np.sum(np.abs(stft)**2)*deltanu, where
#    deltanu is the frequency resolution, namely deltanu=fs/nperseg
#    This would be equal to 
#    
#    output
#    ------
#    out[0] : 1D array(float), size nperseg
#        array of frequencies
#    out[1] : 1D array (float), size y.size//nperseg
#        array of times
#    out[2] : 2D array (float), shape(y.size//nperseg,nperseg//2+1)
#        array of the short time (real2complex) fourier transform,
#    """
#    from scipy.signal import windows
#    y = np.array(y)
#    ny=y.size
#    if ny//nperseg == ny/nperseg: 
#        sig = y.reshape((int(ny//nperseg),nperseg))
#    else:
#        sig = y[:int(ny//nperseg) * nperseg].reshape((int(ny//nperseg),nperseg))
#    
#    stft = np.fft.rfft(sig*windows.__dict__[window](nperseg)[None,:])
#    stft[:,1:]*=np.sqrt(2)
#
#    freqs = np.fft.rfftfreq(nperseg,1/fs)
#    times = np.arange(ny)[::nperseg]/fs
#    
#    #if norm == 'power':
#    #    stft*=1/fs**2
#    #elif norm == '1/N':
#    stft/=nperseg
#    return freqs,times,stft.transpose()

def stft(y,fs,window='hann',nperseg=256,norm = '1/N',return_windowed_signal = False,\
          noverlap = 0,aux_input={},transpose = True):
    """
    Calculates the STFT of a signal. No overlap is made.

    
    parameters:
    -----------
    y : array-like (1D)
        array of input time series
    fs: float
        sampling frequency
    window : str
        window function (see scipy.signal.windows)
    nperseg : int
        number of points of each FFT
    norm : str
        'power' : 
            the output is normalized such that the POWER contained in the signal is
                
                np.sum(np.abs(stft)**2)*dnu, 
            
            where dnu is the frequency resolution of the FFT, i.e., dnu = nperseg/fs. In such way Parseval theorem reads:
            
                np.sum(np.abs(y)**2)*dt/T !=  np.sum(np.abs(y)**2)/(y.size) = np.mean(np.sum(np.abs(stft)**2)*dnu)
        
        '1/N' :
            the output is normalized such that the POWER contained in the signal is
            
                np.sum(np.abs(stft)**2), 
            
            where dnu is the frequency resolution of the FFT, i.e., dnu = nperseg/fs. In such way Parseval theorem reads:
            
                np.sum(np.abs(y)**2)*dt/T !=  np.sum(np.abs(y)**2)/(y.size) = np.mean(np.sum(np.abs(stft)**2,axis=1))

    The output is such that the POWER contained in the signal is np.sum(np.abs(stft)**2), where
    deltanu is the frequency resolution, namely deltanu=fs/nperseg
    This would be equal to 
    
    output
    ------
    out[0] : 1D array(float), size nperseg
        array of frequencies
    out[1] : 1D array (float), size y.size//nperseg
        array of times
    out[2] : 2D array (float), shape(y.size//nperseg,nperseg//2+1)
        array of the short time (real2complex) fourier transform,
    """
    
    from scipy.signal import windows
    
    y = np.array(y)
    ny=y.size
    if ny//nperseg == ny/nperseg: 
        sig = y.reshape((int(ny//nperseg),nperseg))
    else:
        sig = y[:int(ny//nperseg) * nperseg].reshape((int(ny//nperseg),nperseg))

    if noverlap > 0: 
        step = nperseg - noverlap
        segments = []
        sig = sig.flatten()
        for start in range(0, len(sig) - nperseg + 1, step):
            segment = sig[start:start + nperseg]
            #segment = segment * windows.__dict__[window](nperseg)
            segments.append(segment)

        sig = np.array(segments)
    else:
        step = nperseg

    cf = 1/np.sqrt(np.mean(windows.__dict__[window](nperseg)**2))
    sig = sig*windows.__dict__[window](nperseg)[None,:] 
    stft = np.fft.rfft(sig)*cf
    stft[:,1:]*=np.sqrt(2)

    freqs = np.fft.rfftfreq(nperseg,1/fs)
    times = np.arange(ny)[::step]/fs
    
    if norm == 'power':
        stft/=np.sqrt(fs*nperseg)
    elif norm == '1/N':
        stft/=nperseg
    if transpose: stft = stft.transpose()
    out = (freqs, times, stft)
    if len(aux_input) > 0:
        try:
            aux_output = {i:aux_input[i][::step] for i in aux_input}
            out = out + (aux_output,)
        except KeyError:
            raise KeyError("Auxiliary input keys must match the time array length.")
    if return_windowed_signal:
        out = out + (sig,)
    return out

    





def wavelet_transform(*args,**kwargs):
    return cwt(*args,**kwargs)

def cwt(y, fs, wavelet='cmor1.5-1.0', nscales=64, fmin=1, fmax=None,return_dict=False):
    """
    Computes the Continuous Wavelet Transform (CWT) of the signal.

    Parameters
    ----------
    y : array_like
        Input signal.
    fs : float
        Sampling frequency.
    wavelet : str
        Wavelet to use (must be complex-valued). Default is 'cmor1.5-1.0'.
    nscales : int
        Number of frequency scales to use.
    fmin : float
        Minimum frequency to analyze.
    fmax : float or None
        Maximum frequency. If None, it is set to fs / 2.

    Returns
    -------
    freqs : ndarray
        Array of frequencies (Hz).
    times : ndarray
        Array of time points (s).
    coef : 2D ndarray
        Wavelet coefficients with shape (nscales, len(y)).
    """
    import pywt
    y = np.array(y)
    if fmax is None:
        fmax = fs / 2

    # Frequency range (log-spaced)
    freqs = np.logspace(np.log10(fmin), np.log10(fmax), num=nscales)
    # Convert frequencies to scales using scale = fc / (freq * dt)
    dt = 1 / fs
    wavelet_obj = pywt.ContinuousWavelet(wavelet)
    fc = pywt.central_frequency(wavelet_obj)  # center frequency of the wavelet
    scales = fc / (freqs * dt)

    # Perform CWT
    coef, _ = pywt.cwt(y, scales, wavelet, sampling_period=dt)

    times = np.arange(len(y)) / fs
    if return_dict:
        return {'freq':freqs, 'time':times, 'coef':coef, 'scale':scales}

    return freqs, times, coef
