import csespy
import matplotlib.pyplot as plt

plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12
plt.rcParams['axes.labelsize'] = 15

#fpath = '/Volumes/BackupMac/CSES01data/'
#css0 = csespy.CSES(path = fpath,unstructured_path = True, orbitn = '104371')
#css1 = csespy.CSES(path = fpath,unstructured_path = True, orbitn = '104371')
#css2 = csespy.CSES(path = fpath,unstructured_path = True, orbitn = '104371')
#css0.load_HEP(instrument_no = '1',channel='all',energy_selection_list = [['>=0.1','<=1'],[]] )
#css1.load_HEP(instrument_no = '1',channel='0',energy_selection_list = [['>=0.1','<=1'],[]] )
#css2.load_HEP(instrument_no = '1',channel='0',energy_selection_list = [['>=0.1','<=2'],[]] )
##css.interpolate_inst1_to_inst2(inst1='EFD_ULF',inst2='HEPP_L',tags=['Ex', 'Ey', 'Ez'])

'''
orbitn = '104380'

fpath = '/Users/francescofollega/Documents/WORK/Limaodu_work/HEPD01/TimeCorr/CSES01tool/outputH5/'
css0 = csespy.CSES(path = fpath,unstructured_path = True, orbitn = orbitn)
css0.load_HEP(instrument_no = '3')
fpath = '/Volumes/BackupMac/CSES01data/'
css1 = csespy.CSES(path = fpath,unstructured_path = True, orbitn = orbitn)
css1.load_HEP(instrument_no = '1',channel='all',energy_selection_list = [['>=0.1','<=1'],[]] )

plt.figure(figsize=(12, 10))
#plt.plot(css0.data.HEPD.lat,css0.data.HEPD.Counts_0, 'o', alpha=0.5, label = 'HEPD01 - T')
#plt.plot(css0.data.HEPD.lat,css0.data.HEPD.Counts_1, 'o', alpha=0.5, label = 'HEPD01 - T&(P1|P2)')
#plt.plot(css1.data.HEPP_L.lat,css1.data.HEPP_L.Count_Electron, 'o', alpha=0.5, label = 'HEPP_L - Counts Electron')

plt.plot(css0.data.HEPD.lat,css0.data.HEPD.Counts_0, 'o', alpha=0.5, label = 'HEPD01 - T')
plt.plot(css0.data.HEPD.lat,css0.data.HEPD.Counts_1, 'o', alpha=0.5, label = 'HEPD01 - T & P1')
plt.plot(css1.data.HEPP_L.lat,css1.data.HEPP_L.Count_Electron, 'o', alpha=0.5, label = 'HEPP_L - Counts All Electron')
plt.legend(title = 'orbit number: '+str(orbitn), fontsize = 15, title_fontsize = 15)
plt.xlabel('Latitude [Deg]')
plt.ylabel('Counts [1/s]')
plt.yscale('log')
plt.show()
plt.savefig('../fig/orbit_'+str(orbitn)+'.png')
#plt.figure(figsize=(12, 10))
#plt.plot(css0.data.HEPP_L.Flux_Electrons, 'o', alpha=0.5)
#plt.plot(css1.data.HEPP_L.Flux_Electrons, 'o', alpha=0.5)
#plt.plot(css2.data.HEPP_L.Flux_Electrons, 'o', alpha=0.5)
#plt.show()
'''

import csespy
from csespy.blombly import pylab as plt
fpath = '/Volumes/BackupMac/CSES01data/20211211/'
css = csespy.CSES(path = fpath,unstructured_path = True, orbitn = ['214061'])
css.load_CSES(instrument='SCM',frequency='ULF')
css.load_CSES(instrument='LAP',frequency='50mm')
#css.load_CSES(instrument='EFD',frequency='ULF')
css.load_CSES(instrument='EFD',frequency='ELF')
css.load_HEP(instrument_no = '1')
css.load_HEP(instrument_no = '2')
css.load_HEP(instrument_no = '4')
css.load_HEP(instrument_no = '3')
fig,ax = css.plot_payloads([i for i in css.data.keys()], ion=True)
ax[-1].set_xlabel('UT time')
ax[-3].set_ylabel('Counts')
ax[-4].set_ylabel('Counts')
ax[-2].set_ylabel('Counts')
ax[-1].set_ylabel('Counts')
plt.tight_layout()
plt.savefig('./fig/20211211_orbit_214061.png')

