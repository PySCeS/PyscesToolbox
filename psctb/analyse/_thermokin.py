from os import path

from numpy import log10, array, float, NaN, nanmin, nanmax, savetxt, hstack, float
from pysces import ModelMap, ParScanner, Scanner
from sympy import sympify, diff, Symbol

from ._thermokin_file_tools import get_subs_dict, get_reqn_path, \
    get_all_terms, get_term_types_from_raw_data, create_reqn_data, \
    write_reqn_file, create_gamma_keq_reqn_data, term_to_file
from ..latextools import LatexExpr
from ..modeltools import make_path, get_file_path
from ..utils.misc import do_safe_state, get_value, silence_print, print_f, \
    is_number, stringify, scanner_range_setup, DotDict, formatter_factory, \
    find_min, find_max
from ..utils.plotting import Data2D

__author__ = 'carl'
__all__ = ['ThermoKin']


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
            if not add_raw_data.get(reaction) or not add_raw_data.get(
                    reaction).get('gamma_keq'):
                gamma_keq_todo.append(reaction)
        if len(gamma_keq_todo) != 0:
            reaction_printout = ', '.join(gamma_keq_todo[:-1]) + ' or ' + \
                                gamma_keq_todo[-1]
            print_f('%s does not contain Gamma/Keq terms for %s:' % (
                self._path_to, reaction_printout), warnings)
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
            ma_terms, vc_binding_terms, gamma_keq_terms, messages = create_reqn_data(
                self.mod)
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

    def save_results(self, file_name=None, separator=',',fmt='%.9f'):
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
                    header=separator.join(head),
                    delimiter=separator,
                    fmt=['%s', fmt, '%s', '%s'], )

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
            ec = diff(self._unfac_expression, each) * \
                (each / self._unfac_expression)
            ec_name = 'ec%s_%s' % (self._rname, each)
            self.ec_results[ec_name] = Term(self, self.mod, ec_name,
                                            self._rname, ec,
                                            self._ltxe)
        for each in self.terms.itervalues():
            self.ec_results.update(each.ec_results)

    def _repr_latex_(self):
        return get_repr_latex(self)

    @property
    def _str_expression(self):
        if not self._str_expression_:
            self._str_expression_ = str(self._unfac_expression)
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
        subs_dict = get_subs_dict(self._unfac_expression, self.mod)
        for each in self.terms.itervalues():
            if type(each) is not AdditionalRateTerm:
                each._calc_value(subs_dict)
        self._value = mult([each._value for each in self.terms.itervalues() if
                            type(each) is not AdditionalRateTerm])

    def _valscan_x(self, parameter, scan_range):
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

    def _valscan(self,
                 parameter,
                 scan_range,
                 par_scan=False,
                 par_engine='multiproc'):

        # choose between parscanner or scanner
        if par_scan:
            # This is experimental
            scanner = ParScanner(self.mod, par_engine)
        else:
            scanner = Scanner(self.mod)
            scanner.quietRun = True

        # parameter scan setup and execution
        start, end, points, log = scanner_range_setup(scan_range)
        scanner.addScanParameter(parameter,
                                 start=start,
                                 end=end,
                                 points=points,
                                 log=log)

        needed_symbols = [parameter] + \
            stringify(list(self.expression.atoms(Symbol)))

        scanner.addUserOutput(*needed_symbols)
        scanner.Run()

        # getting term/reaction values via substitution
        subs_dict = {}
        for i, symbol in enumerate(scanner.UserOutputList):
            subs_dict[symbol] = scanner.UserOutputResults[:, i]

        term_expressions = [term.expression for term in self.terms.values()]\
            + [self.expression]
        term_str_expressions = stringify(term_expressions)
        parameter_values = subs_dict[parameter].reshape(points, 1)

        scan_res = []

        # collecting results in an array
        for expr in term_str_expressions:
            scan_res.append(get_value(expr, subs_dict))
        scan_res = array(scan_res).transpose()
        scan_res = hstack([parameter_values, scan_res])
        return scan_res

    def _ecscan(self,
                parameter,
                scan_range,
                par_scan=False,
                par_engine='multiproc'):

        # choose between parscanner or scanner
        if par_scan:
            # This is experimental
            scanner = ParScanner(self.mod, par_engine)
        else:
            scanner = Scanner(self.mod)
            scanner.quietRun = True

        # parameter scan setup and execution
        start, end, points, log = scanner_range_setup(scan_range)
        scanner.addScanParameter(parameter,
                                 start=start,
                                 end=end,
                                 points=points,
                                 log=log)

        needed_symbols = [parameter] + \
            stringify(list(self.expression.atoms(Symbol)))

        scanner.addUserOutput(*needed_symbols)
        scanner.Run()

        # getting term/reaction values via substitution
        subs_dict = {}
        for i, symbol in enumerate(scanner.UserOutputList):
            subs_dict[symbol] = scanner.UserOutputResults[:, i]

        # we include all ec_terms that are not zero (even though they are
        # included in the main dict)
        ec_term_expressions = [ec_term.expression for ec_term in
                               self.ec_results.values() if
                               ec_term.expression != 0 and
                               not ec_term.name.endswith('gamma_keq')]
        ec_term_str_expressions = stringify(ec_term_expressions)
        parameter_values = subs_dict[parameter].reshape(points, 1)

        scan_res = []

        # collecting results in an array
        for expr in ec_term_str_expressions:
            val = get_value(expr, subs_dict)
            scan_res.append(val)
        scan_res = array(scan_res).transpose()
        scan_res = hstack([parameter_values, scan_res])
        return scan_res

    def _ecscan_x(self, parameter, scan_range):
        mca_objects = [ec_term for ec_term in self.ec_results.values() if
                       ec_term.expression != 0 and not ec_term.name.endswith(
                           'gamma_keq')]

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

    def do_par_scan(self,
                    parameter,
                    scan_range,
                    scan_type='value',
                    init_return=True,
                    par_scan=False,
                    par_engine='multiproc'):

        try:
            assert scan_type in ['elasticity', 'value'], 'scan_type must be one\
                of "value" or "elasticity".'
        except AssertionError as ae:
            print ae

        init = getattr(self.mod, parameter)

        if scan_type == 'elasticity':
            mca_objects = [ec_term for ec_term in self.ec_results.values() if
                           ec_term.expression != 0 and
                           not ec_term.name.endswith('gamma_keq')]

            additional_cat_classes = {
                'All Coefficients': ['Term Elasticities']}
            additional_cats = {
                'Term Elasticities': [ec_term.name for ec_term in mca_objects
                                      if
                                      ec_term.name.startswith('p')]}
            column_names = [parameter] + \
                [ec_term.name for ec_term in mca_objects]
            y_label = 'Elasticity Coefficient'
            scan_res = self._ecscan(parameter,
                                    scan_range,
                                    par_scan,
                                    par_engine)
            data_array = scan_res
            # ylim = [nanmin(data_array[:, 1:]),
            #         nanmax(data_array[:, 1:]) * 1.1]
            yscale = 'linear'
            category_manifest = {pec: True for pec in
                                 additional_cats['Term Elasticities']}
            category_manifest['Elasticity Coefficients'] = True
            category_manifest['Term Elasticities'] = True

        elif scan_type == 'value':
            additional_cat_classes = {'All Fluxes/Reactions/Species':
                                      ['Term Rates']}
            term_names = [term.name for term in self.terms.values()]
            additional_cats = {'Term Rates': term_names}
            column_names = [parameter] + term_names + [self.name]
            y_label = 'Reaction/Term rate'
            scan_res = self._valscan(parameter,
                                     scan_range,
                                     par_scan,
                                     par_engine)
            data_array = scan_res
            # ylim = [nanmin(data_array[:, 1:]),
            #         nanmax(data_array[:, 1:]) * 1.1]
            yscale = 'log'
            category_manifest = {'Flux Rates': True, 'Term Rates': True}

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

        xscale = 'log' if scanner_range_setup(scan_range)[3] else 'linear'
        ax_properties = {'ylabel': y_label,
                         'xlabel': x_label,
                         'xscale': xscale,
                         'yscale': yscale, }

        data = Data2D(mod=self.mod,
                      column_names=column_names,
                      data_array=data_array,
                      ltxe=self._ltxe,
                      analysis_method='thermokin',
                      ax_properties=ax_properties,
                      additional_cat_classes=additional_cat_classes,
                      additional_cats=additional_cats,
                      category_manifest=category_manifest,)

        if scan_type == 'elasticity':
            ec_names = [ec_term.name for ec_term in mca_objects if
                        ec_term.name.startswith('ec')]
            for line in data._lines:
                for ec_name in ec_names:
                    condition1 = line.name != ec_name
                    condition2 = self.ec_results[line.name]._rname == ec_name
                    if condition1 and condition2:
                        line.categories.append(ec_name)

        return data

    def __add__(self, other):
        return generic_term_operation(self, other, '+')

    def __mul__(self, other):
        return generic_term_operation(self, other, '*')

    def __sub__(self, other):
        return generic_term_operation(self, other, '-')

    def __div__(self, other):
        return generic_term_operation(self, other, '/')

    def __radd__(self, other):
        return generic_term_operation(self, other, '+')

    def __rmul__(self, other):
        return generic_term_operation(self, other, '*')

    def __rsub__(self, other):
        return generic_term_operation(self, other, 'rsub')

    def __rdiv__(self, other):
        return generic_term_operation(self, other, 'rdiv')

    def __neg__(self):
        return AdditionalTerm(self,
                              self.mod,
                              '-' + self.name,
                              '-' + self._rname,
                              (-self._unfac_expression),
                              self._ltxe,
                              '-' + self.name)

    def __pow__(self, power, modulo=None):
        return AdditionalTerm(self,
                              self.mod,
                              self.name + '**' + str(power),
                              self._rname + '**' + str(power),
                              self._unfac_expression ** power,
                              self._ltxe,
                              self.name + '**' + str(power))


