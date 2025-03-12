
#
# Core routines to read and process CSES data
#
# Author: Emanuele Papini (EP) && Francesco Maria Follega (FMF)
#
# Dependencies : numpy, os, datetime, glob, h5py, pandas
#
# Date: 30/11/2023
#
# NOTES: 
# Ported from an experimental package firstly made on 30/03/2021 by Emanuele Papini
#
#
# 
# UPDATES: 
#   30/11/2023: Porting of basic functions from EP cses private repository
#
# TODOS: 
#   ** implement XARRAYS options in PSD output
#   ** implement filling option in 
#   everything :)       
#
from .CSES_aux import *
from .CSES_raw import *

def CSES_load(filename,path='./', return_pandas = False,
            with_mag_coords = False,keep_verse_time = True, fill_missing=None):
    """
    Generic method to read any CSES DataProduct, info to read properly the hdf5 file are 
    saved in CSES_DATASETS in CSES_aux
    Filename conventions should be according to the following example:
        
        'CSES_01_EFD_2_L02_A1_031190_20180826_095004_20180826_102510_000.h5'

    data are loaded into a pandas dataframe. Time is taken by the VERSE_TIME variable
    present in the h5 file, but sampling rate is used to calculate dt, due to truncation
    error introduced in the data (it is an integer number in milliseconds,
    but dt sampling may not be a multiple integer of 1ms)

    Parameters
    ----------
    filename : str
            string containing the name of the file
    path : str (optional)
        string containing the filepath. default is current working directory.
    return_pandas : bool
        if True, data are returned as a pandas dataframe.
    with_mag_coords : bool
        if True, magnetic coordinates contained in the file are also loaded
        (to avoid since mag coords contained in the data are often wrong).
    keep_verse_time : bool
        if True, add the VerseTime to the output.
    fill_missing : str or None or np.nan or float
        Determines filling method for gaps in the data. 
        If set to float, fill gaps with desired value.
        Allowed values:
          
          None : it does not fill any temporal gap/missing packets
          
          'zero'or 0 : fills gaps with zeroes.
          
          'nan' or np.nan : fills gaps with NaNs
          
          float : fills gaps with the desired floating value
          
          'linear': fits the gaps with a linear function between the two points
          
          'raised stats': TO IMPLEMENT: (DELIRIUM PAPINIENSIS)
                  Filling done with a half cosine between the two points filled with 
                  fluctuations reproducing the same statistics of nearby data

    Output: (res, aux) (tuple)
    ------
        res : numpy.recarray or pandas.dataframe 
            contains instrument data and coordinate data
        aux : dict
            contains ancillary data with the following keywords:
            {'ORBITNUM':int,
             'units':'V/m', (for the electric field, nT for B, etc.)
             'UTC':utc time of first datapoint, 
             'verse_time': VERSE time of first datapoint,
             'verse_zero_utc': utc time of the zero VERSE time (i.e, 2009/1/1) }
    """
    
    import h5py
    from .blombly.tools import arrays
    from .blombly.tools.objects import dict_to_recarray
    import pandas as pd
    from datetime import timedelta
    #from numpy import interp as interp1
    from scipy.interpolate import interp1d #as interp1
   

    def interp1(x,xp,fp):#*args,**kwargs):
        finterp=interp1d(xp,fp,fill_value='extrapolate')
        return finterp(x)

    info = parse_CSES_filename(filename)
    fldtags = CSES_FILE_TABLE[info['Instrument']][info['InstrumentNum']]
    
    # check extension
    if info['extension'] == '.h5':
        fil = h5py.File(path+filename,'r')
        orbitnum = int(fil.attrs['ORBITNUM'][0])
    elif info['extension'] == '.zarr.zip':
        import zarr
        fil = zarr.open(path+filename)
        orbitnum = int(fil.attrs['ORBITNUM'])

    try:
        units = {fldtags[i]:fil[i].attrs['units'][0] for i in fldtags}
    except:
        try:
            units = {fldtags[i]:[fil[i].attrs[j][0] for j in fil[i].attrs.keys()][0] for i in fldtags}
        except:
            fldtags = CSES_DATASETS
            try:
                units = {fldtags[i]:fil[i].attrs['units'][0] for i in fldtags if i in fil}
            except:
                units = {fldtags[i]:[fil[i].attrs[j][0] for j in fil[i].attrs.keys()][0] \
                            for i in fldtags if i in fil}
            fldtags = {i:fldtags[i] for i in fldtags if i in fil}
    data =  {fldtags[i]:fil[i][...] for i in fldtags}
    pos = {CSES_POSITION[i]:fil[i][...] for i in CSES_POSITION if i in fil}

    ms, ns = dshape = data[[fldtags[i] for i in fldtags][0]].shape


    if not with_mag_coords:
        if 'mag_lat' in pos : del pos['mag_lat']
        if 'mag_lon' in pos : del pos['mag_lon']
    
    Vtime = fil['VERSE_TIME'][...]
    Utime = fil['UTC_TIME'][...]
    if filename[-3:] == '.h5':
        fil.close()
    else:
        pass
    
    #fixing bad jumps in orbital position
    lont,latt = fix_lonlat(pos['lon'],pos['lat'],Vtime)
    pos['lon'] = lont; pos['lat'] = latt
    del lont,latt
    
    #convert from CSES date (VERSE_TIME) to standard date
    vt0_utc, utc = datenum(2009,1,1,utc = str(Utime[0][0]))    #CSES initial time
    Utime = np.array([j[1] for j in [datenum(2009,1,1,utc=str(i[0])) for i in Utime]])

    tx=Vtime
    Vtime0 = tx[0][0] #VERSE_TIME a t=0 in milliseconds
    tx -=Vtime0
    tx = tx/1000
    Vtime0/=1000
    time1=tx     #verse_time in seconds
    del tx

    packet_size  = ns
    dtrate = 1/CSES_SAMPLINGFREQS[info['Instrument']+'_'+info['DataProduct']]
    do_interp = dshape != time1.shape

    time1 = time1.flatten()
    time = np.zeros(dshape)
    
    #finding missing packages positions (time jumps)
    jumps = np.where(np.diff(time1)>packet_size*dtrate*1.2)[0]
  
    #filling the time array
    ij0=0
    for ij in jumps:
        time[ij0:ij+1,:] = time1[ij0] +dtrate*np.arange((ij+1-ij0)*ns).reshape((ij+1-ij0,ns))
        ij0 = ij+1
    #last chunk
    if ij0<ms: 
        time[ij0:,:] = time1[ij0] +dtrate*np.arange((ms-ij0)*ns).reshape((ms-ij0,ns))

    t_old = time1.copy()
    if fill_missing is not None:
        #calculating gap in terms of number of packets missing
        dtjumps = np.diff(time1)[jumps] 
        npacks = np.rint(dtjumps/(packet_size*dtrate)).astype(int)-1
        #filling with linear interpolation
        t_new, mask_old = add_packets(time,jumps,npacks,dtrate)
    else:
        t_new = time.copy()
        mask_old = np.ones(ms,dtype = bool)

    msnew, ns = t_new.shape
    t_new = t_new.flatten() 
    #because Vtime has a precision of 1ms (i.e. 1kHz) and the sampling rate is 5kHz,
    #it happens that some delta_t is negative between the packets.
    #a quick fix is to simply shift by 5kHz the whole time array in those points
    neg_t = np.where(np.diff(t_new)<0)[0]
    if np.size(neg_t)>0:
        for it in neg_t:
            dt = t_new[it+1] -t_new[it]
            t_new[it+1:] += -dt + dtrate
    
    t_old = t_new.reshape((msnew,ns))[mask_old,0]
    t_new = t_new.flatten()

    if do_interp:
        #interpolate altitude DOUBLE INTERPOLATION BECAUSE WE READJUSTED THE ORIGINAL TIMES
        #i.e., t_old != time1. THIS IS BECAUSE we dont know how exactly coordinates in 
        #L2 data have been calculated
        #ON A SECOND THOUGHT, probably need only direct linear interpolation
        pos1 = {i:interp1(t_new,time1.flatten(),pos[i].flatten()) for i in pos}
        #interpolate longitude 
        if 'lon' in pos:
            pos1['lon'] = arrays.interp1_jumps(t_new,time1.flatten(),pos['lon'].flatten(),np.array([-180,180]))
        if 'mag_lon' in pos:
            pos1['mag_lon'] = arrays.interp1_jumps(t_new,time1.flatten(),\
                pos['mag_lon'].flatten(),np.array([-180,180]))
        del pos
        pos = pos1
    else:
        pos1 = {i:pos[i].flatten() for i in pos}

    if fill_missing is not None and any(~mask_old):
        
        data1 = {i:np.zeros((msnew,ns)) for i in data}
        for i in data: data1[i][mask_old] = data[i]

        if type(fill_missing) is not str:
            for i in data.keys(): data1[i][~mask_old] = fill_missing

        elif fill_missing == 'zero':
            for i in data.keys(): data1[i][~mask_old] = 0

        elif fill_missing == 'nan':
            for i in data.keys(): data1[i][~mask_old] = np.nan

        elif fill_missing == 'linear':
            data1 = {i:interp1(t_new,t_new.reshape((msnew,ns))[mask_old].flatten(),data[i].flatten()) for i in data}

        data = data1 
        mm = np.zeros((msnew,ns),dtype = bool)
        for i,j in enumerate(mask_old): mm[i]=j
        data['gaps_mask'] = ~mm.flatten()
   
        if any([pos1[i].shape != data['gaps_mask'].shape for i in pos1]):
            pos1 = {i:interp1(t_new,t_new.reshape((msnew,ns))[mask_old].flatten(),pos1[i].flatten()) for i in pos1}
    
    if fill_missing is not None and 'gaps_mask' not in data:
        data['gaps_mask'] = np.zeros(data[[i for i in data][0]].shape,dtype=bool)

    data = {i:data[i].flatten() for i in data} 
    data.update(pos1)
    data['time'] = t_new.flatten()
    
    if info['Instrument'] == 'EFD':
        for i in fldtags:
            if units[fldtags[i]] == b'mV/m': 
                data[fldtags[i]] /=1000
                units[fldtags[i]] = b'V/m'

    res = dict_to_recarray(data)
    if return_pandas:
        index = pd.to_timedelta( res['time'] - res['time'][0],unit='sec') + utc
        df = pd.DataFrame(res,index=index)
        if not keep_verse_time : 
            df.drop('time',axis='columns',inplace=True)
        else:
            df['time']+=Vtime0
        df['orbitn']=int(info['orbitn'])
        res = df 
    


    return res, {'ORBITNUM':orbitnum,'units':units ,'UTC':utc, 'verse_zero_utc':vt0_utc, 'verse_time':utc-vt0_utc}

