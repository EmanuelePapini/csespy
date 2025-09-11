

import os


def create_folder(infolder, rename_if_file_exists = True):
    folder = infolder
    try:
        if os.path.exists(folder):
            if not os.path.isdir(folder):
                #os.rename(folder,folder+'_file') 
                if rename_if_file_exists:
                    new_folder = folder+'_new'
                    print ("file %s with desired name already exists. Renaming to %s" % (folder,new_folder))
                    return create_folder(new_folder)
                else:
                    print("file %s with desired name already exists. folder not created" % (folder))
                    return None
        else:
            os.makedirs(folder)
            print ("Creating the directory %s " % folder)
    except OSError:
        print ("Creation of the directory %s failed" % folder)
    return folder

def run_fast_scandir_ext(dir, ext,recursive = False):    # dir: str, ext: list
    subfolders, files = [], []

    for f in os.scandir(dir):
        if f.is_dir():
            subfolders.append(f.path)
        if f.is_file():
            if os.path.splitext(f.name)[1].lower() in ext:
                files.append(f.path)

    if recursive :
        for dir in list(subfolders):
            sf, f = run_fast_scandir_ext(dir, ext,recursive)
            subfolders.extend(sf)
            files.extend(f)
    return subfolders, files

def search_file(spath,string, recursive = False, abs_path = False, extension= None):    # dir: str, ext: list
    
    subfolders, files = [], []
    if abs_path:
        get_path = os.path.abspath
    else:    
        get_path = lambda x : x

    if type(string) is not list : string = [string]
    
    for f in os.scandir(spath):
        if f.is_dir():
            subfolders.append(get_path(f.path))
        if f.is_file():
            if any([istr in f.name for istr in string]):
                files.append(get_path(f.path))

    if recursive:
        for spath in list(subfolders):
            sf, f = search_file(spath, string, recursive = recursive,abs_path = abs_path)
            subfolders.extend(sf)
            files.extend(f)
    if extension is not None:
        files = [ifile for ifile in files if ifile[-len(extension):] == extension] 
    return subfolders, files

def split_path(pathstr):
    """
    split path string in in folder string and file string
    WARNING: It requires that the special character '\' is not present in any file/folder names
    """
    filename = pathstr.split('/')[-1].split('\\')[-1].split('/')[-1].split('\\')[-1]    
    return pathstr[:-len(filename)], filename