import sys
import os
from numpy import array as np_array
from IPython.display import HTML

__all__ = ['cc_list',
           'ec_list',
           'rc_list',
           'prc_list',
           'silence_print',
           'DotDict',
           'PseudoDotDict',
           'is_number',
           'formatter_factory',
           'html_table']


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
    number = False
    try:
        int(suspected_number)
        number = True
    except ValueError:
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
    'formatter_factory' : Creates formatter function

    """

    raw_table = matrix_or_array_like
    if not float_fmt:
        float_fmt = '%.2f'

    if not formatter:
        formatter = formatter_factory(default_fmt=float_fmt,
                                      outlier_fmt=float_fmt)

    if 'sympy.matrices' in str(type(matrix_or_array_like)):
        raw_table = np_array(raw_table)
    if style:
        html_table = ['<table  style="%s">' % style]
    else:
        html_table = ['<table>']
    if caption:
        html_table.append('<caption>%s</caption>' % caption)
    row_count = 0
    for row in raw_table:
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

    def wrapper(*args, **kwargs):
        stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        returns = func(*args, **kwargs)
        sys.stdout = stdout
        return returns
    return wrapper


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
