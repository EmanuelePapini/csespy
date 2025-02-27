
#
# Auxiliary functions/methods for the CSES_main.py
#
# Author: Emanuele Papini (EP) && Francesco Maria Follega (FMF)
#
# Dependencies : numpy, os, datetime, glob
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
#   everything :)       
#

import numpy as np
import os
from datetime import datetime,timedelta,date
from glob import glob
from .CSES_params import *

def get_datakey(instrument,frequency):

    if instrument != 'HEP': return instrument+'_'+frequency

    return instrument+frequency

def versetime_to_utc(versetime,t0=(2009,1,1)):
    """
    convert versetime to utc time
    output is a datetime object
    """
    
    vt0 = datetime(t0[0],t0[1],t0[2])

    return datetime(t0[0],t0[1],t0[2]) + timedelta(milliseconds=int(versetime))

def utc_to_versetime(date):
    """"convert datetime to versetime in seconds"""
    return datetime_to_versetime(date)
    
def datetime_to_versetime(date):
    """"convert datetime to versetime in seconds"""
    return (date-datetime(2009,1,1)).total_seconds()
    
def datenum(yy,mm,dd, utc = None):
    """
    Convert string to datetime objects
    Assumes utc is a string of format YYYYMMDDHHMMSSms
    """
    
    if utc is None:
        return datetime(yy,mm,dd)
    
    if len(utc) > 14 :
        utcdate = datetime(int(utc[0:4]),int(utc[4:6]),int(utc[6:8]),\
                int(utc[8:10]),int(utc[10:12]),int(utc[12:14]),int(utc[14:])*1000)
    else:
        utcdate = datetime(int(utc[0:4]),int(utc[4:6]),int(utc[6:8]),\
                int(utc[8:10]),int(utc[10:12]),int(utc[12:14]))

    return datetime(yy,mm,dd), utcdate

def utctime_to_datetime(utc):
    """
    Convert string to datetime objects
    Assumes utc is a string of format YYYYMMDDHHMMSSms
    """
    
    utc = str(utc) 
    utcdate = datetime(int(utc[0:4]),int(utc[4:6]),int(utc[6:8]),\
            int(utc[8:10]),int(utc[10:12]),int(utc[12:14]),int(utc[14:])*1000)

    return utcdate

#################################################################################
############### AACGM CONVERSION TOOLS   TO BE DEFINED                ###########
#################################################################################
def convert_GPS_to_ECEF(lat,lon,alt):
    """
    convert Lat,Lon,Altitude in X,Y,Z Earth Centered Earth Fixed (ECEF WGS84) coordinate system
    
    input:
    ------
        lat : (float)
            Input latitude in degrees N 
        lon : (float)
            Input longitude in degrees E 
        alt : (float)
            Altitude above the surface of the earth in km
    """
    from pyproj import Proj, transform
    ecef = Proj(proj='geocent', ellps='WGS84', datum='WGS84')
    
    lla = Proj(proj='latlong', ellps='WGS84', datum='WGS84')
    
    return transform(lla, ecef, lon, lat, alt*1000, radians=False)

