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
from .blombly.io import msg
from attrdict import AttrDict


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

    def __init__(self, path='./',search_string = None,orbitn=None,timespan=None,unstructured_path=False,\
                 orbit_database_buf = None, database_source = 'pandas-hdf5'):


        self.path = path
        self.files = AttrDict()
        #self.files['input'] = None #THIS IS DEPRECATED AND HAS TO BE REMOVED
        self.search_string = search_string
        self.orbitn = orbitn
        self.append_data = False
        self.timespan = None
        self._ancillary_={}
        self._unstructured_path_ = unstructured_path
        if not unstructured_path: self.check_path()

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
                            latspan = None, lonspan = None, append = True):
        """
        set the data selection method for loading the data (using CSES.load_CSES or other methods)

        Data selections are mutually exclusive and ordered in priority
        
        1) orbitn; 2) search_string; 3) timespan , latspan, lonspan

        parameters
        ----------
        orbitn : str or list of str
            orbit number(s) of CSES to be loaded.
        search_string : str
            string that is contained in the filename that one wants to load
        timespan : tuple 
            either a tuple of datetime of len == 2 or a tuple of len ==3 with two datetime
            and a string specifying day 'D', night 'N' side or both ''
            
            The two datetime specify the desired time interval to be loaded 
        latspan : 2-elements arraylike
            latitudinal range of the desired orbit
        lonspan : 2-elements arraylike
            longitudinal range of the desired orbit
        
        WARNING: both latspan and lonspan require an orbit database to be loaded. If not so, an error will be thrown.
        """
        self.search_string = search_string
        self.orbitn = orbitn
        self.timespan = timespan
        self.latspan = latspan
        self.lonspan = lonspan
        self.append_data = append

        if not append:
            self.files = AttrDict()
            self.files['input'] = None #THIS IS DEPRECATED AND HAS TO BE REMOVED
            self._ancillary_={}
            if hasattr(self,'data') : 
                del self.data 
                del self.aux
       
        if latspan is None and lonspan is None:
            return
        #Section executed if latlon ranges are given
        if orbitn is None and search_string is None:
            
            if not hasattr(self,'orbitdb'):
                self.latspan = None
                self.lonspan = None
                msg.error('Orbit database not loaded! Ignoring input latspan/lonspan...')
                return
            
            csdb = self.orbitdb
           
            use_sel_db = False
            if timespan is not None:
                orbits = csdb.search_orbit_timespan(timespan, return_orbitn = True, use_selected_db = use_sel_db)
                use_sel_db = True
            if latspan is not None:
                orbits = csdb.search_orbit_lat(latspan, return_orbitn = True, use_selected_db = use_sel_db)
                use_sel_db = True
            if lonspan is not None:
                orbits = csdb.search_orbit_lon(lonspan, return_orbitn = True, use_selected_db = use_sel_db)
                use_sel_db = True

            self.orbitn = list(orbits)

            if len(self.orbitn) == 0 :
                msg.warning('Orbit(s) satisfying lon/lat/time constraint NOT FOUND!')

    def find_available_files(self,search_string ='',orbitn=None,timespan=None,**kwargs):
        outs = {}

        for instr in CSES_DATA_TABLE:
            outs[instr]={}
            for ino in CSES_DATA_TABLE[instr]:
                ifreq = CSES_DATA_TABLE[instr][ino]
                outs[instr][ifreq] = self.search_file(search_string = search_string, orbitn= orbitn, \
                    instrument=instr, frequency = ifreq, timespan = timespan,**kwargs)
        return outs

    def find_files_to_load(self,instrument,frequency,instrument_no,unique=True,verbose=False):
        if self.orbitn is not None:
            if type(self.orbitn) is str:
                files = self.search_file(orbitn=self.orbitn,instrument=instrument,\
                    frequency = frequency, instrument_no = instrument_no)
                #sometimes there are two files for the same orbit.
                #In that case, the file with the larger timespan is selected.
                files = uniquefy(files)
            elif type(self.orbitn) is list:
                try:
                    files = []
                    for iorbitn in self.orbitn:
                        ifiles = self.search_file(orbitn=iorbitn,instrument=instrument,\
                            frequency = frequency, instrument_no = instrument_no)
                        #sometimes there are two files for the same orbit.
                        #In that case, the file with the larger timespan is selected.
                        ifiles = uniquefy(ifiles)
                        [files.append(ifi) for ifi in ifiles]
                except:
                    raise ValueError('Not all values inside self.orbitn are strings') 
        elif type(self.search_string) is str:
            files = self.search_file(self.search_string,instrument=instrument,\
                frequency = frequency, instrument_no = instrument_no)
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
                files = self.search_file(instrument=instrument, frequency = frequency,\
                    instrument_no = instrument_no, timespan = timespan[:-1])
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
            if instrument+'_'+frequency not in self.files:
                self.files[instrument+'_'+frequency] = files
            else:
                [self.files[instrument+'_'+frequency].append(iff) for iff in files]
        else:
            self.files[instrument+'_'+frequency] = files

        self.files[instrument+'_'+frequency] = uniquefy(self.files[instrument+'_'+frequency])
    
    def check_if_loaded(self,instrument,frequency,load_RAW=False):
       
        datastr = 'data_raw' if load_RAW else 'data'

        dsetname = instrument+'_'+frequency
        if not hasattr(self,datastr): return self.files[dsetname] 
            
        if dsetname not in getattr(self,datastr) : return self.files[dsetname]

        if dsetname not in self.files : 
            msg.error('self.find_files_to_load must be run before self.check_if_loaded')
            return

        orbits_to_load = set([int(parse_CSES_filename(i)['orbitn']) \
            for i in self.files[dsetname]]) -  set(self.data[dsetname].orbitn)

        return [i for i in self.files[dsetname] if int(parse_CSES_filename(i)['orbitn']) in orbits_to_load]
        
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
            self.instruments = [i[len(self.path):] for i in glob(self.path+'*')] 
        except:
            print('WARNING: the provided folder is not a CSES folder. Reading data will likely fail!')

        instr = []
        for i in CSES_DATA_TABLE:
            if i in self.instruments:
                instr.append(i)
            else:
                print('WARNING: '+i+' CSES folder not found in '+ self.path)
        #[print('WARNING: '+i+' CSES folder not found in '+ self.path) for i in CSES_DATA_TABLE if i not in self.instruments]
        del self.instruments
        self.instruments = tuple(instr)

    def get_dataset_path(self, instrument='EFD', instrument_no=None, frequency = 'ELF'):

        #if self.files.input is None:
        if type(self.orbitn) is str:
            files = self.search_file(orbitn=self.orbitn,instrument=instrument,\
                instrument_no=instrument_no, frequency = frequency,return_path = True)
        elif type(self.search_string) is str:
            files = self.search_file(search_string=self.search_string,instrument=instrument,\
                instrument_no=instrument_no, frequency = frequency,return_path = True)
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
        return self.search_file(orbitn=info['orbitn'], instrument=info['Instrument'],\
            frequency = info['Data Product'], get_file_path = True)[0]
        
    

    def search_file(self,search_string ='',orbitn=None, instrument='EFD', instrument_no=None,\
        frequency = 'ELF',return_path = False, timespan = None, get_file_path = False):
        """
        Search for a file matching the desired string for the desired instrument and frequency
        
        WARNING: Instrument_no and frequency are redundant, since they give the same information
        if instrument_no is not None, then this key overrides the frequency key.
        """
        from glob import glob
       
        files = None
        unstruct_path = self._unstructured_path_
        
        if instrument_no is not None : 
            frequency = CSES_DATA_TABLE[instrument][instrument_no]
        else:
           instrument_no = get_dictkey_from_value(CSES_DATA_TABLE[instrument],frequency)[0]
       
        if unstruct_path:
            ppath = self.path
        else:
            fs_struct = CSES_FILESYSTEM[instrument]

            ppath = self.path+instrument+'/'

            for ipath in fs_struct.split('/'):
                if ipath == 'frequency':
                    ppath += frequency.lower()+'/'
                elif ipath == 'FREQUENCY':
                    ppath += frequency.upper()+'/'
                else:
                    ppath += '*/'
        
        filespaths = glob(ppath)

        if orbitn is None:
            files = [(i,ipath) for ipath in filespaths for i in find_file(ipath,search_string)]
            files = [(i,ipath) for i,ipath in files if \
                parse_CSES_filename(i)['Instrument'] == instrument and\
                parse_CSES_filename(i)['Instrument No.'] == instrument_no]
        else:
            files = [(i,ipath) for ipath in filespaths for i in find_file(ipath,orbitn)]
            files = [(i,ipath) for i,ipath in files if \
                parse_CSES_filename(i)['orbitn'] == orbitn and\
                parse_CSES_filename(i)['Instrument'] == instrument and\
                parse_CSES_filename(i)['Instrument No.'] == instrument_no]

        
        
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

        datakey = 'HEP'+CSES_DATA_TABLE['HEP'][instrument_no]
        instrument = 'HEP'
        frequency=CSES_DATA_TABLE['HEP'][instrument_no]

        if not hasattr(self,'data'): 
            self.data=AttrDict()
        if not hasattr(self,'aux'): 
            self.aux=AttrDict()
        if not hasattr(self.aux,datakey): 
            self.aux[datakey]={}

        self.find_files_to_load(instrument,frequency,instrument_no,unique=True)
        
        files = self.check_if_loaded(instrument,frequency)

        for ifiles in files:
            
            infos = parse_CSES_filename(ifiles)
            
            if infos['Instrument'] == 'HEP':
                ifile = ifiles
            else:
                ifile = self.search_file(orbitn=infos['orbitn'],instrument='HEP',instrument_no=instrument_no)[0]
            
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
                self.data[datakey] = self.data[datakey].append(df)

            self.aux[datakey][infos['orbitn']]= aux

            self.aux[datakey]['instrument'] = instrument
            self.aux[datakey]['frequency'] = frequency
            self.aux[datakey]['instrument_no'] = instrument_no

    def load_HPM(self, subset = None,instrument_no='5',unique = True, keep_verse_time = True,**kwargs):
        """
        This method is kept for legacy reasons. Now is simply a wrapper that calls
        
        CSES.load_CSES(instrument='HPM',frequency='FGM1Hz')
        load HPM data from files matching the string and put them into a pandas dataframe
        
        Optional arguments:
            subset = 3-elements tuple or tuple/list of 3-elements tuples with the following structures
                (('key', boolean_function, comparing value),)

                for example: self.load_HPM(subset = [('lat',numpy.greater,44)]) will select 
                a subset of the timeseries that fullfill the condition "latitude > 44".

        """
        
        self.load_CSES(instrument='HPM',frequency='FGM1Hz',subset=subset,keep_verse_time = keep_verse_time,**kwargs)


    def load_EFD_ELF(self, subset = None, get_PSD = False, keep_verse_time = True,\
        versetime_to_datetime = False, **kwargs):
        """
        This method is kept for legacy reasons. Now is simply a wrapper that calls
        CSES.load_CSES(instrument='EFD',frequency='ELF')
        
        load EFD ELF files and put it into a pandas dataframe
        

        Optional arguments:
            subset = 3-elements tuple or tuple/list of 3-elements tuples with the following structures
                (('key', boolean_function, comparing value),)

                for example: self.load_EFD(subset = [('lat',numpy.greater,44)]) will select a subset of the timeseries
                that fullfill the condition "latitude > 44".

        """
        self.load_CSES(instrument='EFD',frequency='ELF',subset=subset, get_PSD = False\
            ,keep_verse_time = keep_verse_time,**kwargs)
        df = self.data['EFD_ELF']
        if versetime_to_datetime:
                df.drop('time',axis='columns',inplace=True)
                df['time'] = df.index.to_pydatetime()
        
    def load_EFD(self,**kwargs):
        """
        Warning: The use of load_EFD is DEPRECATED! For historical reasons (compatibility) it can still be used
        however, we recomend to use load_EFD_ELF instead.
        """
        self.load_EFD_ELF(**kwargs)

    def load_CSES(self, subset = None, get_PSD = False, \
        instrument = 'EFD', frequency = 'ULF',keep_verse_time = True,instrument_no=None,\
        load_RAW = False, **kwargs):
        """
        Load desired data from CSES instrument using CSES_load (see CSES_core.py)
        """
        import pandas as pd
        from glob import glob

        if instrument == 'LAP':
            frequency='50mm'
            instrument_no='1'
        if instrument == 'HPM':
            frequency='FGM1Hz'
            instrument_no='5'
            
        if frequency is None and instrument_no is None:
            msg.error('either frequency or instrument_no must be provided')
            return
        if frequency is None:
            frequency = CSES_DATA_TABLE[instrument][instrument_no]

        instrument_no = [i[0] for i  in CSES_DATA_TABLE[instrument].items() if i[1] == frequency][0]
        print('selected instrument-frequency: ' + msg.INFO(instrument+'-'+frequency))

        dsetname=instrument+'_'+frequency
        if not hasattr(self,'data'): 
            self.data=AttrDict()
        if not hasattr(self,'aux'): 
            self.aux=AttrDict()
        if get_PSD:
            if not hasattr(self.aux,dsetname+'_psd'): 
                self.aux[dsetname+'_psd']={}
        else:
            if not hasattr(self.aux,dsetname): 
                self.aux[dsetname] = {}

        if load_RAW:
            if not hasattr(self,'data_raw'):
                self.data_raw = AttrDict()
        
        self.find_files_to_load(instrument,frequency,instrument_no,unique=True)
        
        files = self.check_if_loaded(instrument,frequency,load_RAW=load_RAW)
        #files = self.files[dsetname] 


        for ifile in files:
            
            infos = parse_CSES_filename(ifile)
            
            ipath = self.get_file_path(ifile)
            
            print('loading file: '+msg.INFO(ipath+ifile))
            if load_RAW:
                df = load_CSES_raw(ipath+ifile, convert_names = True)
                if dsetname not in self.data_raw.keys():
                    self.data_raw[dsetname] = [df]
                else:
                    self.data_raw[dsetname].append(df)
            else:
                if get_PSD:
                    res, aux = CSES_load_PSD(ifile,ipath,**kwargs)
                else:
                    df, aux = CSES_load(ifile, path = ipath,\
                        return_pandas = True,\
                        keep_verse_time = keep_verse_time, **kwargs)

            
                if subset is not None:
                    for Cond in subset:
                       df = df[Cond[1](df[Cond[0]],Cond[2])] 

                if get_PSD:
                    dsetname += '_psd'
                    if dsetname not in self.data.keys():
                        self.data[dsetname] = res.copy()
                        self.data[dsetname+'_freq'] = aux['FREQ']
                        del df
                    else:
                        self.data[dsetname].append(res)
                    self.aux[dsetname][infos['orbitn']]= aux
                else:
                    if dsetname not in self.data.keys():
                        self.data[dsetname] = df.copy()
                        del df
                    else:
                        self.data[dsetname] = pd.concat([self.data[dsetname],df])
                    self.aux[dsetname][infos['orbitn']]= aux
                
                self.aux[dsetname]['instrument'] = instrument
                self.aux[dsetname]['frequency'] = frequency
                self.aux[dsetname]['instrument_no'] = instrument_no

        #resorting dataframe
        if dsetname in self.data:
            if type(self.data[dsetname]) is pd.DataFrame:
                self.data[dsetname].sort_index(inplace=True)