class Term(object):
    def __init__(self, parent, mod, name, rname, expression, ltxe):
        super(Term, self).__init__()
        self.name = name
        self._rname = rname
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
            self._str_expression_ = str(self._unfac_expression)
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
            subs_dict = get_subs_dict(self._unfac_expression, self.mod)
        self._value = get_value(self._str_expression, subs_dict)

    def __add__(self, other):
        return generic_term_operation(self, other, '+')

    def __mul__(self, other):
        return generic_term_operation(self, other, '*')

    def __sub__(self, other):
        return generic_term_operation(self, other, '-')

    def __div__(self, other):
        return generic_term_operation(self, other, '/')

    def __radd__(self, other):
        return generic_term_operation(self, other, '+')

    def __rmul__(self, other):
        return generic_term_operation(self, other, '*')

    def __rsub__(self, other):
        return generic_term_operation(self, other, 'rsub')

    def __rdiv__(self, other):
        return generic_term_operation(self, other, 'rdiv')

    def __neg__(self):
        return AdditionalTerm(self._parent,
                              self.mod,
                              '-' + self.name,
                              '-' + self._rname,
                              (-self._unfac_expression),
                              self._ltxe,
                              '-' + self.name)

    def __pow__(self, power, modulo=None):
        return AdditionalTerm(self._parent,
                              self.mod,
                              self.name + '**' + str(power),
                              self._rname + '**' + str(power),
                              self._unfac_expression ** power,
                              self._ltxe,
                              self.name + '**' + str(power))