def dataframe_aacgm_convert(df, method="ALLOWTRACE"):
    """
    return geomagnetic coordinates of the panda dataframe 
    uses the python wrapper of aacgmv2 C library
    """
    
    #dates = efd.index.to_pydatetime()
    #import aacgmv2
    #aacgm = [aacgmv2.get_aacgm_coord(efd.lat[i],efd.lon[i],efd.alt[i],dates[i]) for i in range(efd.shape[0])]    
    efd=df
    
    method_code = "G2A|{:s}".format(method)
    import aacgmv2._aacgmv2 as c_aacgmv2
    from aacgmv2._aacgmv2 import TRACE, ALLOWTRACE, BADIDEA
    import aacgmv2
    import sys
    # Recast the data as numpy arrays
    dates = efd.index.to_pydatetime()
    in_lat =efd.lat.to_numpy()  
    in_lon =efd.lon.to_numpy() 
    height =efd.alt.to_numpy()
    
    # Initialise output
    lat_out = np.full(shape=in_lat.shape, fill_value=np.nan)
    lon_out = np.full(shape=in_lon.shape, fill_value=np.nan)
    r_out = np.nan
    # Set the coordinate coversion method code in bits
    try:
        bit_code = aacgmv2.convert_str_to_bit(method_code.upper())
    except AttributeError:
        bit_code = method_code
    
    for i in range(in_lat.size):
        
        dtime = dates[i]
        # Set current date and time
        try:
            c_aacgmv2.set_datetime(dtime.year, dtime.month, dtime.day, dtime.hour,
                                   dtime.minute, dtime.second)
        except (TypeError, RuntimeError) as err:
            raise RuntimeError("cannot set time for {:}: {:}".format(dtime, err))
        try:
            lat_out[i], lon_out[i], r_out = c_aacgmv2.convert(in_lat[i], in_lon[i], height[i],
                                                        bit_code)
        except Exception:
            err = sys.exc_info()[0]
            estr = "unable to perform conversion at {:.1f},".format(in_lat[i])
            estr = "{:s}{:.1f} {:.1f} km, {:} ".format(estr, in_lon[i], height[i], dtime)
            estr = "{:s}using method {:}: {:}".format(estr, bit_code, err)
            aacgmv2.logger.warning(estr)
            pass
    
    
    if np.any(np.isfinite(lon_out)):
        # Get magnetic local time
        mlt = aacgmv2.convert_mlt(lon_out, dates, m2a=False)
    else:
        mlt = np.full(shape=len(lat_out), fill_value=np.nan)

    return lat_out,lon_out, mlt


#################################################################################
############### FUNCTION TOOLS FOR FILENAME RETRIEVAL AND MANIPULATION###########
#################################################################################

def parse_CSES_filename(filename):

    fl_list = filename.split('_')
    out={}
    if len(filename) == 66 or len(filename) == 72:
        out['Satellite'] = fl_list[0]+fl_list[1]
        out['Instrument'] = fl_list[2]
        try:
            out['DataProduct'] = CSES_DATA_TABLE[fl_list[2]][fl_list[3]]
        except:
            out['DataProduct'] = 'Unknown' 
        out['InstrumentNum'] = fl_list[3]
        out['DataLevel'] = fl_list[4]
        out['orbitn'] = fl_list[6]
        out['year'] = fl_list[7][0:4]
        out['month'] = fl_list[7][4:6]
        out['day'] = fl_list[7][6:8]
        out['time'] = fl_list[8][0:2]+':'+fl_list[8][2:4]+':'+fl_list[8][4:6]
        out['t_start'] = datetime(int( out['year']),int(out['month']),int(out['day']),\
                            int(fl_list[8][0:2]),int(fl_list[8][2:4]),int(fl_list[8][4:6])) 
        out['t_end'] = datetime(int(fl_list[9][0:4]),int(fl_list[9][4:6]),int(fl_list[9][6:8]),\
                            int(fl_list[10][0:2]),int(fl_list[10][2:4]),int(fl_list[10][4:6]))
        out['extension'] = fl_list[-1][3:]
    elif len(filename) == 69:
        out['Satellite'] = fl_list[0]+'_01'
        out['Instrument'] = fl_list[1]
        out['DataProduct'] = fl_list[2]
        out['DataLevel'] = fl_list[-2]
        out['orbitn'] = fl_list[3]
        out['year'] = fl_list[4][0:4]
        out['month'] = fl_list[4][4:6]
        out['day'] = fl_list[4][6:8]
        out['time'] = fl_list[5][0:2]+':'+fl_list[5][2:4]+':'+fl_list[5][4:6]
        out['t_start'] = datetime(int( out['year']),int(out['month']),int(out['day']),\
                            int(fl_list[5][0:2]),int(fl_list[5][2:4]),int(fl_list[5][4:6])) 
        out['t_end'] = datetime(int(fl_list[6][0:4]),int(fl_list[6][4:6]),int(fl_list[6][6:8]),\
                            int(fl_list[7][0:2]),int(fl_list[7][2:4]),int(fl_list[7][4:6]))
        out['extension'] = fl_list[-1][3:]
    return out