################################################################################
############################### PLOTTING TOOLS #################################
################################################################################


    def plot_EFD(self,xaxis = 'lat', xlabel=None,modulus = False, keys = ['Ex','Ey','Ez'],\
        ax = None,fig = None,twiny = True, frequency='ELF',ion=False):
        from .blombly import pylab as plt
        cols = plt.rcParams['axes.prop_cycle'].by_key()['color'] #colors
        ncol=len(cols) 
        
        tag = 'EFD_'+frequency
        fig,ax = plt.get_figure(fig,ax) 
        
        dff = self.data[tag]
        orbits = list(set(dff.orbitn))
        orbits.sort()
        
        if modulus:
            for iorbit in orbits:
                mask = dff.orbitn == iorbit
                df = dff[mask]
                
                ax.plot(df[xaxis],np.sqrt(df['Ex']**2+\
                                             df['Ey']**2+\
                                             df['Ez']**2),\
                                             label='|E|',linewidth=1,color='black')
        else:
            for iorbit in orbits:
                mask = dff.orbitn == iorbit
                df = dff[mask]
                [ax.plot(df[xaxis],df[i],label=i,linewidth=1,color=cols[j]) for j,i in enumerate(keys) if i in df]
        ax.set_xlabel(xaxis) if xlabel is None else ax.set_xlabel(xlabel)
        ax.set_ylabel('E [V/m]')
        ylims = ax.set_ylim()
        if twiny: 
            ax2 = ax.twiny()
            ax2.plot(self.data[tag].index,np.zeros(len(self.data[tag].index)),linestyle=None,linewidth = 0)
            ax2.set_xlabel('time (UT)')
        else:
            ax2 = None
        ax.legend()
        if ion : plt.ion()
        plt.show()
        return fig,ax,ax2 

    def plot_HPM(self,xaxis = 'time',what = 'modulus',color = None):
        from .blombly import pylab as plt
        plt.ion()
        hd = self.data['hpm']
        if xaxis == 'time':
            if what == 'modulus':
                [plt.plot((hd[hd.orbitn==i].Bx**2+hd[hd.orbitn==i].By**2 + hd[hd.orbitn==i].Bz**2)**0.5) for i in set(hd.orbitn)]
            elif type(what) is list:
                if color is not None:
                    for iitem,icol in zip(what,color):
                        [plt.plot(hd[hd.orbitn==i][iitem],color=icol,label=iitem) for i in set(hd.orbitn)]
                else:
                    for iitem in what:
                        [plt.plot(hd[hd.orbitn==i][iitem],label=iitem) for i in set(hd.orbitn)]
            else:
                [plt.plot(hd[hd.orbitn==i].Bx,color='red') for i in set(hd.orbitn)]
                [plt.plot(hd[hd.orbitn==i].By,color='green') for i in set(hd.orbitn)]
                [plt.plot(hd[hd.orbitn==i].Bz,color='blue') for i in set(hd.orbitn)]
        else:
            [plt.plot(hd[hd.orbitn==i][xaxis],hd[hd.orbitn==i].Bx,color='red') for i in set(hd.orbitn)]
            [plt.plot(hd[hd.orbitn==i][xaxis],hd[hd.orbitn==i].By,color='green') for i in set(hd.orbitn)]
            [plt.plot(hd[hd.orbitn==i][xaxis],hd[hd.orbitn==i].Bz,color='blue') for i in set(hd.orbitn)]


    def plot_orbit(self,instrument,frequency,y='lat',x='lon',basemap = None, fig = None, ax = None,profile = 'default',overplot_continents = True,ion=True,show=True):
        """
        Plot the orbit of the loaded instrument_frequency on the worldmap, using CSES_aux.plot_orbit

        Parameters
        ----------

        instrument : str
            id. string of the desired (data already loaded) instrument
        frequency : str
            id. string of the desired (data already loaded) frequency

        basemap : None or Basemap object (optional)
            if not None, then the input basemap is used.

        fig : None or figure object (optional)
            if not None, then input figure is used
            (used if basemap and ax are None).

        ax : None or list of axis objects (optional)
            if not None, then input axes are used
            (used if basemap is None).

        profile : str or dict
            if str, then the key with the desired CSES_aux.plot_orbit kwargs is used.
            available kwargs are stored in CSES_aux.ORBIT_PLOT_TEMPLATES
            if dict, then use the input dictionary as kwargs (see CSES_aux.ORBIT_PLOT_TEMPLATES 
            and CSES_aux.plot_orbit to get an idea of what must go in the dictionary).

        returns:

        fig,ax,mm : figure, axis, and basemap mm objects
        """
        
        df = self.data[get_datakey(instrument,frequency)]

        pltkwargs = ORBIT_PLOT_TEMPLATES[profile] if type(profile) is str else profile
        
        fig,ax,mm = plot_orbit(df[y].values,df[x].values, basemap = basemap, fig = fig, ax = ax,ion=ion,show=show,**pltkwargs)

        if overplot_continents:
            [imm.fillcontinents() for imm in mm]
            #[imm.drawlsmask() for imm in mm]
        return fig,ax,mm


    def plot_payloads(self,datakeys,xaxis = 'time', xlabel=None,\
        secondary_xaxis = '',ion=False,spectrograms = None,psdkwargs={}):
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


        fig,ax = plt.subplots(nplots,sharex=True, figsize=(8,2.5*len(datakeys)))
        
        fig.subplots_adjust(hspace=0,right=0.8,left=0.1)
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

        ax[-1].set_xlabel(xaxis)
        # rotate thicks
        ax[-1].tick_params(axis='x',rotation=45)
        return fig,ax

    def plot_payload(self,datakey,xaxis='time',secondary_xaxis=None,fig=None,ax=None,xlabel=None):
        
        from .blombly import pylab as plt
        cols = plt.rcParams['axes.prop_cycle'].by_key()['color'] #colors
        ncol=len(cols) 
        dff = self.data[datakey]
        xxx = dff.index.values if xaxis == 'time' else dff[xaxis].values
        
        orbits = list(set(dff.orbitn))
        orbits.sort()
        for iorbit in orbits:
            mask = dff.orbitn == iorbit
            df = dff[mask]
            xx = xxx[mask]
            if datakey == 'LAP_50mm':
                ax.set_title(datakey)
                ax.semilogy(xx,df['ne'][mask],label=r'$n_e$',color=cols[0])
                ax.set_ylabel(r'$n_e \quad (m^{-3})$')
                print(datakey)
            elif datakey in ['EFD_ULF','EFD_ELF','EFD_VLF']:
                ax.set_title(datakey)
                ax.plot(xx,np.sqrt(df['Ex']**2+df['Ey']**2+df['Ez']**2),label='|E|',linewidth=1,color='black')
                ax.plot(xx,df['Ex'],label=r'$E_x$',linewidth=1,color=cols[0])
                ax.plot(xx,df['Ey'],label=r'$E_y$',linewidth=1,color=cols[1])
                ax.plot(xx,df['Ez'],label=r'$E_z$',linewidth=1,color=cols[2])
                ax.set_ylabel('E [V/m]')
                print(datakey)
            elif datakey in ['SCM_ULF','SCM_ELF','HPM_FGM1Hz']:
                ax.set_title(datakey)
                ax.plot(xx,np.sqrt(df['Bx']**2+df['By']**2+df['Bz']**2),label='|B|',linewidth=1,color='black')
                ax.plot(xx,df['Bx'],label=r'$B_x$',linewidth=1,color=cols[0])
                ax.plot(xx,df['By'],label=r'$B_y$',linewidth=1,color=cols[1])
                ax.plot(xx,df['Bz'],label=r'$B_z$',linewidth=1,color=cols[2])
                ax.set_ylabel('B [nT]')
                print(datakey)
            elif datakey == 'HEPD':
                ax.set_title(datakey)
                instrument = self.aux[datakey]['instrument']
                instr_no = self.aux[datakey]['instrument_no']
                toplot = [[i[1] for i in CSES_FILE_TABLE[instrument][instr_no].items()][0]]
                for j,i in enumerate(toplot):
                    if 'Proton' in i:
                        continue
                    ax.semilogy(xx,df[i].values,label=i,linewidth=1,color=cols[j%ncol])
                print(datakey)
            elif datakey == 'HEPP_L':
                ax.set_title(datakey)
                instrument = self.aux[datakey]['instrument']
                instr_no = self.aux[datakey]['instrument_no']
                toplot = [i[1] for i in CSES_FILE_TABLE[instrument][instr_no].items()]
                for j,i in enumerate(toplot):                
                    ax.semilogy(xx,df[i].values,label=i,linewidth=1,color=cols[j%ncol])
                print(datakey)
            elif datakey == 'HEPP_H':
                ax.set_title(datakey)
                instrument = self.aux[datakey]['instrument']
                instr_no = self.aux[datakey]['instrument_no']
                toplot = [i[1] for i in CSES_FILE_TABLE[instrument][instr_no].items()]
                for j,i in enumerate(toplot):
                    if 'Proton' in i:
                        continue
                    ax.semilogy(xx,df[i].values,label=i,linewidth=1,color=cols[j%ncol])
                print(datakey)
            elif datakey == 'HEPP_X':
                ax.set_title(datakey)
                instrument = self.aux[datakey]['instrument']
                instr_no = self.aux[datakey]['instrument_no']
                toplot = [i[1] for i in CSES_FILE_TABLE[instrument][instr_no].items()]
                for j,i in enumerate(toplot):
                    if 'Proton' in i:
                        continue
                    ax.semilogy(xx,df[i].values,label=i,linewidth=1,color=cols[j%ncol])
                print(datakey)
            



        if secondary_xaxis is not None:
            if secondary_xaxis in df.keys():
                yy = df[secondary_xaxis].values if secondary_xaxis != 'time' else df.index.values
                ax2 = ax.twiny()
                ax2.plot(yy,np.zeros(len(yy)),linestyle=None,linewidth = 0)
                ax2.set_xlabel(secondary_xaxis)
            
            print("last")
        ax.legend(loc='upper right')
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
        xx = df['position'].index.values if xaxis == 'time' else df['position'][xaxis].values

        if fieldkey in self.aux[datakey][self.orbitn]['units'].keys():
            units  = '['+self.aux[datakey][self.orbitn]['units'][fieldkey].decode()+r'$]^2/\mathrm{Hz}$'
        elif fieldkey.split('_')[0] in self.aux[datakey][self.orbitn]['units'].keys():
            units  = '['+self.aux[datakey][self.orbitn]['units'][fieldkey.split('_')[0]].decode()+r'$]^2/\mathrm{Hz}$'
        else:
            units = r'[?]^2/\mathrm{Hz}$' 

        if vmax is None : vmax = df['psd'][fieldkey].max()
        if vmin is None : vmin = np.percentile(df['psd'][fieldkey],5)
        ims = ax.pcolormesh(xx,df['freq'],df['psd'][fieldkey],cmap=cmap,norm=LogNorm(vmin=vmin,vmax=vmax))
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
    
    def interpolate_inst1_to_inst2(self,inst1 = 'HPM',inst2 = 'EFD',tags = ['Bx','By','Bz'], track_origin = False):
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

    def get_spectrogram(self,datakey,fieldkeys,packetsize = None,window='hann'):
        """
        Calculate Spectrograms (STFT PSD) from the desired instrument_frequency
        previouly loaded in self.data on the selected keys/fields,
        based on csespy.CSES_PACKETSIZE (if packetsize is None).

        Parameters
        ----------
        datakey : str
            key of self.data containing the pandas.Dataframe with the field keys
            of which one want to compute the STFT PSD
        fieldkeys: list of str
            keys of which one wants to compute the spectrogram
        packetsize : None or int
            size of the STFT chunk. Default is None, which is equivalent to
            the packet size of EFD-02, stored in csespy.CSES_PACKETSIZE
        """

        from scipy.signal import stft
        if datakey not in self.data:
            msg.error('datakey '+datakey+' not found in self.data! Please load the desired data first.')
            return

        df = self.data[datakey]
        nx = df.shape[0]
        fs = CSES_SAMPLINGFREQS[datakey]
        if not all([i in df.keys() for i in fieldkeys]):
            msg.error('Some of the fieldkeys '+str(fieldkeys) +'not found in self.data.'+datakey+'. Returning')
            return

        if packetsize is None:
            packetsize = CSES_PACKETSIZE[datakey]
        if nx// packetsize != nx/ packetsize:
            msg.error('wrong input packetsize! Returning')
            return

        #extracting and manipulating the desired fields
        #ff = {i:df[i].values.reshape([nx//packetsize,packetsize]) for i in fieldkeys}
        ff = {i:stft(df[i].values, fs = fs, window = window, \
                        nperseg = packetsize, noverlap=0, boundary = None,padded = False) for i in fieldkeys}
        psd = {i:np.abs(ff[i][-1])**2 for i in ff}
        nu = ff[fieldkeys[0]][0]
        tt = df.index.values[::packetsize]
        dff = df[::packetsize].drop(columns=fieldkeys)
        self.data[datakey+'_P'] = {'psd':psd,'freq':nu,'time':tt,'position':dff}


