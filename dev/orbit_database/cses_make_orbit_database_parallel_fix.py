
from datetime import datetime
import pandas as pd
import csespy
from csespy import fix_lonlat,split_orbit
from csespy.blombly.io import io_tools as iot
import h5py

from csespy import datenum
import pandas as pd
from joblib import delayed, Parallel
from csespy.blombly.tools.arrays import start_end
from csespy.blombly.tools import time
timeit= time.timeit()


OUT_DIR = '/data/emanuele/data/CSES/orbitdb2026/'
csespath= '/CSES_Data/CSES01/'


def fix_lonlat_df(dff):
    lons,lats = fix_lonlat(dff.lon.values,dff.lat.values,dff.index.values)
    dff['lon'] = lons
    dff['lat'] = lats
    return dff

def split_orbit_df(dff):
    """
    split orbit if dff contains more than one semiorbit and label it accordingly
    ('1': night ascending, '0': day descending)
    using the input orbitn as starting number for the first orbit. 
    """
    sorbit = dff.orbitn.values[0][:-1]
    
    sdata = split_orbit(dff.lat.values,dff.lon.values,dff.index.values)#*argsi)
    
    for idd in sdata:
            
        dff.loc[idd[3][0],'orbitn'] = sorbit+str(idd[2])
        #increasing orbitnumber by 1
        if idd[2] == 1:
            sorbit = (str(int(sorbit)+1)+'x').zfill(6)[:-1]
    return dff

def load_file4db(filpath,filname,nskip):
    fil= h5py.File(filpath+filname,'r')

    res = {}
    res['lat'] = fil['GEO_LAT'][::nskip].flatten()
    res['lon'] = fil['GEO_LON'][::nskip].flatten()
    res['alt'] = fil['ALTITUDE'][::nskip].flatten()
    
    Vtime = fil['VERSE_TIME'][::nskip].flatten()
    Utime = fil['UTC_TIME'][::nskip].flatten()
    
    fil.close()
    
    #convert from CSES date (VERSE_TIME) to standard date
    vt0_utc, utc = datenum(2009,1,1,utc = str(Utime[0]))    #CSES initial time
    Utime = np.array([j[1] for j in [datenum(2009,1,1,utc=str(i)) for i in Utime]])

    tx=np.copy(Vtime)
    Vtime0 = tx[0] #VERSE_TIME a t=0 in milliseconds
    tx -=Vtime0
    tx = tx/1000
    Vtime0/=1000
    time=tx     #verse_time in seconds
    del tx

    res['verse_time'] = Vtime 
    res['utc'] = Utime
    index = pd.to_timedelta( time - time[0],unit='sec') + utc
    df = pd.DataFrame(res,index=index)
    
    return df
                
def check_orbit_goodness(dfdum):
    n=dfdum.shape[0]
    #first remove points in the origin which 99.9999% are wrong.
    mask = (dfdum.lat == 0) & (dfdum.lon == 0)
    dfdum.drop(dfdum[mask].index,inplace=True)
    if np.sum(dfdum.lon.diff().values == 0) > n*0.2:
        outcome = False
    else:
        outcome = True
    dfdum.drop(dfdum[dfdum.lon.diff() == 0].index,inplace = True)
    if dfdum.shape[0] < n*0.8: 
        outcome = False
    return dfdum,outcome 




css = csespy.CSES(path=csespath)

inst = [  'EFD','LAP' ,'EFD']
freqs = [ 'ULF','50mm','ELF']


#looking for the files to use as template to get orbits
fils = [css.search_file(ii+'_'+jj) for ii,jj in zip(inst,freqs)]

#orbits found
orbits = [[csespy.parse_CSES_filename(i)['orbitn'] for i in ii] for ii in fils]
orbits = [np.array(i) for i in orbits]
unique_orbits = np.unique(np.concatenate(orbits))

fils = [np.array(i) for i in fils]

#creating the orbit database object
def inner_loop(itask,istend,orbits,unique_orbits,fils,inst,freqs):
    orbitdb = None
    skipped = []
    print(itask,istend)
    for inum in range(istend[0],istend[1]):
        success = False
        iinst=0
        while not success:
            #check if reached limit of available sources for the orbit
            if iinst == len(inst):
                skipped.append(unique_orbits[inum])
                success = True
                continue

            ifile = fils[iinst][orbits[iinst] == unique_orbits[inum]]
            
            #check if orbit present in the desired instr_freq
            if ifile.size == 0: 
                iinst+=1
                continue
            ifile = csespy.uniquefy(ifile)[0] 
            info = csespy.parse_CSES_filename(ifile)
            
            ipath=css.search_file(info['datakey'],orbitn=info['orbitn'],\
                get_file_path=True)[0]
            
            
            try :
                tag = info['datakey']
                
                if tag == 'LAP_50mm':
                    nskip=2
                    
                elif tag =='EFD_ULF':
                    nskip=3
                elif tag =='EFD_ELF':
                    nskip=15
               
                dfdum = load_file4db(ipath,ifile,nskip)
                
                #check goodness of orbit:
                #if some isolated points are bad, these are removed
                #if orbital data are too degraded, outcome is False
                #and then the algorithm skip to the next instrument
                dfdum,outcome = check_orbit_goodness(dfdum)
                if not outcome:
                    iinst+=1
                    continue
                else:
                    success = True
                
                dfdum['orbitn'] = info['orbitn']
                dfdum['source'] = tag
                dfdum = fix_lonlat_df(dfdum)
                dfdum = split_orbit_df(dfdum)
                if orbitdb is None:
                   orbitdb = dfdum 
                else:
                    orbitdb = pd.concat([orbitdb,dfdum])
            except:
                success = False
                iinst+=1
                continue

    orbitdb.to_pickle(OUT_DIR+'cses_orbit_db'+str(itask)+'.pckle')


nchunks = 64
ntasks = 32
stend = start_end(unique_orbits,nchunks)
print("processing {} orbits".format(np.max([int(i) for i in unique_orbits])))
#
# istend: range of orbits
# orbits: list of 3 nn arrays of string orbitn
# unique_orbits : array of unique orbits
# fils: list of 3 nn lists of files
# inst,freqs: ordered list of instruments to try to get orbit info from
timeit.tic
Parallel(n_jobs=ntasks)(delayed(inner_loop)(itask,istend,orbits,unique_orbits,fils,inst,freqs) for itask,istend in enumerate(stend))
timeit.toc
print('done')

