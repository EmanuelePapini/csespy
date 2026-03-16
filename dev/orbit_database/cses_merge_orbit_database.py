from glob import glob
import pandas as pd

remove_source = True
to_hdf=True
OUT_DIR = '/data/emanuele/data/CSES/orbitdb2026/'

files = glob(OUT_DIR+'cses_orbit_db[0123456789]*.pckle')

db = pd.read_pickle(files[0])
for ifile in files[1:]:
    dbdum = pd.read_pickle(ifile)
    db = pd.concat([db,dbdum])
    print(dbdum.index.min(),dbdum.index.max())

db=db.sort_index()

if remove_source : del db['source']
if to_hdf:
    db.to_hdf(OUT_DIR+'cses_orbit_db_mergedLfix.h5','db',complevel=9)
else:
    db.to_pickle(OUT_DIR+'cses_orbit_db_mergedLfix.pckle')
