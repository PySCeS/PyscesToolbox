from os import path, mkdir
from pysces import model, model_dir, output_dir
import cStringIO,string

__all__ = ['get_model_name','make_path']

def get_model_name(mod):
    """Returns the name of a model 'mod' sans the extension

    Arguments:
    ==========
    mod             - The model of interest
    """
    return path.split(mod.ModelFile)[1][:-4]

def make_path(mod,analysis_method,subdirs = []):
    """
    make_path(mod,analysis_method,subdirs = [])

    This function is used to create directories 
    (if they don't exist) to write analysis
    results to and return the path name. The 
    return value will be:

    /path/to/Pysces/model_name/analysis_method/subdir1/subdir2/

    Arguments:
    ==========
    mod             - The model being analysed 
    analysis_method - The tool being used to analyse the model
    subdirs         - An optional list of subdirectories


    """

    model_name = get_model_name(mod)
    
    model_path = path.join(output_dir,
                           model_name)

    analysis_path = path.join(output_dir,
                              model_name,
                              analysis_method)

    dirs = [model_path,analysis_path]

    for i,each in enumerate(subdirs):
        tpth = path.join(dirs[1+i], each)
        dirs.append(tpth)

    for each in dirs:
        if not path.exists(each):
            mkdir(each)

    return dirs[-1] + '/'


