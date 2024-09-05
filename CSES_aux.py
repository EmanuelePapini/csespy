
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

    return datetime(t0[0],t0[1],t0[2]) + timedelta(milliseconds=versetime)

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


#################################################################################
############### FUNCTION TOOLS FOR FILENAME RETRIEVAL AND MANIPULATION###########
#################################################################################

def parse_CSES_filename(filename):

    fl_list = filename.split('_')
    out={}
    if len(filename) == 66:
        out['Satellite'] = fl_list[0]+fl_list[1]
        out['Instrument'] = fl_list[2]
        try:
            out['Data Product'] = CSES_DATA_TABLE[fl_list[2]][fl_list[3]]
        except:
            out['Data Product'] = 'Unknown' 
        out['Instrument No.'] = fl_list[3]
        out['Data Level'] = fl_list[4]
        out['orbitn'] = fl_list[6]
        out['year'] = fl_list[7][0:4]
        out['month'] = fl_list[7][4:6]
        out['day'] = fl_list[7][6:8]
        out['time'] = fl_list[8][0:2]+':'+fl_list[8][2:4]+':'+fl_list[8][4:6]
        out['t_start'] = datetime(int( out['year']),int(out['month']),int(out['day']),\
                            int(fl_list[8][0:2]),int(fl_list[8][2:4]),int(fl_list[8][4:6])) 
        out['t_end'] = datetime(int(fl_list[9][0:4]),int(fl_list[9][4:6]),int(fl_list[9][6:8]),\
                            int(fl_list[10][0:2]),int(fl_list[10][2:4]),int(fl_list[10][4:6]))
    elif len(filename) == 69:
        out['Satellite'] = fl_list[0]+'_01'
        out['Instrument'] = fl_list[1]
        out['Data Product'] = fl_list[2]
        out['Data Level'] = fl_list[-2]
        out['orbitn'] = fl_list[3]
        out['year'] = fl_list[4][0:4]
        out['month'] = fl_list[4][4:6]
        out['day'] = fl_list[4][6:8]
        out['time'] = fl_list[5][0:2]+':'+fl_list[5][2:4]+':'+fl_list[5][4:6]
        out['t_start'] = datetime(int( out['year']),int(out['month']),int(out['day']),\
                            int(fl_list[5][0:2]),int(fl_list[5][2:4]),int(fl_list[5][4:6])) 
        out['t_end'] = datetime(int(fl_list[6][0:4]),int(fl_list[6][4:6]),int(fl_list[6][6:8]),\
                            int(fl_list[7][0:2]),int(fl_list[7][2:4]),int(fl_list[7][4:6]))

    return out


def find_file(path,search_string ='',extension = '.h5'):
    """
    find all files with a given extension whose name contains the search_string in the path and return them into a list
    """
    return [i[len(path):] for i in  glob(path+'*'+search_string+'*'+extension) if is_valid_CSES_filename(i[len(path):])] 

def is_valid_CSES_filename(filname,thorough = False):
    """Check whether a given input string is a valid CSES filename"""

    if len(filname) != 66 : return False #first check its length
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
             basemap_kwargs = None,pltkwargs={},ion=True,show=True):
   
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
    time = times.flatten()
    dt = np.diff(time)
    lon = lons.flatten()
    lat = lats.flatten()
    mm = np.zeros(len(lat),dtype=bool)
    
    #fix_zero_diff = lambda x : np.interp(np.arange(np.size(x)),np.unique(x,return_index=True)[1],np.unique(x))
    fix_zero_diff = lambda x : interp1d(np.unique(x,return_index=True)[1],np.unique(x),fill_value='extrapolate')(np.arange(np.size(x)))
    if any(np.diff(lat)==0) : lat = fix_zero_diff(lat)
    if any(np.diff(lon)==0) : lon = fix_zero_diff(lon)
    if np.median(np.diff(lat)) < 0:
        #descending orbit (day side)
        mm[1:-1] = ~((lat[1:-1]>lat[2::])*(lat[1:-1]<lat[0:-2]))
    else:
        #ascending orbit (night side)
        mm[1:-1] = ~((lat[1:-1]<lat[2::])*(lat[1:-1]>lat[0:-2]))
    
    if np.sum(mm) > 0:
       tck = splrep(time[~mm],lat[~mm])
       lat[mm] = splev(time[mm],tck)

    mm = np.zeros(len(lon),dtype=bool)
    dalon = np.abs(np.diff(lon))
    mjumps = (dalon>350)*(dalon<360)
    if np.median(np.diff(lon)) < 0:
        mm[1:-1] = ~((lon[1:-1]>lon[2::])*(lon[1:-1]<lon[0:-2]))
    else:
        mm[1:-1] = ~((lon[1:-1]<lon[2::])*(lon[1:-1]>lon[0:-2]))
    mm[1:][mjumps] = False
    if np.sum(mm) > 0:
       tck = splrep(time[~mm],lon[~mm])
       lon[mm] = splev(time[mm],tck)
    return lon.reshape(lons.shape),lat.reshape(lats.shape)