def find_file(path,search_string ='',extension = CSES_EXTENSIONS):
    """
    find all files with a given extension whose name contains the search_string in the path and return them into a list
    """
    #print(path+'*'+search_string+'*'+extension)
    if type(extension) is str:
        return [i[len(path):] for i in  glob(path+'*'+search_string+'*'+extension) if is_valid_CSES_filename(i[len(path):])] 
    return list(np.concatenate([[i[len(path):] for i in  glob(path+'*'+search_string+'*'+iext) if \
                                 is_valid_CSES_filename(i[len(path):])] for iext in extension]))

def is_valid_CSES_filename(filname,thorough = False):
    """Check whether a given input string is a valid CSES filename"""

    if len(filname) != 66 and len(filname) != 72 : return False #first check its length
    if filname[:4] != 'CSES': return False #check if it begins correctly
    if filname.count('_') != 11 : return False # check number of underscores

    #OTHER CHECKS CAN BE IMPLEMENTED, BUT I'LL STOP HERE FOR NOW
    if thorough:
        if len(parse_CSES_filename(filname)) == 0 : return False
    
    return True

def uniquefy(fnames,sort_by='orbitn',keep='longer',check = True):
    """
    If a list of cses filenames is given, it returns a list of files
    of unique records (default discriminant 'orbit'), keeping the one satisfying 
    the constraint (default 'longer' orbit)
    """

    if keep == 'longer': #discriminating filter
        filtby = lambda x : np.argmax([j['t_end']-j['t_start'] for j in x])
    else:
        filtby = lambda x : x
    fns = np.array([parse_CSES_filename(i)[sort_by] for i in fnames])
    fout = []
    for i in set(fns):
        k = np.where(fns == i)[0]
        fout.append(fnames[k[filtby([parse_CSES_filename(fnames[j]) for j in k])]])

    return fout
 
    
def get_dictkey_from_value(dic,value):

    return [k for k,v in dic.items() if v ==value]
################################################################################
#############PLOTTING TOOLS TBD#################################################
################################################################################
#PAYLOAD_PLOT_TEMPLATES = \
#    {'LAP_50mm':{'yscale':'log'},\
#dictionary of several default orbital plot templates to be used
ORBIT_PLOT_TEMPLATES = {'ns':{'axes': [[0.1,0.1,0.4,0.8],[0.55,0.1,0.4,0.8]],\
                             'projection': ['spstere','npstere'],\
                             'latrange': [[-90,0,15],[0,90,15]],\
                             'lonrange': [[-180,180,30],[-180,180,30]],\
                             'basemap_kwargs': {'lon_0':0,'resolution':'l','round':True,'boundinglat':0},\
                             },\
                   'default':{'axes': [[0.1,0.1,0.8,0.8]],\
                             'projection': ['cyl'],\
                             'latrange': [[-90,90,30]],\
                             'lonrange': [[-180,180,30]],\
                             'basemap_kwargs': {'lon_0':0,'resolution':'l','round':False},\
                             'pltkwargs':{'linestyle':'','marker':'.','markersize':0.5}}\
                       }
