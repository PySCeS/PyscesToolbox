__author__ = 'carl'
from re import match, findall
from os import path

from sympy import Symbol, sympify, diff
from numpy import float64, log, array, float, NaN, nanmin, nanmax
from pysces import ModelMap

from ..utils.misc import DotDict, formatter_factory, find_min, find_max
from ..latextools import LatexExpr
from ..modeltools import make_path
from ..utils.plotting import Data2D
from ..utils.misc import do_safe_state, get_value, silence_print


class FormatException(Exception):
    pass


def read_files(path_to_file):
    with open(path_to_file) as f:
        lines = f.readlines()
    return lines


def strip_other(raw_lines):
    return [line[:-1] for line in raw_lines if line.startswith('!T')]


def correct_fmt(lines):
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
    subs_dict = {}
    symbols = expression.atoms(Symbol)
    for symbol in symbols:
        attr = str(symbol)
        subs_dict[attr] = getattr(mod, attr)
    return subs_dict


def get_reqn_path(mod):
    """Gets the default path and filename of`.reqn` files belonging to a model
    
    The `.reqn` files which contain rate equations spilt into different
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
    """Produces and returns a dictionary of filesnames from 
    
    
    
    Parameters
    ----------
    
    
    Returns
    -------
    """
    
    raw_lines = read_files(path_to_read)
    clean_lines = strip_other(raw_lines)
    if correct_fmt(clean_lines):
        term_dict = construct_dict(clean_lines)
        return term_dict


def mult(lst):
    ans = 1
    for each in lst:
        ans *= each
    return ans


def get_term_types_from_raw_data(raw_data_dict):
    term_types = set()
    for v in raw_data_dict.itervalues():
        for k in v.iterkeys():
            term_types.add(k)
    return term_types


def get_repr_latex(obj):
    if obj.value == 0:
        fmt = '$%s = %s = %.3f$'
    elif abs(obj.value) < 0.001 or abs(obj.value) > 10000:
        fmt = '$%s = %s = %.3e$'
    else:
        fmt = '$%s = %s = %.3f$'
    return fmt % (obj.latex_name,
                  obj.latex_expression,
                  obj.value)

@silence_print
def silent_state(mod):
    mod.doMca()
    mod.doState()


class ThermoKin(object):
    def __init__(self, mod, path_to_reqn_file=None, ltxe=None):
        super(ThermoKin, self).__init__()
        self.mod = mod

        silent_state(mod)

        self._analysis_method = 'thermokin'
        self._working_dir = make_path(self.mod, self._analysis_method)

        if ltxe:
            self._ltxe = ltxe
        else:
            self._ltxe = LatexExpr(mod)

        if path_to_reqn_file:
            self._path_to = path_to_reqn_file
        else:
            self._path_to = get_reqn_path(self.mod)

        self._raw_data = get_term_dict_from_path(self._path_to)
        self._ltxe.add_term_types(get_term_types_from_raw_data(self._raw_data))

        self._populate_object()
        self._populate_mca_data()

    def _verify_results(self):
        print '%s\t\t%s\t\t%s' % ('Name', 'Tk val', 'Mod val')
        for reaction in self.reactions:
            mod_val = getattr(self.mod, reaction.name)
            own_val = reaction.value
            is_eq = round(mod_val, 10) == round(own_val, 10)
            print '%s\t\t%.10f\t%.10f\t%s' % (
                reaction.name, own_val, mod_val, is_eq)
        for reaction in self.reactions:
            for var_par in self.mod.parameters + self.mod.species:
                ec_name = 'ec%s_%s' % (reaction.rname, var_par)
                mod_val = getattr(self.mod, ec_name)
                own_val = reaction.mca_data[ec_name].value
                is_eq = round(mod_val, 10) == round(own_val, 10)
                print '%s\t\t%.10f\t%.10f\t%s' % (
                    ec_name, own_val, mod_val, is_eq)

    def _populate_object(self):
        reacts = []
        self.reactions = DotDict()
        self.reactions._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                  formatter_factory())
        for reaction, terms_dict in self._raw_data.iteritems():
            reqn_obj = RateEqn(self.mod,
                               reaction,
                               terms_dict,
                               self._ltxe)
            setattr(self, reaction, reqn_obj)
            self.reactions[reaction] = reqn_obj

    def _populate_mca_data(self):
        self.mca_data = DotDict()
        self.mca_data._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                 formatter_factory())

        for rate_eqn in self.reactions.itervalues():
            self.mca_data.update(rate_eqn.mca_data)


class RateEqn(object):
    def __init__(self, mod, name, term_dict, ltxe):
        super(RateEqn, self).__init__()
        self.mod = mod
        self.terms = DotDict()
        self.terms._make_repr('"$" + v.latex_name + "$"', 'v.value',
                              formatter_factory())
        self.expression = 1
        self.name = 'J_' + name
        self._rname = name
        self._ltxe = ltxe

        for val in term_dict.itervalues():
            self.expression = self.expression * (sympify(val))
        for term_name, expression in term_dict.iteritems():
            term = RateTerm(parent=self,
                            mod=self.mod,
                            name='J_%s_%s' % (self._rname, term_name),
                            rname=term_name,
                            expression=expression,
                            ltxe=self._ltxe)
            setattr(self, term_name, term)
            self.terms[term_name] = term

        self._value = None
        self._str_expression = str(self.expression)
        self._latex_expression = None
        self._latex_name = None

        self.mca_data = DotDict()
        self.mca_data._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                 formatter_factory())

        self._populate_mca_data()

    def _populate_mca_data(self):
        var_pars = self.mod.parameters + self.mod.species
        for each in var_pars:
            each = sympify(each)
            ec = diff(self.expression, each) * (each / self.expression)
            ec_name = 'ec%s_%s' % (self._rname, each)
            self.mca_data[ec_name] = Term(self, self.mod, ec_name, ec,
                                          self._ltxe)
        for each in self.terms.itervalues():
            self.mca_data.update(each.mca_data)

    def _repr_latex_(self):
        return get_repr_latex(self)

    @property
    def value(self):
        self._calc_value()
        return self._value

    @property
    def latex_name(self):
        if not self._latex_name:
            self._latex_name = self._ltxe.expression_to_latex(self.name)
        return self._latex_name

    @property
    def latex_expression(self):
        if not self._latex_expression:
            self._latex_expression = self._ltxe.expression_to_latex(
                self.expression)
        return self._latex_expression

    def _calc_value(self):
        subs_dict = get_subs_dict(self.expression, self.mod)
        for each in self.terms.itervalues():
            each._calc_value(subs_dict)
        self._value = mult([each._value for each in self.terms.itervalues()])

    def _perscan(self, parameter, scan_range):
        scan_res = [list() for _ in range(len(self.terms.values()) + 1)]
        scan_res[0] = scan_range

        for parvalue in scan_range:
            state_valid = do_safe_state(self.mod, parameter, parvalue)
            for i, term in enumerate(self.terms.values()):
                if state_valid:
                    scan_res[i + 1].append(term.percentage)
                else:
                    scan_res[i + 1].append(NaN)

        return scan_res

    def _valscan(self, parameter, scan_range):
        scan_res = [list() for _ in range(len(self.terms.values()) + 2)]
        scan_res[0] = scan_range

        for parvalue in scan_range:
            state_valid = do_safe_state(self.mod, parameter, parvalue)
            for i, term in enumerate(self.terms.values()):
                if state_valid:
                    scan_res[i + 1].append(term.value)
                else:
                    scan_res[i + 1].append(NaN)
            if state_valid:
                scan_res[i + 2].append(self.value)
            else:
                scan_res[i + 2].append(NaN)
        return scan_res

    def _evalscan(self, parameter, scan_range):
        mca_objects = self._get_mca_objects(parameter)

        scan_res = [list() for _ in range(len(mca_objects) + 1)]
        scan_res[0] = scan_range

        for parvalue in scan_range:
            state_valid = do_safe_state(self.mod, parameter, parvalue,
                                        type='mca')
            for i, term in enumerate(mca_objects):
                if state_valid:
                    scan_res[i + 1].append(term.value)
                else:
                    scan_res[i + 1].append(NaN)
        return scan_res

    def par_scan(self, parameter, scan_range, scan_type='value',
                 init_return=True):

        assert scan_type in ['percentage', 'value', 'elasticity']
        init = getattr(self.mod, parameter)

        additional_cat_classes = {
            'All Fluxes/Reactions/Species': ['Term Rates']}
        additional_cats = {
            'Term Rates': [term.name for term in self.terms.values()]}

        if scan_type is 'percentage':
            column_names = [parameter] + [term.name for term in
                                          self.terms.values()]
            y_label = 'Term Percentage Contribution'
            scan_res = self._perscan(parameter, scan_range)
            yscale = 'linear'
            data_array = array(scan_res, dtype=float).transpose()
            ylim = [nanmin(data_array), find_max(data_array) * 1.1]
        elif scan_type is 'value':
            column_names = [parameter] + [term.name for term in
                                          self.terms.values()] + [self.name]
            y_label = 'Reation/Term rate'
            scan_res = self._valscan(parameter, scan_range)
            yscale = 'log'
            data_array = array(scan_res, dtype=float).transpose()
            ylim = [find_min(data_array[:, 1:]),
                    find_max(data_array[:, 1:]) * 2]
        elif scan_type is 'elasticity':
            mca_objects = self._get_mca_objects(parameter)
            column_names = [parameter] + [obj.name for obj in mca_objects]

            y_label = '$\\varepsilon^{%s}_{%s}$' % (self._rname, parameter)
            scan_res = self._evalscan(parameter, scan_range)
            yscale = 'linear'
            data_array = array(scan_res, dtype=float).transpose()
            ylim = [nanmin(data_array[:, 1:]), nanmax(data_array[:, 1:]) * 1.1]
            additional_cat_classes = {
                'All Coefficients': ['Term Elasticities']}
            additional_cats = {
                'Term Elasticities': [elas.name for elas in mca_objects][:-1]}

        if init_return:
            self.mod.SetQuiet()
            setattr(self.mod, parameter, init)
            self.mod.doMca()
            self.mod.SetLoud()

        mm = ModelMap(self.mod)
        species = mm.hasSpecies()
        if parameter in species:
            x_label = '[%s]' % parameter.replace('_', ' ')
        else:
            x_label = parameter

        ax_properties = {'ylabel': y_label,
                         'xlabel': x_label,
                         'xscale': 'log',
                         'yscale': yscale,
                         'xlim': [find_min(scan_range), find_max(scan_range)],
                         'ylim': ylim}

        data = Data2D(mod=self.mod,
                      column_names=column_names,
                      data_array=data_array,
                      ltxe=self._ltxe,
                      analysis_method='thermokin',
                      ax_properties=ax_properties,
                      additional_cat_classes=additional_cat_classes,
                      additional_cats=additional_cats)
        return data

    def _get_mca_objects(self, parameter):
        terms = self.terms.keys()
        reaction_name = self._rname
        mca_objects = []
        for term in terms:
            mca_objects.append(self.mca_data[
                'pec%s_%s_%s' % (reaction_name, parameter, term)])
        mca_objects.append(
            self.mca_data['ec%s_%s' % (reaction_name, parameter)])
        return mca_objects


class Term(object):
    def __init__(self, parent, mod, name, expression, ltxe):
        super(Term, self).__init__()
        self.name = name
        self.expression = sympify(expression).factor()
        self._str_expression = str(self.expression)
        self._parent = parent
        self.mod = mod
        self._value = None
        self._latex_name = None
        self._latex_expression = None
        self._ltxe = ltxe

    def _repr_latex_(self):
        return get_repr_latex(self)

    @property
    def value(self):
        self._calc_value()
        return self._value

    @property
    def latex_name(self):
        if not self._latex_name:
            self._latex_name = self._ltxe.expression_to_latex(self.name)
        return self._latex_name

    @property
    def latex_expression(self):
        if not self._latex_expression:
            self._latex_expression = self._ltxe.expression_to_latex(
                self.expression)
        return self._latex_expression

    def _calc_value(self, subs_dict=None):
        if not subs_dict:
            subs_dict = get_subs_dict(self.expression, self.mod)
        self._value = get_value(self._str_expression, subs_dict)


class RateTerm(Term):
    def __init__(self, parent, mod, name, rname, expression, ltxe):
        super(RateTerm, self).__init__(parent, mod, name, expression, ltxe)
        self.expression = sympify(expression)
        self._rname = rname
        self.mca_data = DotDict()
        self.mca_data._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                 formatter_factory())
        self._populate_mca_data()
        self._percentage = None

    @property
    def percentage(self):
        per = (log(self.value) / log(self._parent.value)) * 100
        return per

    def _populate_mca_data(self):
        var_pars = self.mod.species + self.mod.parameters
        for each in var_pars:
            each = sympify(each)
            ec_name = 'pec%s_%s_%s' % (self._parent._rname, each, self._rname)
            ec = diff(self.expression, each) * (each / self.expression)
            self.mca_data[ec_name] = Term(self._parent, self.mod, ec_name, ec,
                                          self._ltxe)


