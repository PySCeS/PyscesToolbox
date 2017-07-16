import subprocess
from os import devnull
from os.path import join
# from os import mkdir
import sys
#from re import sub
from sympy import Symbol, sympify, nsimplify, fraction, S
from sympy.matrices import Matrix, diag, NonSquareMatrixError
from .ccobjects import CCBase, CCoef
from ...utils.misc import DotDict
from ...utils.misc import formatter_factory
from ...utils import ConfigReader
from ...utils.misc import ec_list, flux_list, ss_species_list


## Everything in this file can be a function rather than a static method
## better yet, almost everything can be part of symca. Finally everything can
## be in a single file.

all = ['SymcaToolBox']


class SymcaToolBox(object):
    """The class with the functions used to populate SymcaData. The project is
    structured in this way to abstract the 'work' needed to build the various
    matrices away from the SymcaData class."""

    @staticmethod
    def get_nmatrix(mod):
        """
        Returns a sympy matrix made from the N matrix in a Pysces model where
        the elements are in the same order as they appear in the k and l
        matrices in pysces.

        We need this to make calculations easier later on.
        """
        nmatrix = mod.nmatrix
        # swap columns around to same order as kmatrix, store in new matrix
        nmatrix_cols = nmatrix[:, mod.kmatrix_row]
        # swap rows around to same oder as lmatrix, store in a new matrix
        nmatrix_cols_rows = nmatrix_cols[mod.lmatrix_row, :]
        # create Sympy symbolic matrix from the numpy ndarray
        nmat = Matrix(nmatrix_cols_rows)
        return nmat

    @staticmethod
    def get_num_ind_species(mod):
        inds = len(mod.lmatrix_col)
        return inds

    @staticmethod
    def get_num_ind_fluxes(mod):
        inds = len(mod.kmatrix_col)
        return inds

    @staticmethod
    def get_species_vector(mod):
        """
        Returns a vector (sympy matrix) with the species in the correct order
        """
        slist = []
        # gets the order of the species from the lmatrix rows
        for index in mod.lmatrix_row:
            slist.append(mod.species[index])

        svector = Matrix(sympify(slist))
        #inds = len(mod.lmatrix_col)
        #Sind = Matrix(svector[:inds])
        #Sdep = Matrix(svector[inds:])
        return svector

    @staticmethod
    def get_fluxes_vector(mod):
        """
        Gets the dependent and independent fluxes (in the correct order)
        """

        jlist = []
        # gets the order of the fluxes from the kmatrix rows
        for index in mod.kmatrix_row:
            jlist.append('J_' + mod.reactions[index])
        jvector = Matrix(sympify(jlist))
        #inds = len(mod.kmatrix_col)
        #Jind = Matrix(jvector[:inds])
        #Jdep = Matrix(jvector[inds:])
        return jvector

    @staticmethod
    def substitute_fluxes(all_fluxes, kmatrix):
        """
        Substitutes equivalent fluxes in the kmatrix (e.i. dependent fluxes
        with independent fluxes or otherwise equal fluxes)
        """
        new_fluxes = all_fluxes[:, :]
        for row in xrange(kmatrix.rows - 1, -1, -1):
            for row_above in xrange(row - 1, -1, -1):
                if kmatrix[row, :] == kmatrix[row_above, :]:
                    new_fluxes[row] = new_fluxes[row_above]
        return new_fluxes

    @staticmethod
    def scale_matrix(all_elements, mat, inds):
        """
        Scales the k or l matrix.

        The procedure is the same for each matrix:
           (D^x)^(-1)   *          y         *        D^(x_i)

        Inverse diagonal   The matrix to be      The diagonal of
        of the x where     scaled. i.e. the      the independent x
        x is either the    k or l matrix         where x is the
        species or the                           species or the
        fluxes                                   fluxes

        """
        d_all_inv = diag(*all_elements).inv()
        d_inds = diag(*inds)
        scaled_matrix = d_all_inv * mat * d_inds
        return scaled_matrix

    @staticmethod
    def get_es_matrix(mod, nmatrix, fluxes, species):
        """
        Gets the esmatrix.

        Goes down the columns of the nmatrix (which holds the fluxes)
        to get the rows of the esmatrix.

        Nested loop goes down the rows of the nmatrix (which holds the species)
        to get the columns of the esmatrix

        so the format is

        ecReationN0_M0 ecReationN0_M1 ecReationN0_M2
        ecReationN1_M0 ecReationN1_M1 ecReationN1_M2
        ecReationN2_M0 ecReationN2_M1 ecReationN2_M2
        """
        nmat = nmatrix

        elas = []

        for col in range(nmat.cols):
            current_reaction = fluxes[col]
            elas_row = []
            for row in range(nmat.rows):
                current_species = species[row]
                ec_name = 'ec' + \
                          str(current_reaction)[2:] + '_' + str(
                    current_species)
                cond1 = getattr(mod, ec_name) != 0

                if cond1:
                    elas_row.append(ec_name)
                else:
                    elas_row.append(0)
            elas.append(elas_row)

        esmatrix = Matrix(elas)
        return esmatrix

    @staticmethod
    def get_es_matrix_no_mca(mod, nmatrix, fluxes, species):
        """
        Gets the esmatrix.

        Goes down the columns of the nmatrix (which holds the fluxes)
        to get the rows of the esmatrix.

        Nested loop goes down the rows of the nmatrix (which holds the species)
        to get the columns of the esmatrix

        so the format is

        ecReationN0_M0 ecReationN0_M1 ecReationN0_M2
        ecReationN1_M0 ecReationN1_M1 ecReationN1_M2
        ecReationN2_M0 ecReationN2_M1 ecReationN2_M2
        """
        nmat = nmatrix

        elas = []
        modifiers = dict(mod.__modifiers__)
        for col in range(nmat.cols):
            current_reaction = fluxes[col]
            elas_row = []
            for row in range(nmat.rows):
                current_species = species[row]
                ec_name = 'ec' + \
                          str(current_reaction)[2:] + '_' + str(
                    current_species)
                cond1 = nmat[row,col] != 0
                cond2 = str(current_species) in modifiers[str(current_reaction)[2:]]
                if cond1 or cond2:
                    elas_row.append(ec_name)
                else:
                    elas_row.append(0)
            elas.append(elas_row)

        esmatrix = Matrix(elas)
        return esmatrix

    @staticmethod
    def simplify_matrix(matrix):
        """
        Replaces floats with ints and puts elements with fractions
        on a single demoninator.
        """
        m = matrix[:, :]
        for i, e in enumerate(m):
            m[i] = nsimplify(e, rational=True).cancel()
        return m

    @staticmethod
    def adjugate_matrix(matrix):
        """
        Returns the adjugate matrix which is the transpose of the
        cofactor matrix.

        Contains code adapted from sympy.
        Specifically:

        cofactorMatrix()
        minorEntry()
        minorMatrix()
        cofactor()
        """

        def cofactor_matrix(mat):
            out = Matrix(mat.rows, mat.cols, lambda i, j:
            cofactor(mat, i, j))
            return out

        def minor_entry(mat, i, j):
            if not 0 <= i < mat.rows or not 0 <= j < mat.cols:
                raise ValueError(
                    "`i` and `j` must satisfy 0 <= i < `mat.rows` " +
                    "(%d)" % mat.rows + "and 0 <= j < `mat.cols` (%d)." % mat.cols)
            return SymcaToolBox.det_bareis(minor_matrix(mat, i, j))

        def minor_matrix(mat, i, j):
            if not 0 <= i < mat.rows or not 0 <= j < mat.cols:
                raise ValueError(
                    "`i` and `j` must satisfy 0 <= i < `mat.rows` " +
                    "(%d)" % mat.rows + "and 0 <= j < `mat.cols` (%d)." % mat.cols)
            m = mat.as_mutable()
            m.row_del(i)
            m.col_del(j)
            return m[:, :]

        def cofactor(mat, i, j):
            if (i + j) % 2 == 0:
                return minor_entry(mat, i, j)
            else:
                return -1 * minor_entry(mat, i, j)

        return cofactor_matrix(matrix).transpose()

    @staticmethod
    def det_bareis(matrix):
        """
        Adapted from original det_bareis function in Sympy 0.7.3.
        cancel() and expand() are removed from function to speed
        up calculations. Maxima will be used to simplify the result

        Original docstring below:

        Compute matrix determinant using Bareis' fraction-free
        algorithm which is an extension of the well known Gaussian
        elimination method. This approach is best suited for dense
        symbolic matrices and will result in a determinant with
        minimal number of fractions. It means that less term
        rewriting is needed on resulting formulae.
        """
        mat = matrix
        if not mat.is_square:
            raise NonSquareMatrixError()

        m, n = mat[:, :], mat.rows

        if n == 1:
            det = m[0, 0]
        elif n == 2:
            det = m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]
        else:
            sign = 1  # track current sign in case of column swap

            for k in range(n - 1):
                # look for a pivot in the current column
                # and assume det == 0 if none is found
                if m[k, k] == 0:
                    for i in range(k + 1, n):
                        if m[i, k] != 0:
                            m.row_swap(i, k)
                            sign *= -1
                            break
                    else:
                        return S.Zero

                # proceed with Bareis' fraction-free (FF)
                # form of Gaussian elimination algorithm
                for i in range(k + 1, n):
                    for j in range(k + 1, n):
                        d = m[k, k] * m[i, j] - m[i, k] * m[k, j]

                        if k > 0:
                            d /= m[k - 1, k - 1]

                        m[i, j] = d

            det = sign * m[n - 1, n - 1]

        return det

    @staticmethod
    def invert(matrix, path_to):
        """
        Returns the numerators of the inverted martix separately from the
        common denominator (the determinant of the matrix)
        """
        common_denom = SymcaToolBox.det_bareis(matrix)
        adjugate = SymcaToolBox.adjugate_matrix(matrix)

        common_denom = SymcaToolBox.maxima_factor(common_denom, path_to)
        #adjugate     = self._maxima_factor('/home/carl/test.txt',adjugate)

        cc_i_sol = adjugate, common_denom
        return cc_i_sol

    @staticmethod
    def maxima_factor(expression, path_to):
        """
        This function is equivalent to the sympy.cancel()
        function but uses maxima instead
        """

        maxima_in_file = join(path_to,'in.txt').replace('\\','\\\\')
        maxima_out_file = join(path_to,'out.txt').replace('\\','\\\\')
        if expression.is_Matrix:
            expr_mat = expression[:, :]
            # print expr_mat
            print 'Simplifying matrix with ' + str(len(expr_mat)) + ' elements'
            for i, e in enumerate(expr_mat):

                sys.stdout.write('*')
                sys.stdout.flush()
                if (i + 1) % 50 == 0:
                    sys.stdout.write(' ' + str(i + 1) + '\n')
                    sys.stdout.flush()
                # print e
                expr_mat[i] = SymcaToolBox.maxima_factor(e, path_to)
            sys.stdout.write('\n')
            sys.stdout.flush()
            return expr_mat
        else:
            batch_string = (
                'stardisp:true;stringout("'
                + maxima_out_file + '",factor(' + str(expression) + '));')
            # print batch_string
            with open(maxima_in_file, 'w') as f:
                f.write(batch_string)

            config = ConfigReader.get_config()
            if config['platform'] == 'win32':
                maxima_command = [config['maxima_path'], '--batch=' + maxima_in_file]
            else:
                maxima_command = ['maxima', '--batch=' + maxima_in_file]

            dn = open(devnull, 'w')
            subprocess.call(maxima_command, stdin=dn, stdout=dn, stderr=dn)
            simplified_expression = ''

            with open(maxima_out_file) as f:
                for line in f:
                    if line != '\n':
                        simplified_expression = line[:-2]
            frac = fraction(sympify(simplified_expression))
            # print frac[0].expand()/frac[1].expand()
            return frac[0].expand() / frac[1].expand()

    @staticmethod
    def solve_dep(cc_i_num, scaledk0, scaledl0, num_ind_fluxes, path_to):
        """
        Calculates the dependent control matrices from the independent control
        matrix CC_i_solution
        """

        j_cci_sol = cc_i_num[:num_ind_fluxes, :]
        s_cci_sol = cc_i_num[num_ind_fluxes:, :]

        j_ccd_sol = scaledk0 * j_cci_sol
        s_ccd_sol = scaledl0 * s_cci_sol

        tempmatrix = j_cci_sol
        for matrix in [j_ccd_sol, s_cci_sol, s_ccd_sol]:
            if len(matrix) != 0:
                tempmatrix = tempmatrix.col_join(matrix)

        cc_sol = tempmatrix

        cc_sol = SymcaToolBox.maxima_factor(cc_sol, path_to)

        # print len(j_cci_sol)
        # print len(j_ccd_sol)
        # print len(s_cci_sol)
        # print len(s_ccd_sol)

        return cc_sol

    @staticmethod
    def build_cc_matrix(j, jind, sind, jdep, sdep):
        """
        Produces the matrices j_cci, j_ccd, s_cci and s_ccd
        which holds the symbols for the independent and dependent flux control
        coefficients and the independent and dependent species control
        coefficients respectively
        """
        j_cci = []
        j_ccd = []
        s_cci = []
        s_ccd = []

        for Ji in jind:
            row = []
            for R in j:
                row.append('ccJ' + str(Ji)[2:] + '_' + str(R)[2:])
            j_cci.append(row)

        for Si in sind:
            row = []
            for R in j:
                row.append('cc' + str(Si) + '_' + str(R)[2:])
            s_cci.append(row)

        for Jd in jdep:
            row = []
            for R in j:
                row.append('ccJ' + str(Jd)[2:] + '_' + str(R)[2:])
            j_ccd.append(row)

        for Sd in sdep:
            row = []
            for R in j:
                row.append('cc' + str(Sd) + '_' + str(R)[2:])
            s_ccd.append(row)

        j_cci = Matrix(j_cci)
        j_ccd = Matrix(j_ccd)
        s_cci = Matrix(s_cci)
        s_ccd = Matrix(s_ccd)

        #cc_i = j_cci.col_join(s_cci)
        tempmatrix = j_cci
        for matrix in [j_ccd, s_cci, s_ccd]:
            if len(matrix) != 0:
                tempmatrix = tempmatrix.col_join(matrix)
        cc = tempmatrix

        # print len(j_cci)
        # print len(j_ccd)
        # print len(s_cci)
        # print len(s_ccd)

        return cc

    @staticmethod
    def get_fix_denom(lmatrix, species_independent, species_dependent):
        num_inds = len(species_independent)
        num_deps = len(species_dependent)
        if num_deps == 0:
            return sympify('1')
        else:
            dependent_ls = lmatrix[num_inds:, :]
            denom = sympify('1')
            for row in range(dependent_ls.rows):
                for each in dependent_ls[row, :] * species_independent * -1:
                    symbol_atoms = each.atoms(Symbol)
                    for symbol_atom in symbol_atoms:
                        if symbol_atom not in denom.atoms(Symbol):
                            denom = denom * symbol_atom
                            #denom = denom * each.atoms(Symbol).pop()
                denom = denom * species_dependent[row]
            return denom.nsimplify()

    def get_fix_denom_jannie(lmatrix, species_independent, species_dependent):
        num_inds = len(species_independent)
        num_deps = len(species_dependent)
        if num_deps == 0:
            return sympify('1')
        else:
            dependent_ls = lmatrix[num_inds:, :]
            denom = sympify('1')
            for row in range(dependent_ls.rows):
                den_new = sympify('1')
                for each in dependent_ls[row, :] * species_independent * -1:
                    symbol_atoms = each.atoms(Symbol)
                    for symbol_atom in symbol_atoms:
                        if den_new == 1:
                            den_new = den_new * symbol_atom
                        else:
                            den_new = den_new + symbol_atom
                            #denom = denom * each.atoms(Symbol).pop()
                if den_new == 1:
                    den_new = den_new * species_dependent[row]
                else:
                    den_new = den_new + species_dependent[row]
                denom = denom * den_new
            return denom.nsimplify()

    @staticmethod
    def fix_expressions(cc_num, common_denom_expr, lmatrix,
                        species_independent, species_dependent):

        fix_denom = SymcaToolBox.get_fix_denom(
            lmatrix,
            species_independent,
            species_dependent
        )
        fix = False
        cd_num, cd_denom = fraction(common_denom_expr)
        ret2 = cd_num


        if type(cc_num) is list:
            new_cc_num = cc_num[:]
        else:
            new_cc_num = cc_num[:, :]

        for i, each in enumerate(new_cc_num):
             new_cc_num[i] = ((each * cd_denom)).expand()

        for each in new_cc_num:
            for symb in fix_denom.atoms(Symbol):
                if symb in each.atoms(Symbol):
                    fix = True
                    break
            if fix: break

        if fix:
            for i, each in enumerate(new_cc_num):
                new_cc_num[i] = (each / fix_denom).expand()

            ret2 = (cd_num / fix_denom).expand()

        return new_cc_num, ret2

    @staticmethod
    def spawn_cc_objects(mod, cc_names, cc_sol, common_denom_exp, ltxe):


        common_denom_object = CCBase(mod,
                                     'common_denominator',
                                     common_denom_exp,
                                     ltxe)
        cc_object_list = [common_denom_object]

        for name, num in zip(cc_names, cc_sol):
            ccoef_object = CCoef(mod,
                                 str(name),
                                 num,
                                 common_denom_object,
                                 ltxe)

            cc_object_list.append(ccoef_object)
        return cc_object_list

    @staticmethod
    def make_internals_dict(cc_sol, cc_names, common_denom_expr, path_to):
        simpl_dic = {}
        for i, each in enumerate(cc_sol):
            expr = each / common_denom_expr
            expr = SymcaToolBox.maxima_factor(expr, path_to)
            num, denom = fraction(expr)
            if not simpl_dic.has_key(denom):
                simpl_dic[denom] = [[], []]
            simpl_dic[denom][0].append(cc_names[i])
            simpl_dic[denom][1].append(num)

        return simpl_dic

    @staticmethod
    def make_CC_dot_dict(cc_objects):
        CC = DotDict()
        for cc in cc_objects:
            CC[cc.name] = cc
        CC._make_repr('"$" + v.latex_name + "$"', 'v.value',
                      formatter_factory())
        return CC


    @staticmethod
    def build_inner_dict(cc_object):
        deep_dict = {}
        for key, value in cc_object.iteritems():
            if key != 'common_denominator':
                deepest_dict = {str(key): str(value.numerator)}
                deep_dict.update(deepest_dict)
        inner_dict = {str(cc_object.common_denominator.expression): deep_dict}
        return inner_dict

    @staticmethod
    def build_outer_dict(symca_object):
        containers = {}
        containers['cc_results'] = SymcaToolBox.build_inner_dict(
            getattr(symca_object, 'cc_results'))
        counter = 0
        while True:
            CC_obj_name = 'cc_results_{0}'.format(counter)
            try:
                CC_obj_dict = getattr(symca_object, CC_obj_name)
            except AttributeError:
                break
            containers[CC_obj_name] = SymcaToolBox.build_inner_dict(
                CC_obj_dict)
            counter += 1
        return containers

    @staticmethod
    def make_inner_dict(cc_container, cc_container_name):
        CC_dict = {}
        CC_dict[cc_container_name] = dict(zip(
            [cc.name for cc in cc_container.values() if
             cc.name is not 'common_denominator'],
            [cc.numerator for cc in cc_container.values() if
             cc.name is not 'common_denominator']))
        CC_dict[cc_container_name]['common_denominator'] = cc_container.common_denominator.expression
        return CC_dict


    @staticmethod
    def generic_populate(mod, function, value = 1):
        names = function(mod)
        for name in names:
            setattr(mod, name, value)

    @staticmethod
    def populate_with_fake_elasticities(mod):
        SymcaToolBox.generic_populate(mod, ec_list)

    @staticmethod
    def populate_with_fake_fluxes(mod):
        SymcaToolBox.generic_populate(mod, flux_list)

    @staticmethod
    def populate_with_fake_ss_concentrations(mod):
        SymcaToolBox.generic_populate(mod, ss_species_list)




        # OLD SAVE FUNCTIONS> Not as good as new ones
        # @staticmethod
        # def save_session(cc_list, common_denominator, path_to_pickle):
        #     mod = common_denominator.mod
        #     common_denominator.mod = ''
        #     for cc in cc_list:
        #         cc.mod = ''
        #         for cp in cc.control_patterns:
        #             cp.mod = ''
        #
        #     cc_list.append(common_denominator)
        #     with open(path_to_pickle, 'w') as f:
        #         pickle.dump(cc_list, f)
        #
        #     cc_list.pop()
        #     common_denominator.mod = mod
        #     for cc in cc_list:
        #         cc.mod = mod
        #         for cp in cc.control_patterns:
        #             cp.mod = mod
        #
        # @staticmethod
        # def load_session(mod, path_to_pickle):
        #     with open(path_to_pickle) as f:
        #         cc_list = pickle.load_session(f)
        #
        #     common_denominator = cc_list.pop()
        #
        #     common_denominator.mod = mod
        #     for cc in cc_list:
        #         cc.mod = mod
        #         for cp in cc.control_patterns:
        #             cp.mod = mod
        #
        #     cc_list.insert(0, common_denominator)
        #     return cc_list