def plot_orbit(lat,lon, basemap = None, fig = None, ax = None,\
             axes = [[0.1,0.1,0.4,0.8],[0.55,0.1,0.4,0.8]],\
             projection = ['spstere','npstere'],\
             latrange = [[-90,0,15],[0,90,15]],\
             lonrange = [[-180,180,30],[-180,180,30]],\
             color = None, basemap_kwargs = None,pltkwargs={},ion=True,show=True):
   
    """
    PURPOSE:
        plot desired orbit defined by lat and lon on the worldmap, using Basemap

    parameters
    ----------

    lat : 1D array-like of size N (float)
        array of latitudes of the orbit.
    
    lon : 1D array-like of size N (float)
        array of longitudes of the orbit.

    basemap : None or Basemap object (optional)
        if not None, then the input basemap is used.

    fig : None or figure object (optional)
        if not None, then input figure is used
        (used if basemap and ax are None).

    ax : None or list of axis objects (optional)
        if not None, then input axes are used
        (used if basemap is None).

    axes : list of length== 4 lists 
        list of coordinates location of the desired axes in  the figure 
        (used if ax and basemap are None).

    projection : list of str
        list of desired projections to be used on the desired basemap
        (used if basemap is None).

    latrange : list of length == 3 lists
        desired latitudinal range and interval over which to draw parallels.

    lonrange : list of length == 3 lists
        desired longitudinal range and interval over which to draw meridians.
    
    Personal notes for  plotting/contouring continents and/or oceans
    using the output basemap object
   
    source : https://jakevdp.github.io/PythonDataScienceHandbook/04.13-geographic-data-with-basemap.html

    drawlsmask() : draw continents in gray and leave oceans
    
    bluemarble(): Project NASA's blue marble image onto the map
    shadedrelief(): Project a shaded relief image onto the map
    etopo(): Draw an etopo relief image onto the map
    warpimage(): Project a user-provided image onto the map

    Other features
      Physical boundaries and bodies of water

        drawcoastlines(): Draw continental coast lines
        drawlsmask(): Draw a mask between the land and sea, for use with projecting images on one or the other
        drawmapboundary(): Draw the map boundary, including the fill color for oceans.
        drawrivers(): Draw rivers on the map
        fillcontinents(): Fill the continents with a given color; optionally fill lakes with another color
        
      Political boundaries
        
        drawcountries(): Draw country boundaries
        drawstates(): Draw US state boundaries
        drawcounties(): Draw US county boundaries
        
      Map features
        
        drawgreatcircle(): Draw a great circle between two points
        drawparallels(): Draw lines of constant latitude
        drawmeridians(): Draw lines of constant longitude
        drawmapscale(): Draw a linear scale on the map

    """
    from mpl_toolkits.basemap import Basemap
    from .blombly import pylab as plt
    from copy import deepcopy
    pltkwargs = deepcopy(pltkwargs)
    if color is not None : pltkwargs['color'] = color
    #axtitle = ('GEO. SOUTHERN HEMISPHERE','GEO. NORTHERN HEMISPHERE') if not aacgm else \
    #          ('MAG. SOUTHERN HEMISPHERE','MAG. NORTHERN HEMISPHERE')
    
    def Basemap_kwargs(proj,kwargs,i):
        if kwargs is None:
            bkwargs={'lon_0':0,'resolution':'l','round':False}

        #if any([proj == ii for ii in ['npstere','spstere','nplaea','splaea','npaeqd','spaeqd'])]):
        #    bkwargs['boundinglat'] = 
        else:
            bkwargs = kwargs
        return bkwargs
    if basemap is None:
        if ax is None:
            if fig is None:
                fig = plt.figure(figsize=(10,5))
            ax = [fig.add_axes(iax) for iax in axes]   
        
        mm=[]
        for i,axi in enumerate(ax):
            latra = latrange[i]
            lonra = lonrange[i]
            bkwargs = Basemap_kwargs(projection[i],basemap_kwargs,i)
            mm.append(Basemap(ax = axi, projection =projection[i],**bkwargs))
            mm[-1].drawparallels(np.arange(latra[0],latra[1],latra[2]))#,labels=[1,0,0,0])
            mm[-1].drawmeridians(np.arange(lonra[0],lonra[1],lonra[2]))#,labels=[0,0,0,1])

        #ms.shadedrelief() 
            for i,ipar in enumerate(np.arange(latra[0],latra[1]+latra[2],latra[2])):
                xx=lonra[0] - (lonra[1]-lonra[0])/0.9*0.04
                axi.annotate(str(ipar),xy=mm[-1](xx,ipar),xycoords='data',annotation_clip = False,va='center',ha='left')
            for i,ipar in enumerate(np.arange(lonra[0],lonra[1]+lonra[2],lonra[2])):
                yy=latra[0] - (latra[1]-latra[0])/0.9*0.02
                axi.annotate(str(ipar),xy=mm[-1](ipar,yy),xycoords='data',annotation_clip = False,va='top',ha='center')
    else: mm = basemap

    #PLOTTING
    if ion:
        plt.ion() 
    else:
        plt.ioff()
    
    #this is done to deal with a bug in Basemap
    latlon = False if mm[0].projection == 'cyl' else True
    [imm.plot(lon,lat,latlon=latlon,**pltkwargs) for imm in mm]
    if show:
        plt.show()
    return fig,ax,tuple(mm)
   