######WRITING TO DATABASES MACHINERY######
    def save_data_to_h5(self,filepath,dataset_name,filename=None,mode='a',return_outputfilepath=False,track_origin=True,**kwargs):

        from .blombly.io import save_dataframe_to_h5
        
        orbitn = self.orbitn if type(self.orbitn) is str else self.orbitn[0]+'-'+self.orbitn[-1]
        if filename is None: filename = dataset_name+'_'+orbitn+'.h5'
        
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
        
        from .blombly.math.derivFD import derivfield as deriv #central finite differences derivative 
        t = data.index.values.astype(float)/1e9 #dt in seconds
        t-=t[0]
        if regularize_speed:
            from scipy.interpolate import splrep,splev
            nskip = CSES_PACKETSIZE[datakey]
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
    
    def remove_vsxb_drift(self,instrument='EFD',frequency='ELF',overwrite=False):
        """
        remove E=vs X B drift from the EFD electric field contained 
        in self.data[instrument+'_'+frequency], so to allow removal from interpolated
        instruments
        the pd dataframe must contain the VsxB_[xyz] fields as given by self.get_vsxb_drift
        and the E_[xyz] fields. 

        WARNING: the two vector fields must be in the same right-handed orthogonal ref.frame.
        """
        datakey = instrument+'_'+frequency
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

