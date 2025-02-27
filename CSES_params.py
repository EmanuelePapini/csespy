"""
#
# Set of dictionaries containing the parameters for the csespy package
#
# Author: Emanuele Papini (EP) && Francesco Maria Follega (FMF)
#
# Date: 17/04/2024
#
"""

#Dictionary containing the bands corresponding to the id number 
#on the CSES filename. See file naming convention for CSES-01
# Dict structure:
# instrument_key:{id:bandname}
# e.g. the id number for the ULF band of the EFD instrument is 1, then
# we have that CSES_DATA_TABLE['EFD']['1'] == 'ULF'
CSES_DATA_TABLE = {'EFD':{'1':'ULF','2':'ELF','3':'VLF','4':'HF'},\
                   'HPM':{'1':'FGM1','2':'FGM2','3':'CDSM','5':'FGM1Hz'},\
                   'SCM':{'1':'ULF','2':'ELF','3':'VLF'},\
                   'LAP':{'1':'50mm', '2':'10mm'},\
                   'PAP':{'0':''}, \
                   'HEP':{'1':'P_L','2':'P_H','3':'D','4':'P_X'}}

#Dictionary of the name translations for the fields contained in the 
#HDF5 output files of CSES-01. 
#N.B. THIS IS STILL KEPT HERE FOR LEGACY. 
#     IT'S USE IS DEPRECATED SINCE CSES_DATASETS 
#     CONTAINS THE SAME INFORMATION
CSES_FILE_TABLE = {'EFD':{\
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

CSES_POSITION = {'ALTITUDE':'alt',\
                 'GEO_LAT':'lat',\
                 'GEO_LON':'lon',\
                 'MAG_LAT':'mag_lat',\
                 'MAG_LON':'mag_lon'}

#Dict containing the translation of the datasets contained in
# the hdf5 files to their corresponding physical name
# e.g. A121_W is the waveform of Ex in ELF band
# while A121_P is the spectrogram, translated as Ex_P
CSES_DATASETS = {'A111_P':'Ex_P','A111_W':'Ex',\
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
CSES_SAMPLINGFREQS = {'EFD_ULF':125.,'EFD_ELF':5000.,'EFD_VLF':50000.,\
                      'SCM_ULF':1024.,'SCM_ELF':10240.,'SCM_VLF':51200.,'LAP_50mm':1/3,'PAP_':1.,\
                      'HPM_FGM1Hz':1.,'HEP':1.}

CSES_PACKETSIZE = {'EFD_ULF':256,'EFD_ELF':2048,'EFD_VLF':2048,'EFD_HF':2048,\
                   'SCM_ULF':4096,'SCM_ELF':4096,'SCM_VLF':4096,'LAP_50mm':1,'PAP_':1,\
                   'HPM_FGM1Hz':1,'HEP':1}

CSES_FILESYSTEM = {'EFD':'year/FREQUENCY/month',\
                   'HPM':'year/month',\
                   'LAP':'year/month',\
                   'SCM':'year/FREQUENCY/month',\
                   'PAP':'',\
                   'HEP':'year/month'}
CSES_EXTENSIONS = ['.h5','.zarr.zip']