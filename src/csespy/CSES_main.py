#!/usr/bin/python3

#
# Collection of python routines to read and process CSES data 
# for the internal use of the Limadou collaboration
#
# Author: Emanuele Papini (EP) && Francesco Maria Follega (FMF)
#
# Dependencies : numpy, h5py, datetime, attrdict
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

from .CSES_core import *
from .CSES_params import SPACECRAFT
from .CSES_fixdata import fix_data as CSES_fix_data

from .blombly.io import msg
#from attrdict import AttrDict
from .blombly.tools.objects import AttrDict
from copy import deepcopy

#CSES MAIN CLASS

class CSES():
    """
    Main class that deals with data loading, analysis, and plotting

    Calling sequence:

        csdata = CSES(filenames, path='./')
    
    Parameters:
    ----------
        filenames : list 
            list containing the names of the files to read contained in the PATH
        path : str 
            default is current path ('./'). If multiple files are provided which are not in the same path, then path 
            must be set to '' and the full file path must be provided for each file in the filenames list
    
    VERSION NOTES:
        I am now rewriting the class to add reading HPM and SCM data as well
    """

    def __init__(self, path='./',search_string = None,orbitn=None,timespan=None,unstructured_path=False, ignore_structure = False,\
                 spacecraft = 'CSES01', orbit_database_buf = None, database_source = 'pandas-hdf5'):

        from pathlib import Path
        self.spacecraft = spacecraft
        self._P = deepcopy(SPACECRAFT[spacecraft])
        self.path = path
        self._path = Path(path)
        if self._path.exists() is False:
            msg.error('Provided path does not exist: '+path)
            raise FileNotFoundError('Provided path does not exist: '+path)
        elif self._path.is_dir() is False:
            msg.error('Provided path is not a directory: '+path)
            raise FileNotFoundError('Provided path is not a directory: '+path)
        self.files = AttrDict()
        #self.files['input'] = None #THIS IS DEPRECATED AND HAS TO BE REMOVED
        self.search_string = search_string
        self.orbitn = orbitn
        self.append_data = False
        self.timespan = None
        self._ancillary_={}
        self._unstructured_path_ = unstructured_path
        self._ignore_structure_ = ignore_structure
        if not unstructured_path and not ignore_structure: self.check_path()

        if orbit_database_buf is not None:
            self.load_orbitdb(orbit_database_buf,database_source)


    def load_orbitdb(self, orbit_database_buf, database_source = 'pandas-hdf5'):
        try:
            self.orbitdb = CSES_database(orbit_database_buf, source = database_source)
        except:
            msg.error('Could not load CSES database from '+orbit_database_buf+' using source: '+database_source+'.')
################################################################################
##################### DATASET SELECTION TOOLS ##################################
################################################################################
    def select_data_to_load(self,orbitn = None, search_string = None, timespan = None,\
                            latspan = None, lonspan = None, append = True,\
                            side = None, orbit_database_ranges = None):
        
        
        """
        Set the data selection method for loading data (using CSES.load_CSES or other methods).
        Data selections are mutually exclusive and ordered by priority:
        1) orbitn
        2) search_string
        3) timespan, latspan, lonspan
        
        Parameters
        ----------
        
        orbitn : str or list of str, optional
            Semi-orbit number(s) of CSES to be loaded.
        search_string : str, optional
            String contained in the filename to load.
        timespan : tuple, optional
            Tuple of either:
            - Two datetime objects specifying the desired time interval
            - Three elements: two datetime objects and a string ('D' for day, 'N' for night, '' for both)
        latspan : array-like, 2 elements, optional
            Latitudinal range of the desired orbit.
        lonspan : array-like, 2 elements, optional
            Longitudinal range of the desired orbit.
        append : bool, optional
            Whether to append data to existing data. Default is True.
            If False, clears existing data and ancillary information.
        side : str, optional
            Day/night side specification ('D', 'N', or 'both').
        orbit_database_ranges : array-like, optional
            Custom orbit database ranges for searching.
        
        Returns
        -------
        None
            Sets internal search parameters and modifies object state.
        
        Raises
        ------
        Warning
            If latspan or lonspan are used without an orbit database loaded.
        
        Notes
        -----
        - latspan and lonspan require an orbit database to be loaded.
        - When using an orbit database, if no orbits satisfy the constraints, a warning is issued.
        - When append=False, existing data, auxiliary data, and files are cleared.
        """
        orbitn = stringfy(orbitn)

        spacecraft = self.spacecraft
        self.search_string = search_string
        self.orbitn = orbitn
        self.timespan = timespan
        self.latspan = latspan
        self.lonspan = lonspan
        self.orbit_database_ranges = orbit_database_ranges
        self.append_data = append
        self.side = side
        self._search_params = {
            'orbitn': orbitn,
            'search_string': search_string,
            'timespan': timespan,
            'latspan': latspan,
            'lonspan': lonspan,
            'orbit_database_ranges': orbit_database_ranges,
            'side': side,
            'spacecraft': spacecraft,
            'append_data': append
        }

        if not append:
            self.files = AttrDict()
            self.files['input'] = None #THIS IS DEPRECATED AND HAS TO BE REMOVED
            self._ancillary_={}
            if hasattr(self,'data') : 
                del self.data 
                del self.aux
       
        #Section executed if latlon ranges are given
        if orbitn is None and search_string is None:
            
            if not hasattr(self,'orbitdb'):
                self.latspan = None
                self.lonspan = None
                self.orbit_database_ranges = None
                msg.error('Orbit database not loaded! Ignoring input latspan/lonspan/orbit_database_ranges...')
                return
            
            csdb = self.orbitdb
           
            use_sel_db = False
            if timespan is not None:
                orbits = csdb.search_orbit_timespan(timespan, return_orbitn = True, \
                                                    use_selected_db = use_sel_db, spacecraft = spacecraft)
                use_sel_db = True
            if latspan is not None:
                orbits = csdb.search_orbit_lat(latspan, return_orbitn = True, \
                                                    use_selected_db = use_sel_db, spacecraft = spacecraft)
                use_sel_db = True
            if lonspan is not None:
                orbits = csdb.search_orbit_lon(lonspan, return_orbitn = True, \
                                                use_selected_db = use_sel_db, spacecraft = spacecraft)
                use_sel_db = True
            if orbit_database_ranges is not None:
                orbits = csdb.search_orbit(orbit_database_ranges, return_orbitn = True, \
                                                use_selected_db = use_sel_db, spacecraft = spacecraft)
                use_sel_db = True
            if side != 'both' and side is not None:
                orbits = csdb.search_orbit_side(side, return_orbitn = True, \
                                                use_selected_db = use_sel_db, spacecraft = spacecraft)
                use_sel_db = True
                
            self.orbitn = orbits.tolist()

            if len(self.orbitn) == 0 :
                msg.warning('Orbit(s) satisfying lon/lat/time constraint NOT FOUND!')

    def find_available_files(self,search_string ='',orbitn=None,timespan=None,**kwargs):
        outs = {}

        CSES_DATA_TABLE = self._P['CSES_DATAKEYS']
        spacecraft = self.spacecraft
        #if spacecraft is None: spacecraft = ['CSES-01','CSES-02']
        for datakey in CSES_DATA_TABLE:
            #outs[instr]={}
            #for ino in CSES_DATA_TABLE[instr]:
            #    ifreq = CSES_DATA_TABLE[instr][ino]
            outs[datakey] = self.search_file(datakey,search_string = search_string, orbitn= orbitn, \
                    timespan = timespan,**kwargs)
        return outs

    def find_files_to_load(self,datakey,unique=True,verbose=False):
        print('searching for files to load...')
        if self.orbitn is not None:
            if type(self.orbitn) is str:
                files = self.search_file(datakey,orbitn=self.orbitn)
                #sometimes there are two files for the same orbit.
                #In that case, the file with the larger timespan is selected.
                files = uniquefy(files)
            elif type(self.orbitn) is list:
                try:
                    files = []
                    for iorbitn in self.orbitn:
                        ifiles = self.search_file(datakey,orbitn=iorbitn)
                        #sometimes there are two files for the same orbit.
                        #In that case, the file with the larger timespan is selected.
                        ifiles = uniquefy(ifiles)
                        [files.append(ifi) for ifi in ifiles]
                except:
                    raise ValueError('Not all values inside self.orbitn are strings') 
        elif type(self.search_string) is str:
            files = self.search_file(datakey, search_string=self.search_string)
            if unique: 
                orbits = [parse_CSES_filename(ifile)['orbitn'] for ifile in files]
                fdum = []
                for iorbit in set(orbits):
                    ifiles = [iff for iff,ior in zip(files,orbits) if ior == iorbit]
                    [fdum.append(i) for i in uniquefy(ifiles)]
                files = fdum
        elif self.timespan is not None:
            
            timespan = self.timespan+('',) if len(self.timespan) == 2 else self.timespan
            try:
                files = self.search_file(datakey, timespan = timespan[:-1])
                if unique: 
                    orbits = [parse_CSES_filename(ifile)['orbitn'] for ifile in files]
                    fdum = []
                    for iorbit in set(orbits):
                        if timespan[-1] == 'N':
                            if iorbit[-1] == '0': continue
                        elif timespan[-1] == 'D':
                            if iorbit[-1] == '1': continue
                        ifiles = [iff for iff,ior in zip(files,orbits) if ior == iorbit]
                        [fdum.append(i) for i in uniquefy(ifiles)]
                    files = fdum
            except:
                raise ValueError('Input timespan not a tuple of two datetime objects!')
        else:
            raise ValueError('not enough input for file search!')
        if verbose:
            print('the following files have been found:'+msg.INFO(files))
        
        if self.append_data:
            if datakey not in self.files:
                self.files[datakey] = files
            else:
                [self.files[datakey].append(iff) for iff in files]
        else:
            self.files[datakey] = files

        self.files[datakey] = uniquefy(self.files[datakey])
    
    def check_if_loaded(self,datakey,load_RAW=False):
       
        datastr = 'data_raw' if load_RAW else 'data'

        if not hasattr(self,datastr): return self.files[datakey] 
            
        if datakey not in getattr(self,datastr) : return self.files[datakey]

        if datakey not in self.files : 
            msg.error('self.find_files_to_load must be run before self.check_if_loaded')
            return

        orbits_to_load = set([int(parse_CSES_filename(i)['orbitn']) \
            for i in self.files[datakey]]) -  set(self.data[datakey].orbitn)

        return [i for i in self.files[datakey] if int(parse_CSES_filename(i)['orbitn']) in orbits_to_load]
        