def CSES_load_PSD(filename,path='./', return_xarray = False,
            with_mag_coords = False,keep_verse_time = True, fill_missing=None):
    """
    Generic method to read any CSES DataProduct PSD, info to read properly the 
    hdf5 file are  saved in CSES_DATASETS in CSES_aux
    Filename conventions should be according to the following example:
        
        'CSES_01_EFD_2_L02_A1_031190_20180826_095004_20180826_102510_000.h5'
    Time is taken by the VERSE_TIME variable
    present in the h5 file. Be aware, however, that there is a truncation
    error introduced in the data timing, since it is an integer number in milliseconds,
    but dt sampling is not a multiple integer of 1ms.

    Parameters
    ----------
    filename : str
            string containing the name of the file
    path : str (optional)
        string contatining the filepath. default is current working directory
    with_mag_coords : bool
        if True, magnetic coordinates contained in the file are also loaded
        (to avoid since mag coords contained in the data are often wrong).
    keep_verse_time : bool
        if True, add the VerseTime to the output.
    
    fill_missing : str or None or np.nan or float  TO BE IMPLEMENTED
        Determines filling method for gaps in the data. 
        If set to float, fill gaps with desired value.
        Allowed values:
          
          None : it does not fill any temporal gap/missing packets
          
          'zero'or 0 : fills gaps with zeroes.
          
          'nan' or np.nan : fills gaps with NaNs
          
          float : fills gaps with the desired floating value

    Output: (res, aux) (tuple)
    ------
        res : numpy.recarray or xarray (TO BE IMPLEMENTED) 
            contains electric field data and coordinate data
        aux : dict
            contains ancillary data with the following keywords:
            {'ORBITNUM':int,
             'units':'V/m',
             'UTC':utc time of first datapoint, 
             'verse_time': VERSE time of first datapoint,
             'verse_zero_utc': utc time of the zero VERSE time (i.e, 2009/1/1) }

    """
    
    import h5py
    from numpy import interp as interp1
    from .blombly.tools import arrays
    from .blombly.tools.objects import dict_to_recarray
    import pandas as pd
    from datetime import timedelta
    
    get_PSD = True
    info = parse_CSES_filename(filename)
    fil = h5py.File(path+filename,'r')
    fldtags = {i:CSES_DATASETS[i] for i in fil.keys() if i in CSES_DATASETS} 
    #if get_PSD:
    fldtags = {i:fldtags[i] for i in fldtags if i[-2:] == '_P'}
    freqs = fil['FREQ'][...].flatten()
    #else:    
    #    fldtags = {i:fldtags[i] for i in fldtags if i[-2:] == '_W'}
    orbitnum = int(fil.attrs['ORBITNUM'][0])
    
    try:
        units = {fldtags[i]:fil[i].attrs['units'][0] for i in fldtags}
    except:
        units = {fldtags[i]:[fil[i].attrs[j][0] for j in fil[i].attrs.keys()][0] \
                            for i in fldtags if i in fil}
        fldtags = {i:fldtags[i] for i in fldtags if i in fil}
    data =  {fldtags[i]:fil[i][...] for i in fldtags}
    pos = {CSES_POSITION[i]:fil[i][...].flatten() for i in CSES_POSITION}

    ms, ns = dshape = data[[fldtags[i] for i in fldtags][0]].shape


    if not with_mag_coords:
        if 'mag_lat' in pos : del pos['mag_lat']
        if 'mag_lon' in pos : del pos['mag_lon']
    
    Vtime = fil['VERSE_TIME'][...]
    Utime = fil['UTC_TIME'][...]
    
    fil.close()
    
    #convert from CSES date (VERSE_TIME) to standard date
    vt0_utc, utc = datenum(2009,1,1,utc = str(Utime[0][0]))    #CSES initial time
    Utime = np.array([j[1] for j in [datenum(2009,1,1,utc=str(i[0])) for i in Utime]])

    tx=Vtime
    Vtime0 = tx[0][0] #VERSE_TIME a t=0 in milliseconds
    tx -=Vtime0
    tx = tx/1000
    Vtime0/=1000
    time1=tx     #verse_time in seconds
    del tx

    
    psd = {i[:-2]:data[i] for i in data}
    #data.update(pos1)
    data = {'psd':psd}
    data['time'] = time1.flatten()
    data['freq'] = freqs.flatten()
    index = pd.to_timedelta( data['time'] - data['time'][0],unit='sec') + utc
    data['time'] = index
    position = pd.DataFrame(pos,index=index)
    position['orbitn']=orbitnum
    data['position'] = position	
    if return_xarray:
        import xarray as xr
        #ds = xr.Dataset( \
        #   coords = dict( time = data['time'], frequency = freqs')
        #)
        pass
    return data, {'ORBITNUM':orbitnum,'units':units ,'UTC':utc, 'verse_zero_utc':vt0_utc, 'verse_time':utc-vt0_utc}



