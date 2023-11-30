

import os


def create_folder(folder):
    try:
        if os.path.exists(folder):
            if not os.path.isdir(folder):
                os.rename(folder,folder+'_file') 
                os.mkdir(folder)
                print ("file %s already exists. Renaming" % folder)
        else:
            os.mkdir(folder)
            print ("Creating the directory %s " % folder)
    except OSError:
        print ("Creation of the directory %s failed" % folder)

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
            sf, f = run_fast_scandir(dir, ext)
            subfolders.extend(sf)
            files.extend(f)
    return subfolders, files

def search_file(spath,string, recursive = False, abs_path = False):    # dir: str, ext: list
    
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
            if f.name in string:
                files.append(get_path(f.path))

    if recursive:
        for spath in list(subfolders):
            sf, f = search_file(spath, string, recursive = recursive,abs_path = abs_path)
            subfolders.extend(sf)
            files.extend(f)
    
    return subfolders, files
