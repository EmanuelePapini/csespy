import numpy as np
from collections import OrderedDict
from attrdict import AttrDict

AttrDictSens = AttrDict
class voidobj(object):

    def __init__(self):
    
        self=type('',(),{})



def get_size(obj, seen=None):
    """
    get real size in bytes of an object
    """
    
    # From https://goshippo.com/blog/measure-real-size-any-python-object/
    # Recursively finds size of objects
    
    import sys
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0

    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size



class NumberedDict(OrderedDict):
   
    def __getitem__(self, index):
    
        if isinstance(index, int):
            return super(NumberedDict, self).__getitem__(self.keys()[index])
        else:
            return super(NumberedDict, self).__getitem__(index)


    def __setitem__(self, index,*args,**kwargs):
    
        if isinstance(index, int):
            return super(NumberedDict, self).__setitem__(self.keys()[index],*args,**kwargs)
        else:
            return super(NumberedDict, self).__setitem__(index,*args,**kwargs)




#########################################################################
###############---OBJECT MANIPULATION/CONVERSION TOOLS---################
#########################################################################
def dict_to_namedtuple_recursive(typename, data):
    from collections import namedtuple
    return namedtuple(typename, data.keys())(
            *(dict_to_namedtuple(typename + '_' + k, v) if isinstance(v, dict) else v for k, v in data.items())
                )
def dict_to_namedtuple(d):
    return namedtuple('GenericDict', d.keys())(**d)

#******************************************************************************
def dict_to_struct(dic,dtype=None):
    keys=list(dic.viewkeys())
    nk=np.size(keys)
    ns=dic[keys[0]].size
    if dtype== None : dtype=['f']*nk
    out_str=np.zeros(ns,dtype={'names':keys,'formats':dtype})
    for i in np.arange(ns) :
        for ikey in keys : out_str[ikey][i]=dic[ikey][i]
    return out_str

#******************************************************************************
def struct_to_dict(struct):

    return {name:struct[name] for name in struct.dtype.names}

def recarray_to_dict(*args):

    return struct_to_dict(*args)

def merge_recarrays(a1,a2):
    """
    no check is done on shapes
    """
    da1 = recarray_to_dict(a1)
    da2 = recarray_to_dict(a2)
    for i in da2.keys(): da1[i] = da2[i]
    try:
        return dict_to_recarray(da1)
    except:
        raise ValueError('merge failed. Maybe due to shape incompatibility?')
#******************************************************************************
def Dict_to_AttrDict(dic):
    """
    recursively change a dictionary to a AttrDict type.
    If one of the items is also a dictionary, it also change it to an AttrDict.
    INPUT
    -----
    dic : dict
        input dictionary
    """

    out=AttrDict(dic)
    for i in out:
        if isinstance(out(i),dict) : out[i] = Dict_to_AttrDict(out[i])

    return out

def list_of_dict_to_recarray(diclist):
    """
    Convert a list of structurally identical dictionaries (i.e. dictionaries with same keys, 
    each of which being a numpy.ndarray of same shape for all keys and for all the dictionaries 
    inside the list) to a numpy.recarray
    """
    nt = len(diclist)
    if hasattr(diclist[0],'keys'):
        keys = [i for i in diclist[0].keys()]
    elif hasattr(diclist[0],'dtype'):
        keys = [i for i in diclist[0].dtype.names]
    nx = diclist[0][keys[0]].shape
    dtyps= [type(diclist[0][i].flatten()[0]) for i in keys]
    
    out = np.recarray((nt,)+nx,dtype = [(i,dtyp) for i,dtyp in zip(keys,dtyps)])
    
    for it in range(nt):
        for i in out.dtype.names: out[i][it,...] =  diclist[it][i][...]

    return out

def dict_to_recarray(dic):
    """
    Convert a list of structurally identical dictionaries (i.e. dictionaries with same keys, 
    each of which being a numpy.ndarray of same shape for all keys and for all the dictionaries 
    inside the list) to a numpy.recarray
    """
    keys = [i for i in dic.keys()]
    if hasattr(dic[keys[0]],'shape'):
        nx = dic[keys[0]].shape 
        dtyps= [type(dic[i].flatten()[0]) for i in keys]
    else:    
        nx = np.size(dic[keys[0]])
        dtyps= [type(np.asarray(dic[i]).flatten()[0]) for i in keys]
    
    out = np.recarray(nx,dtype = [(i,dtyp) for i,dtyp in zip(keys,dtyps)])
    
    for i in out.dtype.names: out[i] =  dic[i]

    return out

def list_of_recarray_to_list_of_dict(ll):
    
    return [recarray_to_dict(i) for i in ll]


def subsample_dataframe(dat,nsubsamples=1000):
    nlat = dat.shape[0]
    n = np.linspace(0,nlat-1,nsubsamples,dtype=int)
    return dat.iloc[n]

def array_add(arr,toadd, **kwargs):
    from numpy import append 
    if arr is None: return toadd
    #if type(arr) != type(toadd) : raise TypeError('Input type mismatch!')
    return append(arr,toadd,**kwargs)

def recursively_convert_dict_contents_to_dict(dic, inplace = False):
    from pandas import DatetimeIndex

    # argument type checking
    if not isinstance(dic, dict):
        raise ValueError("must provide a dictionary")        
    
    if inplace:
        copy = lambda x:x
        out = dic
    else:
        from copy import deepcopy as copy
        out = {}
    # save items to the hdf5 file
    for key, item in dic.items():
        key = str(key)
        if isinstance(item, list):
            if any([type(i) is dict for i in item]):
                item = copy({str(i):ilist for i,ilist in enumerate(item)})
            else:
                item =copy( np.array(item))
        if not isinstance(key, str):
            raise ValueError("dict keys must be strings to save to hdf5")
        # save strings, numpy.int64, and numpy.float64 types
        if isinstance(item, (np.int64, np.float64, str, np.float, float, np.float32,int)):
            out[key] = copy(item)
        #save datetime as list of timestamps
        elif str(type(item)) =="<class 'pandas.core.indexes.datetimes.DatetimeIndex'>":
            out[key] = copy(item) #np.array([i.timestamp() for i in item])
        #save bools as integer
        elif isinstance(item,(np.bool_,bool)):
            #print( 'here' )
            out[key] = copy(item)
        # save numpy arrays
        elif isinstance(item, np.recarray):            
            out[key] = recursively_convert_dict_contents_to_dict(recarray_to_dict(item), inplace)
        # save dictionaries
        elif isinstance(item, np.ndarray):            
            if item.dtype.names is not None:
                out[key] = recursively_convert_dict_contents_to_dict(recarray_to_dict(item), inplace)
            elif item.dtype == 'datetime64[ns]':
                out[key] = DatetimeIndex(item)
            else:
                out[key] = copy(item)
        # save dictionaries
        elif isinstance(item, dict):
            out[key] = recursively_convert_dict_contents_to_dict(item, inplace )
        # other types cannot be saved and will result in an error
        else:
            print(item)
            raise ValueError('Cannot save key "%s" of  %s type.' % (key,type(item)))
    return out
