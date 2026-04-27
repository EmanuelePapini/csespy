
from .blombly.tools.objects import AttrDict
from .CSES_aux import *

fix_data = {'CSES01':AttrDict(),'CSES02':AttrDict()}


def derotate_fields(datakey,CSX,df, overwrite=False, nskip_fixed = False, tags=['Ex','Ey','Ez']):
    """
    Derotate (electric) fields according to de-rotation of the derotate_fields
    function cotained in CSES_aux.py. This rotation is done to remove the jumps
    introduced in EFD Level2 data by the approach used for using attitude 
    quaternions in the  processing pipeline of CSES01.
    
    parameters
    ----------
    overwrite : bool
        True : derotated fields overwrite the original fields.
        False : derotated fields are saved preserving the name (in tags) 
        adding the subscript '_rot'.
    nskip_fixed: bool
        if not fixed, the algorithm will look whether jumps are present or not
        in the data, at multiples of data packet size (2048 for EFD_ELF) and
        if so, will update the rotation between two jumps.
        This workaround is necessary because for some orbits of EFD ELF it was 
        found that this number is be 2048*2 or 2048*3 (consistent with 
        quaternion update rate of CSES-01)
    instrument : str
        desired instrument
    frequency : str
        desired frequency band
    tags : len=3 list of str
        list of str of the three components fo the field to be derotated 
        (contained in self.data.<instrument>_<frequency>).

    """
    nskip = CSX['CSES_PACKETSIZE'][datakey] 

    t1,t2,t3=tags
    print('Derotating '+datakey+' '+str(tags)+'...')
    #1-removing jumps by derotating artificially
    if 'gaps_mask' in df:
        EE = derotate_field(df[t1].values,df[t2].values,df[t3].values,nskip=nskip,\
            nskip_fixed = nskip_fixed, mask = df.gaps_mask.values)
    else:
        EE = derotate_field(df[t1].values,df[t2].values,df[t3].values,nskip=nskip,\
            nskip_fixed = nskip_fixed)

    if not overwrite:
        df[t1+'_rot'] = EE['x'] 
        df[t2+'_rot'] = EE['y'] 
        df[t3+'_rot'] = EE['z'] 
    else:
        df[t1] = EE['x'] 
        df[t2] = EE['y'] 
        df[t3] = EE['z'] 
    return df

for ikey in ['EFD_ULF','EFD_ELF']:
    fix_data['CSES01'][ikey] = lambda  *args,datakey=ikey,**kwargs: derotate_fields(datakey,*args,**kwargs)