def EFD_load_ELF_PSD(filename, path='./', with_mag_coords = False):
    """
    Load EFD-ELF PSD data from h5 file specfied by the path.
    Filename conventions should be according to the following example:
        
        'CSES_01_EFD_2_L02_A1_031190_20180826_095004_20180826_102510_000.h5'

    This is a python implementation of the matlab code EFD_carica_dati_ELF_v1.m
    
    Parameters
    ----------
    filename : str
            string containing the name of the file
    path : str (optional)
        string contatining the filepath. default is current working directory
    cut_last_interval : bool (optional)
        FOR THE TIME BEING THIS OPTION IS BEING SWITCHED OFF, DUE TO UNCERTAINTIES
        ON HOW TO INTERPOLATE THE LAST 2048 ELEMENTS
        if True, then removes the last 2048 points, since it is not sure what 
        is the time associated to them (don't know why, ask the matlab guy)

    Output: (res, aux) (tuple)
    ------
        res : numpy.recarray 
            contains electric field data and coordinate data
        aux : dict
            contains ancillary data with the following keywords:
            {'ORBITNUM':int,
             'units':'V/m',
             'UTC':utc time of first datapoint, 
             'verse_time': VERSE time of first datapoint,
             'verse_zero_utc': utc time of the zero VERSE time (i.e, 2009/1/1) }
    """
    dtrate = 1/5000 #samplerate is 5kHz
    cut_last_interval = True
    import h5py
    from numpy import interp as interp1
    from .blombly.tools import arrays
    fil = h5py.File(path+filename,'r')
    orbitnum = int(fil.attrs['ORBITNUM'][0])
    B1 = fil['A121_W'].attrs['units'][0]
    s2=b'V/m';

    Ex1 = fil['A121_P'][...]
    Ey1 = fil['A122_P'][...]
    Ez1 = fil['A123_P'][...]
    lat1 = fil['GEO_LAT'][...]
    lon1 = fil['GEO_LON'][...]
    ALT1 = fil['ALTITUDE'][...]
    Wmodee = fil['WORKMODE'][...]
    Vtime = fil['VERSE_TIME'][...]
    Utime = fil['UTC_TIME'][...]
    if with_mag_coords:
        mlat1 = fil['MAG_LAT'][...]
        mlon1 = fil['MAG_LON'][...]
   
    ms, ns = Ex1.shape
    #convert from CSES date (VERSE_TIME) to standard date
    vt0_utc, utc = datenum(2009,1,1,utc = str(Utime[0][0]))    #CSES initial time

    tx=Vtime
    tx = tx/1000
    time=tx.flatten()     #verse_time in seconds
    
    ALT = ALT1.flatten()
    lat = lat1.flatten()
    lon = lon1.flatten()
    if with_mag_coords:
        mlat = mlat1.flatten()
        mlon = mlon1.flatten()

    if 'FREQ' in fil.keys():
        freqs = fil['FREQ'][...].flatten()
    else:
        freqs = np.arange(1024.)/1024*2500.
    fil.close()
    
    names = ['Ex','Ey','Ez','alt','lat','lon','time','mag_lat','mag_lon']

    res = {}
    res['time'] = time
    res['alt'] = ALT
    res['lat'] = lat
    res['lon'] = lon
    if with_mag_coords:
        res['mag_lat'] = mlat
        res['mag_lon'] = mlon
    res['Ex'] = list(Ex1)
    res['Ey'] = list(Ey1)
    res['Ez'] = list(Ez1)

    return res, {'ORBITNUM':orbitnum,'units':s2,'UTC':utc, 'verse_zero_utc':vt0_utc, 'verse_time':utc-vt0_utc,'FREQ':freqs}


