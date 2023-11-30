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

    def __init__(self, path='./',search_string = None,orbitn=None,unstructured_path=False):


        self.path = path
        self.files = AttrDict()
        self.search_string = search_string
        self.orbitn = orbitn
        self._ancillary_={}
        self._unstructured_path_ = unstructured_path
        if not unstructured_path: self.check_path()

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

        if self.files.input is None:
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
         
        if self._unstructured_path_:
            if type(filename) is str:
                return self.path if os.path.exists(self.path+filename) else []
            
            fpath = []
            for ifile in filename:  
                fpath.append(self.path) if os.path.exists(self.path+filename) else fpath.append([])
            return fpath

        if type(filename) is str:
            info = parse_CSES_filename(filename)
            if info['Instrument'] == 'EFD':
                l2a = '_L2A/'if info['Data Level'] == 'L2A' else '/'
                return self.path+info['Instrument']+'/'+info['year']+'/'+info['Data Product']+l2a+info['month']+'/'
            elif info['Instrument'] == 'SCM':
                l2a = '_L2A/'if info['Data Level'] == 'L2A' else '/'
                return self.path+info['Instrument']+'/'+info['year']+'/'+info['Data Product']+l2a+info['month']+'/'

            else: 
                return self.path+info['Instrument']+'/'+info['year']+'/'+info['month']+'/'
        
        fpath=[]
        for ifile in filename:
            info = parse_CSES_filename(ifile)
            if info['Instrument'] == 'EFD' or info['Instrument'] == 'SCM':
                l2a = '_L2A/'if info['Data Level'] == 'L2A' else '/'
                fpath.append(self.path+info['Instrument']+'/'+info['year']+'/'+info['Data Product']+l2a+info['month']+'/')
        
        return fpath
    

    def search_file(self,search_string ='',orbitn=None, instrument='EFD', instrument_no=None, frequency = 'ELF',return_path = False, timespan = None):
        """
        Search for a file matching the desired string for the desired instrument and frequency
        """
        from glob import glob
       
        if instrument_no is not None: frequency = ''
        files = None
        unstruct_path = self._unstructured_path_
        if timespan is not None:
            #Lazy way to find orbit in timespan
            #1-get all files available in storage and parse datetimes
            fls = self.search_file()
            b = [parse_CSES_filename(i) for i in fls]
            t0,t1 = timespan
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
            return files
        if instrument == 'EFD':
            if unstruct_path:
                months=[self.path]
            else:
                years = glob(self.path+instrument+'/*')
                months = [i+'/' for year in years for i in glob(year+'/'+frequency+'/*')]
            #for i in years
            if orbitn is None:
                files = [i for month in months for i in find_file(month,search_string)]
                #return files
            else:
                files = [i for month in months for i in find_file(month,orbitn)]
                files = [i for i in files if parse_CSES_filename(i)['orbitn'] == orbitn and \
                    parse_CSES_filename(i)['Instrument']=='EFD' and \
                    parse_CSES_filename(i)['Data Product']==frequency]
        else: 
            if unstruct_path:
                months=[self.path]
            else:
                years = glob(self.path+instrument+'/*')
                months = [i+'/' for year in years for i in glob(year+'/'+frequency+'/*')]
            if orbitn is None:
                files = [i for month in months for i in find_file(month,search_string)]
            else:
                files = [i for month in months for i in find_file(month,orbitn)]
                files = [i for i in files if (parse_CSES_filename(i)['orbitn'] == orbitn or\
                    parse_CSES_filename(i)['orbitn'] == '0'+orbitn) and\
                    parse_CSES_filename(i)['Instrument'] == instrument and\
                    (parse_CSES_filename(i)['Data Product'] == frequency or\
                    parse_CSES_filename(i)['Instrument No.'] == instrument_no)]
            if instrument_no is not None:
                files = [i for i in files if parse_CSES_filename(i)['Instrument No.'] == instrument_no]

            #return files
        
        if files is not None:
            if return_path:
                files = [self.get_file_path(i)+i for i in files]

        return files


    def load_HPM(self, subset = None,instrument_no='5',unique = True, keep_verse_time = True,**kwargs):
        """
        load HPM data from files matching the string and put them into a pandas dataframe
        
        Optional arguments:
            subset = 3-elements tuple or tuple/list of 3-elements tuples with the following structures
                (('key', boolean_function, comparing value),)

                for example: self.load_HPM(subset = [('lat',numpy.greater,44)]) will select 
                a subset of the timeseries that fullfill the condition "latitude > 44".

        """
        import pandas as pd
        from glob import glob
        from .blombly.tools.objects import AttrDict

        if not hasattr(self,'data'): 
            self.data=AttrDict()
        if not hasattr(self,'aux'): 
            self.aux=AttrDict()
        if not hasattr(self.aux,'hpm'): 
            self.aux.hpm={}


        if self.files.input is None:
            if type(self.orbitn) is str:
                files = self.search_file(orbitn=self.orbitn,instrument='HPM',\
                    instrument_no=instrument_no, frequency = '')
            elif type(self.search_string) is str:
                files = self.search_file(self.search_string,instrument='HPM',\
                    instrument_no=instrument_no, frequency = '')
            else:
                raise ValueError('not enough input for file search!')
            self.files['HPM'] = files
        else:
            filess = self.files.input.copy()
            #checking if files are HPM files
            infos = [parse_CSES_filename(ifiles) for ifiles in filess]
            for i,info in enumerate(infos):
                #if the file in the list is not HPM, then it searches for an HPM
                #file in the folders with the same orbit
                if info['Instrument'] != 'HPM':
                    files[i] = self.search_file(orbitn=info['orbitn'],instrument='HPM',\
                    instrument_no=instrument_no, frequency = '')[0]
            self.files['HPM'] = files
  

        if unique : files = uniquefy(files) 

        #for ifile,ipath in zip(files,fpaths):
        for ifiles in files:
            
            infos = parse_CSES_filename(ifiles)
            
            if infos['Instrument'] == 'HPM':
                ifile = ifiles
            else:
                ifile = self.search_file(orbitn=infos['orbitn'],instrument='HPM',instrument_no=instrument_no)[0]
            
            ipath = self.get_file_path(ifile)
            
            print('loading HPM file: '+msg.INFO(ipath+ifile))
            res, aux = HPM_load(ifile,ipath,**kwargs)

            index = pd.to_timedelta( res['time'] - res['time'][0],unit='sec') + aux['UTC']
            df = pd.DataFrame(res,index=index)
            if not keep_verse_time : df.drop('time',axis='columns',inplace=True)
            df['orbitn'] = int(infos['orbitn'])
            
            if subset is not None:
                for Cond in subset:
                   df = df[Cond[1](df[Cond[0]],Cond[2])] 


            if 'hpm' not in self.data.keys():
                self.data.HPM = df.copy()
                del df
            else:
                self.data.HPM = self.data.HPM.append(df)

            self.aux.hpm[infos['orbitn']]= aux

    def load_EFD_ELF(self, subset = None, get_PSD = False, keep_verse_time = True, versetime_to_datetime = False, **kwargs):
        """
        load EFD ELF files and put it into a pandas dataframe
        

        Optional arguments:
            subset = 3-elements tuple or tuple/list of 3-elements tuples with the following structures
                (('key', boolean_function, comparing value),)

                for example: self.load_EFD(subset = [('lat',numpy.greater,44)]) will select a subset of the timeseries
                that fullfill the condition "latitude > 44".

        """

        import pandas as pd
        from glob import glob
        from .blombly.tools.objects import AttrDict

        if not hasattr(self,'data'): 
            self.data=AttrDict()
        if not hasattr(self,'aux'): 
            self.aux=AttrDict()
        if get_PSD:
            if not hasattr(self.aux,'efd_psd'): 
                self.aux.efd_psd={}
        else:
            if not hasattr(self.aux,'efd'): 
                self.aux.efd={}


        if self.files.input is None:
            if type(self.orbitn) is str:
                files = self.search_file(orbitn=self.orbitn,instrument='EFD', frequency = 'ELF')
                #DONT KNOW WHY  but sometimes there are two files for the same orbit.
                #In that case, the file with the larger timespan is selected.
                files = uniquefy(files) 
                #if len(files)>1:
                #    inf = [parse_CSES_filename(ifile) for ifile in files]
                #    inf = [i['t_end']-i['t_start'] for i in inf]
                #    files = [files[np.argmax(inf)]]
            elif type(self.search_string) is str:
                files = self.search_file(self.search_string,instrument='EFD', frequency = 'ELF')
            else:
                raise ValueError('not enough input for file search!')
            self.files['EFD'] = files
        else:
            filess = self.files.input.copy()
            files=[]
            #checking if files are EFD files
            infos = [parse_CSES_filename(ifiles) for ifiles in filess]
            for i,info in enumerate(infos):
                if info['Instrument'] == 'EFD' and info['Data Product'] == 'ELF':
                    files.append(filess[i])
                    #files[i] = self.search_file(orbitn=info['orbitn'],instrument='EFD',\
                    #instrument_no=instrument_no, frequency = '')[0]
            self.files['EFD'] = files
        

        #fpaths = self.get_file_path(files)
        #for ifile,ipath in zip(files,fpaths):
        for ifiles in files:
            
            infos = parse_CSES_filename(ifiles)
            
            if infos['Instrument'] == 'EFD':
                ifile = ifiles
            else:
                ifile = self.search_file(orbitn=infos['orbitn'],instrument='EFD')[0]
            
            ipath = self.get_file_path(ifile)

            print('loading EFD file: '+msg.INFO(ipath+ifile))
            if get_PSD:
                res, aux = EFD_load_ELF_PSD(ifile,ipath,**kwargs)
            else:
                res, aux = EFD_load_ELF(ifile,ipath,**kwargs)

            index = pd.to_timedelta( res['time'] - res['time'][0],unit='sec') + aux['UTC']
            df = pd.DataFrame(res,index=index)
            
            if not keep_verse_time : 
                df.drop('time',axis='columns',inplace=True)
            elif versetime_to_datetime:
                df.drop('time',axis='columns',inplace=True)
                df['time'] = df.index.to_pydatetime()

            if subset is not None:
                for Cond in subset:
                   df = df[Cond[1](df[Cond[0]],Cond[2])] 

            if get_PSD:
                if 'efd_psd' not in self.data.keys():
                    self.data.EFD_PSD = df.copy()
                    self.data.EFD_PSD_freq = aux['FREQ']
                    del df
                else:
                    self.data.EFD_PSD.append(df)
                self.aux.efd_psd[infos['orbitn']]= aux
            else:
                if 'efd' not in self.data.keys():
                    self.data.EFD = df.copy()
                    del df
                else:
                    self.data.EFD = pd.concat([self.data.EFD,df])
                self.aux.efd[infos['orbitn']]= aux
    
    def load_EFD(self,**kwargs):
        """
        Warning: The use of load_EFD is DEPRECATED! For historical reasons (compatibility) it can still be used
        however, we recomend to use load_EFD_ELF instead.
        """
        self.load_EFD_ELF(**kwargs)

    def load_CSES(self, subset = None, get_PSD = False, \
        instrument = 'EFD', frequency = 'ULF',keep_verse_time = True,instrument_no=None, **kwargs):
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
            
        print('selected instrument-frequency: ' + msg.INFO(instrument+'-'+frequency))

        dsetname=instrument.lower()+'_'+frequency.lower()
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


        if self.files.input is None:
            if type(self.orbitn) is str:
                files = self.search_file(orbitn=self.orbitn,instrument=instrument, frequency = frequency, instrument_no = instrument_no)
                #DONT KNOW WHY  but sometimes there are two files for the same orbit.
                #In that case, the file with the larger timespan is selected.
                files = uniquefy(files) 
            elif type(self.search_string) is str:
                files = self.search_file(self.search_string,instrument=instrument, frequency = frequency, instrument_no = instrument_no)
            else:
                raise ValueError('not enough input for file search!')
            self.files[instrument] = files
        else:
            filess = self.files.input.copy()
            files=[]
            #checking if files are EFD files
            infos = [parse_CSES_filename(ifiles) for ifiles in filess]
            for i,info in enumerate(infos):
                if info['Instrument'] == instrument and info['Data Product'] == frequency:
                    files.append(filess[i])
            self.files[instrument] = files
        

        for ifile in files:
            
            infos = parse_CSES_filename(ifile)
            
            #if infos['Instrument'] == 'EFD':
            #    ifile = ifiles
            #else:
            #    ifile = self.search_file(orbitn=infos['orbitn'],instrument='EFD')[0]
            
            ipath = self.get_file_path(ifile)

            print('loading file: '+msg.INFO(ipath+ifile))
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
                    self.data[dsetname] = df.copy()
                    self.data[dsetname+'_freq'] = aux['FREQ']
                    del df
                else:
                    self.data[dsetname].append(df)
                self.aux[dsetname][infos['orbitn']]= aux
            else:
                if dsetname not in self.data.keys():
                    self.data[dsetname] = df.copy()
                    del df
                else:
                    self.data[dsetname] = pd.concat([self.data[dsetname],df])
                self.aux[dsetname][infos['orbitn']]= aux



    def plot_EFD(self,xaxis = 'lat', xlabel=None,modulus = False, keys = ['Ex','Ey','Ez'],ax = None,fig = None,twiny = True, frequency='ELF'):
        from .blombly import pylab as plt
        plt.ion()

        if frequency == 'ELF':
            tag = 'efd'
        elif frequency == 'ULF':
            tag = 'efd_ulf'
        fig,ax = plt.get_figure(fig,ax) 
        if modulus:
            ax.plot(self.data[tag][xaxis],np.sqrt(self.data[tag]['Ex']**2+\
                                             self.data[tag]['Ey']**2+\
                                             self.data[tag]['Ez']**2),label='|E|',linewidth=1)
        else:
            [ax.plot(self.data[tag][xaxis],self.data[tag][i],label=i,linewidth=1) for i in keys if i in self.data[tag]]
            #plt.plot(self.data['efd'][xaxis],self.data['efd']['Ex'],label='Ex',linewidth=1)
            #plt.plot(self.data['efd'][xaxis],self.data['efd']['Ey'],label='Ey',linewidth=1)
            #plt.plot(self.data['efd'][xaxis],self.data['efd']['Ez'],label='Ez',linewidth=1)
        ax.set_xlabel(xaxis) if xlabel is None else ax.set_xlabel(xlabel)
        ax.set_ylabel('E [V/m]')
        ylims = ax.set_ylim()
        if twiny: 
            ax2 = ax.twiny()
            ax2.plot(self.data[tag].index,np.zeros(len(self.data[tag].index)),linestyle=None,linewidth = 0)
            ax2.set_xlabel('time (UT)')
        else:
            ax2 = None
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



######WRITING TO DATABASES MACHINERY######
    def save_data_to_h5(self,filename,dataset_name,mode='a',**kwargs):

        from .blombly.io import save_dataframe_to_h5
        dats = self.data[dataset_name].copy()
        idx = {'time':(dats.index.values.astype(float)-dats.index.values.astype(float)[0])/1e9,'t0':str(dats.index[0])}
        del dats['time']
        save_dataframe_to_h5(filename,dats,index=idx,mode=mode,**kwargs)


################################################################################
#########################some fast diagnostic tool  tbd#########################
################################################################################

