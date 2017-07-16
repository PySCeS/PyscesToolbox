import cPickle as pickle
from sympy.matrices import Matrix
from sympy import sympify
import sys

from ...utils.misc import extract_model
from ...utils.misc import get_filename_from_caller
from ...modeltools import make_path, get_file_path
from ...latextools import LatexExpr
from .symca_toolbox import SymcaToolBox as SMCAtools
from numpy import savetxt, array
from ...utils import ConfigReader
import warnings


all = ['Symca']

class Symca(object):
    """
    A class that performs Symbolic Metabolic Control Analysis.

    This class takes pysces model as an input and performs symbolic inversion
    of the ``E matrix`` using ``Sympy`` by calculating the determinant and
    adjoint matrices of this ``E matrix``.

    Parameters
    ----------
    mod : PysMod
        The pysces model on which to perform symbolic control analysis.
    auto_load : boolean
        If true

    Returns
    ------
    """

    def __init__(self, mod, auto_load=False, internal_fixed=False, ignore_steady_state=False, keep_zero_elasticities=True):
        super(Symca, self).__init__()
        ConfigReader.get_config()

        self._ignore_steady_state = ignore_steady_state
        self._keep_zero_ecs = keep_zero_elasticities
        self.mod, obj_type = extract_model(mod)
        if not self._ignore_steady_state:
            self.mod.doMca()
        else:
            warnings.warn_explicit("\nIgnoring steady-state solution: Steady-state variables set to 1. Note that parameter scan functionality is unavailable.",
                                   Warning,
                                   filename=get_filename_from_caller(),
                                   lineno=36)
            SMCAtools.populate_with_fake_elasticities(mod)
            SMCAtools.populate_with_fake_fluxes(mod)
            SMCAtools.populate_with_fake_ss_concentrations(mod)

        self._analysis_method = 'symca'
        self._internal_filename = 'object_data'
        self._working_dir = make_path(self.mod, self._analysis_method)
        self._ltxe = LatexExpr(self.mod)

        self.cc_results = None

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
                self.load_session()
            except:
                print 'Nothing to load_session: Run `do_symca` first'

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
            if self._ignore_steady_state or self._keep_zero_ecs:
                es_method = SMCAtools.get_es_matrix_no_mca
            else:
                es_method = SMCAtools.get_es_matrix
            self._es_matrix = es_method(
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

    def save_session(self, file_name=None):
        file_name = get_file_path(working_dir=self._working_dir,
                                  internal_filename=self._internal_filename,
                                  fmt='pickle',
                                  file_name=file_name,
                                  write_suffix=False)

        assert self.cc_results, 'Nothing to save_session, run ``do_symca`` method first'
        main_cc_dict = SMCAtools.make_inner_dict(self.cc_results, 'cc_results')
        counter = 0
        while True:
            cc_container_name = 'cc_results_{0}'.format(counter)
            try:
                cc_container = getattr(self, cc_container_name)
                main_cc_dict.update(
                    SMCAtools.make_inner_dict(cc_container, cc_container_name))
                counter += 1
            except:
                break

        to_save = main_cc_dict
        with open(file_name, 'w') as f:
            pickle.dump(to_save, f)

    def load_session(self, file_name=None):
        file_name = get_file_path(working_dir=self._working_dir,
                                  internal_filename=self._internal_filename,
                                  fmt='pickle',
                                  file_name=file_name,
                                  write_suffix=False)

        with open(file_name, 'r') as f:
            main_cc_dict = pickle.load(f)

        cc_containers = {}
        for key, value in main_cc_dict.iteritems():
            common_denom_exp = value.pop('common_denominator')
            cc_container = SMCAtools.spawn_cc_objects(self.mod,
                                                      value.keys(),
                                                      [exp for exp in
                                                       value.values()],
                                                      common_denom_exp,
                                                      self._ltxe)
            cc_containers[key] = SMCAtools.make_CC_dot_dict(cc_container)
        for key, value in cc_containers.iteritems():
            setattr(self, key, value)

    def save_results(self, file_name=None, separator=',',fmt='%.9f'):
        file_name = get_file_path(working_dir=self._working_dir,
                                  internal_filename='cc_summary',
                                  fmt='csv',
                                  file_name=file_name, )

        rows = []
        cc_counter = 0
        cc_dicts = [self.cc_results]
        max_len = 0

        while True:
            try:
                next_dict = getattr(self, 'cc_results_%s' % cc_counter)
                cc_dicts.append(next_dict)
                cc_counter += 1
            except:
                break

        sep = ('######################', 0, '', '')
        cc_counter = -1
        for cc_dict in cc_dicts:
            result_name = '# results from cc_results'
            if cc_counter >= 0:
                result_name += '_%s' % cc_counter
            head = (result_name, 0, '', '')
            rows.append(head)
            for cc_name in sorted(cc_dict.keys()):
                cc_obj = cc_dict[cc_name]

                row_1 = (cc_obj.name,
                         cc_obj.value,
                         cc_obj.latex_name,
                         cc_obj.latex_expression)

                expr_len = len(cc_obj.latex_expression)
                if expr_len > max_len:
                    max_len = expr_len
                rows.append(row_1)
                if not cc_obj.name == 'common_denominator':
                    for cp in cc_obj.control_patterns.itervalues():
                        cols = (cp.name,
                                cp.value,
                                cp.latex_name,
                                cp.latex_expression)
                        rows.append(cols)
            rows.append(sep)
            cc_counter += 1

        str_fmt = 'S%s' % max_len
        head = ['name', 'value', 'latex_name', 'latex_expression']
        X = array(rows,
                  dtype=[(head[0], str_fmt),
                         (head[1], 'float'),
                         (head[2], str_fmt),
                         (head[3], str_fmt)])

        try:
            savetxt(fname=file_name,
                    X=X,
                    header=separator.join(head),
                    delimiter=separator,
                    fmt=['%s', fmt, '%s', '%s'],)

        except IOError as e:
            print e.strerror

    def do_symca(self, internal_fixed=None, auto_save_load=False):
        if internal_fixed is None:
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

            self.cc_results = SMCAtools.make_CC_dot_dict(cc_objects)

            if internal_fixed:
                simpl_dic = SMCAtools.make_internals_dict(cc_sol,
                                                          cc_names,
                                                          common_denom_expr,
                                                          self.path_to('temp'))

                CC_block_counter = 0
                for each_common_denom_expr, name_num in simpl_dic.iteritems():
                    name_num[1], \
                        each_common_denom_expr = SMCAtools.fix_expressions(
                        name_num[1],
                        each_common_denom_expr,
                        self.lmatrix,
                        self.species_independent,
                        self.species_dependent
                    )

                    simpl_cc_objects = SMCAtools.spawn_cc_objects(self.mod,
                                                                  name_num[0],
                                                                  name_num[1],
                                                                  each_common_denom_expr,
                                                                  self._ltxe, )

                    CC_dot_dict = SMCAtools.make_CC_dot_dict(simpl_cc_objects)
                    setattr(self, 'cc_results_%s' %
                            CC_block_counter, CC_dot_dict)
                    CC_block_counter += 1

            self.CC_i_num = CC_i_num

        if auto_save_load:
            try:
                self.load_session()
            except:
                do_symca_internals(self)
                self.save_session()
        else:
            do_symca_internals(self)
