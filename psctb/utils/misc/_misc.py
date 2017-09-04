import sys
from os import path, devnull


from numpy.ma import log10
from numpy import array, errstate, nanmin, nanmax, nonzero, float64,\
    bool_, string_, ones
from pysces.PyscesModel import PysMod
from IPython.display import HTML
from sympy import sympify
from functools import wraps
from ..config import ConfigReader

__all__ = ['cc_list',
           'ec_list',
           'rc_list',
           'prc_list',
           'silence_print',
           'DotDict',
           'PseudoDotDict',
           'is_number',
           'formatter_factory',
           'html_table',
           'do_safe_state',
           'find_min',
           'find_max',
           'split_coefficient',
           'ec_dict',
           'cc_dict',
           'rc_dict',
           'prc_dict',
           'group_sort',
           'extract_model',
           'get_value',
           'get_value_eval',
           'get_value_sympy',
           'print_f',
           'stringify',
           'is_iterable',
           'scanner_range_setup',
           'is_linear',
           'column_multiply',
           'unix_to_windows_path',
           'flux_list',
           'ss_species_list',
           'get_filename_from_caller',
           'memoize',
           'is_reaction',
           'is_species',
           'is_parameter',
           'is_variable',
           'is_attr',
           'is_mca_coef',
           'is_ec',
           'is_cc',
           'is_rc',
           'is_prc',]


def memoize(function):
    memo = {}
    @wraps(function)
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            return_val = function(*args)
            memo[args] = return_val
            return return_val
    return wrapper

@memoize
def is_species(attr, model):
    if attr.endswith('_ss'):
        attr = attr[:-3]
    if attr in model.species:
        return True
    else:
        return False

@memoize
def is_reaction(attr, model):
    if attr.endswith('J_'):
        attr = attr[2:]
    if attr in model.reactions:
        return True
    else:
        return False

@memoize
def is_parameter(attr, model):
    if attr in model.parameters:
        return True
    else:
        return False

@memoize
def is_variable(attr, model):
    if is_species(attr,model) or is_reaction(attr,model) or is_mca_coef(attr, model):
        return True
    else:
        return False

@memoize
def is_attr(attr, model):
    if is_variable(attr, model) or is_parameter(attr, model) or is_mca_coef(attr, model):
        return True
    else:
        return False

@memoize
def is_cc(attr, model):
    vals = split_coefficient(attr, model)
    if vals is not None and vals[0] == 'cc':
        return True
    else:
        return False

@memoize
def is_ec(attr, model):
    vals = split_coefficient(attr, model)
    if vals is not None and vals[0] == 'ec':
        return True
    else:
        return False

@memoize
def is_prc(attr, model):
    vals = split_coefficient(attr, model)
    if vals is not None and vals[0] == 'prc':
        return True
    else:
        return False

@memoize
def is_rc(attr, model):
    vals = split_coefficient(attr, model)
    if vals is not None and vals[0] == 'rc':
        return True
    else:
        return False
@memoize
def is_mca_coef(attr, model):
    mca_func_list = [is_rc, is_prc, is_ec, is_ec]
    return any([func(attr, model) for func in mca_func_list])

def get_filename_from_caller():
    try:
        caller = sys._getframe(1)
    except ValueError:
        globals = sys.__dict__
        lineno = 1
    else:
        globals = caller.f_globals
        lineno = caller.f_lineno
    if '__name__' in globals:
        module = globals['__name__']
    else:
        module = "<string>"
    filename = globals.get('__file__')
    if filename:
        fnl = filename.lower()
        if fnl.endswith((".pyc", ".pyo")):
            filename = filename[:-1]
    else:
        if module == "__main__":
            try:
                filename = sys.argv[0]
            except AttributeError:
                # embedded interpreters don't have sys.argv, see bug #839151
                filename = '__main__'
        if not filename:
            filename = module
    return filename


def unix_to_windows_path(path_to_convert, drive_letter='C'):
    """
    For a string representing a POSIX compatible path (usually
    starting with either '~' or '/'), returns a string representing an
    equivalent Windows compatible path together with a drive letter.

    Parameters
    ----------
    path_to_convert : string
        A string representing a POSIX path
    drive_letter : string (Default : 'C')
        A single character string representing the desired drive letter

    Returns
    -------
    string
        A string representing a Windows compatible path.
    """
    if path_to_convert.startswith('~'):
        path_to_convert = path_to_convert[1:]
    if path_to_convert.startswith('/'):
        path_to_convert = path_to_convert[1:]
    path_to_convert = '{}{}{}'.format(drive_letter,
                                      ':\\',
                                      path_to_convert).replace('/', '\\')
    return path_to_convert