def HEP_load(filename,path='./', instrument_no = '1', channel = 'all', energy_selection_list = None, energy_bin = None, pitch_bin = None, with_mag_coords=False, time_from_samplerate = True, fill_missing = None):
    import h5py
    from numpy import interp as interp1

    if filename[-3:] == '.h5':
        fil = h5py.File(path+filename,'r')
        orbitnum = int(fil.attrs['ORBITNUM'][0])
    elif filename[-9:] == '.zarr.zip':
        import zarr
        fil = zarr.open(path+filename)
        orbitnum = int(fil.attrs['ORBITNUM'])

    print('Loading HEP data from file '+filename)

    B1 = b'counts/s'
    lat1 = fil['GEO_LAT'][...].flatten()
    lon1 = fil['GEO_LON'][...].flatten()
    if with_mag_coords:
        mlat1 = fil['MAG_LAT'][...].flatten()
        mlon1 = fil['MAG_LON'][...].flatten()
    if instrument_no == '1' or instrument_no == '2':
        A411 = fil['A411'][...]
        A412 = fil['A412'][...]
    elif instrument_no == '3':
        Counts_0 = fil['Counts_0'][...]
        Counts_1 = fil['Counts_1'][...]
        Counts_2 = fil['Counts_2'][...]
        Counts_3 = fil['Counts_3'][...]
        Counts_4 = fil['Counts_4'][...]
        Counts_5 = fil['Counts_5'][...]
        Counts_6 = fil['Counts_6'][...]
        Counts_7 = fil['Counts_7'][...]
        Counts_8 = fil['Counts_8'][...]
    else:
        A413 = fil['A413'][...]
        A433 = fil['A433'][...]
        

    if instrument_no != '4' and instrument_no != '3':
        electron_energy_table = fil['Energy_Table_Electron'][...][0]
        proton_energy_table = fil['Energy_Table_Proton'][...][0]
        
        if channel == 'all':
            print('No channel specified, summing over all channels')
            if energy_selection_list is None:
                print('No energy selection specified, summing over all energy bins')
                A411_new = np.sum(A411[:,:,:],axis = (1,2))
                A412_new = np.sum(A412[:,:,:],axis = (1,2))
            else:
                print('Energy selection specified, summing over selected energy bins', energy_selection_list)
                # derive boolean vector for energy selection with condition specified in energy_selection_list i.e. [['>10','<=100'],['>10','<=100']]
                condition_ele = np.ones(electron_energy_table.shape[0],dtype = bool)
                condition_prot = np.ones(proton_energy_table.shape[0],dtype = bool)
                for cond in energy_selection_list[0]:
                    condition_ele = condition_ele & eval('electron_energy_table'+cond)
                for cond in energy_selection_list[1]:
                    condition_prot = condition_prot & eval('proton_energy_table'+cond)
                
                # select only the energy bins that satisfy the condition 
                A411_new = np.sum(A411[:,condition_ele,:], axis=(1,2))
                A412_new = np.sum(A412[:,condition_prot,:], axis=(1,2))
            if instrument_no == '2':
                Count_Electron = fil['Count_Electron'][...]
                Count_Proton = fil['Count_Proton'][...]
            else:
                Count_Electron = np.sum(fil['Count_Electron'][...], axis = 1).flatten()
                Count_Proton = np.sum(fil['Count_Proton'][...], axis = 1).flatten()
        # check if channel is an integer
        elif type(channel) == int:
            print('Channel specified, summing over channel '+channel)
            if energy_selection_list is None:
                print('No energy selection specified, summing over all energy bins')
                A411_new = np.sum(A411[:,:,:],axis = (1,2))
                A412_new = np.sum(A412[:,:,:],axis = (1,2))
            else:
                print('Energy selection specified, summing over selected energy bins', energy_selection_list)
                # derive boolean vector for energy selection with condition specified in energy_selection_list i.e. [['>10','<=100'],['>10','<=100']]
                condition_ele = np.ones(electron_energy_table.shape[0],dtype = bool)
                condition_prot = np.ones(proton_energy_table.shape[0],dtype = bool)
                for cond in energy_selection_list[0]:
                    condition_ele = condition_ele & eval('electron_energy_table'+cond)
                for cond in energy_selection_list[1]:
                    condition_prot = condition_prot & eval('proton_energy_table'+cond)
                # select only the energy bins that satisfy the condition 
                A411_new = np.sum(A411[:,condition_ele,:], axis = (1,2))
                A412_new = np.sum(A412[:,condition_prot,:],axis = (1,2))
            Count_Electron = fil['Count_Electron'][:,int(channel)].flatten()
            Count_Proton = fil['Count_Proton'][:,int(channel)].flatten()
        elif type(channel) == list:
            if energy_selection_list is None:
                print('No energy selection specified, summing over all energy bins')
                A411_new = np.sum(A411[:,:,:],axis = (1,2))
                A412_new = np.sum(A412[:,:,:],axis = (1,2))
            else:
                print('Energy selection specified, summing over selected energy bins', energy_selection_list)
                # derive boolean vector for energy selection with condition specified in energy_selection_list i.e. [['>10','<=100'],['>10','<=100']]
                condition_ele = np.ones(electron_energy_table.shape[0],dtype = bool)
                condition_prot = np.ones(proton_energy_table.shape[0],dtype = bool)
                for cond in energy_selection_list[0]:
                    condition_ele = condition_ele & eval('electron_energy_table'+cond)
                for cond in energy_selection_list[1]:
                    condition_prot = condition_prot & eval('proton_energy_table'+cond)
                # select only the energy bins that satisfy the condition 
                A411_new = np.sum(A411[:,condition_ele,:], axis = (1,2))
                A412_new = np.sum(A412[:,condition_prot,:],axis = (1,2))
            Count_Electron = np.zeros(len(A411))
            Count_Proton = np.zeros((len(A411)))
            for i in channel:
                Count_Electron += fil['Count_Electron'][:,int(i)].flatten()
                Count_Proton +=  fil['Count_Proton'][:,int(i)].flatten()
            
        if energy_bin != None or pitch_bin != None:
            print('Energy and/or pitch bin specified, averaging over selected bins')
            if energy_bin != None and pitch_bin == None:
                print('Energy bin specified, summing over pitch bin '+str(energy_bin))
                A411_new = np.sum(A411[:,energy_bin,:], axis = 1)
                A412_new = np.sum(A412[:,energy_bin,:], axis = 1)
            elif energy_bin == None and pitch_bin != None:
                print('Pitch bin specified, summing over energy bin '+str(pitch_bin))
                A411_new = np.sum(A411[:,:,pitch_bin], axis = 1)
                A412_new = np.sum(A412[:,:,pitch_bin], axis = 1)
            else:
                print('Energy and pitch bin specified')
                A411_new = A411[:,energy_bin,pitch_bin]
                A412_new = A412[:,energy_bin,pitch_bin]

    elif instrument_no == '4':
        XrayRate = fil['XrayRate'][...]

    ALT1 = fil['ALTITUDE'][...].flatten()

    Vtime = fil['VERSE_TIME'][...]
    Utime = fil['UTC_TIME'][...]
    #print(Utime)
    if filename[-3:] == '.h5':
        fil.close()
    else:
        pass

    #convert from CSES date (VERSE_TIME) to standard date
    vt0_utc, utc = datenum(2009,1,1,utc = str(Utime[0][0]))    #CSES initial time

    tx=Vtime
    tx = tx
    time=tx.flatten()     #verse_time in seconds
    
    idx = np.where(time<0)[0]
    
    if len(idx)>0:
        for i in idx:
            if i == 0:
                time[i] = time[i+1]-1
            elif i == len(time)-1:
                time[i] = time[i-1]+1
            else:
                time[i] = (time[i-1]+time[i+1])/2


    ALT = ALT1.flatten()
    lat = lat1.flatten()
    lon = lon1.flatten()

    res = {}
    res['time'] = time
    res['alt'] = ALT
    res['lat'] = lat
    res['lon'] = lon
    if with_mag_coords:
        mlat = mlat1.flatten()
        mlon = mlon1.flatten()
    if instrument_no != '4' and instrument_no != '3':
        res['Count_Electron'] = list(Count_Electron)
        res['Count_Proton'] = list(Count_Proton)
        res['Flux_Electrons'] = list(A411_new)
        res['Flux_Protons'] = list(A412_new)
    elif instrument_no == '4':
        res['XrayRate'] = list(XrayRate)
    elif instrument_no == '3':
        res['Counts_0'] = list(Counts_0)
        res['Counts_1'] = list(Counts_1)
        res['Counts_2'] = list(Counts_2)
        res['Counts_3'] = list(Counts_3)
        res['Counts_4'] = list(Counts_4)
        res['Counts_5'] = list(Counts_5)
        res['Counts_6'] = list(Counts_6)
        res['Counts_7'] = list(Counts_7)
        res['Counts_8'] = list(Counts_8)
    return res, {'ORBITNUM':orbitnum,'units':B1,'UTC':utc, 'verse_zero_utc':vt0_utc, 'verse_time':utc-vt0_utc}

