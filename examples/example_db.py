cses_init
import numpy

t0 = datetime(2018,8,11)
t1 = datetime(2018,8,22)

ranges=[('lat',numpy.greater,44),('lat',numpy.less,48),('lon',numpy.greater,10),('lon',numpy.less,15)]
pwd
csdb=csespy.CSES_database('CSES01_orbitdb.h5')
csdb.search_orbit(ranges)
csdb.search_orbit_latlon([80,82],[-10,-8],use_selected_db=True)
csdb.search_orbit_timespan([t0,t1,''], return_orbitn = True)
csdb.search_orbit_latlontimespan([20,22],[-10,-8],[t0,t1])#,use_selected_db=True)

#testing integration with CSES class
cses_init
import numpy

t0 = datetime(2023,6,11)
t1 = datetime(2023,6,11,2)
css= csespy.CSES(path=fpath, orbit_database_buf = 'CSES01_orbitdb.h5')

css.select_data_to_load(timespan=(t0,t1,'N'),latspan=[10,20],lonspan=[0,10])
print(css.orbitn)
css.load_CSES(frequency='ULF')
css.data.EFD_ULF
np.unique(css.data.EFD_ULF.orbitn)
css.data.EFD_ULF.sort_index()
