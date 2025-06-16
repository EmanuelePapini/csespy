import numpy as np

def stft(y,fs,window='hann',nperseg=256):
    """
    Calculates the STFT of a signal. No overlap is made.

    The output is such that the POWER contained in the signal is np.sum(np.abs(stft)**2)*deltanu, where
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
    
    stft = np.fft.rfft(sig*windows.__dict__[window](nperseg)[None,:])
    stft[:,1:]*=np.sqrt(2)

    freqs = np.fft.rfftfreq(nperseg,1/fs)
    times = np.arange(ny)[::nperseg]/fs
    
    #if norm == 'power':
    #    stft*=1/fs**2
    #elif norm == '1/N':
    stft/=nperseg
    return freqs,times,stft.transpose()

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