def column_multiply(arr):
    """
    For any 2d array returns a column vector with the product of the
    columns of each row.

    Parameters
    ----------
    arr : numpy.ndarray

    Returns
    -------
    numpy.ndarray
        A ndarray (column vector) with the products of columns of each
        row of arr as values

    Examples
    --------
    >>> arr = np.arrange(10).reshape(5,2)
    >>> arr
    array([[0, 1],
           [2, 3],
           [4, 5],
           [6, 7],
           [8, 9]])
    >>> column_multiply(arr)
    array([[  0.],
           [  6.],
           [ 20.],
           [ 42.],
           [ 72.]])
    """
    new_arr = ones((arr.shape[0], 1))
    for col in xrange(arr.shape[1]):
        new_arr = new_arr * arr[:, col].reshape(arr.shape[0], 1)
    return new_arr


def stringify(symbol_or_list):
    """
    Returns a list of strings from a list of sympy.Symbol objects or
    a string from a sympy.Symbol.

    Parameters
    ----------
    symbol_or_list : sympy.Symbol or list of sympy.Symbol.

    Returns
    -------
    str or list of str
        A str or list of str representation of the sympy.Symbol or
        list of sympy.Symbol.

    Examples
    --------
    >>> import sympy
    >>> symbol_list = sympy.sympify(['a','c','d'])
    >>> a = stringify(symbol_list[0])
    >>> a
    'a'
    >>> type(a)
    <type 'str>'
    >>> str_list = stringify(symbol_list)
    >>> str_list
    ['a', 'b', 'c']
    >>> type(str_list[0])
    <type 'str>'

    """
    if is_iterable(symbol_or_list):
        return [str(symbol) for symbol in symbol_or_list]
    else:
        return str(symbol_or_list)


def is_iterable(obj):
    """
    Returns True if an object is iterable and False if it is not.

    This function makes the assumtion that any iterable object can be
    cast as an iterator using the build-in function `iter`. This might
    not be the case, but works within the context of PySCeSToolbox.

    Parameters
    ----------
    obj : object
        Any object that might or might not be iterable.

    Returns
    -------
    bool
        A boolean indicating if `ob` is iterable.
    """
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def is_linear(scan_range):
    """
    For any 1-demensional data structure containing numbers return True
    if the numbers follows a linear sequence.

    Within the context of PySCeSToolbox this function will be called on
    either a linear range or a log range. Thus, while not indicative
    of log ranges, this is what a False return value indicates in this
    software.

    Parameters
    ----------
    scan_range : iterable
        Any iterable object containing a range of numbers.

    Returns
    -------
    bool
        A boolean indicating if `scan_range` is a linear sequence of
        numbers.
    """

    if scan_range[1] - scan_range[0] == scan_range[-1] - scan_range[-2]:
        return True
    else:
        return False


def scanner_range_setup(scan_range):
    """
    From a range of numbers, returns its start point, end point, number
    of points and if it is a log range.

    The assumption is made that only log or linear ranges are valid
    inputs, thus lists of random numbers would likely be classified as
    logarithmic.

    Parameters
    ----------
    scan_range : iterable
        Any iterable object containing a range of numbers. Most probably
        numpy.ndarray.

    Returns
    -------
    start : number
        A number indicating the start point of the scan range.
    end: number
        A number indicating the end point of the scan range.
    scan_points: number
        A number indicating the number of scan point in the scan range
    is_log_range: bool
        A boolean indicating whether the scan range has a logarithmic
        scale or not.
    """
    start = scan_range[0]
    end = scan_range[-1]
    scan_points = len(scan_range)
    # based on input not linear == log
    is_log_range = not is_linear(scan_range)
    return start, end, scan_points, is_log_range


def extract_model(obj):
    mod = obj
    try:
        mod = obj.mod
    except:
        pass

    assert isinstance(mod, PysMod), "The object provided does not contain a " \
        "valid Pysces model. Reinstantiate with a" \
        " valid model."

    the_type = str(type(obj))[:-2]
    the_type = the_type[the_type.rindex('.') + 1:]

    return mod, the_type


