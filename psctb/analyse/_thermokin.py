__author__ = 'carl'
from re import match, findall
from os import path

from sympy import Symbol, sympify, diff
from numpy import float64, log

from ..utils.misc import DotDict, formatter_factory
from ..latextools import LatexExpr
from ..modeltools import make_path


def read_files(path):
    with open(path) as f:
        lines = f.readlines()
    return lines


def strip_other(raw_lines):
    return [line[:-1] for line in raw_lines if line.startswith('!T')]


def correct_fmt(lines):
    errors_in = []
    for line in lines:
        if not match('!T{\w*}{\w*} .*', line):
            errors_in.append(line)
    if len(errors_in) == 0:
        return True
    else:
        return errors_in


def construct_dict(lines):
    outer_dict = {}
    for line in lines:
        in_brackets = findall('(?<={)\w+', line)
        r_name = in_brackets[0]
        t_name = in_brackets[1]
        expr = findall('(?<=\w} ).*', line)[0]

        inner_dict = {t_name: expr}
        if outer_dict.has_key(r_name):
            outer_dict[r_name].update(inner_dict)
        else:
            outer_dict[r_name] = inner_dict
    return outer_dict


def get_value_eval(expression, subs_dict):
    for k, v in subs_dict.iteritems():
        subs_dict[k] = float64(v)
    # print expression
    ans = eval(expression, {}, subs_dict)
    return ans


def get_subs_dict(expression, mod):
    subs_dict = {}
    symbols = expression.atoms(Symbol)
    for symbol in symbols:
        attr = str(symbol)
        subs_dict[attr] = getattr(mod, attr)
    return subs_dict


def get_reqn_path(mod):
    fname = mod.ModelFile
    dot_loc = fname.find('.')
    fname_min_ext = fname[:dot_loc]
    fname_ext = fname_min_ext + '.reqn'
    return path.join(mod.ModelDir, fname_ext)


def get_term_dict_from_path(path):
    raw_lines = read_files(path)
    clean_lines = strip_other(raw_lines)
    if correct_fmt(clean_lines) == True:
        term_dict = construct_dict(clean_lines)
        return term_dict
    else:
        print 'Errors in following lines'
        for each in correct_fmt(clean_lines): print each
        return None


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


class ThermoKin(object):
    def __init__(self, mod, path_to_reqn_file=None, ltxe=None):
        super(ThermoKin, self).__init__()
        self.mod = mod
        self.mod.doMca()

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
            reqn_obj = rate_eqn(self.mod,
                                reaction,
                                terms_dict,
                                self._ltxe)
            setattr(self, reaction, reqn_obj)
            self.reactions[reaction] = reqn_obj



class rate_eqn(object):
    def __init__(self, mod, name, term_dict, ltxe):
        super(rate_eqn, self).__init__()
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
            term = rate_term(parent=self,
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
            self.mca_data[ec_name] = term(self, self.mod, ec_name, ec,
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


class term(object):
    def __init__(self, parent, mod, name, expression, ltxe):
        super(term, self).__init__()
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
        self._value = get_value_eval(self._str_expression, subs_dict)


class rate_term(term):
    def __init__(self, parent, mod, name, rname, expression, ltxe):
        super(rate_term, self).__init__(parent, mod, name, expression, ltxe)
        self.expression = sympify(expression)
        self._rname = rname
        self.mca_data = DotDict()
        self.mca_data._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                  formatter_factory())
        self._populate_mca_data()
        self._percentage = None

    @property
    def percentage(self):
        per = (log(self.value)/log(self._parent.value)) * 100
        return per

    def _populate_mca_data(self):
        var_pars = self.mod.species + self.mod.parameters
        for each in var_pars:
            each = sympify(each)
            ec_name = 'pec%s_%s_%s' % (self._parent._rname, each, self._rname)
            ec = diff(self.expression, each) * (each / self.expression)
            self.mca_data[ec_name] = term(self._parent, self.mod, ec_name, ec,
                                          self._ltxe)


