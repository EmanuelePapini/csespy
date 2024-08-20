import csespy

fpath='/CSES_Data/CSES01/'
css.select_data_to_load(orbitn = '028981')
css.load_CSES(instrument='EFD',frequency='ELF',fill_missing = 'linear')
css.load_CSES(instrument='SCM',frequency='ELF',fill_missing = 'linear')
css.load_CSES(instrument='HPM',frequency='FGM1Hz',fill_missing = 'linear')
css.load_CSES(instrument='LAP',frequency='50mm',fill_missing = 'linear')

