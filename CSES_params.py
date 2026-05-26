"""
#
# Set of dictionaries containing the parameters for the csespy package
#
# Author: Emanuele Papini (EP) && Francesco Maria Follega (FMF)
#
# Date: 17/04/2024
#
"""
from .blombly.tools.objects import AttrDict
#Dictionary containing the bands corresponding to the id number 
#on the CSES filename. See file naming convention for CSES-01
# Dict structure:
# instrument_key:{id:bandname}
# e.g. the id number for the ULF band of the EFD instrument is 1, then
# we have that CSES_DATA_TABLE['EFD']['1'] == 'ULF'
CS1 = {}

CS1['NAME'] = 'CSES01'
CS1['CSES_DATA_TABLE'] = {'EFD':{'1':'ULF','2':'ELF','3':'VLF','4':'HF'},\
                   'HPM':{'1':'FGM1','2':'FGM2','3':'CDSM','5':'FGM1Hz','6':'CDSM1Hz'},\
                   'SCM':{'1':'ULF','2':'ELF','3':'VLF'},\
                   'LAP':{'1':'50mm', '2':'10mm'},\
                   'PAP':{'0':''}, \
                   'HEP':{'1':'P_L','2':'P_H','3':'D','4':'P_X'}}

CS1['CSES_DATAKEYS'] = {
               'EFD_ULF':dict(instrument='EFD',InstrumentNo='1',band='ULF'),\
               'EFD_ELF':dict(instrument='EFD',InstrumentNo='2',band='ELF'),\
               'EFD_VLF':dict(instrument='EFD',InstrumentNo='3',band='VLF'),\
               'EFD_HF': dict(instrument='EFD',InstrumentNo='4',band='HF'),\
               'SCM_ULF':dict(instrument='SCM',InstrumentNo='1',band='ULF'),\
               'SCM_ELF':dict(instrument='SCM',InstrumentNo='2',band='ELF'),\
               'SCM_VLF':dict(instrument='SCM',InstrumentNo='3',band='VLF'),\
               'HPM_FGM1':  dict(instrument='HPM',InstrumentNo='1',band=None),\
               'HPM_FGM3':  dict(instrument='HPM',InstrumentNo='2',band=None),\
               'HPM_CDSM':  dict(instrument='HPM',InstrumentNo='3',band=None),\
               'HPM_FGM1Hz':dict(instrument='HPM',InstrumentNo='5',band=None),\
               'HPM_CDSM1Hz':dict(instrument='HPM',InstrumentNo='6',band=None),\
               'LAP_50mm':  dict(instrument='LAP',InstrumentNo='1',band=None),\
               'LAP_10mm':  dict(instrument='LAP',InstrumentNo='2',band=None),\
               'PAP':  dict(instrument='PAP',InstrumentNo='0',band=None),\
               'HEPP_L':  dict(instrument='HEP',InstrumentNo='1',band=None),\
               'HEPP_H':  dict(instrument='HEP',InstrumentNo='2',band=None),\
               'HEPD':    dict(instrument='HEP',InstrumentNo='3',band=None),\
               'HEPP_X':  dict(instrument='HEP',InstrumentNo='4',band=None)\
                   }