################################################################################
############################# FILESYSTEM TOOLS #################################
################################################################################

    def check_path(self):
        """
        Check whether the given path is a path to CSES data, i.e. it is structured in subfolders with the
        following scheme:
            INSTRUMENT/YEAR/DATA/MONTH/FILEN.H5
        e.g. EFD/2018/ELF/08/CSES_01_EFD_2_L02_A1_031920_20180831_050134_20180831_054154_000.h5
        In reality it does only a check of the main folders.
        """
        from glob import glob
        try:
            self.instruments = [i.name for i in self._path.iterdir() if i.is_dir()] 
            #self.instruments = [i[len(self.path):] for i in glob(self.path+'*')] 
        except:
            print('WARNING: the provided folder is not a CSES folder. Reading data will likely fail!')

        CSX = self._P
        instr = []
        for i in CSX['CSES_DATA_TABLE']:
            if i in self.instruments:
                instr.append(i)
            else:
                print('WARNING: '+i+' CSES folder not found in '+ self.path)
        #[print('WARNING: '+i+' CSES folder not found in '+ self.path) for i in CSES_DATA_TABLE if i not in self.instruments]
        del self.instruments
        self.instruments = tuple(instr)

    def get_dataset_path(self, datakey):

        #if self.files.input is None:
        if type(self.orbitn) is str:
            files = self.search_file(datakey, orbitn=self.orbitn,return_path = True)
        elif type(self.search_string) is str:
            files = self.search_file(datakey, search_string=self.search_string,return_path = True)
        else:
            msg.error('file for the desired dataset not found!')
            return None

        return files

    def get_file_path(self,filename):
        """ 
        find file path corresponding to file inside the tree (could be changed to be more universal if
        the convention for the folder changes)
        """ 
        info = parse_CSES_filename(filename)
        return self.search_file(info['datakey'],orbitn=info['orbitn'], get_file_path = True)[0]
        
    

    def search_file(self,datakey, search_string ='',orbitn=None\
        ,return_path = False, timespan = None, get_file_path = False):
        """
        Search for a file matching the desired string for the desired datakey
        
        """
        from glob import glob

        file_identifiers = self._P['CSES_DATAKEYS'][datakey]

        files = None
        unstruct_path = self._unstructured_path_
        CSES_FILESYSTEM = self._P['CSES_FILESYSTEM'] 
        instrument_no = file_identifiers['InstrumentNo']
        instrument = file_identifiers['instrument']
        band = file_identifiers['band']
        
        ignore_structure = self._ignore_structure_
        
        ppath = str(self._path)+'/'
        if not unstruct_path and not ignore_structure:
            fs_struct = CSES_FILESYSTEM[instrument]

            ppath = ppath+instrument+'/'

            for ipath in fs_struct.split('/'):
                if ipath == 'band' or ipath == 'frequency':
                    ppath += band.lower()+'/'
                elif ipath == 'BAND' or ipath == 'FREQUENCY':
                    ppath += band.upper()+'/'
                else:
                    ppath += '*/'
        
        filespaths = glob(ppath)

        if orbitn is None:
            files = [(i,ipath) for srcpath in filespaths for ipath,i in find_file(srcpath,search_string, recursive = ignore_structure)]
            #files = [(i,ipath) for ipath in filespaths for i in find_file(ipath,search_string)]
            files = [(i,ipath) for i,ipath in files if parse_CSES_filename(i)['datakey'] == datakey]
        else:
            files = [(i,ipath) for srcpath in filespaths for ipath,i in find_file(srcpath,orbitn, recursive = ignore_structure)]
            #files = [(i,ipath) for i,ipath in find_file(ipath,orbitn, recursive = ignore_structure)]
            files = [(i,ipath) for i,ipath in files if \
                parse_CSES_filename(i)['orbitn'] == orbitn and\
                parse_CSES_filename(i)['datakey'] == datakey]
        
        if timespan is not None:
            #Lazy way to find orbit in timespan
            #1-get all files available in storage and parse datetimes
            fls = files
            b = [parse_CSES_filename(i) for i,ipath in fls]
            if len(timespan) == 2: 
                t0,t1 = timespan 
                sides = 'both'
            else:
                t0,t1,sides = timespan
            #2-cycle through all of them and for each file do:
            #  a-create list of dates with t0,t1,itstart,itend, labeled with [0,0,1,1]
            #  b-get the argsort of the list: if ranges do overlap or one is contained in the other,
            #    then one of the two elements of the list will change
            #  c-sum the first to element of the label array [0,0,1,1] sorted according to argsort
            #    if overlap or one interval contained in the other, then sum==1, else sum==0 or 2
            files = []
            for ii,i in enumerate(b):
                c = np.array([0,0,1,1])[np.argsort([t0,t1,i['t_start'],i['t_end']])][0:2].sum()
                if c == 1: files.append(fls[ii])
            
            if len(files) and sides !='both': 
                orbits = [parse_CSES_filename(i)['orbitn'] for i,ipath in files]
                fdum = []
                for iorbit,ifile in zip(orbits,files):
                    
                    if sides == 'N':
                        if iorbit[-1] == '0': continue
                    elif sides == 'D':
                        if iorbit[-1] == '1': continue
                    print(iorbit[-1])
                    fdum.append(ifile)
                files = fdum
        
        if files is not None:
            if return_path:
                files = [ipath+i for i,ipath in files]
                #files = [self.get_file_path(i)+i for i in files]
            elif get_file_path:
                files = [ipath for i,ipath in files]
            else:
                files = [i for i,ipath in files]

        return files
    

    def load_HEP(self,instrument_no = '1',unique = True, subset = None, keep_verse_time = True, **kwargs):
        import pandas as pd
        from glob import glob
        from .blombly.tools.objects import AttrDict

        CSX = self._P        
        datakey = 'HEP'+CSX['CSES_DATA_TABLE']['HEP'][instrument_no]
        instrument = 'HEP'
        frequency=CSX['CSES_DATA_TABLE']['HEP'][instrument_no]

        if not hasattr(self,'data'): 
            self.data=AttrDict()
        if not hasattr(self,'aux'): 
            self.aux=AttrDict()
        if not hasattr(self.aux,datakey): 
            self.aux[datakey]={}

        self.find_files_to_load(datakey,unique=True)
        
        files = self.check_if_loaded(datakey)

        for ifiles in files:
            
            infos = parse_CSES_filename(ifiles)
            
            if infos['Instrument'] == 'HEP':
                ifile = ifiles
            else:
                ifile = self.search_file(datakey,orbitn=infos['orbitn'])[0]
            
            ipath = self.get_file_path(ifile)
            
            print('loading HEP file: '+msg.INFO(ipath+ifile))
            res, aux = HEP_load(ifile,ipath,instrument_no,**kwargs)

            index = pd.to_timedelta( res['time'] - res['time'][0],unit='sec') + aux['UTC']
            df = pd.DataFrame(res,index=index)
            if not keep_verse_time : df.drop('time',axis='columns',inplace=True)
            df['orbitn'] = int(infos['orbitn'])
            
            if subset is not None:
                for Cond in subset:
                   df = df[Cond[1](df[Cond[0]],Cond[2])] 

            if datakey not in self.data.keys():
                self.data[datakey] = df.copy()
                del df
            else:
                
                self.data[datakey] = pd.concat([self.data[datakey],df]).sort_index() #self.data[datakey].append(df)

            self.aux[datakey][infos['orbitn']]= aux

            self.aux[datakey]['instrument'] = instrument
            self.aux[datakey]['frequency'] = frequency
            self.aux[datakey]['instrument_no'] = instrument_no


    def load_CSES(self, datakey, subset = None, get_PSD = False, \
        keep_verse_time = True,\
        load_RAW = False, fix_data = True, **kwargs):
        """
        Load desired data from CSES instrument using CSES_load (see CSES_core.py)
        """
        import pandas as pd
        from glob import glob

        CSX = self._P
        print('loading '+datakey+' data...')

        instrument = CSX['CSES_DATAKEYS'][datakey]['instrument']
        instrument_no = CSX['CSES_DATAKEYS'][datakey]['InstrumentNo']
        if instrument == 'HEP':
            self.load_HEP(instrument_no = instrument_no, subset = subset,\
                keep_verse_time = keep_verse_time, **kwargs)
            return

        if datakey is None or datakey not in CSX['CSES_DATAKEYS']:
            msg.error('correct datakey must be provided. use self.available_datakeys() for a list of implemented datakeys')
            return

        print('selected datakey: ' + msg.INFO(datakey))

        dsetname=datakey
        if not hasattr(self,'data'): 
            self.data=AttrDict()
        if not hasattr(self,'aux'): 
            self.aux=AttrDict()
        if get_PSD:
            if not hasattr(self.aux,dsetname+'_P'): 
                self.aux[dsetname+'_P']={}
        else:
            if not hasattr(self.aux,dsetname): 
                self.aux[dsetname] = {}

        if load_RAW:
            if not hasattr(self,'data_raw'):
                self.data_raw = AttrDict()
        
        self.find_files_to_load(datakey,unique=True)
        files = self.check_if_loaded(datakey,load_RAW=load_RAW)
        #files = self.files[dsetname] 
        if files is None or len(files) == 0:
            print(msg.ERROR('WARNING, no file found to load for datakey ')+msg.INFO(dsetname)+\
                  msg.ERROR(' and the given research parameters (self._search_params)'))
            return None
        
        for ifile in files:
            infos = parse_CSES_filename(ifile)
            
            ipath = self.get_file_path(ifile)
            
            print('loading file: '+msg.INFO(ipath+ifile))
            if load_RAW:
                df = load_CSES_raw(ipath+ifile, convert_names = True,spacecraft = self.spacecraft)
                if dsetname not in self.data_raw.keys():
                    self.data_raw[dsetname] = [df]
                else:
                    self.data_raw[dsetname].append(df)
            else:
                if get_PSD:
                    res, aux = CSES_load_PSD(ifile,ipath,CSX = CSX,**kwargs)
                else:
                    df, aux = CSES_load(ifile, path = ipath,\
                        return_pandas = True,\
                        keep_verse_time = keep_verse_time, CSX = CSX, **kwargs)
            
                if subset is not None:
                    subset = sorted(subset, key=len, reverse=True) #sort by length to avoid problems with subset conditions
                    for Cond in subset:
                        if len(Cond) == 4:
                            psize = CSX['CSES_PACKETSIZE'][dsetname]
                            maskd = Cond[1](df[Cond[0]].values[::psize],Cond[2]) 
                            mask = np.zeros(df.shape[0],dtype=bool).reshape(df.shape[0]//psize,psize)
                            mask[maskd,:] = True
                            df = df[mask.flatten()]
                        else:
                            df = df[Cond[1](df[Cond[0]],Cond[2])] 

                if get_PSD:
                    dsetname += '_P'
                    if dsetname not in self.data.keys():
                        self.data[dsetname] = res.copy()
                        del res
                    else:
                        self.data[dsetname] = res.copy() #OVERRIDE UNTIL WE FIND A WAY TO MERGE
                        #self.data[dsetname].append(res)
                    self.aux[dsetname][infos['orbitn']]= aux
                else:
                    if dsetname not in self.data.keys():
                        self.data[dsetname] = df.copy()
                        del df
                    else:
                        self.data[dsetname] = pd.concat([self.data[dsetname],df])
                    self.aux[dsetname][infos['orbitn']]= aux
                
                self.aux[dsetname].update(CSX['CSES_DATAKEYS'][datakey])

        #resorting dataframe
        if dsetname in self.data:
            if type(self.data[dsetname]) is pd.DataFrame:
                self.data[dsetname].sort_index(inplace=True)
            #ADD xarray for PSD sorting and reading   
        if fix_data:
            self.fix_data(datakey,overwrite = True)

    def fix_data(self,datakey,**kwargs):
        """
        Fix known issues in CSES Level 2 data.
        So far only EFD data product are handled. 
        Issues from other product may be found and fixed in the future
        """
        # CHECK IF DATA WERE ALREADY FIXED
        
        if self._ancillary_.get('fix_data_'+datakey,False):
            print(f'{datakey} data already fixed.')
            return

        if datakey in CSES_fix_data[self.spacecraft]:
            df = CSES_fix_data[self.spacecraft][datakey](self._P,self.data[datakey],**kwargs)
            self._ancillary_['fix_data_'+datakey] = True
            #self.data[datakey] = df
        else:
            print(f'{datakey} as no fix method set. skipping...') 
################################################################################
############################### PLOTTING TOOLS #################################
################################################################################


    def plot_orbit(self,datakey,y='lat',x='lon', fig = None, ax = None,profile = 'default',\
                   ion=True,show=True,nskip = 256):
        """
        Plot the orbit of the loaded instrument on the worldmap.
        Parameters
        ----------

        datakey : str
            Key to access the data dictionary containing the orbit data.
        y : str, optional
            Column name for y-axis (latitude). Default is 'lat'.
        x : str, optional
            Column name for x-axis (longitude). Default is 'lon'.
        fig : None or figure object, optional
            If not None, then input figure is used. Default is None.
        ax : None or Axes object, optional
            If not None, then input axes are used. Default is None.
        profile : str or dict, optional
            If str, then the key with the desired plot_orbit kwargs is used.
            Available kwargs are stored in ORBIT_PLOT_TEMPLATES.
            If dict, then use the input dictionary as kwargs. Default is 'default'.
        ion : bool, optional
            If True, enable interactive mode. Default is True.
        show : bool, optional
            If True, display the plot. Default is True.
        Returns
        -------
        fig : figure object
            The matplotlib figure object.
        ax : Axes object
            The matplotlib axes object.
        """

        df = self.data[datakey]

        pltkwargs = ORBIT_PLOT_TEMPLATES[profile] if type(profile) is str else profile
        
        fig,ax = plot_orbit(df[y].values[::nskip],df[x].values[::nskip], fig = fig, ax = ax,ion=ion,show=show,**pltkwargs)

        return fig,ax


    def plot_payloads(self,datakeys,xaxis = 'time', xlabel=None,\
        secondary_xaxis = '',ion=False,spectrograms = None,rotate_xticks=True,psdkwargs={},\
        plot_coordinates=None):
        """
        TBD
        """


        from .blombly import pylab as plt
        
        if ion : plt.ion()

        plot_der = False
        datakeys = [i for i in datakeys if i[-2:] !='_P']
        if spectrograms is not None:
            plot_der = True
            der_key = spectrograms[0]
            der_fld = spectrograms[1]
            addplots = np.sum([len(i) for i in der_fld])
            nplots = len(datakeys) + addplots
        else:
            nplots = len(datakeys)

        if plot_coordinates is not None:
            nplots +=np.size(plot_coordinates)


        fig,ax = plt.subplots(nplots,sharex=True, figsize=(8,2.5*nplots))
        
        fig.subplots_adjust(hspace=0,right=0.8,left=0.1,top=0.95,bottom=0.10)
        if nplots == 1 : ax = [ax] 
        for i,ikey in enumerate(datakeys):
            if i == 0:
                if secondary_xaxis != '':
                    self.plot_payload(ikey,xaxis=xaxis,secondary_xaxis=secondary_xaxis,\
                        fig=fig,ax=ax[i])
                else:
                    self.plot_payload(ikey,xaxis=xaxis,fig=fig,ax=ax[i])
            else:
                self.plot_payload(ikey,xaxis=xaxis,fig=fig,ax=ax[i])
        
        if plot_der:
            j=len(datakeys)
            for i,ikey in enumerate(der_key):
                for k,ifld in enumerate(der_fld[i]):
                    self.plot_spectrogram(ikey,ifld,xaxis=xaxis,fig=fig,ax=ax[j],**psdkwargs)
                    j+=1

        if plot_coordinates is not None:
            if 'j' not in locals(): j=len(datakeys)
            for ikey in plot_coordinates:
                xxx = self.data[datakeys[0]].index.values if xaxis == 'time' else self.data[datakeys[0]][xaxis].values
                ax[j].plot(xxx,self.data[datakeys[0]][ikey])
                ax[j].set_ylabel(ikey)
                j+=1

        ax[-1].set_xlabel(xaxis)
        # rotate thicks
        if rotate_xticks:
            ax[-1].tick_params(axis='x',rotation=45)
        return fig,ax

    def plot_payload(self,datakeyvars,xaxis='time',secondary_xaxis=None,fig=None,ax=None,xlabel=None, unwrap_xrange = None):
        

        CSX = self._P
        if type(datakeyvars) is str: 
            datakey = datakeyvars
            keytoplot = None
        else:
            datakey = datakeyvars[0]
            keytoplot = datakeyvars[1]
        
        from .blombly import pylab as plt
        cols = plt.rcParams['axes.prop_cycle'].by_key()['color'] #colors
        ncol=len(cols) 
        dff = self.data[datakey]
        xxx = dff.index.values if xaxis == 'time' else dff[xaxis].values
        
        orbits = list(set(dff.orbitn))
        orbits.sort()
        for idorb,iorbit in enumerate(orbits):
            mask = dff.orbitn == iorbit
            df = dff[mask]
            xx = xxx[mask]
            if unwrap_xrange is not None:
                xx = arrays.remove_jumps(xx,unwrap_xrange)
            if datakey == 'LAP_50mm':
                ax.semilogy(xx,df['ne'],label=r'$n_e$',color=cols[0])
                ax.set_ylabel(r'$\mathrm{n_e \quad [m^{-3}]}$')
                print(datakey)
            elif datakey in ['EFD_ULF','EFD_ELF','EFD_VLF']:
                ax.plot(xx,np.sqrt(df['Ex']**2+df['Ey']**2+df['Ez']**2),label='|E|',linewidth=1,color='black')
                ax.plot(xx,df['Ex'],label=r'$E_x$',linewidth=1,color=cols[0])
                ax.plot(xx,df['Ey'],label=r'$E_y$',linewidth=1,color=cols[1])
                ax.plot(xx,df['Ez'],label=r'$E_z$',linewidth=1,color=cols[2])
                ax.set_ylabel('E [V/m]')
                print(datakey)
            elif datakey in ['SCM_ULF','SCM_ELF','HPM_FGM1Hz']:
                ax.plot(xx,np.sqrt(df['Bx']**2+df['By']**2+df['Bz']**2),label='|B|',linewidth=1,color='black')
                ax.plot(xx,df['Bx'],label=r'$B_x$',linewidth=1,color=cols[0])
                ax.plot(xx,df['By'],label=r'$B_y$',linewidth=1,color=cols[1])
                ax.plot(xx,df['Bz'],label=r'$B_z$',linewidth=1,color=cols[2])
                ax.set_ylabel('B [nT]')
                print(datakey)
            elif datakey == 'HEPD':
                instrument = self.aux[datakey]['instrument']
                instr_no = self.aux[datakey]['instrument_no']
                
                toplot = [[i[1] for i in CSX['CSES_FILE_TABLE'][instrument][instr_no].items()][0]] if keytoplot is None else keytoplot
                for j,i in enumerate(toplot):
                    #if 'Electron' in i:
                    #    continue
                    ax.semilogy(xx,df[i].values,label=i,linewidth=1,color=cols[j%ncol])
                ax.set_ylabel('Counts')
                print(datakey)
            elif datakey == 'HEPP_L':
                instrument = self.aux[datakey]['instrument']
                instr_no = self.aux[datakey]['instrument_no']
                toplot = [i[1] for i in CSX['CSES_FILE_TABLE'][instrument][instr_no].items()] if keytoplot is None else keytoplot
                for j,i in enumerate(toplot):                
                    ax.semilogy(xx,df[i].values,label=i,linewidth=1,color=cols[j%ncol])
                ax.set_ylabel(toplot[0].split('_')[0])
                print(datakey)
            elif datakey == 'HEPP_H':
                instrument = self.aux[datakey]['instrument']
                instr_no = self.aux[datakey]['instrument_no']
                toplot = [i[1] for i in CSX['CSES_FILE_TABLE'][instrument][instr_no].items()] if keytoplot is None else keytoplot
                for j,i in enumerate(toplot):
                    #if 'Electron' in i:
                    #    continue
                    ax.semilogy(xx,df[i].values,label=i,linewidth=1,color=cols[j%ncol])
                ax.set_ylabel('Counts')
                print(datakey)
            elif datakey == 'HEPP_X':
                instrument = self.aux[datakey]['instrument']
                instr_no = self.aux[datakey]['instrument_no']
                toplot = [i[1] for i in CSX['CSES_FILE_TABLE'][instrument][instr_no].items()] if keytoplot is None else keytoplot
                for j,i in enumerate(toplot):
                    #if 'Electron' in i:
                    #    continue
                    ax.semilogy(xx,df[i].values,label=i,linewidth=1,color=cols[j%ncol])
                ax.set_ylabel('Counts')
                print(datakey)
            elif datakey == 'PAP_':
                [ax.semilogy(xx,df[ikey],label=ikey) for ikey in ['nH+', 'nHe+', 'nO+']]
        
            if idorb==0: 
                ax.legend(loc='best',title=datakey)
            
        #ax.set_title(datakey,loc='left',y=1.0,pad=-14)
            



        if secondary_xaxis is not None:
            if secondary_xaxis in df.keys():
                yy = df[secondary_xaxis].values if secondary_xaxis != 'time' else df.index.values
                ax2 = ax.twiny()
                ax2.plot(yy,np.zeros(len(yy)),linestyle=None,linewidth = 0)
                ax2.set_xlabel(secondary_xaxis)
            
        if xlabel is not None:
            ax[-1].set_xlabel(xlabel)
        return fig,ax
    

    def plot_spectrogram(self,datakey,fieldkey,xaxis='time',secondary_xaxis=None,\
        fig=None,ax=None,xlabel=None,cmap='jet',vmin=None,vmax=None,colorbar_width='2%',plot_colorbar = False):
        
        from .blombly import pylab as plt
        from .blombly.pylab import plots as epp
        from matplotlib.colors import LogNorm

        fig,ax = plt.get_figure(fig,ax,axes=[0.1,0.1,0.7,0.7])
        df = self.data[datakey+'_P']
        orbitn = str(df['position'].orbitn.values[0]).zfill(6)
        xx = df['position'].index.values if xaxis == 'time' else df['position'][xaxis].values

        if datakey+'_P' in self.aux: #in this case, spectra were loaded directly from the files
            field_unit = self.aux[datakey+'_P'][orbitn]['units'][fieldkey+'_P']
            units = r'$\mathrm{' + (field_unit.decode('utf-8') if isinstance(field_unit, bytes) else field_unit) + r'}$'
        elif fieldkey in self.aux[datakey][orbitn]['units'].keys():
            field_unit = self.aux[datakey][orbitn]['units'][fieldkey]
            units = r'$[\mathrm{' + (field_unit.decode('utf-8') if isinstance(field_unit, bytes) else field_unit) + r'}]^2/\mathrm{Hz}$'
        elif fieldkey.split('_')[0] in self.aux[datakey][orbitn]['units'].keys():
            base_field_unit = self.aux[datakey][orbitn]['units'][fieldkey.split('_')[0]]
            units = '[' + (base_field_unit.decode('utf-8') if isinstance(base_field_unit, bytes) else base_field_unit) + r'$]^2/\mathrm{Hz}$'
        else:
            units = r'[?$]^2/\mathrm{Hz}$' 
        units = units.replace("(", "{").replace(")", "}")

        if vmax is None : vmax = df['psd'][fieldkey].max()
        if vmin is None : vmin = np.percentile(df['psd'][fieldkey],5)
        ims = ax.pcolormesh(xx,df['freq'],df['psd'][fieldkey].transpose(),cmap=cmap,norm=LogNorm(vmin=vmin,vmax=vmax))
        if plot_colorbar:
            epp.add_subplot_colorbar(fig,ax,ims,width=colorbar_width,\
                        label=units)
        ax.set_ylabel( 'Hz  ('+fieldkey+')') 

        if secondary_xaxis is not None:
            if secondary_xaxis in df.keys():
                yy = df.position[secondary_xaxis].values if secondary_xaxis != 'time' else df.index.values
            
                ax2 = ax.twiny()
                ax2.plot(yy,np.zeros(len(yy)),linestyle=None,linewidth = 0)
                ax2.set_xlabel(secondary_xaxis)
        if xlabel is not None:
            ax[-1].set_xlabel(xlabel)
        return fig,ax
################################################################################
#################### MANIPULATION AND DATA ANALYSIS TOOLS ######################
################################################################################
    
    def interpolate_inst1_to_inst2(self, inst1, inst2, tags, track_origin=False):
        """
        Interpolates data from one instrument (inst1) to another (inst2) for specified tags.
        Parameters
        ----------
        inst1 : str
            The datakey of the source instrument whose data will be interpolated (stored in self.data).
        inst2 : str
            The datakey of the target instrument to which data will be interpolated (stored in self.data).
        tags : list
            List of column names (tags) to interpolate from inst1 to inst2.
        track_origin : bool, optional
            If True, appends the source instrument name to the interpolated column name in inst2.
            If False, overwrites or creates columns in inst2 with the same tag names.
        Notes
        -----
        - The method assumes that `self.data` is a dictionary-like object containing pandas DataFrames for each instrument.
        - The index of each DataFrame is expected to be time-based and convertible to integer nanoseconds.
        - Interpolated columns are added to the target instrument's DataFrame.
        - The interpolation operation is recorded in `self._ancillary_['interpolate']`.
        """
    
        t_1 = self.data[inst1].index.values.astype(np.int64)
        t_2 = self.data[inst2].index.values.astype(np.int64)
        t0 = t_1[0]
        t_1 -=t0
        t_2 -=t0
        t_1 = t_1.astype(np.float64)
        t_2 = t_2.astype(np.float64)
        
        for i in tags:
            if track_origin:
                self.data[inst2][i+'_'+inst1] = np.interp(t_2,t_1,self.data[inst1][i].values)
            else:
                self.data[inst2][i] = np.interp(t_2,t_1,self.data[inst1][i].values)

        self._ancillary_['interpolate'] = {}

        self._ancillary_['interpolate'][inst1+'2'+inst2] = tags

    def get_spectrogram(self,datakey,fieldkeys,packetsize = None,\
        method = 'stft', allow_shrinking = True,  **kwargs ):
        """
        Calculate Spectrograms (STFT PSD) from the desired instrument_frequency
        previouly loaded in self.data on the selected keys/fields,
        based on csespy.CSES_PACKETSIZE (if packetsize is None).

        Parameters
        ----------
        datakey : str
            key of self.data containing the pandas.Dataframe with the field keys
            of which one want to compute the PSD
        fieldkeys: list of str
            keys of which one wants to compute the spectrogram
        packetsize : None or int (used if STFT is selected)
            size of the STFT chunk. Default is None, which is equivalent to
            the packet size of EFD-02, stored in csespy.CSES_PACKETSIZE
        allow_shrinking : bool
            if True, then the STFT will be computed on the whole data and
            if the length of the data is not a multiple of packetsize, the data will be
            shrinked by discarding the last points.
            If False, then an error is raised if the length of the data is not
            a multiple of packetsize.
        method : 
        **kwargs : 
            optional keyword arguments passed to stft or wavelet transform function
            (see blombly.analysis.spectra)
        """
        CSX = self._P
        if datakey not in self.data:
            msg.error('datakey '+datakey+' not found in self.data! Please load the desired data first.')
            return

        df = self.data[datakey]
        nx = df.shape[0]
        fs = CSX['CSES_SAMPLINGFREQS'][datakey]
        if not all([i in df.keys() for i in fieldkeys]):
            msg.error('Some of the fieldkeys '+str(fieldkeys) +'not found in self.data.'+datakey+'. Returning')
            return

        if packetsize is None:
            packetsize = CSX['CSES_PACKETSIZE'][datakey]
        if nx// packetsize != nx/ packetsize:
            if allow_shrinking:
                nx = nx - (nx % packetsize)
            else:
                msg.error('wrong input packetsize! Returning')
                return

        if method == 'stft':
            from .blombly.analysis.spectra import stft as trans
            if 'window' not in kwargs : kwargs['window']='hann'
            if 'nperseg' not in kwargs : kwargs['nperseg'] = packetsize
            kwargs['transpose'] = True
        if method == 'cwt':
            from .blombly.analysis.spectra import cwt as trans

        #extracting and manipulating the desired fields
        #ff = {i:df[i].values.reshape([nx//packetsize,packetsize]) for i in fieldkeys}
        ff = {i:trans(df[i].values[:nx], fs, **kwargs) for i in fieldkeys}
        #ff = {i:stft(df[i].values, fs = fs, window = window, \
        #                nperseg = packetsize, noverlap=0, boundary = None,padded = False) for i in fieldkeys}
        psd = {i:(np.abs(ff[i][-1])**2).transpose() for i in ff}
        nu = ff[fieldkeys[0]][0]
        tt = df.index.values[:nx:packetsize]
        dff = df[:nx:packetsize].drop(columns=fieldkeys)
        self.data[datakey+'_P'] = {'psd':psd,'freq':nu,'time':tt,'position':dff}

######WRITING TO DATABASES MACHINERY######
    def save_data_to_h5(self,filepath,dataset_name,filename=None,mode='a',return_outputfilepath=False,track_origin=True,**kwargs):

        from .blombly.io import save_dataframe_to_h5
        
        orbitn = self.orbitn if type(self.orbitn) is str else self.orbitn[0]+'-'+self.orbitn[-1]
        
        if filename is None: 
            if dataset_name in self.aux:
                time0=self.aux[dataset_name][orbitn]['UTC'].isoformat('_')
            filename = dataset_name+'_'+orbitn+'_'+time0+'.h5'
        
        msg.info('saving '+dataset_name+' DataFrame to '+filepath+filename+'...')
        
        dats = self.data[dataset_name].copy()
        
        idx = {'time':(dats.index.values.astype(float)-dats.index.values.astype(float)[0])/1e9,\
               't0':datetime_to_versetime(dats.index[0])}
        del dats['time']
        if track_origin:
            save_dataframe_to_h5(filepath+filename,dats,group=dataset_name+'/',index=idx,mode=mode,**kwargs)
        else:
            save_dataframe_to_h5(filepath+filename,dats,group='/',index=idx,mode=mode,**kwargs)
        if return_outputfilepath:
            return filepath+filename
    
################################################################################
#########################      AUXILIARY TOOLS         #########################
################################################################################

    def get_CHAOS(self,datakey,as_output = False,ref_frame='ecef'):
        
        if all([i in self.data[datakey] for i in ['Bx_chaos','By_chaos','Bz_chaos']]):
            print('Mag. field from CHAOS already calculated for '+datakey+'.')
            return
        if as_output:
            return get_CHAOSmag(self.data[datakey],as_output = True,ref_frame=ref_frame)
        get_CHAOSmag(self.data[datakey],as_output=False,ref_frame = ref_frame)
    
    def get_spacecraft_speed(self,datakey='EFD_ELF',ref_frame='ecef',\
        regularize_speed = False,dt_lowfilt=20):
        """
        Compute spacecraft velocity from lat,lon,alt and time contained in the L2 
        data using central finite differences
        ref_frame : str
            'wgs84_spherical' : this SHOULD be the frame of the data given by the chineses
                in this frame is different from the usual spherical coordinate system, in such that
                    x: is along meridians with the direction of increasing latitude (i.e. -theta)
                    z: is the radial direction, but with an inverse sense (i.e. vectors going TOWARD the center, -r)
                    y: hopefully completes the system with HOPEFULLY a right-handed convention
                       i.e, is along phi
            'ecef' : this is the wgs84 (cartesian) coordinate system
        """

        if not hasattr(self.data,datakey):
            raise ValueError('You must load the data for the desired input datakey :'+datakey)
       
        data = self.data[datakey]
        
        CSX = self._P
        from .blombly.math.derivFD import derivfield as deriv #central finite differences derivative 
        t = data.index.values.astype(float)/1e9 #dt in seconds
        t-=t[0]
        if regularize_speed:
            from scipy.interpolate import splrep,splev
            nskip = CSX['CSES_PACKETSIZE'][datakey]
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

        if ref_frame == 'wgs84_spherical' or ref_frame == 'geo':
            
            x,y,z = convert_GPS_to_ECEF(data.lat.values,data.lon.values,data.alt.values)
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
        
        data['vsx'] = vx
        data['vsy'] = vy
        data['vsz'] = vz
    
    def get_vsxb_drift(self,datakey, vtags = ['vsx','vsy','vsz'],\
        btags = ['Bx_chaos','By_chaos','Bz_chaos']):

        dat = self.data[datakey]

        Bx = dat[btags[0]].values 
        By = dat[btags[1]].values 
        Bz = dat[btags[2]].values 
        vsx = dat[vtags[0]].values 
        vsy = dat[vtags[1]].values 
        vsz = dat[vtags[2]].values 

        #B is in nanoTesla
        dat['VsxB_x'] = (vsy*Bz - vsz*By)*1e-9 
        dat['VsxB_y'] = (vsz*Bx - vsx*Bz)*1e-9 
        dat['VsxB_z'] = (vsx*By - vsy*Bx)*1e-9
    
    def remove_vsxb_drift(self,datakey='EFD_ELF',overwrite=False):
        """
        remove E=vs X B drift from the EFD electric field contained 
        in self.data[instrument+'_'+frequency], so to allow removal from interpolated
        instruments
        the pd dataframe must contain the VsxB_[xyz] fields as given by self.get_vsxb_drift
        and the E_[xyz] fields. 

        WARNING: the two vector fields must be in the same right-handed orthogonal ref.frame.
        """
        efd = self.data[datakey]
        if any([not hasattr(efd,'VsxB_'+i) for i in ['x','y','z']]):
            raise ValueError('VsB not found. use self.get_vsxb_drift!')
        if any([not hasattr(efd,'E'+i) for i in ['x','y','z']]):
            raise ValueError('E field not found in self.data["'+datakey+'"]!')
       
        if overwrite:
            efd['Ex'] -=efd['VsxB_x']
            efd['Ey'] -=efd['VsxB_y']
            efd['Ez'] -=efd['VsxB_z']

        else:
            efd['Ex_nodrift'] =efd['Ex']-efd['VsxB_x']
            efd['Ey_nodrift'] =efd['Ey']-efd['VsxB_y']
            efd['Ez_nodrift'] =efd['Ez']-efd['VsxB_z']
    

    def get_aacgm_coord(self, datakey='EFD_ELF', minify = False, nskip = None, **kwargs):

        CSX = self._P
        #datakey=instrument+'_'+frequency
        inst = self.data[datakey]
        
        if nskip is None:
            nskip = CSX['CSES_PACKETSIZE'][datakey]

        #if instrument.lower() == 'efd' and minify == False:
        #    minify = 1
        #if minify: 
        #    inst = inst.iloc[::nskip] #DETACHING inst from self.data[instrument]
            
        mlat,mlon,mlt = dataframe_aacgm_convert(inst.iloc[::nskip],**kwargs)
        
        if minify:
            inst = inst.iloc[::nskip]
            inst['mag_lat'] = mlat
            inst['mag_lon'] = mlon
            inst['mlt'] = mlt
            return inst

        if nskip > 1:
            fld = self.data[datakey]
            from scipy.interpolate import interp1d as interp1
            xx = inst.iloc[::nskip].index.values.astype(float)
            xnew = inst.index.values.astype(float) - xx[0]
            xx-=xx[0]
            fld['mag_lat'] = interp1(xx,mlat,bounds_error=False,fill_value='extrapolate')(xnew)
            fld['mag_lon'] = arrays.interp1_jumps(xnew,xx,mlon,[-180,180])
            fld['mlt'] = arrays.interp1_jumps(xnew,xx,mlt,[0,24])
            #fld['mlt'] = interp1(xx,mlt,bounds_error=False,fill_value='extrapolate')(xnew)
            #fld['mag_lon'] = interp1(fld['lat'],lat,mlon) 
            #fld['mlt'] = interp1(fld['lat'],lat,mlt) 

################################################################################
#########################some fast diagnostic tool  tbd#########################
################################################################################
    
class CSES_database():

    methods = {'pandas-hdf5':'load_pd_hdf5','pandas-dataframe':'load_pd_dataframe'}

    def __init__(self,dbbuf = None, source = 'pandas-hdf5'):
        """
        Class for managing of CSES orbit databases

        default initialization assumes an hdf5 file containing a pandas Dataframe of the orbits.
        Other methods may be implemented.

        parameters
        ----------
        dbbuf : obj or str
            str: file path of the file containing the database
            obj: buffer of data (e.g. a pd dataframe or an xarray or other) from which to read the database (to be implemented)
                 WARNING: the right method must be chosen accordingly (see below)

        source: str
            'pandas': the buffer/file source is/contains a pandas dataframe
        """

        self._loaded_ = False
        self.source = source
        if type(dbbuf) is str: self.dbfile = dbbuf

        self.check_buf(dbbuf)
        
        self.load_db(dbbuf)

        # Default selection is the full database.
        self.sel_db = self.db

    def check_buf(self,dbbuf):
        import pandas as pd
        if type(dbbuf) is pd.DataFrame:
            self.source = 'pandas-dataframe'
        elif isinstance(dbbuf, CSES_database):
            self.__dict__ = dbbuf.__dict__.copy()
    def load_db(self,dbbuf):
        """
        load database using desired buf/file and source.
        """
        if not self._loaded_:
            getattr(self,self.methods[self.source])(dbbuf)
            self._loaded_ = True

    def load_pd_hdf5(self,dbbuf):
        
        import pandas as pd
        
        self.db = pd.read_hdf(dbbuf)

    def load_pd_dataframe(self,dbbuf):

        self.db = dbbuf
    def search_orbit(self,orbit_database_ranges = None, orbitn = None, timespan = None,\
                     latspan = None, lonspan = None, side = None,\
                     return_orbitn = True, use_selected_db = False,**kwargs): 
        """
        
        This is a generic method to select a subset of orbits fulfilling the conditions set in ranges (see below).

        parameters
        ----------
        orbit_database_ranges = 3-elements tuple or tuple/list of 3-elements tuples with the following structures
            (('key', boolean_function, comparing value),)

            for example: self.search_orbit([('lat',numpy.greater,44),('lat',numpy.less,48),('lon',numpy.greater,10),('lon',numpy.less,15)]) 
            will return all orbit numbers of orbits fulfilling the condition "48>latitude > 44" and "15 > longitude > 10".

        return_orbitn : bool
            if False, then the full database information of the selected orbit is returned.
            if True, only a list of the orbit numbers fulfilling the conditions set in ranges is returned
        
        input_db : None or pandas dataframe
        """
        
        ranges = orbit_database_ranges

        df = self.db if not use_selected_db else self.sel_db
        
        if 'spacecraft' in kwargs:
            if 'spacecraft' in df.keys():
                sc = kwargs['spacecraft']
                mask = [i==sc for i in df.spacecraft.values]
                df = df[mask]
            else:
                msg.warning('spacecraft key not found in database! skipping spacecraft selection!')
        
        seldb = False
        if ranges is not None:
            for Cond in ranges:
                df = df[Cond[1](df[Cond[0]],Cond[2])] 
            seldb = True
            self.sel_db = df

        if orbitn is not None:
            df = self.search_orbit_orbitn(orbitn,use_selected_db = seldb, return_orbitn = False)
            seldb = True
        if timespan is not None:
            df = self.search_orbit_timespan(timespan,use_selected_db = seldb, return_orbitn = False)
            seldb = True
        if latspan is not None:
            df = self.search_orbit_lat(latspan,use_selected_db = seldb, return_orbitn = False)
            seldb = True
        if lonspan is not None:
            df = self.search_orbit_lon(lonspan,use_selected_db = seldb, return_orbitn = False)
            seldb = True
        if side != 'both' and side is not None:
            df = self.search_orbit_side(side,use_selected_db = seldb, return_orbitn = False)
            seldb = True

        #self.sel_db = df

        #if df.size == 0 : return None

        if not return_orbitn:
            return df
        
        return np.unique(df.orbitn)

    def search_orbit_lat(self,lat,**kwargs):
        """
        find all available orbits in given latitude range
        """

        return self.search_orbit([('lat',np.greater,np.min(lat)),('lat',np.less,np.max(lat))],**kwargs)
    
    def search_orbit_lon(self,lon,**kwargs):
        """
        find all available orbits in given latitude range
        """

        return self.search_orbit([('lon',np.greater,np.min(lon)),('lon',np.less,np.max(lon))],**kwargs)


    def search_orbit_latlon(self,lat,lon,**kwargs):
        """
        find all available orbits in given latitude and longitude ranges
        """

        return self.search_orbit([('lat',np.greater,np.min(lat)),('lat',np.less,np.max(lat)),\
                                  ('lon',np.greater,np.min(lon)),('lon',np.less,np.max(lon))],**kwargs)

    def search_orbit_timespan(self,timespan, return_orbitn = True, use_selected_db = False,**kwargs):
        """
        find all available orbits in given temporal range
        """

        df = self.db if not use_selected_db else self.sel_db

        mask = (df.index > timespan[0]) * (df.index < timespan[1])

        df = df[mask]

        if 'spacecraft' in kwargs:
            if 'spacecraft' in df.keys():
                sc = kwargs['spacecraft']
                mask = [i==sc for i in df.spacecraft.values]
                df = df[mask]
            else:
                msg.warning('spacecraft key not found in database! skipping spacecraft selection!')
        
        self.sel_db = df
        
        if self.sel_db.size == 0 : return self.sel_db

        if len(timespan)  == 3:
            if timespan[-1] != '':
                
                ND = [i[-1] for i in self.sel_db.orbitn] 
            
                if timespan[2] == 'D':
                    mask = [i == '0' for i in ND]
                if timespan[2] == 'N':
                    mask = [i == '1' for i in ND]
            
                self.sel_db = self.sel_db[mask]

        if not return_orbitn:
            return self.sel_db

        return np.unique(self.sel_db.orbitn)
    
    #def search_orbit_side(self,side, return_orbit = True, use_selected_db = False):
    #    """
    #    find all available orbits in given temporal range
    #    """

    #    df = self.db if not use_selected_db else self.sel_db

    #    if self.sel_db.size == 0 : return self.sel_db

    #    if side is not None and side != 'both':        
    #        ND = [i[-1] for i in self.sel_db.orbitn] 
    #        if side.upper() == 'D' or side.lower() == 'night':
    #            mask = [i == '0' for i in ND]
    #        if side.upper() == 'N' or side.lower() == 'night':
    #            mask = [i == '1' for i in ND]
    #        
    #        self.sel_db = self.sel_db[mask]

    #    if not return_orbitn:
    #        return self.sel_db

    #    return np.unique(self.sel_db.orbitn)


    def search_orbit_latlontimespan(self,lat,lon,timespan, return_orbitn = True, use_selected_db = False,**kwargs):
        """
        self explaining
        """

        df = self.db if not use_selected_db else self.sel_db

        df = self.search_orbit_latlon(lat,lon,return_orbitn = False)
        
        if 'spacecraft' in kwargs:
            if 'spacecraft' in df.keys():
                sc = kwargs['spacecraft']
                mask = [i==sc for i in df.spacecraft.values]
                df = df[mask]
            else:
                msg.warning('spacecraft key not found in database! skipping spacecraft selection!')
        
        if df.size == 0: return df

        df = self.search_orbit_timespan(timespan,use_selected_db = True)

        if return_orbitn: 
            return np.unique(self.sel_db.orbitn)

        return self.sel_db
    
    def search_orbit_orbitn(self,orbitn, return_orbitn = True, use_selected_db = False,**kwargs):
        """
        self explaining
        """

        df = self.db if not use_selected_db else self.sel_db

        
        orbs = [str(i).zfill(6) for i in orbitn] if type(orbitn) is list else str(orbitn).zfill(6)
                
        if type(orbs) is list:
            mask = np.array([df.orbitn.values == i for i in orbs])
           
            if mask.ndim == 2: mask = np.sum(mask,axis=0,dtype=bool) 
        else:
            mask = df.orbitn.values == orbs 
        
        df = df[mask]
        if 'spacecraft' in kwargs:
            if 'spacecraft' in df.keys():
                sc = kwargs['spacecraft']
                mask = [i==sc for i in df.spacecraft.values]
                df = df[mask]
            else:
                msg.warning('spacecraft key not found in database! skipping spacecraft selection!')
        
        self.sel_db = df

        if return_orbitn: 
            return np.unique(self.sel_db.orbitn)

        return self.sel_db

    def search_orbit_side(self,whichside, return_db = False, return_orbitn = True, use_selected_db = False,**kwargs):
        """
        self explaining
        

        whichside: str
            'night': select only orbits on the night side (ascending, orbitn[-1] = '1')
            'day': select only orbits on the day side (ascending, orbitn[-1] = '0')
            'both': does nothing 
        return_db : bool
            if True, returns the DataFrame with the selected orbit sides. self.sel_db is not updated
        """

        df = self.db if not use_selected_db else self.sel_db

        if whichside == 'both':
            if return_orbitn:
                return np.unique(df.orbitn)
            else:
                self.sel_db = df
                return 
        side = '1' if whichside == 'night' else '0'
        mask = [i[-1]==side for i in df.orbitn.values]

        df = df[mask]
        if 'spacecraft' in kwargs:
            if 'spacecraft' in df.keys():
                sc = kwargs['spacecraft']
                mask = [i==sc for i in df.spacecraft.values]
                df = df[mask]
            else:
                msg.warning('spacecraft key not found in database! skipping spacecraft selection!')
        if return_db:
            return df
        
        self.sel_db = df

        if return_orbitn: 
            return np.unique(self.sel_db.orbitn)

        return self.sel_db
    
    def plot_orbit(self,df=None,y='lat',x='lon', fig = None, ax = None,profile = 'default',\
                   ion=True,show=True):
        """
        Plot the orbit of the input pd.DataFrame or of the sel_db (or of the db) on the worldmap, using CSES_aux.plot_orbit

        Parameters
        ----------

        Plot the orbit of the loaded instrument on the worldmap.
        Parameters
        ----------

        df : pd.DataFrame or None, optional
            Dataframe containing the orbit Information. If None, then the sel_db attribute is used if present,
            otherwise the db attribute is used. Default is None.
        y : str, optional
            Column name for y-axis (latitude). Default is 'lat'.
        x : str, optional
            Column name for x-axis (longitude). Default is 'lon'.
        fig : None or figure object, optional
            If not None, then input figure is used. Default is None.
        ax : None or Axes object, optional
            If not None, then input axes are used. Default is None.
        profile : str or dict, optional
            If str, then the key with the desired plot_orbit kwargs is used.
            Available kwargs are stored in ORBIT_PLOT_TEMPLATES.
            If dict, then use the input dictionary as kwargs. Default is 'default'.
        ion : bool, optional
            If True, enable interactive mode. Default is True.
        show : bool, optional
            If True, display the plot. Default is True.
        Returns
        -------
        fig : figure object
            The matplotlib figure object.
        ax : Axes object
            The matplotlib axes object.
       
        """

        if df is None:
            if hasattr(self,'sel_db'):
                df = self.sel_db
            else:
                df = self.db

        pltkwargs = ORBIT_PLOT_TEMPLATES[profile] if type(profile) is str else profile
        
        fig,ax = plot_orbit(df[y].values,df[x].values, fig = fig, ax = ax,ion=ion,show=show,**pltkwargs)

        return fig,ax


    def fix_lonlat(self,df = None, return_db = False):

        if df is None:
            if hasattr(self,'sel_db'):
                df = self.sel_db
            else:
                df = self.db
        else:
            return_db = True
        
        orbits = set(df.orbitn.values)
        
        for iorbit in orbits:
            dmask = df.orbitn.values == iorbit
            dff = df[df.orbitn.values == iorbit]

            lons,lats = fix_lonlat(dff.lon.values,dff.lat.values,dff.index.values)
            df.loc[dmask,'lon'] = lons
            df.loc[dmask,'lat'] = lats

        if return_db : return df
