
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

from .blombly.tools import arrays

from . import CSES01_core
from . import CSES02_core


cscore = {'CSES01':CSES01_core,'CSES02':CSES02_core}


def CSES_load(filename,path='./', return_pandas = False,
            with_mag_coords = False,keep_verse_time = True, fill_missing=None,CSX=None):
    """
    Generic interface to load any CSES DataProduct
    It uses CSES01_core.CSES_load or CSES02_core.CSES_load depending on the CSX parameter, 
    which should be a dict containing the spacecraft informations (e.g. CSX = SPACECRAFT['CSES01'])
    
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
    CSX : dict
        One item of CSES_params.SPACECRAFT dictionary containing specific spacecraft informations.
    
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
    
    if CSX is None:
        raise ValueError("CSX parameter not specified. Please provide a valid spacecraft key (e.g. CSX = SPACECRAFT['CSES01'])")
    
    return cscore[CSX['NAME']].CSES_load(filename,path=path, return_pandas = return_pandas,
            with_mag_coords = with_mag_coords, keep_verse_time = keep_verse_time, fill_missing= fill_missing,CSX=CSX)
    
def CSES_load_PSD(filename,path='./', return_xarray = False,
            with_mag_coords = False,keep_verse_time = True, fill_missing=None,CSX=None):
    """
    Generic interface to load any CSES DataProduct PSD
    It uses CSES01_core.CSES_load_PSD or CSES02_core.CSES_load_PSD depending on the CSX parameter, 
    which should be a dict containing the spacecraft informations (e.g. CSX = SPACECRAFT['CSES01'])
    

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
    
    CSX : dict
        One item of CSES_params.SPACECRAFT dictionary containing specific spacecraft informations.

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

    if CSX is None:
        raise ValueError("CSX parameter not specified. Please provide a valid spacecraft key (e.g. CSX = SPACECRAFT['CSES01'])")
    
    return cscore[CSX['NAME']].CSES_load_PSD(filename,path=path, return_xarray = return_xarray,
            with_mag_coords = with_mag_coords,keep_verse_time = keep_verse_time, fill_missing=fill_missing,CSX=CSX) 
    

def HEP_load(*args,**kwargs):
    """
    Interface to load data from Particle detectors onboard CSES-01 or CSES-02.
    It uses CSES01_core.HEP_load or CSES02_core.HEP_load depending on the CSX parameter, 
    which should be a dict containing the spacecraft informations (e.g. CSX = SPACECRAFT['CSES01'])
    """ 
    if 'CSX' not in kwargs:
        raise ValueError("CSX parameter not specified. Please provide a valid spacecraft key (e.g. CSX = SPACECRAFT['CSES01'])")
    elif kwargs['CSX'] is None:
        raise ValueError("CSX parameter not specified. Please provide a valid spacecraft key (e.g. CSX = SPACECRAFT['CSES01'])")

    return cscore[kwargs['CSX']['NAME']].HEP_load(*args,**kwargs)

def HPM_load(*args,**kwargs):
    #filename,path='./', time_from_samplerate = True, fill_missing = None):
    """
    Interface to load data from HPM onboard CSES-01 or CSES-02.
    It uses CSES01_core.HPM_load or CSES02_core.HPM_load depending on the CSX parameter, 
    which should be a dict containing the spacecraft informations (e.g. CSX = SPACECRAFT['CSES01'])
    """
    if 'CSX' not in kwargs:
        raise ValueError("CSX parameter not specified. Please provide a valid spacecraft key (e.g. CSX = SPACECRAFT['CSES01'])")
    elif kwargs['CSX'] is None:
        raise ValueError("CSX parameter not specified. Please provide a valid spacecraft key (e.g. CSX = SPACECRAFT['CSES01'])")

    return cscore[kwargs['CSX']['NAME']].HPM_load(*args,**kwargs)


#
# def fill_missing_times(xx,xp,jumps,packet_size,dt,fill_missing):
#    """
#    xp,xx = fill_missing_times(xx,xp,jumps,packet_size,fill_missing)
#    """
#    xout = xp.reshape((xp.size//packet_size,packet_size))
#    #xp = np.insert(xp, jumps+1,np.zeros(packet_size),axis=0)  
#    for i in np.flipud(jumps): #filling missing vals starting from the end
#        #x0 = xx[i]; x1 = xx[i+1]
#        nx = int((xx[i+1] - xx[i])//(packet_size*dt))-1
#        xout = np.insert(xout,[i+1]*nx,np.zeros(packet_size),axis=0)
#        #xout = np.insert(xout, jumps+1,np.zeros(packet_size),axis=0)  
#        if fill_missing == 'linear':
#            xout[i+1:i+nx+1] = (np.arange(nx*packet_size).reshape((nx,packet_size))+2048)*dt + xx[i]
#
#    return xout



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
def get_CHAOSmag(dfin,as_output = True,ref_frame='ecef',chaosfile=None,memory_friendly = True,chunk_size=65536,\
                 nskip=1,interpolate = True, verbose = False):
    """
    Compute magnetic field from CHAOS model on the desired orbit
    
    df : pandas.Dataframe
        dataframe containing latitude, longitude, altitude, and time ('lat','lon','alt','time')
    """
    from . import chaosmagpy as chaos

    if interpolate:
        from .blombly.interpolate import spline_interpolate
    if chaosfile is None:
        import os
        chaosfile = os.path.dirname(__file__)+'/CHAOS-8.5.mat'



    df = dfin[::nskip] if nskip > 1 else dfin

    time = chaos.data_utils.mjd2000(df.index.to_pydatetime()) #28 seconds
    radius = np.sqrt(np.sum(np.array(\
        convert_GPS_to_ECEF(df.lat.values,df.lon.values,df.alt.values))**2,\
                            axis=0))/1000
    lon = df.lon.values
    colat = 90-df.lat.values
    lat= df.lat.values
    model = chaos.load_CHAOS_matfile(chaosfile)

    if verbose:
        print('chunking %s points using a chunk_size of %s' %(df.shape[0], chunk_size))
    if memory_friendly and df.shape[0] < 2*chunk_size:
        print('%s < %s . Overriding memory_friendly to False'%(df.shape[0], 2*chunk_size))
        memory_friendly = False


    if memory_friendly:
        stend = arrays.start_end(df.shape[0],int(df.shape[0]//chunk_size))
        Br = np.zeros(df.shape[0])
        Bthta = np.zeros(df.shape[0])
        Bphi = np.zeros(df.shape[0])
        for istart,iend in stend:
            tB1,tB2,tB3=model.synth_values_tdep(time[istart:iend],radius[istart:iend],colat[istart:iend],lon[istart:iend])
            Br[istart:iend] = tB1
            Bthta[istart:iend] = tB2
            Bphi[istart:iend] = tB3
    else:
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
    if nskip > 1:
        bkeys = ['Bx_chaos','By_chaos','Bz_chaos']
        for ikey in bkeys:
            #if ikey in dfin.keys(): dfin = dfin.drop(columns=ikey)
            dfin.loc[df.index,ikey] = df[ikey]
            if interpolate : dfin[ikey] = spline_interpolate(df.index.values,df[ikey].values,dfin.index.values)
    else:
        bkeys = ['Bx_chaos','By_chaos','Bz_chaos']
        dfin.loc[df.index,bkeys] = df[bkeys]
    if as_output:
        return dfin.Bx_chaos.values,dfin.By_chaos.values,dfin.Bz_chaos.values






def get_pwd():
    import os
    print(__name__)
    print(os.path.dirname(__file__))
