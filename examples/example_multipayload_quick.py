import csespy
from datetime import datetime

#Path to CSES-01 database and to orbit database
datapath = '/CSES01Data/'

#select time interval with highest Kp index (known from the web)
t0 = datetime(2024,5,10,18)
t0 = datetime(2024,5,12,28)

#initialize the CSES object and look for desired orbits
orbitn='348201' #the other orbit is '337561'
css = csespy.CSES(path=datapath,orbitn=orbitn,unstructured_path=True)
css.orbitdb.search_orbit_timespan((t0,t1))
css.load_CSES(instrument='SCM',frequency='VLF',get_PSD=True)
css.load_CSES(instrument='LAP',frequency='50mm',fill_missing='nan')
css.load_CSES(instrument='EFD',frequency='ELF')
css.load_CSES(instrument='EFD',frequency='VLF',get_PSD=True)
css.load_CSES(instrument='HEP',frequency='P_L',\
energy_selection_list=[['>1','<=100'],['>1','<=100']])

#Plot data
figax=css.plot_payloads(['EFD_ELF','LAP_50mm',\
['HEPP_L',['Flux_Electrons','Flux_Protons']]],\
spectrograms=[['SCM_VLF','EFD_VLF'],[['By'],['Ex']]],psdkwargs={'plot_colorbar':True},xaxis='lat')
dat = str(css.aux['EFD_VLF_P'][orbitn]['UTC'])[:10]
figax[1][0].set_title('Quicklook' + dat + ' orbit: '+orbitn)
figax[1][2].set_ylabel(r'Flux > 1 MeV [$\mathrm{cm^{-2}/s/srad}$]')
#this step is not necessary.
#Is done to have same limits on both plots.
figax[1][2].set_ylim([1.8e-2,3.2e3])

#Saving the figure
figax[0].savefig('quicklook_'+orbitn+'.png',format='png',dpi=300)