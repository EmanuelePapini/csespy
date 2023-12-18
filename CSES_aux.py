
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

#Dictionary containing the bands corresponding to the id number 
#on the CSES filename. See file naming convention for CSES-01
# Dict structure:
# instrument_key:{id:bandname}
# e.g. the id number for the ULF band of the EFD instrument is 1, then
# we have that CSES_DATA_TABLE['EFD']['1'] == 'ULF'
CSES_DATA_TABLE = {'EFD':{'1':'ULF','2':'ELF','3':'VLF','4':'HF'},\
                   'HPM':{'1':'FGM1','2':'FGM2','3':'CDSM','5':'FGM1Hz'},\
                   'SCM':{'1':'ULF','2':'ELF','3':'VLF'},\
                   'LAP':{'1':'50mm', '2':'10mm'},\
                   'PAP':{'0':''}, \
                   'HEP':{'1':'P_L','2':'P_H','3':'D','4':'P_X'}}

#Dictionary of the name translations for the fields contained in the 
#HDF5 output files of CSES-01. 
#N.B. THIS IS STILL KEPT HERE FOR LEGACY. 
#     IT'S USE IS DEPRECATED SINCE CSES_DATASETS 
#     CONTAINS THE SAME INFORMATION
CSES_FILE_TABLE = {'EFD':{\
                       '1':{'A111_W':'Ex',\
                            'A112_W':'Ey',\
                            'A113_W':'Ez'
                           },\
                       '2':{'A121_W':'Ex',\
                            'A122_W':'Ey',\
                            'A123_W':'Ez'
                           },\
                       '3':{'A131_W':'Ex',\
                            'A132_W':'Ey',\
                            'A133_W':'Ez'
                           },\
                         },\
                   'SCM':{\
                       '1':{'A231_W':'Bx',\
                            'A232_W':'By',\
                            'A233_W':'Bz'
                           },\
                       '2':{'A241_W':'Bx',\
                            'A242_W':'By',\
                            'A243_W':'Bz'
                           },\
                       '3':{'A251_W':'Bx',\
                            'A252_W':'By',\
                            'A253_W':'Bz'
                           },\
                         },\
                   'HPM':{\
                       '5':{'A221':'Bx',\
                            'A222':'By',\
                            'A223':'Bz'\
                           },\
                         },\
                   'PAP':{\
                       '0':{'A313':'nH+',\
                            'A314':'nHe+',\
                            'A315':'nO+',\
                            'A322':'Ti',\
                            'A331':'vx',\
                            'A332':'vy',\
                            'A333':'vz'}\
                         },\
                    'LAP':{\
                       '1':{'A311':'ne',\
                            'A321':'Te'}\
                         },\
                    'HEP':{\
                        '1':{'Count_Electron':'Count_Electron',\
                             'Count_Proton':'Count_Proton'},\
                        '2':{'Count_Electron':'Count_Electron',\
                             'Count_Proton':'Count_Proton'},\
                        '3':{'Counts_0':'Counts_0',\
                             'Counts_1':'Counts_1',\
                             'Counts_2':'Counts_2',\
                             'Counts_3':'Counts_3',\
                             'Counts_4':'Counts_4',\
                             'Counts_5':'Counts_5',\
                             'Counts_6':'Counts_6',\
                             'Counts_7':'Counts_7',\
                             'Counts_8':'Counts_8'},\
                        '4':{'XrayRate':'XrayRate'}\
                        }
                   }

CSES_POSITION = {'ALTITUDE':'alt',\
                 'GEO_LAT':'lat',\
                 'GEO_LON':'lon',\
                 'MAG_LAT':'mag_lat',\
                 'MAG_LON':'mag_lon'}

#Dict containing the translation of the datasets contained in
# the hdf5 files to their corresponding physical name
# e.g. A121_W is the waveform of Ex in ELF band
# while A121_P is the spectrogram, translated as Ex_P
CSES_DATASETS = {'A111_P':'Ex_P','A111_W':'Ex',\
                 'A112_P':'Ey_P','A112_W':'Ey',\
                 'A113_P':'Ez_P','A113_W':'Ez',\
                 'A121_P':'Ex_P','A121_W':'Ex',\
                 'A122_P':'Ey_P','A122_W':'Ey',\
                 'A123_P':'Ez_P','A123_W':'Ez',\
                 'A131_P':'Ex_P','A131_W':'Ex',\
                 'A132_P':'Ey_P','A132_W':'Ey',\
                 'A133_P':'Ez_P','A133_W':'Ez',\
                 'A221':'Bx',\
                 'A222':'By',\
                 'A223':'Bz',\
                 'A241':'Bx',\
                 'A242':'By',\
                 'A243':'Bz',\
                 'A311':'ne',\
                 'A313':'nH+',\
                 'A314':'nHe+',\
                 'A315':'nO+',\
                 'A321':'Te',\
                 'A322':'Ti',\
                 'A331':'vx',\
                 'A332':'vy',\
                 'A333':'vz'}

#SAMPLING FREQUENCIES OF VARIOUS INSTRUMENTS, TO BE USED WHEN READING DATA
CSES_SAMPLINGFREQS = {'EFD_ULF':125.,'EFD_ELF':5000.,'EFD_VLF':50000.,\
                      'SCM_ULF':1024.,'SCM_ELF':10240.,'SCM_VLF':51200.,'LAP_50mm':1/3,'PAP_':1.,\
                      'HPM_FGM1Hz':1.,'HEP':1.}

CSES_PACKETSIZE = {'EFD_ULF':256,'EFD_ELF':2048,'EFD_VLF':2048,'EFD_HF':2048,\
                   'SCM_ULF':4096,'SCM_ELF':4096,'SCM_VLF':4096,'LAP_50mm':1,'PAP_':1,\
                   'HPM_FGM1Hz':1,'HEP':1}

CSES_FILESYSTEM = {'EFD':'year/FREQUENCY/month',\
                   'HPM':'year/month',\
                   'LAP':'year/month',\
                   'SCM':'year/FREQUENCY/month'}


def versetime_to_utc(versetime,t0=(2009,1,1)):
    """
    convert versetime to utc time
    output is a datetime object
    """
    
    vt0 = datetime(t0[0],t0[1],t0[2])

    return datetime(t0[0],t0[1],t0[2]) + timedelta(milliseconds=versetime)

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
    return [i[len(path):] for i in  glob(path+'*'+search_string+'*'+extension)] 

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
             basemap_kwargs = None,pltkwargs={}):
   
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
    plt.ion() 
    
    [imm.plot(lon,lat,latlon=True,**pltkwargs) for imm in mm]
    plt.show()
    return fig,ax,tuple(mm)
   