class RateTerm(Term):
    def __init__(self, parent, mod, name, rname, expression, ltxe):
        super(RateTerm, self).__init__(parent, mod, name, rname, expression,
                                       ltxe)
        self.ec_results = DotDict()
        self.ec_results._make_repr('"$" + v.latex_name + "$"', 'v.value',
                                   formatter_factory())
        self._populate_ec_results()
        self._percentage = None

    @property
    def percentage(self):
        per = (log10(self.value) / log10(self._parent.value)) * 100
        return per

    def _populate_ec_results(self):
        expression_symbols = self._parent._unfac_expression.atoms(Symbol)
        expression_symbols.update(self._unfac_expression.atoms(Symbol))
        for each in expression_symbols:
            each = sympify(each)
            ec_name = 'ec%s_%s' % (self._parent._rname, each)
            pec_name = 'p%s_%s' % (ec_name, self._rname)
            ec = diff(self._unfac_expression, each) * \
                (each / self._unfac_expression)
            self.ec_results[pec_name] = Term(self._parent,
                                             self.mod,
                                             pec_name,
                                             ec_name,
                                             ec,
                                             self._ltxe)


class AdditionalRateTerm(RateTerm):
    @property
    def percentage(self):
        return 0.0

    def append_to_file(self, file_name, term_name=None, parent=None):
        if not parent:
            parent = self._parent._rname
        if not term_name:
            term_name = self._rname
        term_to_file(file_name, self._unfac_expression, parent, term_name)


