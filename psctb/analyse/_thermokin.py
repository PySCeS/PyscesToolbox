__author__ = 'carl'

from numpy import log10, array, float, NaN, nanmin, nanmax, savetxt
from os import path

from pysces import ModelMap
from sympy import sympify, diff, Symbol

from ._thermokin_file_tools import get_subs_dict, get_reqn_path, \
    get_all_terms, get_term_types_from_raw_data, create_reqn_data, \
    write_reqn_file, create_gamma_keq_reqn_data
from ..latextools import LatexExpr
from ..modeltools import make_path, get_file_path
from ..utils.misc import DotDict, formatter_factory, find_min, find_max
from ..utils.misc import do_safe_state, get_value, silence_print
from ..utils.plotting import Data2D

# __all__ = ['ThermoKin','AdditionalRateTerm']


def mult(lst):
    """
    Multiplies values of a list with each other and returns the result.

    Parameters
    ----------
    lst : list of numbers

    Returns
    -------
    number
        Same type as numbers in ``lst``.

    """
    ans = 1
    for each in lst:
        ans *= each
    return ans


def get_repr_latex(obj):
    """
    Creates the string that will be returned by the ``__repr_latex__``
    method of any of objects of ``Thermokin``. The value of the
    ``value`` field is used to dermine the float format.

    Parameters
    ----------
    obj : RateTerm, Term or RateEqn

    Returns
    -------
    str

    """
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


def print_f(message, status):
    if status:
        print message


class ThermoKin(object):
    def __init__(self, mod, path_to_reqn_file=None, overwrite=False,
                 warnings=True, ltxe=None):
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

        self._do_auto_actions(overwrite, warnings)
        self._raw_data, self._add_raw_data = get_all_terms(self._path_to)
        self._do_gamma_keq(overwrite, warnings)

        term_types = get_term_types_from_raw_data(self._raw_data).union(
                get_term_types_from_raw_data(self._add_raw_data))
        self._ltxe.add_term_types(term_types)

        self._populate_object()
        self._populate_ec_results()

    def _do_gamma_keq(self, overwrite, warnings):
        if overwrite:
            return None
        gamma_keq_todo = []
        add_raw_data = self._add_raw_data
        for reaction in self._raw_data.iterkeys():
            if not add_raw_data.get(reaction) or not add_raw_data.get(reaction).get('gamma_keq'):
                gamma_keq_todo.append(reaction)
        if len(gamma_keq_todo) != 0:
            reaction_printout = ', '.join(gamma_keq_todo[:-1]) + ' or ' + \
                                gamma_keq_todo[-1]
            print_f('%s does not contain Gamma/Keq terms for %s:' % (
                    self._path_to, reaction_printout),warnings)
            gamma_keq_data, messages = create_gamma_keq_reqn_data(self.mod)
            for required in gamma_keq_todo:
                print_f('{:10.10}: {}'.format(required, messages[required]),
                        warnings)
                if required not in add_raw_data:
                    add_raw_data[required] = {}
                add_raw_data[required]['gamma_keq'] = gamma_keq_data[required]

    def _do_auto_actions(self, overwrite, warnings):
        condition_1 = path.exists(self._path_to) and overwrite
        condition_2 = not path.exists(self._path_to)
        if condition_1:
            print_f(
                'The file %s will be overwritten with automatically generated file.' % self._path_to,
                warnings)
        elif condition_2:
            print_f('A new file will be created at "%s".' % self._path_to,
                    warnings)
        if condition_1 or condition_2:
            ma_terms, vc_binding_terms, gamma_keq_terms, messages = create_reqn_data(self.mod)
            for k, v in messages.iteritems():
                print_f('{:10.10}: {}'.format(k, v), warnings)
            write_reqn_file(self._path_to, self.mod.ModelFile, ma_terms,
                            vc_binding_terms, gamma_keq_terms, messages)

    def _populate_object(self):
        self.reaction_results = DotDict()
        self.reaction_results._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                         formatter_factory())
        for reaction, terms_dict in self._raw_data.iteritems():
            additional_terms = self._add_raw_data.get(reaction)
            reqn_obj = RateEqn(self.mod,
                               reaction,
                               terms_dict,
                               self._ltxe,
                               additional_terms)
            setattr(self, 'J_' + reaction, reqn_obj)
            self.reaction_results['J_' + reaction] = reqn_obj
            for term in reqn_obj.terms.itervalues():
                self.reaction_results[term.name] = term

    def _populate_ec_results(self):
        self.ec_results = DotDict()
        self.ec_results._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                   formatter_factory())

        for rate_eqn in self.reaction_results.itervalues():
            self.ec_results.update(rate_eqn.ec_results)

    def save_results(self, file_name=None, separator=','):
        file_name = get_file_path(working_dir=self._working_dir,
                                  internal_filename='tk_summary',
                                  fmt='csv',
                                  file_name=file_name, )

        values = []
        max_len = 0
        for reaction_name in sorted(self.reaction_results.keys()):
            cols = (reaction_name,
                    self.reaction_results[reaction_name].value,
                    self.reaction_results[reaction_name].latex_name,
                    self.reaction_results[reaction_name].latex_expression)
            values.append(cols)
            if len(cols[3]) > max_len:
                max_len = len(cols[3])

        for elasticity_name in sorted(
                [ec for ec in self.ec_results.keys() if ec.startswith('ec')]):
            if self.ec_results[elasticity_name].expression != 0:
                related_ecs = sorted([ec for ec in self.ec_results.keys() if
                                      elasticity_name in ec])
                for related_ec_name in related_ecs:
                    cols = (related_ec_name,
                            self.ec_results[related_ec_name].value,
                            self.ec_results[related_ec_name].latex_name,
                            self.ec_results[related_ec_name].latex_expression)
                    values.append(cols)
                    if len(cols[3]) > max_len:
                        max_len = len(cols[3])

        str_fmt = 'S%s' % max_len
        head = ['name', 'value', 'latex_name', 'latex_expression']
        X = array(values,
                  dtype=[(head[0], str_fmt),
                         (head[1], 'float'),
                         (head[2], str_fmt),
                         (head[3], str_fmt)])

        try:
            savetxt(fname=file_name,
                    X=X,
                    header=','.join(head),
                    delimiter=separator,
                    fmt=['%s', '%.9f', '%s', '%s'], )

        except IOError as e:
            print e.strerror