def fif_lowfilter(flds,MM,returnIMCs=False):
    """
    returns the low-filtered time-series contained in flds using fif and the desired mask length MM
    flds : list-like
    MM : int
    """
    from .blombly.filters import fif_lowfilter as lowfilt
    out = []
    if returnIMCs:
        for ifld in flds:
            lowsig = lowfilt(ifld,MM,preprocess='extend-periodic')
            highsig = ifld-lowsig
            out.append(np.vstack([highsig,lowsig]))
    else:
        for ifld in flds:
            out.append(lowfilt(ifld,MM,preprocess='extend-periodic'))
    
    return out

#################################################################################
############### GENERIC FUNCTIONS FOR AUXILIARY OPERATIONS ######################
#################################################################################

def fix_lonlat(lons,lats,times):
    from scipy.interpolate import splrep,splev,interp1d
    from scipy.signal import argrelextrema
    from scipy.ndimage import uniform_filter1d as running_avg
    from .blombly.math.derivFD import derivfield as deriv #central finite differences derivative 
    from .blombly.tools.arrays import remove_jumps,add_jumps
    time = times.flatten()
    dt = np.diff(time)
    lon = lons.flatten()
    lat = lats.flatten()
    mm = np.zeros(len(lat),dtype=bool)
    
    #-1- fix non increasing coordinate. Some contiguous points have same
    #    coordinate, due to the fact that satellite telemetry did not update.
    #    this code part deal with it by interpolating linearly with neighbor different
    #    points.
    fix_zero_diff = lambda x : interp1d(np.unique(x,return_index=True)[1],np.unique(x),fill_value='extrapolate')(np.arange(np.size(x)))
    if any(np.diff(lat)==0) : lat = fix_zero_diff(lat)
    if any(np.diff(lon)==0) : lon = fix_zero_diff(lon)
    
    #-2- CHECK if orbit is in the polar cap
    #    and eventually split the orbit
    split_coord = split_orbit(lat,lon,times,return_index = True)
    if len(split_coord[1]) > 1 : 
        idx,otype = split_coord 
        idx[-1]-=1
        #idx:split orbit ranges indices
        #otype: orbit type (ascending or descending)
        for i in range(len(otype)):
            if otype[i] == 0:
                #descending orbit (day side)
                mm[idx[i]+1:idx[i+1]] = ~((lat[idx[i]+1:idx[i+1]]>lat[idx[i]+2:idx[i+1]+1])*\
                    (lat[idx[i]+1:idx[i+1]]<lat[idx[i]:idx[i+1]-1]))
            else:
                #ascending orbit (night side)
                mm[idx[i]+1:idx[i+1]] = ~((lat[idx[i]+1:idx[i+1]]<lat[idx[i]+2:idx[i+1]+1])*\
                    (lat[idx[i]+1:idx[i+1]]>lat[idx[i]:idx[i+1]-1]))
        
        if np.sum(mm) > 0:
           tck = splrep(time[~mm],lat[~mm])
           lat[mm] = splev(time[mm],tck)

    else:
        if np.median(np.diff(lat)) < 0:
            #descending orbit (day side)
            mm[1:-1] = ~((lat[1:-1]>lat[2::])*(lat[1:-1]<lat[0:-2]))
        else:
            #ascending orbit (night side)
            mm[1:-1] = ~((lat[1:-1]<lat[2::])*(lat[1:-1]>lat[0:-2]))
    
        if np.sum(mm) > 0:
           tck = splrep(time[~mm],lat[~mm])
           lat[mm] = splev(time[mm],tck)

    
    #doing the same for longitude
    
    #removing bad longitudinal points that are found in some data 
    #(e.g. sporadic points clearly outside
    #def fix_bad_lonlat_linear(lon,lat,n):
    #    dlondlat = deriv(lon,lat)
    #    mdlondlat= uniform_filter1d(dlondlat,n)
    #    idx = np.where(np.abs(dlondlat/dmlondlat-1)>0.4)[0]
    #    if ~len(idx) % 2 :
    #        idx = idx.reshape((idx.size//2,2))
    def fix_bad_lon_linear(lon,nk=11):
        """
        Rationale: a point out of the orbit will be above/below the mean
        given by the neighbor points. Conversely, the neighbor points will be
        below/above average. 
        The procedure localizes thes points using std and np.sign, then adjust them
        using linear interpolation.
        """
        #from .blombly.stats import running_mean1D
 
        #meanlon = running_mean1D(lon,nk,meantype='neighbor')
        #meanlon = lon/meanlon - 1
        #meanlon[0] = 0
        #meanlon[-1] = 0
        #mask = np.abs(meanlon)>0.05
        #meanlon = np.sign(meanlon)
        #meanlon = np.zeros(lon.shape)
        #meanlon[1:-1] = (lon[:-2]+lon[2:])/2
        #meanlon[1:-1] = (meanlon/lon)[1:-1] - 1
        #meanlon/=np.std(meanlon)
        #meanlon[np.abs(meanlon)<5] = 0
        #meanlon = np.sign(meanlon)
        #mask = (meanlon[1:-1] != 0) & (meanlon[0:-2] !=0) & (meanlon[2:] !=0)
        #mask = np.concatenate([[False],mask,[False]])
        #lont[1:-1][mask] = (lont[0:-2][mask]+lont[2:][mask])/2
        from scipy.interpolate import splrep,splev
        from .blombly.filters import hampel_filter
        _,idx = hampel_filter(lon,nk)
        if np.size(idx) > 0:
            tt = np.arange(lon.shape[0])
            tck = splrep(np.delete(tt,idx),np.delete(lon,idx))
            return splev(tt,tck)
        
        return lon[...]
        
    
    lon = fix_bad_lon_linear(lon,3) #first remove spikes
    lon = fix_bad_lon_linear(lon) #then remove longer outliers
    lon = fix_bad_lon_linear(lon,3) #then remove residual spikes
    lon = remove_jumps(lon,np.array([-180,180]))
    split_coord = split_orbit(lon,lat,return_index = True)
    if len(split_coord[1]) > 1 : 
        mm = np.zeros(len(lon),dtype=bool)
        for i in range(len(otype)):
            if otype[i]==0:
                #recessing orbit 
                mm[idx[i]+1:idx[i+1]] = ~((lon[idx[i]+1:idx[i+1]]>lon[idx[i]+2:idx[i+1]+1])*(lon[idx[i]+1:idx[i+1]]<lon[idx[i]:idx[i+1]-1]))
            else:
                #precessing orbit 
                mm[idx[i]+1:idx[i+1]] = ~((lon[idx[i]+1:idx[i+1]]<lon[idx[i]+2:idx[i+1]+1])*(lon[idx[i]+1:idx[i+1]]>lon[idx[i]:idx[i+1]-1]))
        
        if np.sum(mm) > 0:
           tck = splrep(time[~mm],lon[~mm])
           lon[mm] = splev(time[mm],tck)
    
    else:
        mm = np.zeros(len(lon),dtype=bool)
        if np.median(np.diff(lon)) < 0:
            mm[1:-1] = ~((lon[1:-1]>lon[2::])*(lon[1:-1]<lon[0:-2]))
        else:
            mm[1:-1] = ~((lon[1:-1]<lon[2::])*(lon[1:-1]>lon[0:-2]))
        if np.sum(mm) > 0:
           tck = splrep(time[~mm],lon[~mm])
           lon[mm] = splev(time[mm],tck)
    
    lon = add_jumps(lon,np.array([-180,180]))
    return lon.reshape(lons.shape),lat.reshape(lats.shape)

