import numpy as np
#from PyscesToolBox import PyscesToolBox as PYCtools
from sympy import Symbol
from ...utils.plotting import LineData, ScanFig


class CCBase(object):

    """The base object for the control coefficients and control patterns"""

    def __init__(self, mod, name, expression, ltxe):
        super(CCBase, self).__init__()

        self.expression = expression
        self.mod = mod
        self._ltxe = ltxe
        self.name = name
        self._latex_name = '\\Sigma'

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
    def value(self):
        """The value property. Calls self._calc_value() when self._value
        is None and returns self._value"""
        if not self._value:
            self._calc_value()
        return self._value

    def _calc_value(self):
        """Calculates the value of the expression"""
        symbols = self.expression.atoms(Symbol)
        subsdic = {}
        for symbol in symbols:
            subsdic[symbol] = getattr(self.mod, str(symbol))
        self._value = self.expression.subs(subsdic)


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

        self._control_patterns = None

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
            self._latex_expression = self.latex_numerator + '/ \\,\\Sigma'
        return self._latex_expression

    @property
    def latex_name(self):
        if not self._latex_name:
            self._latex_name = self._ltxe.expression_to_latex(
                self.name
            )
        return self._latex_name

    @property
    def control_patterns(self):
        if not self._control_patterns:
            self._set_control_patterns()
        return self._control_patterns

    def parscan(self, parameter, scan_range, init_return=False):
        """Performs a parameter scan and returns numpy array object
           with the parameter values in the first column and
           percentage contribution of each control pattern
           in subsequent columns

           Arguments:
           parameter   --  the parameter of the model to scan
           scan_range  --  the range across which to scan 'parameter'

           calls self._recalculate_value() for each value of
           parameter in scan_range"""
        scan_res = [list() for i in range(len(self.control_patterns) + 1)]
        scan_res[0] = scan_range

        # print type(scan_res)
        init = getattr(self.mod, parameter)
        for parvalue in scan_range:
            setattr(self.mod, parameter, parvalue)
            self.mod.SetQuiet()
            self.mod.doMca()
            self.mod.SetLoud()

            self._recalculate_value()
            for i, cp in enumerate(self.control_patterns):
                # print type(scan_res[i+1])
                scan_res[i + 1].append(cp.percentage)

        if init_return:
            setattr(self.mod, parameter, init)

        cp_names = [cp.name for cp in self.control_patterns]
        data = np.array(scan_res, dtype=np.float).transpose()
        line_data_list = []
        for i, cp in enumerate(cp_names):
            ld = LineData(name=cp,
                          x_data=data[:, 0],
                          y_data=data[:, 1+i],
                          categories=[cp])
            line_data_list.append(ld)

        if parameter in self.mod.fixed_species:
            x_label = '[%s]' % parameter.replace('_', ' ')
        else:
            x_label = '%s' % parameter.replace('_', ' ')
        scan_fig = ScanFig(line_data_list,
                           ax_properties={'xlabel': x_label,
                                          'ylabel': 'Percentage Contribution',
                                          'xscale': 'log',
                                          'xlim': [np.min(scan_range),
                                                   np.max(scan_range)],
                                          'ylim':  [0, 100]},
                           category_classes={'Control Patterns': cp_names})
        return scan_fig

        #return np.array(scan_res, dtype=np.float).transpose()

    def _recalculate_value(self):
        """Recalculates the control coefficients and control pattern
           values. calls _calc_value() for self and each control
           pattern. Useful for when model parameters change"""
        for pattern in self.control_patterns:
            pattern._calc_value()
            self._calc_value()

    def _calc_value(self):
        """Calculates the numeric value of the control pattern from the
           values of its control patterns."""
        self._value = sum([pattern.value for pattern in self.control_patterns])

    def _set_control_patterns(self):
        """Divides control coefficient into control pattens and saves
           results in self.CPx where x is a number is the number of the
           control pattern as it appears in in control coefficient
           expression"""
        pattens = self.numerator.as_coeff_add()[1]
        cps = []
        for i, pattern in enumerate(pattens):
            name = 'CP' + str(1 + i)
            cp = CPattern(self.mod,
                          name,
                          pattern,
                          self.denominator_object,
                          self,
                          self._ltxe)
            setattr(self, name, cp)
            cps.append(cp)
        self._control_patterns = cps
        #assert self._check_control_patterns == True

    def _check_control_patterns(self):
        """Checks that all control patterns are either positive or negative"""
        all_same = False
        poscomp = [i.value > 0 for i in self.control_patterns]
        negcomp = [i.value < 0 for i in self.control_patterns]
        if all(poscomp):
            all_same = True
        elif all(negcomp):
            all_same = True
        return all_same


class CPattern(CCBase):

    """docstring for CPattern"""

    def __init__(self, mod, name, expression, denominator, parent, ltxe):
        super(CPattern, self).__init__(mod, name, expression, ltxe)
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
            self._latex_expression = self.latex_numerator + '/ \\,\\Sigma'
        return self._latex_expression

    @property
    def latex_name(self):
        if not self._latex_name:
            self._latex_name = self._ltxe.expression_to_latex(
                self.name
            )
        return self._latex_name

    @property
    def percentage(self):
        self._percentage = (self.value / self.parent.value) * 100
        return self._percentage