#Dictionary of the name translations for the fields contained in the 
#HDF5 output files of CSES-01. 
#N.B. THIS IS STILL KEPT HERE FOR LEGACY. 
#     IT'S USE IS DEPRECATED SINCE CSES_DATASETS 
#     CONTAINS THE SAME INFORMATION
CS1['CSES_FILE_TABLE'] = {'EFD':{\
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
                       '6':{'A211':'B'},\
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

CS1['CSES_POSITION'] = {'ALTITUDE':'alt',\
                 'GEO_LAT':'lat',\
                 'GEO_LON':'lon',\
                 'MAG_LAT':'mag_lat',\
                 'MAG_LON':'mag_lon'}

#Dict containing the translation of the datasets contained in
# the hdf5 files to their corresponding physical name
# e.g. A121_W is the waveform of Ex in ELF band
# while A121_P is the spectrogram, translated as Ex_P
CS1['CSES_DATASETS'] = {'A111_P':'Ex_P','A111_W':'Ex',\
                 'A112_P':'Ey_P','A112_W':'Ey',\
                 'A113_P':'Ez_P','A113_W':'Ez',\
                 'A121_P':'Ex_P','A121_W':'Ex',\
                 'A122_P':'Ey_P','A122_W':'Ey',\
                 'A123_P':'Ez_P','A123_W':'Ez',\
                 'A131_P':'Ex_P','A131_W':'Ex',\
                 'A132_P':'Ey_P','A132_W':'Ey',\
                 'A133_P':'Ez_P','A133_W':'Ez',\
                 'A231_P':'Bx_P','A231_W':'Bx',\
                 'A232_P':'By_P','A232_W':'By',\
                 'A233_P':'Bz_P','A233_W':'Bz',\
                 'A241_P':'Bx_P','A241_W':'Bx',\
                 'A242_P':'By_P','A242_W':'By',\
                 'A243_P':'Bz_P','A243_W':'Bz',\
                 'A251_P':'Bx_P','A251_W':'Bx',\
                 'A252_P':'By_P','A252_W':'By',\
                 'A253_P':'Bz_P','A253_W':'Bz',\
                 'A211':'B',\
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
CS1['CSES_SAMPLINGFREQS'] = {'EFD_ULF':125.,'EFD_ELF':5000.,'EFD_VLF':50000.,\
                      'SCM_ULF':1024.,'SCM_ELF':10240.,'SCM_VLF':51200.,'LAP_50mm':1/3,'PAP_':1.,\
                      'HPM_FGM1Hz':1.,'HPM_CDSM1Hz':1.,'HEP':1.}

CS1['CSES_PACKETSIZE'] = {'EFD_ULF':256,'EFD_ELF':2048,'EFD_VLF':2048,'EFD_HF':2048,\
                   'SCM_ULF':4096,'SCM_ELF':4096,'SCM_VLF':4096,'LAP_50mm':1,'PAP_':1,\
                   'HPM_FGM1Hz':1,'HPM_CDSM1Hz':1,'HEP':1}

CS1['CSES_FILESYSTEM'] = {'EFD':'year/FREQUENCY/month',\
                   'HPM':'year/month',\
                   'LAP':'year/month',\
                   'SCM':'year/FREQUENCY/month',\
                   'PAP':'',\
                   'HEP':'year/month'}

#conversion factors for the various quantitities that are read: 'Bx_P':(a,b) means that 
# Bx_P out = a*(Bx_P**b)
CS1['CSES_CF'] = {'Bx_P':(1,1),'By_P':(1,1),'Bz_P':(1,1),\
           'Ex_P':(1,2),'Ey_P':(1,2),'Ez_P':(1,2)}



#PARAMS FOR CSES-02
CS2 = {}

CS2['NAME'] = 'CSES02'
CS2['CSES_DATA_TABLE'] = {'EFD':{'1':'ULF','2':'ELF','3':'VLF','4':'VLFe','5':'HF'}}
CS2['CSES_DATAKEYS'] = {'EFD_ULF':dict(instrument='EFD',InstrumentNo='1',band='ULF'),\
                 'EFD_ELF':dict(instrument='EFD',InstrumentNo='2',band='ELF'),\
                 'EFD_VLF':dict(instrument='EFD',InstrumentNo='3',band='VLF'),\
                 'EFD_VLFe':dict(instrument='EFD',InstrumentNo='4',band='VLFe'),\
                 'EFD_VLF_P':dict(instrument='EFD',InstrumentNo='3',band='VLF',type='fft'),\
                 'EFD_VLFe_P':dict(instrument='EFD',InstrumentNo='4',band='VLFe',type='fft'),\
                 'EFD_HF_P':dict(instrument='EFD',InstrumentNo='5',band='HF',type='fft'),}
CS2['CSES_FILE_TABLE'] = {'EFD':{\
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
                       '4':{'A141_W':'Ex',\
                            'A142_W':'Ey',\
                            'A143_W':'Ez'
                           },\
                         }}

CS2['CSES_POSITION'] = {'ALTITUDE':'alt',\
                 'GEO_LAT':'lat',\
                 'GEO_LON':'lon',\
                 'MAG_LAT':'mag_lat',\
                 'MAG_LON':'mag_lon'}
CS2['CSES_DATASETS'] = {'W_Va':'Va','W_Vb':'Vb','W_Vc':'Vc','W_Vd':'Vd',\
                 'A111_W':'Ex','A111_W_sp':'Ex_sp', 'A111_W_efd':'Ex_efd',\
                 'A112_W':'Ey','A112_W_sp':'Ey_sp', 'A112_W_efd':'Ey_efd',\
                 'A113_W':'Ez','A113_W_sp':'Ez_sp', 'A113_W_efd':'Ez_efd',\
                 'A121_W':'Ex','A121_W_sp':'Ex_sp', 'A121_W_efd':'Ex_efd',\
                 'A122_W':'Ey','A122_W_sp':'Ey_sp', 'A122_W_efd':'Ey_efd',\
                 'A123_W':'Ez','A123_W_sp':'Ez_sp', 'A123_W_efd':'Ez_efd',\
                 'A131_W':'Ex','A131_W_sp':'Ex_sp', 'A131_W_efd':'Ex_efd',\
                 'A132_W':'Ey','A132_W_sp':'Ey_sp', 'A132_W_efd':'Ey_efd',\
                 'A133_W':'Ez','A133_W_sp':'Ez_sp', 'A133_W_efd':'Ez_efd',\
                 'A131e_W':'Ex','A131e_W_sp':'Ex_sp', 'A131e_W_efd':'Ex_efd',\
                 'A132e_W':'Ey','A132e_W_sp':'Ey_sp', 'A132e_W_efd':'Ey_efd',\
                 'A133e_W':'Ez','A133e_W_sp':'Ez_sp', 'A133e_W_efd':'Ez_efd',\
                 'A131_Pm':'Ex_Pm','A131_Pd':'Ex_Pd', 'A131_Pk':'Ex_Pk',\
                 'A132_Pm':'Ey_Pm','A132_Pd':'Ey_Pd', 'A132_Pk':'Ey_Pk',\
                 'A133_Pm':'Ez_Pm','A133_Pd':'Ez_Pd', 'A133_Pk':'Ez_Pk',\
                 'A131e_Pm':'Ex_Pm','A131e_Pd':'Ex_Pd', 'A131e_Pk':'Ex_Pk',\
                 'A132e_Pm':'Ey_Pm','A132e_Pd':'Ey_Pd', 'A132e_Pk':'Ey_Pk',\
                 'A133e_Pm':'Ez_Pm','A133e_Pd':'Ez_Pd', 'A133e_Pk':'Ez_Pk',\
                 'A151_Pm':'Ex_Pm','A151_Pd':'Ex_Pd', 'A151_Pk':'Ex_Pk',\
                 'A152_Pm':'Ey_Pm','A152_Pd':'Ey_Pd', 'A152_Pk':'Ey_Pk',\
                 'A153_Pm':'Ez_Pm','A153_Pd':'Ez_Pd', 'A153_Pk':'Ez_Pk'}

CS2['CSES_SAMPLINGFREQS'] = {'EFD_ULF':244.140625,'EFD_ELF':5000.,'EFD_VLF':80000.,'EFD_VLFe':200000.,'EFD_HF':8e6}
CS2['CSES_PACKETSIZE'] = {'EFD_ULF':2048,'EFD_ELF':2048,'EFD_VLF':2048,'EFD_HF':2048,'EFD_VLFe':2048,\
                          'EFD_VLF_P':2048,'EFD_HF_P':2048,'EFD_VLFe_P':2048}

CS2['CSES_FILESYSTEM'] = {'EFD':'year/month/FREQUENCY',\
                          'HPM':'INSTRUMENT/year/month',\
                          'LAP':'INSTRUMENT/year/month',\
                          'SCM':'INSTRUMENT/year/FREQUENCY/month',\
                          'PAP':'INSTRUMENT/',\
                          'HEP':'INSTRUMENT/year/month'}
#conversion factors for the various quantitities that are read: 'Bx_P':(a,b) means that 
# Bx_P out = a*(Bx_P**b)
CS2['CSES_CF'] = {'Bx_P':(1,1),'By_P':(1,1),'Bz_P':(1,1),\
           'Ex_P':(1,1),'Ey_P':(1,1),'Ez_P':(1,1)}



SPACECRAFT = {'CSES01':AttrDict(CS1),'CSES02':AttrDict(CS2)}
CSES_EXTENSIONS = ['.h5','.zarr.zip']
