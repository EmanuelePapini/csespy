import csespy_dev as csespy
from datetime import datetime, timezone
import pandas as pd
import numpy as np

#path to the CSES orbit database
odbfile = '/storage/gpfs_data/limadou/dagiorda/csespy_dev/examples/aux/CSES01_orbitdb.h5'

#date span (Jan to Apr 2019)
t0 = datetime(2019, 1, 1, tzinfo=timezone.utc)
t1 = datetime(2020, 4, 30, tzinfo=timezone.utc)
 
#initialize CSES_database object
odb = csespy.CSES_database(dbbuf = odbfile)

#quick DB coverage info
db = odb.db
print(f"DB time range: {db.index.min()} -> {db.index.max()}")
print(f"DB rows: {len(db):,} | orbits: {db['orbitn'].nunique():,}")
 
#restrict to desired date span
# odb.search_orbit_timespan((t0,t1))
# odb.search_orbit_lat([-27,-25.49],use_selected_db = True)
# odb.search_orbit_lon([-10,60],use_selected_db = True)

#plot orbits
fig,ax,mm=odb.plot_orbit(profile='default_lines',\
   annotate_orbitn=False,color='night-day',ion=True)

#label axes (only if a figure was created)
if fig is not None:
   fig.text(0.5, 0.01, 'Geographic Longitude', horizontalalignment='center')
   fig.text(0.03, 0.5, 'Geographic Latitude', verticalalignment='center',\
      rotation='vertical')
else:
   print("No orbits found in the selected timespan.")

exit()
#there are 76 ascending and 76 descending orbit types.
ntype = 76
#restrict to the equator
odb.search_orbit_lat([-1,1],use_selected_db = True)
#divide into dayside and nightside orbits
dbnight = odb.search_orbit_side('night', return_db = True,use_selected_db = True)
dbday = odb.search_orbit_side('day', return_db = True,use_selected_db = True)
#select, for each orbit, the closest point to the equator.
dbnight = dbnight.loc[
   dbnight.groupby('orbitn')['lat'].apply(lambda x: x.abs().idxmin())
]
dbday = dbday.loc[
   dbday.groupby('orbitn')['lat'].apply(lambda x: x.abs().idxmin())
]
#label orbits according to longitude, using KMeans clustering algorithm
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=ntype, random_state=47, n_init=10)
#clustering data
dbnight['OrbitType'] = kmeans.fit_predict(dbnight[['lon']])
dbday['OrbitType'] = kmeans.fit_predict(dbday[['lon']])
#find latitudinal point closest to the equator for each orbit type
dbnight = dbnight.loc[
   dbnight.groupby('OrbitType')['lat'].apply(lambda x: x.abs().idxmin())
]
dbday = dbday.loc[
   dbday.groupby('OrbitType')['lat'].apply(lambda x: x.abs().idxmin())
]
#resorting OrbitType labeling starting from longitude -180
dbday.sort_values('lon',inplace=True)
dbnight.sort_values('lon',inplace=True)
#now relabeling OrbitTypes,
#labeling with even numbers day orbits and with odd numbers night orbits
dbday['OrbitType'] = np.arange(ntype)*2
dbnight['OrbitType'] = np.arange(ntype)*2 + 1
#now we define two dataframes containing
#the equatorial longitude and orbit_type pairs
daytype = pd.DataFrame(
   {'lon': dbday['lon'].values, 'OrbitType': dbday['OrbitType'].values}
)
nighttype = pd.DataFrame(
   {'lon': dbnight['lon'].values, 'OrbitType': dbnight['OrbitType'].values}
)
#last step consists in labeling all orbits in the original database
#NOTE: we use the whole database by setting ``use_selected_db = False''
odb.search_orbit_lat([-1,1],use_selected_db = False)
#splitting in day and night orbits
dbnight = odb.search_orbit_side('night', return_db = True,use_selected_db = True)
dbday = odb.search_orbit_side('day', return_db = True,use_selected_db = True)
#select, for each orbit, the closest point to the equator.
dbnight = dbnight.loc[
   dbnight.groupby('orbitn')['lat'].apply(lambda x: x.abs().idxmin())
]
dbday = dbday.loc[
   dbday.groupby('orbitn')['lat'].apply(lambda x: x.abs().idxmin())
]
# Find the closest longitude for each row in df
dbnight['OrbitType'] = dbnight['lon'].apply(
   lambda lon: nighttype.loc[(nighttype['lon'] - lon).abs().idxmin(), 'OrbitType']
)
dbday['OrbitType'] = dbday['lon'].apply(
   lambda lon: daytype.loc[(daytype['lon'] - lon).abs().idxmin(), 'OrbitType']
)
#dblabeled now contains all orbits labeled
dblabeled = pd.concat([dbnight, dbday], ignore_index=True)
#we translate the information on the orbit and orbit type into a dictionary
mapping_dict = dict(zip(dblabeled.orbitn.values, dblabeled.OrbitType.values))
#We label the whole the orbit database by assigning
#the label -1 to orbits in case of error.
#The DataFrame containing the database of the orbits is in ``odb.db''.
odb.db['OrbitType'] = odb.db['orbitn'].map(mapping_dict).fillna(-1).astype(int)

day_or_night='night' #set to: 'day' to plot dayside orbits
#select orbits of interest
odb.search_orbit_timespan((t0,t1))
odb.search_orbit_side(day_or_night,use_selected_db = True)
#Select plotting profile
prof=csespy.ORBIT_PLOT_TEMPLATES['default_lines'].copy()
#select which parallel and meridian to overplot
prof['latrange'] = [[55,75,5]]
prof['lonrange'] = [[0,40,5]]
#make the plot
figs=odb.plot_orbit(profile=prof,\
annotate_orbitn=False,color='night-day',ion=True)
figs[1][0].set_ylim([55,75])
figs[1][0].set_xlim([0,40])
#label axes
figs[0].text(0.5,0.01,'Geographic Longitude',horizontalalignment='center')
figs[0].text(0.03,0.5,'Geographic Latitude',\
verticalalignment='center',rotation='vertical')
#extract OrbitType labels
orbit_type = list(set(odb.sel_db.OrbitType))
#annotate labels into the plot at orbit location
ilon = 0 if day_or_night=='day' else -1
for itype in orbit_type:
   dff = odb.sel_db[odb.sel_db.OrbitType == itype]
   figs[1][0].annotate(itype,[dff['lon'][ilon], 66],fontsize=14)