def split_orbit(lat,lon,*args,return_index = False):
    """
    given a series of latitudinal and longitudinal points, it return
    a list containing the coordinates of the orbit, split according to 
    whether latitude passes from being ascending to be descending. This
    is done to properly process orbits that pass through the poles

    parameters
    ----------
    lat : 1D array like (size N)
        latitudinal coordinates of the orbit
    lon : 1D array like (size N)
        longitudinal coordinates of the orbit
    *args: 1D array like (size N)
        additional arrays to split accordingly
    return_index : bool
        if True, then it return the index ranges of the orbits instead
    output
    ------
    [(lat_1,lon_1,0),(lat_2,lon_2,1),(...)]:
        list of tuples.
        the len of the list is the number of split orbits
        each element of the list is a tuple (lat_i,lon_i,type) 
        in which the first two elements are latitude and longitude of the split orbit
        and the third element is an integer: 
            0 -> if it is a descending orbit 
            1 -> if it is an ascending orbit
    
    if *args is provided, then the output takes the form (pseudo code)
        [(lat_i,lon_i,orbit_type_i,[arg_i for arg in args])]
    where the last element of the tuple contains the arrays passed through args and split 
    according to latitude.
    """
    from scipy.signal import argrelextrema
    inorth = argrelextrema(lat,np.greater)[0]
    isouth = argrelextrema(lat,np.less)[0]
    ilast = np.size(lat)-1
    if np.size(inorth):
        inorth = inorth[inorth !=0 and inorth !=ilast]
    if np.size(isouth):
        isouth = isouth[isouth !=0 and isouth !=ilast]

    idxlr = np.sort(np.concatenate([[0,ilast+1],inorth,isouth]))

    #selecting ascending or descending
    orbit_type = lambda x: 1 if np.sign(np.mean(np.diff(x)))>0 else 0

    if return_index:
        otype = [orbit_type(lat[idxlr[i]:idxlr[i+1]]) for i in range(len(idxlr)-1)]
        return idxlr,otype

    if args is None: 
        return [(lat[idxlr[i]:idxlr[i+1]],lon[idxlr[i]:idxlr[i+1]],\
            orbit_type(lat[idxlr[i]:idxlr[i+1]])) for i in range(len(idxlr)-1)]

    return [(lat[idxlr[i]:idxlr[i+1]],lon[idxlr[i]:idxlr[i+1]],orbit_type(lat[idxlr[i]:idxlr[i+1]]),\
            [karg[idxlr[i]:idxlr[i+1]] for karg in args]) for i in range(len(idxlr)-1)]

