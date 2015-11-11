import numpy as np
from numpy import array, nanmin, nanmax
from sympy import Symbol
from pysces import ModelMap
from numpy import NaN, abs

from ...utils.model_graph import ModelGraph
from ...utils.misc import silence_print, DotDict, formatter_factory, \
    do_safe_state, find_min, find_max, get_value
from ...utils.plotting import Data2D


def cctype(obj):
    return 'ccobjects' in str(type(obj))


@silence_print
def get_state(mod, do_state=False):
    if do_state:
        mod.doState()
    ss = [getattr(mod, 'J_' + r) for r in mod.reactions] + \
        [getattr(mod, s + '_ss') for s in mod.species]
    return ss



class CCBase(object):

    """The base object for the control coefficients and control patterns"""

    def __init__(self, mod, name, expression, ltxe):
        super(CCBase, self).__init__()

        self.expression = expression
        self.mod = mod
        self._ltxe = ltxe
        self.name = name
        self._latex_name = '\\Sigma'
        self._analysis_method = 'symca'

        self._str_expression_ = None
        self._value = None
        self._latex_expression = None

    @property
    def latex_expression(self):
        if not self._latex_expression:
            self._latex_expression = self._ltxe.expression_to_latex(
                self.expression
            )
        return self._latex_expression

    @property
    def latex_name(self):
        return self._latex_name

    @property
    def _str_expression(self):
        if not self._str_expression_:
            self._str_expression_ = str(self.expression)
        return self._str_expression_

    @property
    def value(self):
        """The value property. Calls self._calc_value() when self._value
        is None and returns self._value"""
        self._calc_value()
        return self._value

    def _repr_latex_(self):
        return '$%s = %s = %.3f$' % (self.latex_name,
                                     self.latex_expression,
                                     self.value)

    def _calc_value(self):
        """Calculates the value of the expression"""
        keys = self.expression.atoms(Symbol)
        subsdict = {}
        for key in keys:
            str_key = str(key)
            subsdict[str_key] = getattr(self.mod, str_key)
        self._value = get_value(self._str_expression, subsdict)

    def __repr__(self):
        return self.expression.__repr__()

    def __add__(self, other):
        if cctype(other):
            return self.expression.__add__(other.expression)
        else:
            return self.expression.__add__(other)

    def __mul__(self, other):
        if cctype(other):
            return self.expression.__mul__(other.expression)
        else:
            return self.expression.__mul__(other)

    def __div__(self, other):
        if cctype(other):
            return self.expression.__div__(other.expression)
        else:
            return self.expression.__div__(other)

    def __pow__(self, other):
        if cctype(other):
            return self.expression.__pow__(other.expression)
        else:
            return self.expression.__pow__(other)