class RateEqn(object):
    def __init__(self, mod, name, term_dict, ltxe, additional_terms=None):
        super(RateEqn, self).__init__()
        self.mod = mod
        self.terms = DotDict()
        self.terms._make_repr('"$" + v.latex_name + "$"', 'v.value',
                              formatter_factory())
        self._unfac_expression = 1
        self.name = 'J_' + name
        self._rname = name
        self._ltxe = ltxe

        for val in term_dict.itervalues():
            self._unfac_expression = self._unfac_expression * (sympify(val))
        for term_name, expression in term_dict.iteritems():
            term = RateTerm(parent=self,
                            mod=self.mod,
                            name='J_%s_%s' % (self._rname, term_name),
                            rname=term_name,
                            expression=expression,
                            ltxe=self._ltxe)
            setattr(self, term_name, term)
            self.terms[term_name] = term

        if additional_terms:
            for term_name, expression in additional_terms.iteritems():
                term = AdditionalRateTerm(parent=self,
                                          mod=self.mod,
                                          name='J_%s_%s' % (
                                              self._rname, term_name),
                                          rname=term_name,
                                          expression=expression,
                                          ltxe=self._ltxe)
                setattr(self, term_name, term)
                self.terms[term_name] = term

        self._value = None
        self._str_expression_ = None
        self._expression = None
        self._latex_expression = None
        self._latex_name = None

        self.ec_results = DotDict()
        self.ec_results._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                   formatter_factory())

        self._populate_ec_results()

    def _populate_ec_results(self):
        expression_symbols = self._unfac_expression.atoms(Symbol)
        for each in expression_symbols:
            each = sympify(each)
            ec = diff(self.expression, each) * (each / self.expression)
            ec_name = 'ec%s_%s' % (self._rname, each)
            self.ec_results[ec_name] = Term(self, self.mod, ec_name, ec,
                                            self._ltxe)
        for each in self.terms.itervalues():
            self.ec_results.update(each.ec_results)

    def _repr_latex_(self):
        return get_repr_latex(self)

    @property
    def _str_expression(self):
        if not self._str_expression_:
            self._str_expression_ = str(self.expression)
        return self._str_expression_

    @property
    def expression(self):
        if not self._expression:
            self._expression = self._unfac_expression.factor()
        return self._expression

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
                    self.expression,
                    mul_symbol='dot')
        return self._latex_expression

    def _calc_value(self):
        subs_dict = get_subs_dict(self.expression, self.mod)
        for each in self.terms.itervalues():
            if type(each) is not AdditionalRateTerm:
                each._calc_value(subs_dict)
        self._value = mult([each._value for each in self.terms.itervalues() if
                            type(each) is not AdditionalRateTerm])

    def _perscan(self, parameter, scan_range):
        non_additionals = [value for value in self.terms.values() if
                           type(value) is not AdditionalRateTerm]
        scan_res = [list() for _ in range(len(non_additionals) + 1)]
        scan_res[0] = scan_range

        for parvalue in scan_range:
            state_valid = do_safe_state(self.mod, parameter, parvalue)
            for i, term in enumerate(non_additionals):
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
        mca_objects = [ec_term for ec_term in self.ec_results.values() if
                       ec_term.expression != 0 and not ec_term.name.endswith('gamma_keq')]

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

    def do_par_scan(self, parameter, scan_range, scan_type='value',
                    init_return=True):

        assert scan_type in ['percentage', 'value', 'elasticity']
        init = getattr(self.mod, parameter)

        additional_cat_classes = {
            'All Fluxes/Reactions/Species': ['Term Rates']}
        additional_cats = {
            'Term Rates': [term.name for term in self.terms.values()]}

        if scan_type is 'percentage':
            column_names = [parameter] + [term.name for term in
                                          self.terms.values()
                                          if
                                          type(term) is not AdditionalRateTerm]
            y_label = 'Term Percentage Contribution'
            scan_res = self._perscan(parameter, scan_range)
            yscale = 'linear'
            data_array = array(scan_res, dtype=float).transpose()
            ylim = [nanmin(data_array[:,1:]), find_max(data_array[:,1:]) * 1.1]
        elif scan_type is 'value':
            column_names = [parameter] + [term.name for term in
                                          self.terms.values()] + [self.name]
            y_label = 'Reaction/Term rate'
            scan_res = self._valscan(parameter, scan_range)
            yscale = 'log'
            data_array = array(scan_res, dtype=float).transpose()
            ylim = [find_min(data_array[:, 1:]),
                    find_max(data_array[:, 1:]) * 2]
        elif scan_type is 'elasticity':
            mca_objects = [ec_term for ec_term in self.ec_results.values() if
                           ec_term.expression != 0 and not ec_term.name.endswith('gamma_keq')]
            column_names = [parameter] + [obj.name for obj in mca_objects]

            y_label = 'Elasticity Coefficient'
            scan_res = self._evalscan(parameter, scan_range)
            yscale = 'linear'
            data_array = array(scan_res, dtype=float).transpose()
            ylim = [nanmin(data_array[:, 1:]), nanmax(data_array[:, 1:]) * 1.1]
            additional_cat_classes = {
                'All Coefficients': ['Term Elasticities']}
            additional_cats = {
                'Term Elasticities': [elas.name for elas in mca_objects if
                                      elas.name.startswith('p')]}

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

        # Assertions prevents unbound local variables therefore pycharm 
        # inspection can be disabled for the two statements below

        # noinspection PyUnboundLocalVariable
        ax_properties = {'ylabel': y_label,
                         'xlabel': x_label,
                         'xscale': 'log',
                         'yscale': yscale,
                         'xlim': [find_min(scan_range), find_max(scan_range)],
                         'ylim': ylim}

        # noinspection PyUnboundLocalVariable
        data = Data2D(mod=self.mod,
                      column_names=column_names,
                      data_array=data_array,
                      ltxe=self._ltxe,
                      analysis_method='thermokin',
                      ax_properties=ax_properties,
                      additional_cat_classes=additional_cat_classes,
                      additional_cats=additional_cats)
        return data