def find_min(array_like):
    no_zeros = array_like[nonzero(array_like)]
    with errstate(all='ignore'):
        min = nanmin(10 ** log10(no_zeros))
    return min


def find_max(array_like):
    no_zeros = array_like[nonzero(array_like)]
    with errstate(all='ignore'):
        max = nanmax(10 ** log10(no_zeros))
    return max


def do_safe_state(mod, parameter, value, type='ss'):
    setattr(mod, parameter, value)
    mod.SetQuiet()
    mod.doState()
    if mod.__StateOK__:
        if type is 'mca':
            mod.EvalEvar()
            mod.EvalEpar()
            mod.EvalCC()
        ret = True
    else:
        ret = False
    mod.SetLoud()
    return ret


def get_value_eval(expression, subs_dict):
    for k, v in subs_dict.iteritems():
        subs_dict[k] = float64(v)
    ans = eval(expression, {}, subs_dict)
    # sometimes subs_dict is empty
    if not len(subs_dict) == 0:
        # if not, check that if the values of subs_dict are arrays,
        # the answer and the subs_dict arrays are of equal length
        # there is probably a faster solution, but this works fine by
        # falling back to get_value_sympy
        if is_iterable(subs_dict.values()[0]):
            if len(ans) != len(subs_dict.values()[0]):
                raise Exception
    # print 'gve'
    return ans


def get_value_sympy(expression, subs_dict):
    # this is quite inefficient - but probably worth it

    expression = sympify(expression)
    # dont bother with anything if the subs_dict is empty. Just do the
    # "substitution"
    if len(subs_dict) == 0:
        ans = expression.subs(subs_dict)
    else:
        first_value = subs_dict.values()[0]
        if is_iterable(first_value):
            ans = []
            if not isinstance(first_value[0], float64):
                for k, v in subs_dict.iteritems():
                    subs_dict[k] = float64(v)

            number_of_array_elements = len(first_value)
            for i in range(number_of_array_elements):
                temp_subsdict = {k: v[i] for k, v in subs_dict.iteritems()}
                ans_val = expression.subs(temp_subsdict)
                ans.append(ans_val)
            ans = float64(array(ans))
        else:
            if not isinstance(first_value, float64):
                for k, v in subs_dict.iteritems():
                    subs_dict[k] = float64(v)
            ans = expression.subs(subs_dict)
    # print 'gvs'
    return ans


def get_value(expression, subs_dict):
    try:
        # reasons for excepting:
        #    expression is just a single number
        #    expression contains mathematical functions e.g. log, sin, cos
        return get_value_eval(expression, subs_dict)
    except:
        return get_value_sympy(expression, subs_dict)


def split_coefficient(coefficient_name, mod):
    coefficient_2_types = ['cc', 'ec', 'rc']
    coefficient_3_types = ['prc']
    if coefficient_name[:2] in coefficient_2_types:
        coefficient_type = coefficient_name[:2]
    elif coefficient_name[:3] in coefficient_3_types:
        coefficient_type = coefficient_name[:3]
    else:
        return None
    try:
        members = eval(coefficient_type + '_dict(mod)["' + coefficient_name + '"]')
        return_val = tuple([coefficient_type] + list(members))
    except KeyError:
        return_val = None
    return return_val


def is_number(suspected_number):
    """
    Test if an object is a number

    Parameters
    ----------
    suspected_number: object
        This can be any object which might be a number.

    Returns
    -------
    boolean
        True if object is a number, else false

    """

    # We make the assumption that most numbers can be converted to ints.
    # - 21/10/2015 False assumption - strings representing that look like ints
    # can be converted to ints
    # new assumption - only numbers can add another number
    # previous assumption is false - booleans are treated as numbers
    # false many other objects implement addition of numbers
    # original way was fine, we just need to exclude bools and strings.
    # this will not work for invalid types that implement an `__int__` method.
    # but for my cases it should not be a problem.
    number = False
    the_type = type(suspected_number)
    if the_type not in (bool, str, bool_, string_):
        try:
            int(suspected_number)
            # suspected_number + 1
            number = True
        except Exception:
            pass
    return number