def HPM_load(filename,path='./', time_from_samplerate = True, fill_missing = None):
    """
    Load HPM data from h5 file specfied by the path.
    Filename conventions should be according to the following example:
        
        'CSES_01_HPM_5_L02_A2_027321_20180731_233357_20180801_001152_000.h5'

    This is a python implementation of the matlab code 'HPM_carica_dati_v1.m'
    Parameters
    ----------
    filename : str
            string containing the name of the file
    path : str (optional)
        string contatining the filepath. default is current working directory
    time_from_samplerate : bool
        if true, uses sampling time to calculate the array of times
    fill_missing : str or None or np.nan or float
        Determines filling method for Electric Field
        if set to float, fill gaps with desired value
        None: it does not fill any temporal gap/missing packets
        'zero'or 0 : fills gaps with zeroes.
        'nan' or np.nan : fills gaps with NaNs
        'linear': TO IMPLEMENT fits the gaps with a linear function between the two points
        'raised stats': TO IMPLEMENT:
                filling done with a half cosine between the two points filled with 
                fluctuations reproducing the same statistics of nearby data

    Output: (res, aux) (tuple)
    ------
        res : numpy.recarray 
            contains magnetic field data and coordinates data
        aux : dict
            contains ancillary data with the following keywords:
            {'ORBITNUM':int,
             'units':'V/m',
             'UTC':utc time of first datapoint, 
             'verse_time': VERSE time of first datapoint,
             'verse_zero_utc': utc time of the zero VERSE time (i.e, 2009/1/1) }
    """
    dtrate = 1

    import h5py
    from numpy import interp as interp1

    fil = h5py.File(path+filename,'r')
    B1 = fil['A221'].attrs['Units']
    orbitnum = int(fil.attrs['ORBITNUM'])
    lat1 = fil['GEO_LAT'][...].flatten()
    lon1 = fil['GEO_LON'][...].flatten()
    ALT1 = fil['ALTITUDE'][...].flatten()
    Bx1 = fil['A221'][...].flatten()
    By1 = fil['A222'][...].flatten()
    Bz1 = fil['A223'][...].flatten()
    
    Vtime = fil['VERSE_TIME'][...]
    Utime = fil['UTC_TIME'][...]
    fil.close()
    
    #convert from CSES date (VERSE_TIME) to standard date
    vt0_utc, utc = datenum(2009,1,1,utc = str(Utime[0][0]))    #CSES initial time

    tx=Vtime
    tx = tx/1000
    time1=tx     #verse_time in seconds
    
    t_old = time1.flatten().copy()
    jumps = np.where(np.diff(t_old)>1)[0]
    if fill_missing is not None:
        #calculating gap in terms of number of packets missing
        dtjumps = np.diff(t_old)[jumps] 
        npacks = np.rint(dtjumps/dtrate).astype(int)-1
        #filling with linear interpolation
        t_new, mask_old = add_packets(t_old.reshape((t_old.size,1)),jumps,npacks,dtrate)
    else:
        t_new = t_old.copy()
        mask_old = np.ones(t_new.size,dtype = bool)
    if time_from_samplerate:
        t_new = t_new[0] + dtrate*np.arange(t_new.size)

    names = ['Bx','By','Bz','alt','lat','lon','time']
    dtypes = [(i,Bx1.dtype.type) for i in names]
    if fill_missing is not None:
        names.append('gaps_mask')
        dtypes.append(('gaps_mask',np.bool))

    t_new = t_new.flatten()
    res = np.recarray(t_new.shape,dtype=dtypes)
    res['time'] = t_new
    res['alt'][mask_old] = ALT1
    res['lat'][mask_old] = lat1
    res['lon'][mask_old] = lon1
    res['Bx'][mask_old] = Bx1
    res['By'][mask_old] = By1
    res['Bz'][mask_old] = Bz1
    if fill_missing is not None:
        if type(fill_missing) is not str:
            res['Bx'][~mask_old] = fill_missing
            res['By'][~mask_old] = fill_missing
            res['Bz'][~mask_old] = fill_missing
        elif fill_missing == 'zero':
            res['Bx'][~mask_old] = 0
            res['By'][~mask_old] = 0
            res['Bz'][~mask_old] = 0
        elif fill_missing == 'nan':
            res['Bx'][~mask_old] = np.nan
            res['By'][~mask_old] = np.nan
            res['Bz'][~mask_old] = np.nan
        elif fill_missing == 'linear':
            res['Bx'] = interp1(t_new, t_new[mask_old].flatten(), Bx1.flatten())
            res['By'] = interp1(t_new, t_new[mask_old].flatten(), By1.flatten())
            res['Bz'] = interp1(t_new, t_new[mask_old].flatten(), Bz1.flatten())
        #times, alt, lat and lon are always linearly interpolated
        res['alt'] = interp1(t_new, t_new[mask_old].flatten(), ALT1.flatten())
        res['lat'] = interp1(t_new, t_new[mask_old].flatten(), lat1.flatten())
        res['lon'] = interp1(t_new, t_new[mask_old].flatten(), lon1.flatten())
        
        res['gaps_mask'] = True
        res['gaps_mask'][mask_old] = False
    
    return res, {'ORBITNUM':orbitnum,'units':B1,'UTC':utc, 'verse_zero_utc':vt0_utc, 'verse_time':utc-vt0_utc}





