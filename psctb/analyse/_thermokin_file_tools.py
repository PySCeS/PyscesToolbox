from os import path
from re import match, findall

from sympy import Symbol


def get_term_types_from_raw_data(raw_data_dict):
    """
    Determines the types of terms defined for ThermoKin based on the
    file contents. This allows for generation of latex expressions
    based on these terms.

    Parameters
    ----------
    raw_data_dict : dict of str:{str:str}

    Returns
    -------
    set of str

    """
    term_types = set()
    for v in raw_data_dict.itervalues():
        for k in v.iterkeys():
            term_types.add(k)
    return term_types


class FormatException(Exception):
    pass


def read_files(path_to_file):
    """
    Reads the contents of a file and returns it as a list of lines.

    Parameters
    ----------
    path_to_file : str
        Path to file that is to read in

    Returns
    -------
    list of str
        The file contents as separate strings in a list

    """
    with open(path_to_file) as f:
        lines = f.readlines()
    return lines


def strip_other(raw_lines):
    """
    Takes a list of strings and returns a new list containing only
    lines starting with "!T" and strips line endings.

    Parameters
    ----------
    raw_lines : list of str

    Returns
    -------
    list of str
    """
    valid_prefix_lines =  [line for line in raw_lines if line.startswith('!T')]
    no_line_endings = []
    for line in valid_prefix_lines:
        if line[-1] == '\n':
            no_line_endings.append(line[:-1])
        else:
            no_line_endings.append(line)

    return no_line_endings


def correct_fmt(lines):
    """
    Inspects a list of string for the correct ThermoKin syntax. Returns
    `True` in case of correct format. Throws exception otherwise.

    Correct format is a str matching the pattern '!T{\w*}{\w*} .*' .
    Parameters
    ----------
    lines : list of str

    Returns
    -------
    bool

    """
    errors_in = []
    for i, line in enumerate(lines):
        if not match('!T{\w*}{\w*} .*', line):
            errors_in.append(str(i))
    if len(errors_in) == 0:
        return True
    else:
        error_str = ', '.join(errors_in)
        raise FormatException('Incorrect syntax in lines:' + error_str)


def construct_dict(lines):
    """
    Constructs a dictionary of dictionaries for each reaction.

    Here keys of the outer dictionary is reaction name strings while
    the inner dictionary keys are the term names. The inner dictionary
    values are the term expressions

    Parameters
    ----------
    lines : list of str

    Returns
    -------
    dict of str:dict of str:str
    """
    outer_dict = {}
    for line in lines:
        in_brackets = findall('(?<={)\w+', line)
        r_name = in_brackets[0]
        t_name = in_brackets[1]
        expr = findall('(?<=\w} ).*', line)[0]

        inner_dict = {t_name: expr}
        if r_name in outer_dict:
            outer_dict[r_name].update(inner_dict)
        else:
            outer_dict[r_name] = inner_dict
    return outer_dict


def get_subs_dict(expression, mod):
    """
    Builds a substitution dictionary of an expression based of the
    values of these symbols in a model.

    Parameters
    ----------
    expression : sympy expression
    mod : PysMod

    Returns
    -------
    dict of sympy symbol:float

    """
    subs_dict = {}
    symbols = expression.atoms(Symbol)
    for symbol in symbols:
        attr = str(symbol)
        subs_dict[attr] = getattr(mod, attr)
    return subs_dict


def get_reqn_path(mod):
    """
    Gets the default path and filename of`.reqn` files belonging to a model

    The `.reqn` files which contain rate equations split into different
    (arbitrary) components should be saved in the same directory as the model
    file itself by default. It should have the same filename (sans extension)
    as the model file.

    Parameters
    ----------
    mod : PysMod
        A pysces model which has corresponding `.reqn` file saved in the same
        directory with the same file name as the model file.

    Returns
    -------
    str
        A sting with the path and filename of the `.reqn` file.
    """

    fname = mod.ModelFile
    dot_loc = fname.find('.')
    fname_min_ext = fname[:dot_loc]
    fname_ext = fname_min_ext + '.reqn'
    return path.join(mod.ModelDir, fname_ext)


def get_term_dict_from_path(path_to_read):
    """
    Reads a '.reqn' file at provided location and, if the file is
    defined correctly a dict of str:{str:str} is returned representing
    the file contents.



    Parameters
    ----------
    path_to_read : str

    Returns
    -------
    dict of str:{str:str}
    """

    raw_lines = read_files(path_to_read)
    clean_lines = strip_other(raw_lines)
    if correct_fmt(clean_lines):
        term_dict = construct_dict(clean_lines)
        return term_dict