def formatter_factory(min_val=None,
                      max_val=None,
                      default_fmt=None,
                      outlier_fmt=None):
    """Returns a custom `html_table` object cell content formatter function.

    Parameters
    ----------
    min_val : int or float, optional (Default : 0.001)
        The minimum value for float display cutoff.
    max_val : int of float, optional (Default : 10000)
        The maximum value for float display cutoff.
    default_fmt : str, options (Default : '%.3f')
        The default format for any number within the range of min_val to
        max_val.
    outlier_fmt : str, optional (Default : '%.3e')
        The format for any number not in the range of min_val to max_val

    Returns
    -------
    formatter : function
        A function which formats input for `html_table` using the values set
        up by this function.

    Examples
    --------
    >>> f = formatter_factory(min_val=1,
                              max_val=10,
                              default_fmt='%.2f',
                              outlier_fmt='%.2e')
    >>> f(1)
    '1.00'
    >>> f(5.235)
    '5.24'
    >>> f(10)
    '10.00'
    >>> f(0.99842)
    '9.98e-01'
    >>> f('abc')
    'abc'

    """
    if not max_val:
        max_val = 10000
    if not min_val:
        min_val = 0.001
    if not default_fmt:
        default_fmt = '%.3f'
    if not outlier_fmt:
        outlier_fmt = '%.3e'

    def formatter(to_format):
        fmt = '%s'
        if is_number(to_format):
            if abs(to_format) == 0:
                fmt = default_fmt
            elif abs(to_format) >= max_val or abs(to_format) < min_val:
                fmt = outlier_fmt
            else:
                fmt = default_fmt
        return fmt % to_format

    return formatter


def html_table(matrix_or_array_like,
               float_fmt=None,
               raw=False,
               first_row_headers=False,
               caption=None,
               style=None,
               formatter=None):
    """Constructs an html compatible table from 2D list, numpy array or sympy
    matrix.

    Parameters
    ----------
    matrix_or_array_like : list of lists or array or matrix
        A compatible object to be converted to an html table
    float_fmt : str, optional (Default : '%.2f')
        The formatter string for numbers. This formatter will be applied to all
        numbers. This optional argument is only used when the argument
        `formatter` is None. Useful for simple tables where different types
        of formatting is not needed.
    raw : boolean, optional (Default : False)
        If True a raw html string will be returned, otherwise an IPython `HTML`
        object will be returned.
    first_row_headers : boolean, optional (Default : False)
        If True elements in the fist row in `matrix_or_array_like` will be
        considered as part of a header and will get the <th></th> tag,
        otherwise there will be no header.
    caption : str, optional (Default : None)
        An optional caption for the table.
    style : str, optional (Default : None)
        An optional html table style
    formatter: function, optional (Default : None)
        An optional `formatter` function. If none float_fmt will be used to
        format numbers.

    Returns
    -------
    str
        A string containing an html table.
    OR
    HTML
        An IPython notebook `HTML` object.


    See Also
    --------
    formatter_factory

    """

    raw_table = matrix_or_array_like
    if not float_fmt:
        float_fmt = '%.2f'

    if not formatter:
        formatter = formatter_factory(default_fmt=float_fmt,
                                      outlier_fmt=float_fmt)

    if 'sympy.matrices' in str(type(matrix_or_array_like)):
        raw_table = array(raw_table)
    if style:
        html_table = ['<table  style="%s">' % style]
    else:
        html_table = ['<table>']
    if caption:
        html_table.append('<caption>%s</caption>' % caption)
    row_count = 0
    for row in raw_table:
        html_table.append('<tr>')
        for col in row:
            to_append = formatter(col)

            if first_row_headers and row_count == 0:
                html_table.append('<th>{0}</th>'.format(to_append))
            else:
                html_table.append('<td>{0}</td>'.format(to_append))

        html_table.append('</tr>')
        row_count += 1
    html_table.append('</table>')
    if raw:
        return ''.join(html_table)
    else:
        return HTML(''.join(html_table))