#################################################################################
#################### TIMESERIES MANIPULATION TOOLS ##############################
#################################################################################
def derotate_field(Ex, Ey, Ez, nskip = 2048, rot_mat = None, nskip_fixed = True, mask = None):#, min_angle = 0):
    """
    Remove the artificial jumps between data packets introduced by rotations performed in 
    the chinese CSES pipeline to rotate the electric field from the spacecraft frame to ECEF.
    The jumps are present every nskip steps (length of one packet). 
    It compensate for the wrong rotation in the following way:
        1) It assumes that the electric field vectors measured at every i*nskip 
           (i.e. at the beginning of the packet) are correctly rotated,
        2) calculates the rotation matrix from i*nskip-1 to i*nskip
        3) create a sequence of matrices which perform a rotation from the first point of 
           the packet (i.e. i*nskip-nskip) to the last point (i*nskip-1) calculated by 
           interpolating from zero rotation (identity matrix) to the calculated 
           rotation matrix.
        4) Performs the rotation of the points.

    N.B. The orientation of the electric field with respect to (e.g.) GCS reference frame 
         should be preserved in this way.
    """

    import numpy as np
    from .blombly.geometry import transformations as rot 
    nn =  np.size(Ex)#[::nskip])
    oex = np.copy(Ex)#[::nskip])
    oey = np.copy(Ey)#[::nskip])
    oez = np.copy(Ez)#[::nskip])
    EE =  np.array([Ex,Ey,Ez])
    
    def perform_rotation(ex,ey,ez,mrot):
        from scipy.spatial.transform import Rotation as R
        from scipy.spatial.transform import Slerp
        #creating interpolant
        nskip = np.size(ex)
        mrotl2r = np.zeros((2,3,3)) 
        mrotl2r[0] = np.eye(3) #identity matrix
        mrotl2r[1] = mrot
        slerpint = Slerp([0,1],R.from_matrix(mrotl2r))
        #rotation matrices from identity to mrot
        interp_rot = slerpint(np.arange(nskip)/nskip).as_matrix()
        
        BB = np.array([ex,ey,ez]).transpose()
        return np.array([np.dot(interp_rot[i],BB[i]) for i in range(nskip)]).transpose()
        
    if nskip_fixed:
        if rot_mat is None:
            mats = []
            for i in range(nskip,nn,nskip):
            
                il = i-1 
                ir = i
            
                r=np.array((oex[ir],oey[ir],oez[ir]))
                l=np.array((oex[il],oey[il],oez[il]))
            
                l/= np.sqrt(np.sum(l**2))  
                r/= np.sqrt(np.sum(r**2))  
                mat = rot.get_rotation_matrix_from_vectors(l,r) #rotate from l to r
                mats.append(mat)
                #if cost[-1][1] >= min_angle:
                
                #NOW rotating electric field in the packet
                ee = perform_rotation(Ex[i-nskip:i],Ey[i-nskip:i],Ez[i-nskip:i],mat)
           
                EE[:,i-nskip:i] = ee 
            return {'x':EE[0],'y':EE[1],'z':EE[2],'rot_mat':mats}

        else:
            for j,i in enumerate(range(nskip,nn,nskip)):
                mat = rot_mat[j]
                #NOW rotating electric field in the packet
                ee = perform_rotation(Ex[i-nskip:i],Ey[i-nskip:i],Ez[i-nskip:i],mat)
           
                EE[:,i-nskip:i] = ee 
            return {'x':EE[0],'y':EE[1],'z':EE[2]}
    else:
        if rot_mat is None:
            mats = []
            jumps = find_rotational_jumps({'Ex':Ex,'Ey':Ey,'Ez':Ez},['Ex','Ey','Ez'],nskip,mask = mask)
            for j,i in enumerate(jumps):
            
                il = i-1 
                ir = i
            
                r=np.array((oex[ir],oey[ir],oez[ir]))
                l=np.array((oex[il],oey[il],oez[il]))
            
                l/= np.sqrt(np.sum(l**2))  
                r/= np.sqrt(np.sum(r**2))  
                mat = rot.get_rotation_matrix_from_vectors(l,r) #rotate from l to r
                mats.append(mat)
                #if cost[-1][1] >= min_angle:
                
                #NOW rotating electric field in the packet
                if j == 0:
                    ee = perform_rotation(Ex[i-nskip:i],Ey[i-nskip:i],Ez[i-nskip:i],mat)
                    EE[:,i-nskip:i] = ee 
                else:
                    ee = perform_rotation(Ex[jumps[j-1]:i],Ey[jumps[j-1]:i],Ez[jumps[j-1]:i],mat)
                    EE[:,jumps[j-1]:i] = ee 

            return {'x':EE[0],'y':EE[1],'z':EE[2],'rot_mat':mats,'kjumps':jumps}

