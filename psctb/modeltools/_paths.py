from os import path, mkdir, listdir
from pysces import output_dir

__all__ = ['get_model_name', 'make_path', 'next_suffix']


def get_model_name(mod):
    """Returns the file name of a pysces model object sans the file extension.

    Parameters
    ----------
    mod : PysMod
        Model of interest.

    Returns
    -------
    str
        File name of a `mod` sans extension.

    """
    return path.split(mod.ModelFile)[1][:-4]

def next_suffix(directory, base_name, ext=None):
    """Returns the number of the next suffix to be appended to a base file name
    when saving a file.

    This function checks a ``directory`` for files containing ``base_name`` and
    returns a number that is equal to the suffix of a file named ``base_name``
    with the largest suffix plus one.

    Parameters
    ----------
    directory : str
        The directory to inspect for files.
    base_name : str
        The base name (sans suffix) to check for.

    Returns
    -------
    int
        The next suffix to write
    """

    #find all files in dir, exclude subdirs
    files = [each for each in listdir(directory) if path.isfile(path.join(directory,each))]
    #start counting at zero
    next_num = 0
    if not ext:
        ext = ''
    for each in files:
        if base_name in each and ext in each:
            start = len(base_name + '_')
            end = start + 1
            num = int(each[start:end])
            if num >= next_num:
                next_num = num+1
    return next_num

def make_path(mod, analysis_method, subdirs=[]):
    """Creates paths based on model name and analysis type.


    This function is used to create directories (in the case where they don't
    already exist) to write analysis  results to and return the path name.
    Subdirectories can also be created.



    /path/to/Pysces/model_name/analysis_method/subdir1/subdir2/

    Parameters
    ----------
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

    return dirs[-1]
