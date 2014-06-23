from sympy.matrices import Matrix

from ...modeltools import make_path
from ...latextools import LatexExpr
from .symca_toolbox import SymcaToolBox as SMCAtools
#from LatexOut import LatexOut

import logging

all = ['Symca']

class Symca(object):

    def __init__(self, mod):
        super(Symca, self).__init__()

        self.mod = mod
        self.mod.doMca()

        self._analysis_method = 'symca'
        self._working_dir = make_path(self.mod, self._analysis_method)
        self._ltxe = LatexExpr(mod)

        logging.basicConfig(
            filename=self._working_dir + 'symca.log',
            level=logging.DEBUG
        )
        print self._working_dir + 'symca.log'

        #self._latex_out = LatexOut(self)

        self._object_populated = False

        self._nmatrix = None
        self._species = None
        self._num_ind_species = None
        self._species_independent = None
        self._species_dependent = None
        self._fluxes = None
        self._num_ind_fluxes = None
        self._fluxes_independent = None
        self._fluxes_dependent = None
        self._kmatrix = None
        self._lmatrix = None
        self._subs_fluxes = None
        self._scaled_k = None
        self._scaled_l = None
        self._scaled_k0 = None
        self._scaled_l0 = None
        self._es_matrix = None
        self._esL = None
        self._ematrix = None

    @property
    def nmatrix(self):
        if not self._nmatrix:
            self._nmatrix = SMCAtools.get_nmatrix(self.mod)

        return self._nmatrix

    @property
    def num_ind_species(self):
        if not self._num_ind_species:
            self._num_ind_species = SMCAtools.get_num_ind_species(self.mod)

        return self._num_ind_species

    @property
    def species(self):
        if not self._species:
            self._species = SMCAtools.get_species_vector(self.mod)

        return self._species

    @property
    def species_independent(self):
        if not self._species_independent:
            self._species_independent = Matrix(
                self.species[:self.num_ind_species]
            )

        return self._species_independent

    @property
    def species_dependent(self):
        if not self._species_dependent:
            self._species_dependent = Matrix(
                self.species[self.num_ind_species:]
            )

        return self._species_dependent

    @property
    def num_ind_fluxes(self):
        if not self._num_ind_fluxes:
            self._num_ind_fluxes = SMCAtools.get_num_ind_fluxes(self.mod)

        return self._num_ind_fluxes

    @property
    def fluxes(self):
        if not self._fluxes:
            self._fluxes = SMCAtools.get_fluxes_vector(self.mod)

        return self._fluxes

    @property
    def fluxes_independent(self):
        if not self._fluxes_independent:
            self._fluxes_independent = Matrix(
                self.fluxes[:self.num_ind_fluxes]
            )

        return self._fluxes_independent

    @property
    def fluxes_dependent(self):
        if not self._fluxes_dependent:
            self._fluxes_dependent = Matrix(
                self.fluxes[self.num_ind_fluxes:]
            )

        return self._fluxes_dependent

    @property
    def kmatrix(self):
        if not self._kmatrix:
            self._kmatrix = Matrix(self.mod.kmatrix)

        return self._kmatrix

    @property
    def lmatrix(self):
        if not self._lmatrix:
            self._lmatrix = Matrix(self.mod.lmatrix)

        return self._lmatrix

    @property
    def subs_fluxes(self):
        if not self._subs_fluxes:
            self._subs_fluxes = SMCAtools.substitute_fluxes(
                self.fluxes,
                self.kmatrix
            )

        return self._subs_fluxes

    @property
    def scaled_l(self):
        if not self._scaled_l:
            self._scaled_l = SMCAtools.scale_matrix(
                self.species,
                self.lmatrix,
                self.species_independent
            )

        return self._scaled_l

    @property
    def scaled_k(self):
        if not self._scaled_k:
            self._scaled_k = SMCAtools.scale_matrix(
                self.subs_fluxes,
                self.kmatrix,
                self.fluxes_independent
            )
        return self._scaled_k

    @property
    def scaled_l0(self):
        if not self._scaled_l0:
            self._scaled_l0 = self.scaled_l[self.num_ind_species:, :]

        return self._scaled_l0

    @property
    def scaled_k0(self):
        if not self._scaled_k0:
            self._scaled_k0 = self.scaled_k[self.num_ind_fluxes:, :]

        return self._scaled_k0

    @property
    def es_matrix(self):
        if not self._es_matrix:
            self._es_matrix = SMCAtools.get_es_matrix(
                self.mod,
                self.nmatrix,
                self.fluxes,
                self.species
            )

        return self._es_matrix

    @property
    def esL(self):
        if not self._esL:
            self._esL = self.es_matrix * self.scaled_l

        return self._esL

    @property
    def ematrix(self):
        if not self._ematrix:
            self._ematrix = SMCAtools.simplify_matrix(
                self.scaled_k.row_join(
                    -self.esL
                )
            )

        return self._ematrix

    def path_to(self, path):
        full_path = make_path(self.mod, self._analysis_method, [path])
        return full_path

    def export_latex(self):
        self._latex_out.make_main()

    def save(self):
        if not self._object_populated:
            print 'No data to save, run do_symca first'
        else:
            SMCAtools.save(self.CC,
                           self.common_denominator,
                           self._working_dir + 'data.dump'
                           )

    def load(self):
        cc_objects = SMCAtools.load(self.mod,
                                    self._working_dir + 'data.dump'
                                    )

        for cc in cc_objects:
            setattr(self, cc.name, cc)
        self.CC = cc_objects[1:]
        self._object_populated = True

    def do_symca(self):

        CC_i_num, common_denom_expr = SMCAtools.invert(
            self.ematrix,
            self.path_to('temp')
        )

        logging.info('CC_i_num:')
        logging.info(CC_i_num)
        logging.info('common_denom_expr:')
        logging.info(common_denom_expr)

        cc_sol = SMCAtools.solve_dep(
            CC_i_num,
            self.scaled_k0,
            self.scaled_l0,
            self.num_ind_fluxes,
            self.path_to('temp')
        )

        cc_sol, common_denom_expr = SMCAtools.fix_expressions(
            cc_sol,
            common_denom_expr,
            self.lmatrix,
            self.species_independent,
            self.species_dependent
        )

        cc_names = SMCAtools.build_cc_matrix(
            self.fluxes,
            self.fluxes_independent,
            self.species_independent,
            self.fluxes_dependent,
            self.species_dependent
        )

        cc_objects = SMCAtools.spawn_cc_objects(
            self.mod,
            cc_sol,
            cc_names,
            common_denom_expr,
            self._ltxe
        )

        for cc in cc_objects:
            setattr(self, cc.name, cc)
        self.CC = cc_objects[1:]
        self._object_populated = True
        self.CC_i_num = CC_i_num
