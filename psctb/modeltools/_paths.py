from os import path, mkdir, listdir

from pysces import output_dir


__all__ = ['get_model_name', 'make_path', 'next_suffix', 'get_file_path',
           'get_fmt']


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

    # find all files in dir, exclude subdirs
    files = [each for each in listdir(directory) if
             path.isfile(path.join(directory, each))]
    # start counting at zero
    next_num = 0
    if not ext:
        ext = ''
    for each in files:
        if each.startswith(base_name) and each.endswith(ext):
            start = len(base_name + '_')
            end = start + 1
            num = int(each[start:end])
            if num >= next_num:
                next_num = num + 1
    return next_num


def get_file_path(working_dir, internal_filename, fmt, fixed=None,
                  file_name=None, write_suffix=True ):
    """An heuristic for determining the correct file name.

    This function determines the file name according to the information
    supplied by the user and the internals of a specific class.

    Parameters
    ----------
    working_dir : str
        The working dir of the specific class (where files are saved if no
        file name is supplied)
    internal_filename : str
        The default base name (sans numbered suffix) of files when no other
        details are provided.
    fmt : str
        The format (extension) that the file should be saved in. This is
        used both in determining file name if no file name is provided as
        well as when a file name without extension is provided.
    fixed : str, Optional (Default : None)
        In the case that a metabolite is fixed, files will be saved in a
        subdirectory of the working directory that corresponds to the
        fixed metabolite.
     file_name : str, Optional (Default : None)
        If a file name is supplied it overwrites all other options except
        ``fmt`` in the case where no extension is supplied.
    Returns
    -------
    str
        The final file name

    """
    if not file_name:
        if fixed:
            save_path = path.join(working_dir, fixed)
        else:
            save_path = working_dir
        if not path.exists(save_path):
            mkdir(save_path)
        suffix = ''
        if write_suffix:
            suffix = '_' + str(next_suffix(save_path,
                                     internal_filename,
                                     fmt))
        fname = internal_filename +  suffix + '.' + fmt
        file_name = path.join(save_path, fname)
    else:
        if path.splitext(file_name)[1] == '':
            file_name = file_name + '.' + fmt
        save_path = path.split(file_name)[0]
        if not path.exists(save_path):
            pass
            mkdir(save_path)
    return file_name


def get_fmt(file_name):
    """Gets the extension (fmt) from a file name.

    Parameters
    ----------
    file_name : str
        The file to get an extension from

    Returns
    -------
    str
        The extension string
    """
    return path.splitext(file_name)[1][1:]


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
