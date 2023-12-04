
#
# Collection of python routines to read CSES raw data
#
# Author: Emanuele Papini (EP) && Francesco Maria Follega (FMF)
#
# Dependencies : numpy, h5py, datetime
#
# Date: 30/11/2023
#
# NOTES: 
# Ported from an experimental package firstly made on 21/02/2023 by Emanuele Papini
#
#
# 
# UPDATES: 
#   30/11/2023: Porting of basic functions from EP cses private repository
#
# TODOS: 
#
import numpy as np
from .CSES_aux import *

def load_CSES_raw(filename, convert_names = False):
    import h5py

    #1st - load data
    with h5py.File(filename,'r') as fil:
        a={i:fil[i][...] for i in fil}
    #convert to names if asked
    if convert_names:
        keys = [i for i in a.keys()]
        for i in keys:
            if i in CSES_DATASETS: 
                a[CSES_DATASETS[i]] = a[i]
                del a[i]
    return a

def load_CSES_burst_raw(filename, instrument='EFD', frequency = 'VLF'):
    import datetime
    a = load_CSES_raw(filename, convert_names = False)
    
    W_keys = [i for i in a.keys() if i[-2:] == '_W']
    P_keys = [i for i in a.keys() if i[-2:] == '_P']
    
    if len(W_keys) < 1: return a

    if 'WORKMODE' not in a: raise('ERROR, WORKMODE flag not found!')

    mask = a['WORKMODE'] == 2
    mask = mask.flatten()
    #aux = {i:a[i][mask] for i in a if i not in np.concatenate([W_keys,P_keys])}
    keys = [i for i in a if i not in np.concatenate([W_keys,P_keys])]
    bshape = a[W_keys[0]].shape
    if instrument =='EFD' and frequency == 'VLF':
        dt = 40.96e-3
        for ikey in keys:
            out = np.zeros(bshape[0]) #creating output array
            iaux = a[ikey].flatten()
            #converting VERSE_TIME to float
            if ikey == 'VERSE_TIME':
                #out[0::25] = iaux
                for i in range(bshape[0]//25): out[i*25:(i+1)*25] = iaux[mask][i] + np.arange(25)*dt*2
                a[ikey+'_W'] = out
            elif ikey == 'UTC_TIME':
                out = np.zeros(bshape[0],dtype=datetime.datetime) #creating output array
                #out[0::25] = iaux
                for i in range(bshape[0]//25): 
                    it = iaux[i]
                    date = utctime_to_datetime(it)
                    out[i*25:(i+1)*25] = date+datetime.timedelta(milliseconds=dt*2)*np.arange(25)
                a[ikey+'_W'] = out
            elif ikey in ['ALTITUDE', 'FREQ', 'GEO_LAT', 'GEO_LON', 'MAG_LAT', 'MAG_LON']:
                #out[0::25] = iaux
                idx = np.where(mask)[0]
                for i,j in enumerate(idx):
                    out[i*25:(i+1)*25] = np.interp(np.arange(25),[0,25],iaux[j:j+2])
                a[ikey+'_W'] = out
    return a