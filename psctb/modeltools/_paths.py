from os import path, mkdir
from pysces import output_dir

__all__ = ['get_model_name', 'make_path']


def get_model_name(mod):
    """Returns the file name of a pysces model object sans the file extension.

    Arguments
    ---------
    mod : PysMod
        Model of interest.

    Returns
    -------
    str
        File name of a `mod` sans extension.

    """
    return path.split(mod.ModelFile)[1][:-4]


def make_path(mod, analysis_method, subdirs=[]):
    """Creates paths based on model name and analysis type.


    This function is used to create directories (in the case where they don't
    already exist) to write analysis  results to and return the path name.
    Subdirectories can also be created.



    /path/to/Pysces/model_name/analysis_method/subdir1/subdir2/

    Arguments
    ---------
    mod : PysMod
        The model being analysed.
    analysis_method : str
        The name of the tool being used to analyse the model.
    subdirs : list of str
        An optional list of subdirectories where each additional entry in the
        list will create a subdirectory in the previous directories.

    Returns
    -------
    str
        The directory string

    Examples
    --------
    >>> print make_path(mod, 'analysis_method', subdirs = ['subdir1', subdir2])
    '/path/to/Pysces/model_name/analysis_method/subdir1/subdir2/'


    """

    model_name = get_model_name(mod)

    model_path = path.join(output_dir,
                           model_name)

    analysis_path = path.join(output_dir,
                              model_name,
                              analysis_method)

    dirs = [model_path, analysis_path]

    for i, each in enumerate(subdirs):
        tpth = path.join(dirs[1 + i], each)
        dirs.append(tpth)

    for each in dirs:
        if not path.exists(each):
            mkdir(each)

    return dirs[-1] + '/'