def fill_missing_times(xx,xp,jumps,packet_size,dt,fill_missing):
    """
    xp,xx = fill_missing_times(xx,xp,jumps,packet_size,fill_missing)
    """
    xout = xp.reshape((xp.size//packet_size,packet_size))
    #xp = np.insert(xp, jumps+1,np.zeros(packet_size),axis=0)  
    for i in np.flipud(jumps): #filling missing vals starting from the end
        #x0 = xx[i]; x1 = xx[i+1]
        nx = int((xx[i+1] - xx[i])//(packet_size*dt))-1
        xout = np.insert(xout,[i+1]*nx,np.zeros(packet_size),axis=0)
        #xout = np.insert(xout, jumps+1,np.zeros(packet_size),axis=0)  
        if fill_missing == 'linear':
            xout[i+1:i+nx+1] = (np.arange(nx*packet_size).reshape((nx,packet_size))+2048)*dt + xx[i]

    return xout

def EFD_load_ELF(filename, path='./', cut_last_interval = True,\
                         with_mag_coords = False, fill_missing = None):
    """
    Load EFD-ELF data from h5 file specfied by the path.
    Filename conventions should be according to the following example:
        
        'CSES_01_EFD_2_L02_A1_031190_20180826_095004_20180826_102510_000.h5'

    data are loaded into a pandas dataframe. Time is taken by the VERSE_TIME variable
    present in the h5 file, but sampling rate is used to calculate dt, due to truncation
    error introduced in the data (it is an integer number in milliseconds but dt=409.6 ms)
    

    Parameters
    ----------
    filename : str
            string containing the name of the file
    path : str (optional)
        string contatining the filepath. default is current working directory
    cut_last_interval : bool (optional)
        FOR THE TIME BEING THIS OPTION IS BEING SWITCHED OFF, DUE TO UNCERTAINTIES
        ON HOW TO INTERPOLATE THE LAST 2048 ELEMENTS
        if True, then removes the last 2048 points, since it is not sure what 
        is the time associated to them (don't know why, ask the matlab guy)

    time_from_samplerate : bool
        if true, uses sampling time to calculate the array of times
    fill_missing : str or None or np.nan or float
        Determines filling method for Electric Field
        if set to float, fill gaps with desired value
        None: it does not fill any temporal gap/missing packets
        'zero'or 0 : fills gaps with zeroes.
        'nan' or np.nan : fills gaps with NaNs
        'linear': TO IMPLEMENT fits the gaps with a linear function between the two points
        'raised stats': TO IMPLEMENT:
                filling done with a half cosine between the two points filled with 
                fluctuations reproducing the same statistics of nearby data

    Output: (res, aux) (tuple)
    ------
        res : numpy.recarray 
            contains electric field data and coordinate data
        aux : dict
            contains ancillary data with the following keywords:
            {'ORBITNUM':int,
             'units':'V/m',
             'UTC':utc time of first datapoint, 
             'verse_time': VERSE time of first datapoint,
             'verse_zero_utc': utc time of the zero VERSE time (i.e, 2009/1/1) }
    """
    dtrate = 1/CSES_SAMPLINGFREQS['EFD_ELF'] #samplerate is 5kHz
    #cut_last_interval = True
    import h5py
    from numpy import interp as interp1
    from .blombly.tools import arrays
    fil = h5py.File(path+filename,'r')
    orbitnum = int(fil.attrs['ORBITNUM'][0])
    B1 = fil['A121_W'].attrs['units'][0]
    s2=b'V/m';

    Ex1 = fil['A121_W'][...]
    Ey1 = fil['A122_W'][...]
    Ez1 = fil['A123_W'][...]
        
    lat1 = fil['GEO_LAT'][...]
    lon1 = fil['GEO_LON'][...]
    ALT1 = fil['ALTITUDE'][...]
    Wmodee = fil['WORKMODE'][...]
    Vtime = fil['VERSE_TIME'][...]
    Utime = fil['UTC_TIME'][...]
    if with_mag_coords:
        mlat1 = fil['MAG_LAT'][...]
        mlon1 = fil['MAG_LON'][...]
   
    ms, ns = Ex1.shape
    packet_size  = ns
    #convert from CSES date (VERSE_TIME) to standard date
    vt0_utc, utc = datenum(2009,1,1,utc = str(Utime[0][0]))    #CSES initial time

    tx=Vtime
    Vtime0 = tx[0][0] #VERSE_TIME a t=0 in milliseconds
    tx -=Vtime0
    tx = tx/1000
    time1=tx     #verse_time in seconds
    
    time1 = time1.flatten()
    time = np.zeros(Ex1.shape)
    
    #finding missing packages positions (time jumps)
    jumps = np.where(np.diff(time1)>1)[0]
  
    #filling the time array
    ij0=0
    for ij in jumps:
        time[ij0:ij+1,:] = time1[ij0] +dtrate*np.arange((ij+1-ij0)*ns).reshape((ij+1-ij0,ns))
        ij0 = ij+1
    #last chunk
    if ij0<ms: 
        time[ij0:,:] = time1[ij0] +dtrate*np.arange((ms-ij0)*ns).reshape((ms-ij0,ns))

    t_old = time1.copy()
    if fill_missing is not None:
        #calculating gap in terms of number of packets missing
        dtjumps = np.diff(time1)[jumps] 
        npacks = np.rint(dtjumps/(packet_size*dtrate)).astype(int)-1
        #filling with linear interpolation
        t_new, mask_old = add_packets(time,jumps,npacks,dtrate)
    else:
        t_new = time.copy()
        mask_old = np.ones(ms,dtype = bool)

    msnew, ns = t_new.shape
    t_new = t_new.flatten() 
    #because Vtime has a precision of 1ms (i.e. 1kHz) and the sampling rate is 5kHz,
    #it happens that some delta_t is negative between the packets.
    #a quick fix is to simply shift by 5kHz the whole time array in those points
    neg_t = np.where(np.diff(t_new)<0)[0]
    if np.size(neg_t)>0:
        for it in neg_t:
            dt = t_new[it+1] -t_new[it]
            t_new[it+1:] += -dt + dtrate
    
    t_old = t_new.reshape((msnew,ns))[mask_old,0]
    t_new = t_new.flatten()
    #interpolate altitude DOUBLE INTERPOLATION BECAUSE WE READJUSTED THE ORIGINAL TIMES
    #i.e., t_old != time1. THIS IS BECAUSE we dont know how exactly coordinates in 
    #L2 data have been calculated
    #ON A SECOND THOUGHT, probably need only direct linear interpolation
    ALT = interp1(t_new,t_old,interp1(t_old,time1.flatten(),ALT1.flatten()))
    #interpolate latitude 
    lat = interp1(t_new,t_old,interp1(t_old,time1.flatten(),lat1.flatten()))
    #interpolate longitude 
    lon = arrays.interp1_jumps(t_old,time1.flatten(),lon1.flatten(),np.array([-180,180]))
    lon = arrays.interp1_jumps(t_new,t_old,lon,np.array([-180,180]))
    if with_mag_coords:
        mlat = interp1(t_new,t_old,interp1(t_old,time1.flatten(),mlat1.flatten()))
        mlon = arrays.interp1_jumps(t_old,time1.flatten(),mlon1.flatten(),np.array([-180,180]))
        mlon = arrays.interp1_jumps(t_new,t_old,mlon,np.array([-180,180]))

    Ex = np.zeros((msnew,ns)); Ex[mask_old] = Ex1
    Ey = np.zeros((msnew,ns)); Ey[mask_old] = Ey1
    Ez = np.zeros((msnew,ns)); Ez[mask_old] = Ez1
   
    if fill_missing is not None:
        if type(fill_missing) is not str:
            Ex[~mask_old] = fill_missing
            Ey[~mask_old] = fill_missing
            Ez[~mask_old] = fill_missing
        elif fill_missing == 'zero':
            Ex[~mask_old] = 0
            Ey[~mask_old] = 0
            Ez[~mask_old] = 0
        elif fill_missing == 'nan':
            Ex[~mask_old] = np.nan
            Ey[~mask_old] = np.nan
            Ez[~mask_old] = np.nan
        elif fill_missing == 'linear':
            Ex=interp1(t_new,t_new.reshape((msnew,ns))[mask_old].flatten(),Ex1.flatten())
            Ey=interp1(t_new,t_new.reshape((msnew,ns))[mask_old].flatten(),Ey1.flatten())
            Ez=interp1(t_new,t_new.reshape((msnew,ns))[mask_old].flatten(),Ez1.flatten())
    Ex = Ex.flatten()
    Ey = Ey.flatten()
    Ez = Ez.flatten()
        
    #check that units are [V/m]
    if B1 != s2:               
        Ex /=1000
        Ey /=1000
        Ez /=1000
    
    fil.close()
    
    #formatting the output
    names = ['Ex','Ey','Ez','alt','lat','lon','time','mag_lat','mag_lon'] 
    dtypes = [(i,Ex1.dtype.type) for i in names]
    if fill_missing is not None:
        names.append('gaps_mask')
        dtypes.append(('gaps_mask',np.bool))

    res = np.recarray(Ex.shape,dtype=dtypes)
    res['time'] = t_new #+ Vtime0
    res['alt'] = ALT
    res['lat'] = lat
    res['lon'] = lon
    res['Ex'] = Ex
    res['Ey'] = Ey
    res['Ez'] = Ez
    
    if with_mag_coords:
        res['mag_lat'] = mlat
        res['mag_lon'] = mlon
    
    if fill_missing is not None:
        mm = np.zeros(res['Ex'].shape,dtype = bool).reshape((msnew,ns))
        for i,j in enumerate(mask_old): mm[i]=j
        res['gaps_mask'] = ~mm.flatten()
    
    if cut_last_interval:
        res = np.delete(res,range(-ns,0))
    
    return res, {'ORBITNUM':orbitnum,'units':s2,'UTC':utc, 'verse_zero_utc':vt0_utc, 'verse_time':utc-vt0_utc}


def add_packets(xbig,jumps,npacks,dt,fill_missing = 'sampling'):
    """
    fills gap according to fill_missing option
    xbig : 2D array of size nrows,packet_size
    jumps: 1D array of indices where you have jumps (of size NJUMPS)
    npacks: 1D integer array of size NJUMPS containing the number of missing packets
    dt : sampling time (if fill_missing == 'sampling')
    """
    nrows,packet_size = xbig.shape
    xout = xbig.copy()
    
    mask = np.ones(nrows,dtype=bool)
    #filling missing columns starting from the end
    for i,nx in zip(np.flipud(jumps),np.flipud(npacks)): 
        
        #inserting packets
        xout = np.insert(xout,[i+1]*nx,np.zeros(packet_size),axis=0)
        mask = np.insert(mask,[i+1]*nx,False)
        #xout = np.insert(xout, jumps+1,np.zeros(packet_size),axis=0)  
        if fill_missing == 'sampling':
            xout[i+1:i+nx+1] = (np.arange(nx*packet_size).reshape((nx,packet_size))+packet_size)*dt + xbig[i,0]

    return xout, mask

def get_spacecraft_speed(df,ref_frame='ecef',as_output = True,\
    regularize_speed = False,dt_lowfilt=20,nskip=None):
    """
    Compute spacecraft velocity from lat,lon,alt and time contained in the input
    pandas dataframe df using central finite differences
    
    Parameters
    ----------

    df : pandas.Dataframe
        dataframe containing latitude, longitude, altitude, and time ('lat','lon','alt','time')
        
        ref_frame : str
            'wgs84_spherical' : this SHOULD be the frame of the data given by the chineses
                in this frame is different from the usual spherical coordinate system, in such that
                    x: is along meridians with the direction of increasing latitude (i.e. -theta)
                    z: is the radial direction, but with an inverse sense 
                       (i.e. vectors going TOWARD the center, -r)
                    y: hopefully completes the system with HOPEFULLY a right-handed convention
                       i.e, is along phi
            'ecef' : this is the wgs84 (cartesian) coordinate system
    """

   
    data = df
    
    from .blombly.math.derivFD import derivfield as deriv #central finite differences derivative 
    t = data.index.values.astype(float)/1e9 #dt in seconds
    t-=t[0]
    if regularize_speed:
        if nskip is None:
         raise Exception ('regularize_speed == True requires setting an int value for nskip')
        from scipy.interpolate import splrep,splev
        MM = int(dt_lowfilt//np.diff(t[::nskip]).mean())
        if MM == 1:
            print('WARNING: dt_lowfilt < temporal resolution! Skipping lowfiltering!')
            x,y,z = convert_GPS_to_ECEF(data.lat.values,data.lon.values,data.alt.values)
            vx = deriv(x,t); vy = deriv(y,t); vz = deriv(z,t)
        else:
            tt = t[::nskip]
            x,y,z = convert_GPS_to_ECEF(data.lat.values[::nskip],data.lon.values[::nskip],data.alt.values[::nskip])
            vx,vy,vz = deriv(x,tt),deriv(y,tt),deriv(z,tt)
            vx,vy,vz = fif_lowfilter([vx,vy,vz],MM)
            #SPLINE INTERPOLATION TO FULL CADENCE
            tck = splrep(tt,vx); vx = splev(t,tck)
            tck = splrep(tt,vy); vy = splev(t,tck)
            tck = splrep(tt,vz); vz = splev(t,tck)
    else:
        x,y,z = convert_GPS_to_ECEF(data.lat.values,data.lon.values,data.alt.values)
        vx = deriv(x,t); vy = deriv(y,t); vz = deriv(z,t)
        #vx = np.diff(x)/t; vy = np.diff(y)/t; vz = np.diff(z)/t

    if ref_frame == 'wgs84_spherical' or ref_frame == 'geo':
        
        x,y,z = convert_GPS_to_ECEF(data.lat.values,data.lon.values,data.alt.values)
        #vx = np.diff(x)/t; vy = np.diff(y)/t; vz = np.diff(z)/t
        #now converting to vlat, -vr, and vphi
        cost = (z /np.sqrt(x**2+y**2+z**2))#[:-1]
        sint = np.sqrt(1-cost**2)
        phi =np.arctan2(y,x); cosp=np.cos(phi); sinp=np.sin(phi)#[:-1]
        vr = vx*sint*cosp + vy*sint*sinp + vz*cost
        vt = vx*cost*cosp + vy*cost*sinp - vz*sint
        vp = -vx*sinp +vy*cosp
        
        vx = -vt #v_lat
        vy =  vp #v_lon
        vz = -vr #v_radial
    
    if as_output:
        return vx,vy,vz
    
    data['vsx'] = vx
    data['vsy'] = vy
    data['vsz'] = vz

################################################################################
####################         AUXILIARY FUNCTIONS             ###################
################################################################################
def get_CHAOSmag(df,as_output = True,ref_frame='ecef',chaosfile=None):
    """
    Compute magnetic field from CHAOS model on the desired orbit
    
    df : pandas.Dataframe
        dataframe containing latitude, longitude, altitude, and time ('lat','lon','alt','time')
    """
    from . import chaosmagpy as chaos

    if chaosfile is None:
        import os
        chaosfile = os.path.dirname(__file__)+'/CHAOS-7.14.mat'
        

    time = chaos.data_utils.mjd2000(df.index.to_pydatetime()) #28 seconds
    radius = np.sqrt(np.sum(np.array(\
        convert_GPS_to_ECEF(df.lat.values,df.lon.values,df.alt.values))**2,\
                            axis=0))/1000
    lon = df.lon.values
    colat = 90-df.lat.values
    lat= df.lat.values
    model = chaos.load_CHAOS_matfile(chaosfile)


    Br,Bthta,Bphi=model.synth_values_tdep(time,radius,colat,lon)

    if ref_frame.lower() == 'ecef' or ref_frame.lower() == 'wgs84': 

        bb = np.concatenate([-Bthta,Bphi,-Br]).reshape((3,Br.shape[0]))

        from .blombly.geometry.transformations import transform_vector_sph2car

        bb = transform_vector_sph2car(bb,lat,lon,sphtype='latlon')
    
    
        if as_output:
            return bb[0],bb[1],bb[2]
        
        df['Bx_chaos'] = bb[0]
        df['By_chaos'] = bb[1]
        df['Bz_chaos'] = bb[2]

    elif ref_frame.lower() == 'geo' or ref_frame.lower() == 'wgs84_spherical': 
        if as_output: 
            return -Bthta, Bphi, -Br

        df['Bx_chaos'] = -Bthta
        df['By_chaos'] = Bphi
        df['Bz_chaos'] = -Br
    else:
        print('unknown input reference frame, returning None')
        return None


def get_pwd():
    import os
    print(__name__)
    print(os.path.dirname(__file__))