################################################################################
#########################some fast diagnostic tool  tbd#########################
################################################################################
    
class CSES_database():

    methods = {'pandas-hdf5':'load_pd_hdf5'}

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

        self.source = source
        if type(dbbuf) is str: self.dbfile = dbbuf

        self.load_db(dbbuf,source)

    def load_db(self,dbbuf,source):
        """
        load database using desired buf/file and source.
        """

        getattr(self,self.methods[source])(dbbuf)


    def load_pd_hdf5(self,dbbuf):
        
        import pandas as pd
        
        self.db = pd.read_hdf(dbbuf)

    def search_orbit(self,ranges, return_orbitn = True, use_selected_db = False): 
        """
        
        This is a generic method to select a subset of orbits fulfilling the conditions set in ranges (see below).

        parameters
        ----------
        ranges = 3-elements tuple or tuple/list of 3-elements tuples with the following structures
            (('key', boolean_function, comparing value),)

            for example: self.search_orbit([('lat',numpy.greater,44),('lat',numpy.less,48),('lon',numpy.greater,10),('lon',numpy.less,15)]) 
            will return all orbit numbers of orbits fulfilling the condition "48>latitude > 44" and "15 > longitude > 10".

        return_orbitn : bool
            if False, then the full database information of the selected orbit is returned.
            if True, only a list of the orbit numbers fulfilling the conditions set in ranges is returned
        
        input_db : None or pandas dataframe
        """
        
        df = self.db if not use_selected_db else self.sel_db
        
        for Cond in ranges:
           df = df[Cond[1](df[Cond[0]],Cond[2])] 

        self.sel_db = df

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

    def search_orbit_timespan(self,timespan, return_orbitn = True, use_selected_db = False):
        """
        find all available orbits in given temporal range
        """

        df = self.db if not use_selected_db else self.sel_db

        mask = (df.index > timespan[0]) * (df.index < timespan[1])

        self.sel_db = df[mask]
        
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

    def search_orbit_latlontimespan(self,lat,lon,timespan, return_orbitn = True, use_selected_db = False):
        """
        self explaining
        """

        df = self.db if not use_selected_db else self.sel_db

        df = self.search_orbit_latlon(lat,lon,return_orbitn = False)

        if df.size == 0: return df

        df = self.search_orbit_timespan(timespan,use_selected_db = True)

        if return_orbitn: 
            return np.unique(self.sel_db.orbitn)

        return self.sel_db
    

    def plot_orbit(self,df=None,y='lat',x='lon',basemap = None, fig = None, ax = None,\
        profile = 'default',overplot_continents = True,ion=True,show=True,\
        annotate_orbitn = True, color = None):
        """
        Plot the orbits present in df  in the worldmap, using CSES_aux.plot_orbit

        Parameters
        ----------

        df : None or pandas dataframe
            if not None, then it plots the orbit contained in df, otherwise plots 
            the orbits contained in self.sel_db (if orbits were selected using search_orbit method)
            or plots all orbits in database.

        basemap : None or Basemap object (optional)
            if not None, then the input basemap is used.

        fig : None or figure object (optional)
            if not None, then input figure is used
            (used if basemap and ax are None).

        ax : None or list of axis objects (optional)
            if not None, then input axes are used
            (used if basemap is None).

        profile : str or dict
            if str, then the key with the desired CSES_aux.plot_orbit kwargs is used.
            available kwargs are stored in CSES_aux.ORBIT_PLOT_TEMPLATES
            if dict, then use the input dictionary as kwargs (see CSES_aux.ORBIT_PLOT_TEMPLATES 
            and CSES_aux.plot_orbit to get an idea of what must go in the dictionary).
        
        annotate_orbitn : bool
            if True, for each orbit, the orbitnumber is annotated at the lowermost (nightside)
            or uppermost (dayside) orbit point.

        returns:

        fig,ax,mm : figure, axis, and basemap mm objects
        """
        from .blombly import pylab as plt
        
        if df is None:
            if hasattr(self,'sel_db'):
                df = self.sel_db
            else:
                df = self.db

        pltkwargs = ORBIT_PLOT_TEMPLATES[profile] if type(profile) is str else profile
        
        orbits = set(df.orbitn.values)

        for iorbit in orbits:
            dff = df[df.orbitn.values == iorbit]
            fig,ax,basemap = plot_orbit(dff[y].values,dff[x].values, \
                basemap = basemap, fig = fig, ax = ax,ion=False,show=False,color = color, **pltkwargs)
            if annotate_orbitn:
                [axi.annotate(iorbit,[dff[x][0],dff[y][0]*1.1],fontsize=10) for axi in ax]

        if overplot_continents:
            [imm.fillcontinents() for imm in basemap]
            #[imm.drawlsmask() for imm in basemap]
        if ion:
           plt.ion()
        else:
            plt.ioff()
        if show:
            plt.show()

        return fig,ax,basemap