class Term(object):
    def __init__(self, parent, mod, name, expression, ltxe):
        super(Term, self).__init__()
        self.name = name
        self._unfac_expression = sympify(expression)
        self._parent = parent
        self.mod = mod
        self._ltxe = ltxe
        # properties
        self._expression = None
        self._str_expression_ = None
        self._value = None
        self._latex_name = None
        self._latex_expression = None

    def _repr_latex_(self):
        return get_repr_latex(self)

    @property
    def _str_expression(self):
        if not self._str_expression_:
            self._str_expression_ = str(self.expression)
        return self._str_expression_

    @property
    def expression(self):
        if not self._expression:
            self._expression = self._unfac_expression.factor()
        return self._expression

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
                    self.expression,
                    mul_symbol='dot')
        return self._latex_expression

    def _calc_value(self, subs_dict=None):
        if not subs_dict:
            subs_dict = get_subs_dict(self.expression, self.mod)
        self._value = get_value(self._str_expression, subs_dict)


class RateTerm(Term):
    def __init__(self, parent, mod, name, rname, expression, ltxe):
        super(RateTerm, self).__init__(parent, mod, name, expression, ltxe)
        self._rname = rname
        self.ec_results = DotDict()
        self.ec_results._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                   formatter_factory())
        self._populate_ec_results()
        self._percentage = None

    @property
    def expression(self):
        if not self._expression:
            self._expression = self._unfac_expression
        return self._expression

    @property
    def percentage(self):
        per = (log10(self.value) / log10(self._parent.value)) * 100
        return per

    def _populate_ec_results(self):
        expression_symbols = self._parent._unfac_expression.atoms(Symbol)
        expression_symbols.update(self._unfac_expression.atoms(Symbol))
        for each in expression_symbols:
            each = sympify(each)
            ec_name = 'pec%s_%s_%s' % (self._parent._rname, each, self._rname)
            ec = diff(self.expression, each) * (each / self.expression)
            self.ec_results[ec_name] = Term(self._parent, self.mod, ec_name,
                                            ec,
                                            self._ltxe)


class AdditionalRateTerm(RateTerm):
    @property
    def percentage(self):
        return 0.0


class AdditionalTerm(Term):
    def __init__(self, parent, mod, name, expression, ltxe):
        super(AdditionalTerm, self).__init__(parent, mod, name, expression,
                                             ltxe)
        self._parent = None