class AdditionalTerm(Term):
    def __init__(self, parent, mod, name, rname, expression, ltxe,
                 creation_operation):
        super(AdditionalTerm, self).__init__(parent, mod, name, rname,
                                             expression,
                                             ltxe)

        self.creation_operation = creation_operation

    def simplify_expression(self):
        self._expression = self._unfac_expression.factor()
        self._latex_expression = None

    def get_elasticity(self, var_par, term_name=None):
        if not term_name:
            term_name = self.name

        var_par = sympify(var_par)
        ec = diff(self._unfac_expression, var_par) * \
            (var_par / self._unfac_expression)
        ec_name = 'ec_%s_%s' % (term_name, var_par)
        ec_term = Term(self, self.mod, ec_name, ec_name, ec, self._ltxe)
        ec_term._latex_name = '\\varepsilon^{%s}_{%s}' % (
            term_name.replace('_', ''),
            str(var_par).replace('_', ''))
        return ec_term

    def append_to_file(self, file_name, term_name=None, parent=None):
        if not parent and self._parent:
            parent = self._parent._rname
        if not term_name and self.name != 'new_term':
            term_name = self.name
        term_to_file(file_name, self._unfac_expression, parent, term_name)

    @property
    def expression(self):
        if not self._expression:
            self._expression = self._unfac_expression
        return self._expression


def generic_term_operation(self, other, operator, parent=None, name=None,
                           rname=None):
    def get_parent(self):
        if type(self) is RateEqn:
            parent = self
        else:
            parent = self._parent
        return parent

    if operator == 'rsub':
        self = -self
        operator = '+'

    if operator == 'rdiv':
        self = AdditionalTerm(get_parent(self),
                              self.mod,
                              self.name,
                              self._rname,
                              (1 / self._unfac_expression),
                              self._ltxe,
                              '1/' + self.name)
        operator = '*'

    if is_number(other):
        other = AdditionalTerm(get_parent(self),
                               self.mod,
                               str(other),
                               str(other),
                               sympify(other),
                               self._ltxe,
                               str(other))

    # TODO this type check is a hack - no idea how to check specifically for
    # sympy expressions
    elif 'sympy' in str(type(other)):
        other = AdditionalTerm(get_parent(self),
                               self.mod,
                               str(other),
                               str(other),
                               other,
                               self._ltxe,
                               str(other))

    mod = self.mod
    operated_on = []
    for term in (self, other):
        if type(term) is AdditionalTerm:
            operated_on.append(term.creation_operation)
        else:
            operated_on.append(term.name)

    if not name:
        name = 'new_term'
    if not rname:
        rname = 'new_term'

    if not parent:
        if hasattr(self, '_parent') and hasattr(other, '_parent'):
            parent = self._parent
        elif type(self) is RateEqn and type(other) is not RateEqn:
            parent = self
        elif type(other) is RateEqn and type(self) is not RateEqn:
            parent = other

    creation_operation = sympify(
        '%s %s %s' % (operated_on[0], operator, operated_on[1]))
    expression = sympify('(%s) %s (%s)' % (
        self._str_expression, operator, other._str_expression))
    ltxe = self._ltxe
    return AdditionalTerm(parent, mod, name, rname, expression, ltxe,
                          creation_operation)
