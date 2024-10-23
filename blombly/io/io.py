import numpy as np
from ..tools.objects import Dict_to_AttrDict
import flammkuchen as fl
from . import msg
import h5py 

def write_h5(*args,**kwargs):
    fl.save(*args,**kwargs)

def save_dict_to_h5(filename,indata):

    data=indata.copy()
    if type(data) == np.recarray :
            data = {name:data[name] for name in data.dtype.names}
    else :
        for i in data:
            item = data[i]
            if type(item) == np.recarray :
                data[i] = {name:item[name] for name in item.dtype.names}
        
    fl.save(filename,data) 

def save_np_to_h5(filename,indata):

    data=indata.copy()
    if type(data) == np.recarray :
            data = {name:data[name] for name in data.dtype.names}
            fl.save(filename,data) 
    
def load_h5(filename,**kwargs):

    out = fl.load(filename,**kwargs)

    #out=Dict_to_AttrDict(out)
    
    return out

def save_dataframe_to_h5(filename,df,group='/',index=None,compression='gzip',\
    compression_opts=9,**kwargs):

    fil = h5py.File(filename,**kwargs)

    try:
        for i in df.keys():
            if type(df[i].values[0]) == np.bool_:
                fil.create_dataset(group+i,data=df[i].values.astype(int),\
                compression=compression,compression_opts=compression_opts)
            else:
                fil.create_dataset(group+i,data=df[i].values,\
                compression=compression,compression_opts=compression_opts)
        if type(index) == dict:
            for i in index:
                fil.create_dataset(group+i,data=index[i],\
                compression=compression,compression_opts=compression_opts)
    except:
        print("unable to save dataframe to file, please find the mistake!")
    fil.close()

#amazing set of routines to recursively save dictionaries of dictionaries to hdf5 file
#taken directly from stack overflow 
#https://codereview.stackexchange.com/questions/120802/recursively-save-python-dictionaries-to-hdf5-files-using-h5py/121308

def save_dict_to_hdf5(dic, filename,mode = 'w',**kwargs):

    with h5py.File(filename, mode = mode,**kwargs) as h5file:
        #try:
        recursively_save_dict_contents_to_group(h5file, '/', dic)
        #except:
        #h5file.close()

def load_dict_from_hdf5(filename):

    with h5py.File(filename, 'r') as h5file:
        return recursively_load_dict_contents_from_group(h5file, '/')



def recursively_save_dict_contents_to_group( h5file, path, dic):

    # argument type checking
    if not isinstance(dic, dict):
        raise ValueError("must provide a dictionary")        

    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if not isinstance(h5file, h5py._hl.files.File):
        raise ValueError("must be an open h5py file")
    # save items to the hdf5 file
    #print([key for key,item in dic.items()])
    for skey in dic.keys():
        #print(key,item)
        item = dic[skey]
        key = str(skey)
        #print(key,type(item))
        if isinstance(item, list):
            item = np.array(item)
            #print(item)
        #if not isinstance(key, str):
        #    raise ValueError("dict keys must be strings to save to hdf5")
        # save strings, numpy.int64, and numpy.float64 types
        if isinstance(item, (np.int64, np.float64, str, np.float16, float, np.float32,int)):
            #print( 'here',key )
            h5file.create_dataset(path + key,data = item)
            #print( 'still here',key )

            if not np.array_equal(h5file[path + key], item):
                msg.warning('Dataset <'+path+key+'> written on HDF5, but the data representation in the HDF5 file does not match the original dict.')
                #raise ValueError('The data representation in the HDF5 file does not match the original dict.')
        #save datetime as list of timestamps
        elif str(type(item)) =="<class 'pandas.core.indexes.datetimes.DatetimeIndex'>":
            h5file[path + key] = np.array([i.timestamp() for i in item])

        #save bools as integer
        elif isinstance(item,(np.bool_,bool)):
            #print( 'here' )
            h5file[path + key] = int(item)
            if not np.array_equal(h5file[path + key], item):
                raise ValueError('The data representation in the HDF5 file does not match the original dict.')
        # save numpy arrays
        elif isinstance(item, np.recarray):            
            recursively_save_dict_contents_to_group(h5file, path + key + '/', _recarray_to_dict(item))
        # save ndarrays
        elif isinstance(item, np.ndarray):            
            try:
                h5file.create_dataset(path + key, data = item)
            except:
                item = np.array(item).astype('|S9')
                h5file[path + key] = item
            if not np.array_equal(h5file[path + key], item):
                #print(np.array_equal(h5file[path + key], item))
                #print(path+key)
                #print(h5file[path+key].shape)
                #print(np.shape(item))
                #print('ciao3')
                msg.warning('Dataset <'+path+key+'> written on HDF5, but the data representation in the HDF5 file does not match the original dict.')
        # save dictionaries
        elif isinstance(item, dict):
            recursively_save_dict_contents_to_group(h5file, path + key + '/', item)
        # other types cannot be saved and will result in an error
        #save dataframes
        elif str(type(item)) == "<class 'pandas.core.frame.DataFrame'>":
            try:
               for i in item.keys():
                   #print(i)
                   if type(item[i].values[0]) == np.bool_:
                       h5file.create_dataset(path+key+'/'+i,data=item[i].values.astype(int))
                   else:
                       h5file.create_dataset(path+key+'/'+i,data=item[i].values)
               #if type(index) == dict:
               #    for i in index:
               #        fil.create_dataset(path+key+'/'+i,data=index[i])
            except:
                print("unable to save dataframe to file, please find the mistake!")
            
        else:
            #print(item)
            print('Cannot save key "%s" of  %s type.' % (key,type(item)))
        #print( 'ola',key )