def find_rotational_jumps(EE,keys,nskip, n_sigma = 4.,mask = None):
    """
    finds rotational jumps location in the electric field, using outlier detection.
    Calculates the diff of Ex[(i+1)*2048] -  Ex[(i+1)*2048-1]. If such diff is 
    above n_sigma times the median diff (i.e. it is an outlier), then the point is identified as an outlier
    """

    dn = np.max([15,int(nskip//50)])
    nn = np.size(EE[keys[0]])
    kjump = []
    for i in range(nskip,nn,nskip):
        
        if mask is not None:
           if mask[i]: continue 
        spks = [np.abs(EE[ikey][i] - EE[ikey][i-1]) for ikey in keys]
        #stds = [np.nanmedian(np.diff(EE[ikey][i-dn:i+dn])) for ikey in keys]
        x0 = [np.nanmedian(np.diff(EE[ikey][i-dn:i+dn])) for ikey in keys]
        stds = [np.nanmedian(np.abs(np.diff(EE[ikey][i-dn:i+dn]) - ix0)) for ix0,ikey in zip(x0,keys)]
        
        #if any([(ispk/istd > n_sigma) *(istd != 0) for ispk,istd in zip(spks,stds)]):
        if any([ispk/istd > n_sigma for ispk,istd in zip(spks,stds)]):
            kjump.append(i)

    return kjump