def silence_print(func):
    """
    A function wrapper that silences the stdout output of a function.

    This function is *very* useful for silencing pysces functions that
    print a lot of unneeded output.

    Parameters
    ----------
    func : function
        A function that talks too much.

    Returns
    -------
    function
        A very quiet function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # stdout = sys.stdout
        try:
            sys.stdout = open(devnull, 'w')
            returns = func(*args, **kwargs)
            fix_printing()
            return returns
        except KeyboardInterrupt, e:
            fix_printing()
            raise e
    return wrapper

def fix_printing():
    sys.stdout = ConfigReader.get_config()['stdout']


@memoize
def cc_list(mod):
    """
    Retuns a list of control coefficients of a model.

    The list contains both flux and species control coefficients and control
    coefficients follow the syntax of 'cc_controlled_controller'.

    Parameters
    ----------
    mod : PysMod
        The Pysces model contains the reactions and species which is used to
        construct the control coefficient list.

    Returns
    -------
    list of str
        The cc_list is sorted alphabetically.

    See Also
    --------
    ec_list, rc_list, prc_list

    """
    ccs = []
    for base_reaction in mod.reactions:
        for top_species in mod.species:
            cc = 'cc%s_%s' % (top_species, base_reaction)
            ccs.append(cc)
        for top_reaction in mod.reactions:
            cc = 'ccJ%s_%s' % (top_reaction, base_reaction)
            ccs.append(cc)
    ccs.sort()
    return ccs

@memoize
def cc_dict(mod):
    ccs = {}
    for base_reaction in mod.reactions:
        for top_species in mod.species:
            cc = 'cc%s_%s' % (top_species, base_reaction)
            ccs[cc] = (top_species, base_reaction)
        for top_reaction in mod.reactions:
            cc = 'ccJ%s_%s' % (top_reaction, base_reaction)
            ccs[cc] = (top_reaction, base_reaction)
    return ccs

@memoize
def ec_list(mod):
    """
    Retuns a list of elasticity coefficients of a model.

    The list contains both species and parameter elasticity coefficients and
    elasticity coefficients follow the syntax of 'ec_reaction_sp-or-param'.

    Parameters
    ----------
    mod : PysMod
        The Pysces model contains the reactions, species and parameters
        which is used to construct the elasticity coefficient list.

    Returns
    -------
    list of str
        The ec_list is sorted alphabetically.

    See Also
    --------
    cc_list, rc_list, prc_list

    """
    ecs = []
    for top_reaction in mod.reactions:
        for base_species in mod.species:
            ec = 'ec%s_%s' % (top_reaction, base_species)
            ecs.append(ec)
        for base_param in mod.parameters:
            ec = 'ec%s_%s' % (top_reaction, base_param)
            ecs.append(ec)
    ecs.sort()
    return ecs

@memoize
def ec_dict(mod):
    ecs = {}
    for top_reaction in mod.reactions:
        for base_species in mod.species:
            ec = 'ec%s_%s' % (top_reaction, base_species)
            ecs[ec] = (top_reaction, base_species)
        for base_param in mod.parameters:
            ec = 'ec%s_%s' % (top_reaction, base_param)
            ecs[ec] = (top_reaction, base_param)
    return ecs

@memoize
def rc_list(mod):
    """
    Retuns a list of response coefficients of a model.

    The list contains both species and flux response coefficients and
    response coefficients follow the syntax of 'rc_responder_parameter'.

    Parameters
    ----------
    mod : PysMod
        The Pysces model contains the reactions, species and parameters
        which is used to construct the response coefficient list.

    Returns
    -------
    list of str
        The rc_list is sorted alphabetically.

    See Also
    --------
    cc_list, ec_list, prc_list

    """
    rcs = []
    for base_param in mod.parameters:
        for top_species in mod.species:
            rc = 'rc%s_%s' % (top_species, base_param)
            rcs.append(rc)
        for top_reaction in mod.reactions:
            rc = 'rcJ%s_%s' % (top_reaction, base_param)
            rcs.append(rc)
    rcs.sort()
    return rcs

@memoize
def rc_dict(mod):
    rcs = {}
    for base_param in mod.parameters:
        for top_species in mod.species:
            rc = 'rc%s_%s' % (top_species, base_param)
            rcs[rc] = (top_species, base_param)
        for top_reaction in mod.reactions:
            rc = 'rcJ%s_%s' % (top_reaction, base_param)
            rcs[rc] = (top_reaction, base_param)
    return rcs

@memoize
def prc_list(mod):
    """
    Retuns a list of partial response coefficients of a model.

    The list contains both species and flux partial response coefficients and
    partial response coefficients follow the syntax of
    'prc_responder_parameter_route'.

    Parameters
    ----------
    mod : PysMod
        The Pysces model contains the reactions, species and parameters
        which is used to construct the partial response coefficient list.

    Returns
    -------
    list of str
        The prc_list is sorted alphabetically.

    See Also
    --------
    cc_list, ec_list, rc_list

    """
    prcs = []
    for base_param in mod.parameters:
        for back_reaction in mod.reactions:
            for top_species in mod.species:
                prc = 'prc%s_%s_%s' % (top_species, base_param, back_reaction)
                prcs.append(prc)
            for top_reaction in mod.reactions:
                prc = 'prcJ%s_%s_%s' % (top_reaction,
                                        base_param,
                                        back_reaction)
                prcs.append(prc)
    prcs.sort()
    return prcs

@memoize
def prc_dict(mod):
    prcs = {}
    for base_param in mod.parameters:
        for back_reaction in mod.reactions:
            for top_species in mod.species:
                prc = 'prc%s_%s_%s' % (top_species, base_param, back_reaction)
                prcs[prc] = (top_species, base_param, back_reaction)
            for top_reaction in mod.reactions:
                prc = 'prcJ%s_%s_%s' % (top_reaction,
                                        base_param,
                                        back_reaction)
                prcs[prc] = (top_reaction,
                             base_param,
                             back_reaction)
    return prcs

@memoize
def flux_list(mod):
    fluxes = []
    for reaction in mod.reactions:
        fluxes.append('J_' + reaction)
    return fluxes

@memoize
def ss_species_list(mod):
    ss_species = []
    for species in mod.species:
        ss_species.append(species + '_ss')
    return ss_species

def group_sort(old_list, num_of_groups):
    # Normally scan columns are sorted in a way that they are sorted together
    # in the order they were scanned. This function sorts the lines so that
    # each item in each group is equally spaced away from each other so that
    # they can be assigned colors (using matplotlib's colormap functionality)
    # that differ from each other. This is better than sorting lines before
    # sending the data tp data2d because otherwise button grouping will also be
    # affected by this sorting scheme.
    group_size = len(old_list) / num_of_groups
    first_group = range(0, len(old_list), num_of_groups)
    groups = first_group
    for i in xrange(1, group_size - 1):
        groups = groups + [j + i for j in first_group]
    new_list = [old_list[pos] for pos in groups]

    return new_list

def print_f(message, status):
    """
    Prints a message if status is `True`
    Parameters
    ----------
    message : object
        Any object with a `__str__` method.
    status : bool
    """
    if status:
        print message


class PseudoDotDict:
    """
    A class that acts like a dictionary with dot accessible elements.

    This class is not subsclassed from ``dict`` like DotDict, but rather wraps
    dictionary functionality.

    This object has trouble being pickled :'(

    See Also
    --------
    dict
    DotDict
    """
    _reserved = ['__class__', '__format__', '__init__', '__reduce_ex__',
                 '__sizeof__', '__delattr__', '__getattribute__', '__new__',
                 '__repr__', '__str__', '__doc__', '__hash__', '__reduce__',
                 '__setattr__', '__subclasshook__', 'keys', 'items', 'values']

    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)
        self._setall_init
        self.keys = self._dict.keys
        self.values = self._dict.values
        self.items = self._dict.items

    def _setall_init(self):
        """
        Internal function that populates the self namespace on
        initialisation. Throws exception if any of the keys are
        reserved.
        """
        for k, v in self._dict.iteritems():
            if k in PseudoDotDict._reserved:
                raise Exception('%s is a reserved key' % k)
            else:
                setattr(self, k, v)

    def __setitem__(self, x, y):
        self._dict[x] = y
        if x in PseudoDotDict._reserved:
            raise Exception('%s is a reserved key' % x)
        else:
            setattr(self, x, y)

    def __getitem__(self, x):
        return self._dict[x]

    def __repr__(self):
        return self._dict.__repr__()

    def update(self, dic):
        for k, v in dic.iteritems():
            self.__setitem__(k, v)


class DotDict(dict):
    """A class that inherits from ``dict``.

    The DotDict class has the same functionality as ``dict`` but with the added
    feature that dictionary elements may be accessed via dot notation.

    See Also
    --------
    dict
    PseudoDotDict
    """

    _reserved1 = ['clear', 'fromkeys', 'has_key', 'iteritems', 'itervalues',
                  'pop', 'setdefault', 'values', 'viewkeys', 'copy', 'get',
                  'items', 'iterkeys', 'keys', 'popitem', 'update',
                  'viewitems', 'viewvalues']

    _reserved2 = ['__class__', '__delitem__', '__ge__', '__hash__', '__len__',
                  '__reduce__', '__setitem__', '__cmp__', '__doc__',
                  '__getattribute__', '__init__', '__lt__', '__reduce_ex__',
                  '__sizeof__', '__contains__', '__eq__', '__getitem__',
                  '__iter__', '__ne__', '__repr__', '__str__', '__delattr__',
                  '__format__', '__gt__', '__le__', '__new__',
                  '__setattr__', '__subclasshook__']

    _reserved = _reserved1 + _reserved2

    def __init__(self, *args, **kwargs):
        super(DotDict, self).__init__(*args, **kwargs)
        self._setall_init()
        # self._reassign_reserved_to_internals()

    def __setitem__(self, x, y):
        dict.__setitem__(self, x, y)
        if x in DotDict._reserved:
            raise Exception
        else:
            setattr(self, x, y)

    def _setall_init(self):
        """
        Internal method that populates the self namespace on
        initialisation. Throws exception if any of the keys are
        reserved.
        """
        for k, v in self.iteritems():
            if k in DotDict._reserved:
                raise Exception('%s is a reserved key' % k)
            else:
                setattr(self, k, v)

    def update(self, dic):
        for k, v in dic.iteritems():
            self.__setitem__(k, v)

    def _make_repr(self, key, value, formatter=None):
        """
        Internal method makes a _repr_html_ method and attaches it to self so
        that values contained in self can be displayed as an html table in the
        IPython notebook.

        Parameters
        ----------
        key : str
            A string that will be evaluated indicating how to represent the
            dictionary keys. If 'k' is passed, the key will be displayed as is.
        value : str
            A string that will be evaluated indicating how to represent
            dictionary values. If 'v' is passed, the value will be displayed as
            is.
        formatter : function, optional (Default : None)
            A formatter function that formats numbers. If none, the default
            function produced by `formatter_factory` will be used.

        See Also
        --------
        formatter_factory


        """
        if not formatter:
            formatter = formatter_factory()

        def representation(the_self=self):
            keys = self.keys()
            keys.sort()
            values = [self[the_key] for the_key in keys]
            items = zip(keys, values)
            lst = []
            for k, v in items:
                col1 = eval(key)
                col2 = eval(value)
                lst.append((col1, col2))

            tables = []
            cur_list = []
            for i, each in enumerate(lst):
                if (i + 1) % 10 == 0:
                    cur_list.append(each)
                    tables.append(
                        html_table(cur_list,
                                   style='display: inline-table',
                                   raw=True,
                                   formatter=formatter))
                    cur_list = []
                elif (i + 1) == len(lst):
                    # print 'Final'
                    cur_list.append(each)
                    tables.append(
                        html_table(cur_list,
                                   style='display: inline-table',
                                   raw=True,
                                   formatter=formatter))
                    cur_list = []
                else:
                    cur_list.append(each)

            div_string = '<div>'
            for each in tables:
                div_string += each
                div_string += '\t\t'
            div_string += '</div>'
            return div_string

        self._repr_html_ = representation


# no use yet for this class but seemed like a nice/quick/simple way to address
# directory trees with no overlapping subdirectory names.
# will work for ['/a/b/c/d',/a/b/c/e'] but not for ['/a/b/c/d',/a/b/d']
class SimpleDirectoryStructure(object):
    def __init__(self, fpaths=None):
        self._path_dict = {}
        if type(fpaths) is list:
            self.add_paths(fpaths)
        if type(fpaths) is str:
            self.add_path(fpaths)

    def add_path(self, fpath):
        top_path = fpath
        temp_split = path.split(top_path)
        self._path_dict[temp_split[1]] = top_path
        while (temp_split[1] != ''):
            top_path = temp_split[0]
            temp_split = path.split(top_path)
            self._path_dict[temp_split[1]] = top_path

    def add_paths(self, list_of_fpaths):
        for fpath in list_of_fpaths:
            self.add_path(fpath)

    def __getitem__(self, key):
        return self._path_dict[key]