def recursively_load_dict_contents_from_group( h5file, path): 

    ans = {}
    for key, item in h5file[path].items():
        if isinstance(item, h5py._hl.dataset.Dataset):
            ans[key] = item.value
        elif isinstance(item, h5py._hl.group.Group):
            ans[key] = recursively_load_dict_contents_from_group(h5file, path + key + '/')
    return ans       




#################################################################################
#UTILITIES TO GET INFOS FROM HDF5 FILES. MAYBE REDUNDANT BUT COULD BE USEFUL
#################################################################################



def descend_obj(obj,sep='\t'):
    """
    Iterate through groups in a HDF5 file and prints the groups and datasets names and datasets attributes
    """
    import h5py
    if type(obj) in [h5py._hl.group.Group,h5py._hl.files.File]:
        for key in obj.keys():
            print(sep,'-',key,':',obj[key])
            descend_obj(obj[key],sep=sep+'\t')
    elif type(obj)==h5py._hl.dataset.Dataset:
        for key in obj.attrs.keys():
            print(sep+'\t','-',key,':',obj.attrs[key])

def h5dump(path,group='/'):
    """
    print HDF5 file metadata

    group: you can give a specific group, defaults to the root group
    """
    with h5py.File(path,'r') as f:
         descend_obj(f[group])

def get_datasets_keys(obj,sep='\t',parent='',verbose=False):
    """
    Iterate through groups in a HDF5 file and prints the groups and datasets names and datasets attributes
    """
    import h5py
    out = []
    if type(obj) in [h5py._hl.group.Group,h5py._hl.files.File]:
        #for key in obj.keys():
            #if verbose: print(key)# print(sep,'-',key,':',obj[key])
            #out.append(get_datasets_keys(obj[key],sep=sep+'\t',parent=parent+key,verbose=verbose))
         out = [get_datasets_keys(obj[key],sep=sep+'\t',parent=parent+'/'+key) for key in obj.keys()]
    elif type(obj)==h5py._hl.dataset.Dataset:
        #for key in obj.attrs.keys():
        #    if verbose : print(key)#print(sep+'\t','-',key,':',obj.attrs[key])
        #    out.append(parent+key)
        return(parent)
    return out

def list_dataset(data, indent=1):

    """Print the list of datasets.

    Keyword arguments:
    data -- dictionary with data
    """

    descend_obj(data,sep='\t') 

#******************************************************************************
def _recarray_to_dict(struct):

    return {name:struct[name] for name in struct.dtype.names}