class CCoef(CCBase):

    """The object the stores control coefficients. Inherits from CCBase"""

    def __init__(self, mod, name, expression, denominator, ltxe):
        super(CCoef, self).__init__(mod, name, expression, ltxe)
        self.numerator = expression
        self.denominator = denominator.expression
        self.expression = self.numerator / denominator.expression
        self.denominator_object = denominator

        self._latex_numerator = None
        self._latex_expression_full = None
        self._latex_expression = None
        self._latex_name = None
        self._abs_value = None

        self.control_patterns = None

        self._set_control_patterns()

    @property
    def abs_value(self):
        self._calc_abs_value()
        return self._abs_value

    @property
    def latex_numerator(self):
        if not self._latex_numerator:
            self._latex_numerator = self._ltxe.expression_to_latex(
                self.numerator
            )
        return self._latex_numerator

    @property
    def latex_expression_full(self):
        if not self._latex_expression_full:
            full_expr = '\\frac{' + self.latex_numerator + '}{' \
                + self.denominator_object.latex_expression + '}'
            self._latex_expression_full = full_expr
        return self._latex_expression_full

    @property
    def latex_expression(self):
        if not self._latex_expression:
            self._latex_expression = '(' + \
                self.latex_numerator + ')' + '/~\\Sigma'
        return self._latex_expression

    @property
    def latex_name(self):
        if not self._latex_name:
            self._latex_name = self._ltxe.expression_to_latex(
                self.name
            )
        return self._latex_name

    def _perscan(self, parameter, scan_range):

        scan_res = [list() for i in range(len(self.control_patterns.values()) + 1)]
        scan_res[0] = scan_range

        for parvalue in scan_range:
            state_valid = do_safe_state(self.mod, parameter, parvalue,type='mca')
            for i, cp in enumerate(self.control_patterns.values()):
                if state_valid:
                    scan_res[i + 1].append(cp.percentage)
                else:
                    scan_res[i + 1].append(NaN)

        return scan_res


    def _valscan(self, parameter, scan_range):

        scan_res = [list() for i in range(len(self.control_patterns.values()) + 2)]
        scan_res[0] = scan_range

        for parvalue in scan_range:
            state_valid = do_safe_state(self.mod, parameter, parvalue,type='mca')
            for i, cp in enumerate(self.control_patterns.values()):
                if state_valid:
                    scan_res[i + 1].append(cp.value)
                else:
                    scan_res[i + 1].append(NaN)
            if state_valid:
                scan_res[i + 2].append(self.value)
            else:
                scan_res[i + 2].append(NaN)

        return scan_res

    def do_par_scan(self, parameter, scan_range, scan_type='percentage', init_return=True):

        assert scan_type in ['percentage', 'value']
        init = getattr(self.mod, parameter)

        if scan_type is 'percentage':
            column_names = [parameter] + \
                [cp.name for cp in self.control_patterns.values()]
            y_label = 'Control pattern percentage contribution'
            scan_res = self._perscan(parameter,scan_range)
            data_array = array(scan_res, dtype=np.float).transpose()
            ylim = [nanmin(data_array[:,1:]), nanmax(data_array[:,1:]) * 1.1]
        elif scan_type is 'value':
            column_names = [
                parameter] + [cp.name for cp in self.control_patterns.values()] + [self.name]
            y_label = 'Control coefficient/pattern value'
            scan_res = self._valscan(parameter,scan_range)
            data_array = array(scan_res, dtype=np.float).transpose()
            ylim = [nanmin(data_array[:,1:]), nanmax(data_array[:,1:]) * 1.1]

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
                         'xscale': 'linear',
                         'yscale': 'linear',
                         'xlim': [find_min(scan_range), find_max(scan_range)],
                         'ylim': ylim}

        data = Data2D(mod = self.mod,
                      column_names=column_names,
                      data_array=data_array,
                      ltxe=self._ltxe,
                      analysis_method='symca',
                      ax_properties=ax_properties,
                      file_name=self.name)

        return data


    # def _recalculate_value(self):
    #     """Recalculates the control coefficients and control pattern
    #        values. calls _calc_value() for self and each control
    #        pattern. Useful for when model parameters change"""
    #     self._calc_value()

    def _calc_abs_value(self):
        """Calculates the absolute numeric value of the control coefficient from the
           values of its control patterns."""
        keys = self.expression.atoms(Symbol)
        subsdict = {}
        if len(keys) == 0:
            subsdict = None
        for key in keys:
            str_key = str(key)
            subsdict[str_key] = getattr(self.mod, str_key)
        for pattern in self.control_patterns.values():
            pattern._calc_value(subsdict)
        self._abs_value = sum(
            [abs(pattern._value) for pattern in self.control_patterns.values()])

    def _calc_value(self):
        """Calculates the numeric value of the control coefficient from the
           values of its control patterns."""
        keys = self.expression.atoms(Symbol)
        subsdict = {}
        if len(keys) == 0:
            subsdict = None
        for key in keys:
            str_key = str(key)
            subsdict[str_key] = getattr(self.mod, str_key)
        for pattern in self.control_patterns.values():
            pattern._calc_value(subsdict)
        self._value = sum(
            [pattern._value for pattern in self.control_patterns.values()])

    def _set_control_patterns(self):
        """Divides control coefficient into control patterns and saves
           results in self.CPx where x is a number is the number of the
           control pattern as it appears in in control coefficient
           expression"""
        patterns = self.numerator.as_coeff_add()[1]
        if len(patterns) == 0:
            patterns = [self.numerator.as_coeff_add()[0]]

        cps = DotDict()
        cps._make_repr('v.name', 'v.value', formatter_factory())
        for i, pattern in enumerate(patterns):
            name = 'CP' + str(1 + i)
            cp = CPattern(self.mod,
                          name,
                          pattern,
                          self.denominator_object,
                          self,
                          self._ltxe)
            setattr(self, name, cp)
            cps[name] = cp
        self.control_patterns = cps
        #assert self._check_control_patterns == True

    def _check_control_patterns(self):
        """Checks that all control patterns are either positive or negative"""
        all_same = False
        poscomp = [i.value > 0 for i in self.control_patterns.values()]
        negcomp = [i.value < 0 for i in self.control_patterns.values()]
        if all(poscomp):
            all_same = True
        elif all(negcomp):
            all_same = True
        return all_same

    def highlight_patterns(self,width=None, height=None, show_dummy_sinks=False, show_external_modifier_links=False):

        mg = ModelGraph(mod=self.mod,analysis_method=self._analysis_method)
        if height:
            mg.height = height
        if width:
            mg.width = width

        mg.highlight_cc(self, show_dummy_sinks, show_external_modifier_links)


class CPattern(CCBase):

    """docstring for CPattern"""

    def __init__(self,
                 mod,
                 name,
                 expression,
                 denominator,
                 parent,
                 ltxe):
        super(CPattern, self).__init__(mod,
                                       name,
                                       expression,
                                       ltxe)
        self.numerator = expression
        self.denominator = denominator.expression
        self.expression = self.numerator / denominator.expression
        self.denominator_object = denominator
        self.parent = parent

        self._latex_numerator = None
        self._latex_expression_full = None
        self._latex_expression = None
        self._latex_name = None
        self._percentage = None

    def _calc_value(self, subsdict=None):
        """Calculates the value of the expression"""
        if subsdict is None:
            keys = self.expression.atoms(Symbol)
            subsdict = {}
            for key in keys:
                str_key = str(key)
                subsdict[str_key] = getattr(self.mod, str_key)
        self._value = get_value(self._str_expression, subsdict)

    @property
    def latex_numerator(self):
        if not self._latex_numerator:
            self._latex_numerator = self._ltxe.expression_to_latex(
                self.numerator
            )
        return self._latex_numerator

    @property
    def latex_expression_full(self):
        if not self._latex_expression_full:
            full_expr = '\\frac{' + self.latex_numerator + '}{' \
                + self.denominator_object.latex_expression + '}'
            self._latex_expression_full = full_expr
        return self._latex_expression_full

    @property
    def latex_expression(self):
        if not self._latex_expression:
            self._latex_expression = self.latex_numerator + '/~\\Sigma'
        return self._latex_expression

    @property
    def latex_name(self):
        if not self._latex_name:
            self._latex_name = self.name
        return self._latex_name

    @property
    def percentage(self):
        self._percentage = (abs(self.value) / self.parent.abs_value) * 100
        return self._percentage
