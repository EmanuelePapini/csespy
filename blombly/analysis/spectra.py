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

