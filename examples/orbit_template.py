import csespy
import numpy as np
#PARAMETERS

#data folder parameters
fpath = '/CSES_Data/CSES01/'
ignore_structure = False
unstructured_path = False

#cses file parameters
datakey = 'EFD_ELF'
eqorbitn = '195931'

EQ_lat = 18.417; # Latitude of the earthquake
EQ_lon = -73.480; # Longitude of the earthquake
EQ_time = datetime(2021, 8, 14, 12, 29); # Time of the earthquake
noEQ_lat = -40; # Latitude of the earthquake
noEQ_lon = -65; # Longitude of the earthquake
cell_size = [3,3]

BG_timespan = (EQ_time - timedelta(days=365), EQ_time -timedelta(days=30))
EQ_timespan = (EQ_time - timedelta(hours=8), EQ_time)

EQ_latspan = [EQ_lat + cell_size[0]*i for i in  [-1,1]]
EQ_lonspan = [EQ_lon + cell_size[1]*i for i in  [-1,1]]
#e_rel parameters
bgkwargs = dict(spectrogram_kwargs = {'packetsize': 16384,'method' : 'stft'},\
                instrument = 'EFD', frequency = 'ELF', fill_missing = 'linear', derotate = False,\
                tags = ['Ex','Ey','Ez'], filter_MM = 8192,
                latspan = EQ_latspan, binning_factor = [16,1], \
                logcoarse_bins = np.logspace(0,np.log10(2000),30)) 

def calculate_erel(csespath,orbitn,datakey,auxiliary_vars = {}, **bgkwargs):
    try:

        css = csespy.CSES(csespath,orbitn=orbitn,\
            ignore_structure=ignore_structure,unstructured_path=unstructured_path)
        subset = [('lat',np.less,bgkwargs['latspan'][1],True),('lat',np.greater,bgkwargs['latspan'][0],True)]
        css.load_CSES(datakey, fill_missing=bgkwargs['fill_missing'],subset=subset)
        if datakey not in css.data:
            return {}
        if bgkwargs['derotate']:
            css.derotate_fields(datakey,overwrite=True)
        flds = [css.data[datakey][ifld].values for ifld in bgkwargs['tags']]
        MM = bgkwargs['filter_MM']  #csespy.CSES_SAMPLINGFREQS[datakey] *  Filter length in seconds
        lflds = csespy.fif_lowfilter(flds,MM)
        for i,ifld in enumerate(bgkwargs['tags']):
            css.data[datakey][ifld] = flds[i] - lflds[i]
    
        css.get_spectrogram(datakey,bgkwargs['tags'], **bgkwargs['spectrogram_kwargs'])

        ds = create_xarray_from_spectrogram(css.data[datakey+'_P'])

        for i in ds.data_vars.keys():
            ds[i+'_erel'] = (("nfreq", "nt"), ds[i].values /ds[i].sum(dim='nfreq').values[None, :])    

        if len(auxiliary_vars):
            for key, value in auxiliary_vars.items():
               ds[key] = (('nt',), np.full(ds.sizes['nt'], value))
        return ds
    except:
        return None

def create_xarray_from_spectrogram(psddic):
    """
    Create an xarray Dataset from a spectrogram dictionary.
    
    Parameters:
    psddic (dict): Dictionary containing spectrogram data.
    
    Returns:
    xr.Dataset: Xarray Dataset with the spectrogram data.
    """
    # Extract necessary data from the dictionary
    nx = psddic['position'].shape[0]
    nfreq = psddic['freq'].shape[0]

    freq = psddic['freq']
    psd = psddic['psd']
    poss = psddic['position']
    coords = {i: (("nt",), poss[i].values) for i in poss.keys() if i not in ['time']}
    coords['time'] = (("nt",), poss.index.values)

    coords['freq'] = (("nfreq",), freq)
    vars = {i: (("nfreq","nt"), psd[i].T) for i in psd.keys()}

    # Create the xarray Dataset
    ##############################################################################
    return xr.Dataset(vars,coords=coords)

if __main__:
    EQ_erel = calculate_erel(fpath,eqorbitn,**bgkwargs)
