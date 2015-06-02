import json
from sympy.matrices import Matrix
from sympy import fraction, sympify

from ...modeltools import make_path, get_file_path
from ...latextools import LatexExpr
from .symca_toolbox import SymcaToolBox as SMCAtools
from ...utils.misc import DotDict
from ...utils.misc import formatter_factory
from os import path


all = ['Symca']


class Symca(object):

    def __init__(self, mod, auto_load=False):
        super(Symca, self).__init__()

        self.mod = mod
        self.mod.doMca()

        self._analysis_method = 'symca'
        self._internal_filename = 'object_data'
        self._working_dir = make_path(self.mod, self._analysis_method)
        self._ltxe = LatexExpr(mod)


        self._object_populated = False
        self.CC = DotDict()

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
        if auto_load:
            self.load()

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
        assert len(self.CC) > 0, 'Nothing to save, run ``do_symca`` method first'
        to_save = SMCAtools.build_outer_dict(self)
        with open(file_name,'w') as f:
            json.dump(to_save,f)

    def load(self, file_name=None):
        file_name = get_file_path(working_dir=self._working_dir,
                                  internal_filename=self._internal_filename,
                                  fmt='json',
                                  file_name=file_name,
                                  write_suffix=False)
        loaded = None
        with open(file_name,'r') as f:
            loaded = json.load(f)

        for attr_name, inner_dict in loaded.iteritems():
            setattr(self,attr_name,DotDict())
            dot_dict = getattr(self,attr_name)
            inner_dict = sympify(inner_dict)
            cc_objects = SMCAtools.spawn_cc_objects(
                    self.mod,
                    inner_dict,
                    self._ltxe
                )[0]
            for cc in cc_objects:
                dot_dict[cc.name] = cc
            dot_dict._make_repr('"$" + v.latex_name + "$"', 'v.value', formatter_factory())




    def do_symca(self, auto_save_load=False, internal_fixed=False):
        def do_symca_internals(self):
            CC_i_num, common_denom_expr = SMCAtools.invert(
                self.ematrix,
                self.path_to('temp')
            )

            # logging.info('CC_i_num:')
            # logging.info(CC_i_num)
            # logging.info('common_denom_expr:')
            # logging.info(common_denom_expr)

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

            full_dic = {common_denom_expr: {}}
            for i, each in enumerate(cc_sol):
                full_dic[common_denom_expr][cc_names[i]] =  each
            if internal_fixed:
                simpl_dic = {}
                for i, each in enumerate(cc_sol):
                    expr = each / common_denom_expr
                    expr = SMCAtools.maxima_factor(expr, self.path_to('temp'))
                    num, denom = fraction(expr)
                    if not simpl_dic.has_key(denom):
                        simpl_dic[denom] = {}
                    simpl_dic[denom][cc_names[i]] = num

            cc_objects = SMCAtools.spawn_cc_objects(
                self.mod,
                full_dic,
                self._ltxe
            )[0]

            for cc in cc_objects:
                self.CC[cc.name] = cc
            self.CC._make_repr(
                '"$" + v.latex_name + "$"', 'v.value', formatter_factory())

            if internal_fixed:
                simp_objects_list = SMCAtools.spawn_cc_objects(self.mod,
                                                               simpl_dic,
                                                               self._ltxe)
                cnt = 0
                for block in simp_objects_list:
                    setattr(self, 'CC' + str(cnt), DotDict())
                    dd = getattr(self, 'CC' + str(cnt))
                    for cc in block:
                        dd[cc.name] = cc
                    dd._make_repr(
                        '"$" + v.latex_name + "$"', 'v.value', formatter_factory())
                    cnt += 1
    
            self._object_populated = True
            self.CC_i_num = CC_i_num

        if auto_save_load:
            try:
                self.load()
            except:
                do_symca_internals(self)
                self.save()
        else:
            do_symca_internals(self)
            self.save()


