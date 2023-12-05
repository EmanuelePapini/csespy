import csespy

fpath = '/Volumes/BackupMac/CSES01data/'
css = csespy.CSES(path = fpath,unstructured_path = True, orbitn = '104371')
css.load_HEP(instrument_no = '1')
hep_file = csespy.load_CSES_raw('/Volumes/BackupMac/CSES01data/CSES_01_HEP_1_L02_A4_104371_20191220_211133_20191220_214829_000.h5')
