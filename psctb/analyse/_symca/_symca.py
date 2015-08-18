import json
from sympy.matrices import Matrix
from sympy import sympify

from ...utils.misc import extract_model
from ...modeltools import make_path, get_file_path
from ...latextools import LatexExpr
from .symca_toolbox import SymcaToolBox as SMCAtools


all = ['Symca']


class Symca(object):
    def __init__(self, mod, auto_load=False, internal_fixed = False):
        super(Symca, self).__init__()

        self.mod, obj_type = extract_model(mod)
        self.mod.doMca()

        self._analysis_method = 'symca'
        self._internal_filename = 'object_data'
        self._working_dir = make_path(self.mod, self._analysis_method)
        self._ltxe = LatexExpr(self.mod)

        self.CC = None

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

        self.internal_fixed = internal_fixed
        if obj_type == 'RateCharData':
            self.internal_fixed = True
        if auto_load:
            try:
                self.load()
            except:
                print 'Nothing to load: Run `do_symca` first'

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

    def save(self, file_name=None):
        file_name = get_file_path(working_dir=self._working_dir,
                                  internal_filename=self._internal_filename,
                                  fmt='json',
                                  file_name=file_name,
                                  write_suffix=False)

        assert self.CC, 'Nothing to save, run ``do_symca`` method first'
        main_cc_dict = SMCAtools.make_inner_dict(self.CC, 'CC')
        counter = 0
        while True:
            cc_container_name = 'CC{0}'.format(counter)
            try:
                cc_container = getattr(self, cc_container_name)
                main_cc_dict.update(
                    SMCAtools.make_inner_dict(cc_container, cc_container_name))
                counter += 1
            except:
                break

        to_save = main_cc_dict
        with open(file_name, 'w') as f:
            json.dump(to_save, f)

    def load(self, file_name=None):
        file_name = get_file_path(working_dir=self._working_dir,
                                  internal_filename=self._internal_filename,
                                  fmt='json',
                                  file_name=file_name,
                                  write_suffix=False)

        with open(file_name, 'r') as f:
                main_cc_dict = json.load(f)

        cc_containers = {}
        for key, value in main_cc_dict.iteritems():
            common_denom_exp = sympify(value.pop('common_denominator'))
            cc_container = SMCAtools.spawn_cc_objects(self.mod,
                                                      value.keys(),
                                                      [sympify(exp) for exp in
                                                       value.values()],
                                                      common_denom_exp,
                                                      self._ltxe)
            cc_containers[key] = SMCAtools.make_CC_dot_dict(cc_container)
        for key, value in cc_containers.iteritems():
            setattr(self,key,value)



    def do_symca(self, internal_fixed=False, auto_save_load = True):
        if not internal_fixed:
            internal_fixed = self.internal_fixed

        def do_symca_internals(self):
            CC_i_num, common_denom_expr = SMCAtools.invert(
                self.ematrix,
                self.path_to('temp')
            )

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

            cc_objects = SMCAtools.spawn_cc_objects(self.mod,
                                                    cc_names,
                                                    cc_sol,
                                                    common_denom_expr,
                                                    self._ltxe)

            self.CC = SMCAtools.make_CC_dot_dict(cc_objects)

            if internal_fixed:
                simpl_dic = SMCAtools.make_internals_dict(cc_sol,
                                                          cc_names,
                                                          common_denom_expr,
                                                          self.path_to('temp'))

                CC_block_counter = 0
                for each_common_denom_expr, name_num in simpl_dic.iteritems():
                    simpl_cc_objects = SMCAtools.spawn_cc_objects(self.mod,
                                                                  name_num[0],
                                                                  name_num[1],
                                                                  each_common_denom_expr,
                                                                  self._ltxe, )

                    CC_dot_dict = SMCAtools.make_CC_dot_dict(simpl_cc_objects)
                    setattr(self, 'CC%s' % CC_block_counter, CC_dot_dict)
                    CC_block_counter += 1

            self.CC_i_num = CC_i_num

        if auto_save_load:
            try:
                self.load()
            except:
                do_symca_internals(self)
                self.save()
        else:
            do_symca_internals(self)


