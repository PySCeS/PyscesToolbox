from sympy import latex, sympify, Symbol

__all__ = ['LatexExpr']


def min_(string):
    """
    Returns a string stripped of underscores.

    Parameters
    ----------
    string : str
        A string containing underscores

    Returns
    -------
    values: str
        A string without underscores
    """
    return string.replace('_', '')


class LatexExpr(object):

    """docstring for LatexExpr"""

    def __init__(self, mod):
        super(LatexExpr, self).__init__()
        self.mod = mod
        self._subs_dict = None
        self._prc_subs = None
        self._added_tk = False
        self._tk_subs = None
        self._term_types = None

    def add_term_types(self, term_types):
        self._term_types = term_types

    def _add_tk_subs(self):
        if not self._subs_dict:
            self.subs_dict
        mod = self.mod
        j_subs = {}
        pec_subs = {}
        for term in self._term_types:
            # Fluxes:
            for reaction in mod.reactions:
                j_subs['J_%s_%s' % (reaction, term)] = 'J__%s_%s' % (min_(term),
                                                                     min_(reaction))
            for top_reaction in mod.reactions:
                for var_par in mod.species + mod.parameters:
                    o_ec = 'pec%s_%s_%s' % (top_reaction,
                                            var_par,
                                            term)
                    n_ec = 'varepsilon__%s_%s__%s' % (min_(top_reaction),
                                                      min_(var_par),
                                                      min_(term))
                    pec_subs[o_ec] = n_ec

        self._subs_dict.update(j_subs)
        self._subs_dict.update(pec_subs)
        self._added_tk = True

    @property
    def subs_dict(self):
        if not self._subs_dict:
            ec_subs = {}
            rc_subs = {}
            cc_subs = {}
            prc_subs = {}
            j_subs = {}
            sp_subs = {}
            par_subs = {}
            mod = self.mod

            # For clarity:
            # lots of code duplication
            # min_() strips string of underscores

            # Species:
            for species in mod.species:
                sp_subs[species] = min_(species)
                sp_subs[species + '_ss'] = min_(species) + '_ss'

            # Fluxes:
            for reaction in mod.reactions:
                j_subs[reaction] = min_(reaction)
                j_subs['J_' + reaction] = 'J_' + min_(reaction)

            # Parameters
            for par in mod.parameters:
                par_subs[par] = min_(par)

            # Control Coefficients:
            for base_reaction in mod.reactions:
                for top_species in mod.species:
                    o_cc = 'cc%s_%s' % (top_species, base_reaction)
                    n_cc = 'C__%s_%s' % (min_(top_species),
                                         min_(base_reaction))
                    cc_subs[o_cc] = n_cc

                for top_reaction in mod.reactions:
                    o_cc = 'ccJ%s_%s' % (top_reaction, base_reaction)
                    n_cc = 'C__J%s_%s' % (min_(top_reaction),
                                          min_(base_reaction))
                    cc_subs[o_cc] = n_cc

            # Elasticity Coefficients:
            for top_reaction in mod.reactions:
                for base_species in mod.species:
                    o_ec = 'ec%s_%s' % (top_reaction, base_species)
                    n_ec = 'varepsilon__%s_%s' % (min_(top_reaction),
                                                  min_(base_species))
                    ec_subs[o_ec] = n_ec

                for base_param in mod.parameters:
                    o_ec = 'ec%s_%s' % (top_reaction, base_param)
                    n_ec = 'varepsilon__%s_%s' % (min_(top_reaction),
                                                  min_(base_param))
                    ec_subs[o_ec] = n_ec

            # Response Coefficients:
            # I'm adding species together with parameter
            # This increases the size of the dictionary
            # but it ensures that only one LatexExpr object
            # is needed for something like RateChar (or SymCa)
            for base_param in set(mod.parameters + mod.species):
                for top_species in mod.species:
                    o_rc = 'rc%s_%s' % (top_species, base_param)
                    n_rc = 'R__%s_%s' % (min_(top_species),
                                         min_(base_param))
                    rc_subs[o_rc] = n_rc

                for top_reaction in mod.reactions:
                    o_rc = 'rcJ%s_%s' % (top_reaction, base_param)
                    n_rc = 'R__J%s_%s' % (min_(top_reaction),
                                          min_(base_param))
                    rc_subs[o_rc] = n_rc

            # Partial Response Coefficients:
            # I'm adding species together with parameter
            # This increases the size of the dictionary
            # but it ensures that only one LatexExpr object
            # is needed for something like RateChar (or SymCa)
            for base_param in set(mod.parameters + mod.species):
                for back_reaction in mod.reactions:
                    for top_species in mod.species:
                        o_prc = 'prc%s_%s_%s' % (top_species,
                                                 base_param,
                                                 back_reaction)
                        n_prc = 'R__%s_%s__%s' % (min_(top_species),
                                                  min_(base_param),
                                                  min_(back_reaction))
                        prc_subs[o_prc] = n_prc

                    for top_reaction in mod.reactions:
                        o_prc = 'prcJ%s_%s_%s' % (top_reaction,
                                                  base_param,
                                                  back_reaction)
                        n_prc = 'R__J%s_%s__%s' % (min_(top_reaction),
                                                   min_(base_param),
                                                   min_(back_reaction))
                        prc_subs[o_prc] = n_prc

            subs_dict = {}
            subs_dict.update(ec_subs)
            subs_dict.update(cc_subs)
            subs_dict.update(rc_subs)
            subs_dict.update(j_subs)
            subs_dict.update(sp_subs)
            subs_dict.update(prc_subs)
            subs_dict.update(par_subs)
            self._subs_dict = subs_dict

        return self._subs_dict

    @property
    def prc_subs(self):
        if not self._prc_subs:
            mod = self.mod
            prc_subs = {}
            for base_param in set(mod.parameters + mod.species):
                for back_reaction in mod.reactions:
                    for top_species in mod.species:
                        o_prc = 'R^{%s %s}_{%s}' % (min_(top_species),
                                                    min_(back_reaction),
                                                    min_(base_param))

                        n_prc = '\,^{%s}R^{%s}_{%s}' % (min_(back_reaction),
                                                        min_(top_species),
                                                        min_(base_param))

                        prc_subs[o_prc] = n_prc

                    for top_reaction in mod.reactions:
                        o_prc = 'R^{J%s %s}_{%s}' % (min_(top_reaction),
                                                     min_(back_reaction),
                                                     min_(base_param))

                        n_prc = '\,^{%s}R^{J%s}_{%s}' % (min_(back_reaction),
                                                         min_(top_reaction),
                                                         min_(base_param))

                        prc_subs[o_prc] = n_prc

            self._prc_subs = prc_subs

        return self._prc_subs

    @property
    def tk_subs(self):
        if not self._tk_subs:

            mod = self.mod
            tk_subs = {}
            pec_subs = {}
            j_subs = {}
            for term_type in self._term_types:
                for top_reaction in mod.reactions:
                    for base_param in mod.parameters + mod.species:
                        o_pec = '\\varepsilon^{%s %s}_{%s}' % (min_(top_reaction),
                                                               min_(term_type),
                                                               min_(base_param))

                        n_pec = '\\varepsilon^{{%s}_{%s}}_{%s}' % (min_(top_reaction),
                                                                   min_(
                                                                       term_type),
                                                                   min_(base_param))
                        pec_subs[o_pec] = n_pec

                    o_j = 'J^{%s}_{%s}' % (min_(term_type), min_(top_reaction))
                    n_j = 'J_{{%s}_{%s}}' % (
                        min_(top_reaction), min_(term_type))
                    j_subs[o_j] = n_j

            tk_subs.update(pec_subs)
            tk_subs.update(j_subs)
            self._tk_subs = tk_subs
        return self._tk_subs

    def expression_to_latex(self, expression,mul_symbol=None):
        if type(expression) == str:
            expression = sympify(expression)

        # symbol substitution in sympy takes longer for larger dicts
        # therefore I only get the symbols that I need
        # for mcanut model substitution of a 2 symbol expression
        # takes 3xxms for conversion with the full dict, but
        # only 1.9x - 2.2xms with the smaller_dict. Thats over 9000 times
        # faster!!! Ok only over 100X
        needed_symbols = expression.atoms(Symbol)
        smaller_dict = {}

        if self._term_types and not self._added_tk:
            self._add_tk_subs()

        for each in needed_symbols:
            each = str(each)
            if each[:2] == 'CP':
                smaller_dict[each] = each
            elif each in self.subs_dict:
                smaller_dict[each] = self.subs_dict[each]

        # using smaller_dict here instead of self.subs_dict
        latex_expr = latex(expression.subs(smaller_dict),
                           long_frac_ratio=10,
                           mul_symbol=mul_symbol)

        for k, v in self.prc_subs.iteritems():
            latex_expr = latex_expr.replace(k, v)

        if self._added_tk:
            for k, v in self.tk_subs.iteritems():
                latex_expr = latex_expr.replace(k, v)

        return latex_expr