fpath = '/Volumes/BackupMac/CSES01data/20190114/'
css = csespy.CSES(path = fpath,unstructured_path = True, orbitn = ['052690'])
css.load_CSES(instrument='SCM',frequency='ULF')
css.load_CSES(instrument='LAP',frequency='50mm')
#css.load_CSES(instrument='EFD',frequency='ULF')
css.load_CSES(instrument='EFD',frequency='ELF')
css.load_HEP(instrument_no = '1')
css.load_HEP(instrument_no = '2')
css.load_HEP(instrument_no = '4')
css.load_HEP(instrument_no = '3')
fig,ax = css.plot_payloads([i for i in css.data.keys()], ion=True)
ax[-1].set_xlabel('UT time')
ax[-4].set_ylabel('Counts')
ax[-3].set_ylabel('Counts')
ax[-2].set_ylabel('Counts')
ax[-1].set_ylabel('Counts')
plt.tight_layout()
plt.savefig('./fig/20190114_orbit_052690.png')

fpath = '/Volumes/BackupMac/CSES01data/20200826/'
css = csespy.CSES(path = fpath,unstructured_path = True, orbitn = ['142380'])
css.load_CSES(instrument='SCM',frequency='ULF')
css.load_CSES(instrument='LAP',frequency='50mm')
#css.load_CSES(instrument='EFD',frequency='ULF')
css.load_CSES(instrument='EFD',frequency='ELF')
css.load_HEP(instrument_no = '1')
css.load_HEP(instrument_no = '2')
css.load_HEP(instrument_no = '4')
css.load_HEP(instrument_no = '3')
fig,ax = css.plot_payloads([i for i in css.data.keys()], ion=True)
ax[-1].set_xlabel('UT time')
ax[-4].set_ylabel('Counts')
ax[-3].set_ylabel('Counts')
ax[-2].set_ylabel('Counts')
ax[-1].set_ylabel('Counts')
plt.tight_layout()
plt.savefig('./fig/20200826_orbit_142380.png')

fpath = '/Volumes/BackupMac/CSES01data/20190305/'
css = csespy.CSES(path = fpath,unstructured_path = True, orbitn = ['060240'])
css.load_CSES(instrument='SCM',frequency='ULF')
css.load_CSES(instrument='LAP',frequency='50mm')
#css.load_CSES(instrument='EFD',frequency='ULF')
css.load_CSES(instrument='EFD',frequency='ELF')
css.load_HEP(instrument_no = '1')
css.load_HEP(instrument_no = '2')
css.load_HEP(instrument_no = '4')
css.load_HEP(instrument_no = '3')
fig,ax = css.plot_payloads([i for i in css.data.keys()], ion=True)
ax[-1].set_xlabel('UT time')
ax[-4].set_ylabel('Counts')
ax[-3].set_ylabel('Counts')
ax[-2].set_ylabel('Counts')
ax[-1].set_ylabel('Counts')
plt.tight_layout()
plt.savefig('./fig/20190305_orbit_060240.png')

fpath = '/Volumes/BackupMac/CSES01data/20190928/'
css = csespy.CSES(path = fpath,unstructured_path = True, orbitn = ['091701'])
css.load_CSES(instrument='SCM',frequency='ULF')
css.load_CSES(instrument='LAP',frequency='50mm')
#css.load_CSES(instrument='EFD',frequency='ULF')
css.load_CSES(instrument='EFD',frequency='ELF')
css.load_HEP(instrument_no = '1')
css.load_HEP(instrument_no = '2')
css.load_HEP(instrument_no = '4')
css.load_HEP(instrument_no = '3')
fig,ax = css.plot_payloads([i for i in css.data.keys()], ion=True)
ax[-1].set_xlabel('UT time')
ax[-4].set_ylabel('Counts')
ax[-3].set_ylabel('Counts')
ax[-2].set_ylabel('Counts')
ax[-1].set_ylabel('Counts')
plt.tight_layout()
plt.savefig('./fig/20190928_orbit_091701.png')

fpath = '/Volumes/BackupMac/CSES01data/20221009/'
css = csespy.CSES(path = fpath,unstructured_path = True, orbitn = ['259970'])
css.load_CSES(instrument='EFD',frequency='ELF')
css.load_CSES(instrument='SCM',frequency='ELF')
css.load_HEP(instrument_no = '1')
css.load_HEP(instrument_no = '2')
css.load_HEP(instrument_no = '4')
fig,ax = css.plot_payloads([i for i in css.data.keys()], ion=True)
ax[-1].set_xlabel('UT time')
ax[-4].set_ylabel('Counts')
ax[-2].set_ylabel('Counts')
ax[-1].set_ylabel('Counts')
plt.tight_layout()
plt.savefig('./fig/20221009_orbit_259970.png')