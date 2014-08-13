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
    # We make the assumption that most numbers
    # can be converted to ints
    number = False
    try:
        int(suspected_number)
        number = True
    except:
        pass
    return number


def formatter_factory(max_val=None,
                      min_val=None,
                      default_fmt=None,
                      outlier_fmt=None):
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
            if abs(int(to_format)) == 0:
                fmt = default_fmt
            elif abs(to_format) >= max_val or abs(to_format) < min_val:
                fmt = outlier_fmt
            else:
                fmt = default_fmt
        return fmt % to_format
    return formatter


def html_table(matrix_or_array_like,
               float_fmt='%.2f',
               raw=False,
               first_row_headers=False,
               caption=None,
               style=None,
               formatter=None):

    raw_table = matrix_or_array_like

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
        A function that talks too much
    Returns
    -------
    values: function
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
        contruct the control coefficient list.

    Returns
    -------
    values : list
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
        which is used to contruct the elasticity coefficient list.

    Returns
    -------
    values : list
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
        which is used to contruct the response coefficient list.

    Returns
    -------
    values : list
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
        which is used to contruct the partial response coefficient list.

    Returns
    -------
    values : list
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
    A class that acts like a dictionary with dot accessable elements.

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
        Internal function that populates the self namespace on
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
                i += 1
                if i % 5 != 0:
                    cur_list.append(each)
                elif i == len(lst):
                    cur_list.append(each)
                    tables.append(
                        html_table(cur_list,
                                   style='display: inline-table',
                                   raw=True,
                                   formatter=formatter))
                    cur_list = []
                else:
                    cur_list.append(each)
                    tables.append(
                        html_table(cur_list,
                                   style='display: inline-table',
                                   raw=True,
                                   formatter=formatter))
                    cur_list = []
            div_string = '<div>'
            for each in tables:
                div_string += each
                div_string += '\t\t'
            div_string += '</div>'
            return div_string

        self._repr_html_ = representation
