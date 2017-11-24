import copy
import warnings
from os import path

import numpy as np
import pandas as pd
from pysces import Scanner, ParScanner
from pysces import model as pysces_model
from matplotlib import pyplot as plt

from .misc import scanner_range_setup, DotDict, cc_dict, rc_dict, ec_dict, prc_dict, is_parameter, is_species, \
    is_mca_coef, silence_print

__all__ = ['compare_models',
           'SteadyStateComparer',
           'SimulationComparer',
           'ParameterScanComparer',
           'ClosedOpenComparer']

def compare_models(model_list, model_mapping = None, augment_mapping=True, comparison_type = 'ss'):
    """
    Returns a specified model comparer for a list of models.

    The returned model comparer object considers the first model in
    `model_list` as the "base model" to which the other models are
    compared. Since models may have a different naming scheme for
    reactions, species, etc. `model_mapping` allows the user to specify
    the names of attributes of other models as they relate to the base
    model's attribute names.

    Parameters
    ----------
    model_list : list of PysMod
        A list of PysMod (Pysces model) objects to be compared.
    model_mapping : array, optional (Default : None)
        An array that maps the names attributes of the base model to
        others. Each column relates to a different model in `model_list`
        in order. The first column contains the names of attributes of
        the base model, whereas each other column contains the name as
        it appears in the other models. Only species, reactions and
        parameters are needed as other attributes (e.g. control
        coefficients) are derived from these three categories. If None
        is supplied, all attributes are assumed to be named in the
        same way.
    augment_mapping : boolean, optional (Default : True)
        This parameter specifies if `model_mapping` should be used to
        augment a model_mapping which assumes all attributes are named
        in the same way. This is useful if only a few model attributes
        differ in their naming. If set to false, `model_mapping` must
        specify the relationships between all species, reaction and
        parameter names.
    comparison_type : str, optional (Default : "ss")
        A string that specifies which type of comparison should be made.
        Options are 'ss' for SteadyStateComparer, "parscan" for
        ParameterScanComparer, 'sim' for SimulationComparer, and
        'closed_open' for 'ClosedOpenComparer'.

    Returns
    -------
    values: ModelComparer
        A model comparer object instantiated with the arguments supplied
        above.
    """
    if comparison_type == 'ss':
        comparer = SteadyStateComparer
    elif comparison_type == 'parscan':
        comparer = ParameterScanComparer
    elif comparison_type == 'sim':
        comparer = SimulationComparer
    elif comparison_type == 'closed_open':
        comparer = ClosedOpenComparer
    else:
        raise AssertionError, 'Incorrect comparison_type'
    return  comparer(model_list, model_mapping, augment_mapping)


class ModelMapper(object):
    @staticmethod
    def map_models(model_list, model_mapping=None, augment_mapping=True):
        # Replace duplicate models with clones
        model_list = ModelMapper.replace_with_clones(model_list)
        base_model = model_list[0]

        # Generate unique model names
        model_names = ModelMapper.generate_unique_model_names(model_list)

        if augment_mapping and model_mapping is not None:
            augment_map_dict_list = ModelMapper.make_map_dict_list(model_mapping)
            model_mapping = None
        else:
            augment_map_dict_list = None

        # Generate model mapping if needed
        if model_mapping is None:
            model_mapping = ModelMapper.auto_map_models(model_list)

        # Ensure that supplied (or generated) model mapping
        # at least has the correct shape
        assert model_mapping.shape[1] == len(model_list)

        # Make list of model_dicts
        map_dict_list = ModelMapper.make_map_dict_list(model_mapping)

        if augment_map_dict_list:
            for map_dict, augment_map_dict in zip(map_dict_list,
                                                  augment_map_dict_list):
                map_dict.update(augment_map_dict)

        # Get newly fixed parameters for other models
        fixed_param_list = [None]
        for i, map_dict in enumerate(map_dict_list[1:]):
            i = 1 + i
            fixed_params = ModelMapper.get_now_fixed(base_model,
                                                     model_list[i],
                                                     map_dict)
            fixed_param_list.append(fixed_params)

        # Add mca coefficients to model_dicts
        base_mca_dict = ModelMapper.make_mca_dict(base_model)
        for map_dict in map_dict_list:
            mca_map_dict = ModelMapper.get_mca_dict_mapping(base_mca_dict,
                                                            map_dict)
            map_dict.update(mca_map_dict)

        model_map_params = zip(model_list, model_names,
                               map_dict_list, fixed_param_list)

        model_maps = []
        for model, model_name, map_dict, fixed_params in model_map_params:
            model_maps.append(ModelMap(model, model_name,
                                       map_dict, fixed_params))

        return model_maps

    @staticmethod
    def make_map_dict_list(mapping_array):
        """
        For a model mapping array, returns a list of dictionaries where
        the keys correspond to the fist column and the values correspond to
        each column (including the first). A 4 column array will thus produce
        a list of dicts of len 4 with the first having the same keys
        as values.
        """
        base_vals = mapping_array[:, 0]
        comp_vals = mapping_array[:, 1:]
        dict_mapping = [dict(zip(base_vals, base_vals))]
        for col in comp_vals.T:
            dict_mapping.append(dict(zip(base_vals, col)))
        return dict_mapping

    @staticmethod
    def replace_with_clones(model_list):
        """
        For a list of models potentially containing duplicate PySMod
        instantiations, returns a list of unique objects.
        """
        new_model_list = []
        for model in model_list:
            if model in new_model_list:
                new_model_list.append(ModelMapper.clone_model(model))
            else:
                new_model_list.append(model)
        return new_model_list

    @staticmethod
    def generate_unique_model_names(model_list):
        """
        Returns a list of unique model names for a list of models.
        """
        model_names = [path.split(model.ModelFile)[-1][:-4] \
                       for model in model_list]

        for i, model_name in enumerate(model_names):
            indices = [j for j, v in enumerate(model_names) \
                       if v == model_name]
            if len(indices) > 1:
                for j, index in enumerate(indices):
                    model_names[index] = model_name + '_' + str(j)
        return model_names

    @staticmethod
    def auto_map_models(model_list):
        """
        For a list of models returns an array where each column maps contains
        the names of model attributes as they appear in each model. Missing
        species, parameters, and reactions are replaced with None.
        """
        base_model = model_list[0]
        comparison_models = model_list[1:]

        base_attributes = list(base_model.species) + \
                          list(base_model.reactions) + \
                          list(base_model.parameters)

        mapping_array = [base_attributes]
        for model in comparison_models:
            match_attributes = [attr if hasattr(model, attr) \
                                    else None \
                                for attr in base_attributes]
            mapping_array.append(match_attributes)
        return np.array(mapping_array).T

    @staticmethod
    def clone_model(model):
        """
        Given a model this method returns a new instantiation of the same
        model.

        See also:
        replace_with_clones
        """
        new_model_path = path.join(model.ModelDir,
                                   model.ModelFile)
        new_model = pysces_model(new_model_path)
        return new_model

    @staticmethod
    def get_mca_dict_mapping(mca_dict, map_dict):
        """
        Given an mca dictionary of the base model and a map dictionary of any
        comparison model, this returns a dictionary that maps the names of
        mca coefficients in the base model to those in the comparison.

        See also:
        get_equiv_coeff
        """
        return {k: ModelMapper.get_equiv_coeff(k, mca_dict, map_dict)
                for k in mca_dict.iterkeys()}

    @staticmethod
    def get_equiv_coeff(coeff, mca_dict, map_dict):
        """
        Given an mca coefficient, an mca dictionary of the base model and a map
        dictionary of any comparison model, this returns the name of the
        equivalent mca coefficient in the comparison model.

        See also:
        get_mca_dict_mapping
        """
        coeff_type = ModelMapper.get_coeff_type(coeff)
        coeff_components = mca_dict[coeff]
        equiv_components = [map_dict[component] for component \
                            in coeff_components]
        if None in equiv_components:
            return None
        else:
            if coeff_type in ['cc', 'prc', 'rc']:
                prefix = coeff_type + 'J'
            else:
                prefix = coeff_type
            if coeff_type == 'prc':
                return prefix + '{}_{}_{}'.format(*equiv_components)
            else:
                return prefix + '{}_{}'.format(*equiv_components)

    @staticmethod
    def make_mca_dict(model):
        """
        Returns a dictionary with the mca coefficients of a model as keys
        and a tuple of the components that make up each coefficient as values.
        """
        full_dict = {}
        full_dict.update(ec_dict(model))
        full_dict.update(cc_dict(model))
        full_dict.update(rc_dict(model))
        full_dict.update(prc_dict(model))
        return full_dict

    @staticmethod
    def get_coeff_type(coefficient):
        """
        Returns the coefficient type.
        """
        if coefficient.startswith('prc'):
            return 'prc'
        elif coefficient.startswith('rc'):
            return 'rc'
        elif coefficient.startswith('ec'):
            return 'ec'
        elif coefficient.startswith('cc'):
            return 'cc'

    @staticmethod
    def get_now_fixed(base_model, comparison_model, map_dict):
        now_fixed_list = []
        for k, v in map_dict.iteritems():
            if is_species(k, base_model) and is_parameter(v, comparison_model):
                now_fixed_list.append(k)
        return now_fixed_list


class ModelMap(object):
    def __init__(self, model, model_name, attr_dict, is_now_fixed=None):
        self.model = model
        self.model_name = model_name
        self.attr_dict = attr_dict
        self._rev_attr_dict = ModelMap._reverse_dict(self.attr_dict)
        if not is_now_fixed:
            is_now_fixed = []
        self.is_now_fixed = is_now_fixed

    @staticmethod
    def _reverse_dict(dict_):
        return {v: k for k, v in dict_.iteritems()}

    def getattrname(self, key):
        prefix, suffix, key = ModelMap._prefix_suffix_getter(key)
        attr = self.attr_dict[key]
        if attr is None:
            return None
        elif key in self.is_now_fixed:
            return attr
        else:
            return prefix + attr + suffix

    def hasattr(self, item):
        _, _, item = ModelMap._prefix_suffix_getter(item)
        if item in self.attr_dict.keys():
            return True
        else:
            return False

    def setattr(self, key, value):
        if self.hasattr(key):
            true_key = self.getattrname(key)
            if true_key is not None and hasattr(self.model, true_key):
                setattr(self.model, true_key, value)

    def getattr(self, item):
        true_key = self.getattrname(item)
        if true_key is None:
            return np.NaN
        else:
            return getattr(self.model, true_key)

    def attr_names_from_base_names(self, key_list, include_nones=False):
        converted_attrs = []
        for key in key_list:
            true_attr = self.getattrname(key)
            if true_attr is None:
                if include_nones:
                    converted_attrs.append(true_attr)
            else:
                converted_attrs.append(true_attr)
        return converted_attrs

    def base_names_from_attr_names(self, attr_list, add_ss = False):
        new_attr_list = [ModelMap._prefix_suffix_getter(attr) for \
                         attr in attr_list]
        for i, p_s_a in enumerate(new_attr_list):
            prefix, suffix, attr = p_s_a
            base_attr = self._rev_attr_dict[attr]
            if base_attr in self.is_now_fixed and add_ss:
                suffix = '_ss'
                new_attr_list[i] = (prefix, suffix, attr)

        converted_attrs = [prefix + self._rev_attr_dict[attr] + suffix for \
                           prefix, suffix, attr in new_attr_list]
        return converted_attrs

    def setattrs_from_dict(self, attr_dict):
        for key, value in attr_dict.iteritems():
            self.setattr(key, value)

    def getattrs_from_list(self, attr_list):
        return [self.getattr(key) for key in attr_list]

    @staticmethod
    def _prefix_suffix_getter(key):
        prefix = ''
        suffix = ''
        flux_prefix = 'J_'
        ssconc_suffix = '_ss'
        init_prefix = '_init'
        if key.startswith(flux_prefix):
            key = key[2:]
            prefix = flux_prefix
        elif key.endswith(ssconc_suffix):
            key = key[:-3]
            suffix = ssconc_suffix
        elif key.endswith(init_prefix):
            key = key[:-5]
            suffix = init_prefix
        return prefix, suffix, key


class ResultsGenerator(object):
    @staticmethod
    def percentage_change(a, b, abs_values = False):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if abs_values:
                return np.divide(np.abs(np.subtract(b, a)), np.abs(a)) * 100
            else:
                return np.divide(np.subtract(b, a), a) * 100

    @staticmethod
    def do_par_scan(model, scan_in, scan_out, start, end, points, is_log_range, par_scan, par_engine):
        if par_scan:
            scanner = ParScanner(model, engine=par_engine)
        else:
            scanner = Scanner(model)
        scan_out = [str(each) for each in scan_out]
        scanner.addScanParameter(scan_in, start=start, end=end, points=points, log=is_log_range)
        scanner.addUserOutput(*scan_out)
        scanner.Run()
        result = scanner.getResultMatrix()
        return result

    @staticmethod
    def do_simulation(model, time_range, sim_out):
        model.sim_time = time_range
        model.Simulate(userinit=1)
        results, labels = model.data_sim.getAllSimData(lbls=True)
        sim_out = ['Time'] + sim_out
        sim_out_index = [labels.index(out_label) for out_label in sim_out]
        results_to_keep = results[:,sim_out_index]
        return results_to_keep


class BaseModelComparer(object):
    def __init__(self, model_list, model_mapping=None, augment_mapping=True):
        super(BaseModelComparer, self).__init__()
        assert len(model_list) > 1, 'Two or more models are needed to make a comparison'

        self.mmap_list = ModelMapper.map_models(model_list=model_list,
                                                model_mapping=model_mapping,
                                                augment_mapping=augment_mapping)

        self.raw_data = None
        self.comparison = None

    @silence_print
    def do_compare(self, output_list=None, custom_init=None, uniform_init=True):
        """
        Performs the comparison of the models.

        Results are stored in `self.raw_data` and `self.comparison`.

        Parameters
        ----------
        output_list : list of str, optional (Default : None)
            A list of model attributes to compare. Valid options are:
            species, reactions, parameters, and mca coefficients.
        custom_init : dict or list of dict, optional (Default : None)
            A dictionary specifying the initial conditions of the models.
            Keys specify model attributes (in str) and values are float
            values of these attributes. A list of dictionaries can also
            be supplied in order to give each model a different set of
            initial conditions. The list follows the same order as
            the `model_list` supplied during object instantiation.
        uniform_init : boolean, optional (Default : True)
            If set to True, the attributes of each model will be set to
            that of the base model prior to comparison. `custom_inits`
            are applied after making model attributes uniform.
        """
        if output_list is None:
            output_list = self._get_default_outputs()

        self._uniform_init(uniform_init)
        self._custom_init(custom_init)
        self._generate_raw_data(output_list)
        self._compare_raw_data()

    @silence_print
    def _get_default_outputs(self):
        base_model = self.mmap_list[0].model
        return list(base_model.species) + list(base_model.reactions)

    @silence_print
    def _custom_init(self, custom_init):
        if custom_init:
            if type(custom_init) is dict:
                for mmap in self.mmap_list:
                    mmap.setattrs_from_dict(custom_init)
            elif type(custom_init) is list:
                num_of_models = len(self.mmap_list)
                all_dicts = all([type(each) is dict for each in custom_init])
                correct_num_of_dicts = len(custom_init) == num_of_models
                assert all_dicts and correct_num_of_dicts, \
                    "list of custom inits must contain {} dictionaries".format(num_of_models)
                for custom_init_dict, mmap in zip(custom_init, self.mmap_list):
                    mmap.setattrs_from_dict(custom_init_dict)
            else:
                raise AssertionError, "custom_inits must be a dictionary or a list of dictionaries"

    @silence_print
    def _uniform_init(self, uniform_init):
        if uniform_init:
            base_model = self.mmap_list[0].model
            base_parameter_dict = {k:getattr(base_model, k) for k in base_model.parameters}
            base_species_dict = {k:getattr(base_model, k) for k in base_model.species}

            base_attribute_dict = {}
            base_attribute_dict.update(base_parameter_dict)
            base_attribute_dict.update(base_species_dict)

            for mmap in self.mmap_list[1:]:
                mmap.setattrs_from_dict(base_attribute_dict)

    def _compare_raw_data(self):
        raise NotImplementedError

    def _generate_raw_data(self, output_list):
        raise NotImplementedError

    @silence_print
    def _output_to_ss(self, output_list):
        base_model = self.mmap_list[0].model
        new_out_list = []
        for each in output_list:
            if each in base_model.species:
                new_out_list.append(each + '_ss')
            elif each in base_model.reactions:
                new_out_list.append('J_' + each)
            else:
                new_out_list.append(each)
        return new_out_list


class SteadyStateComparer(BaseModelComparer):
    @silence_print
    def _generate_raw_data(self, output_list):
        output_list = self._output_to_ss(output_list)
        all_results = []

        base_model = self.mmap_list[0].model
        state_method = 'mca' if any([is_mca_coef(attr, base_model) for attr in output_list]) else 'ss'

        for mmap in self.mmap_list:
            if state_method == 'mca':
                mmap.model.doMca()
            else:
                mmap.model.doState()
            model_results = [mmap.getattr(attr) for attr in output_list]
            all_results.append(model_results)
        all_results = np.array(all_results).T
        self.raw_data = pd.DataFrame(data=all_results,
                                     columns=[mmap.model_name for mmap in self.mmap_list],
                                     index=output_list)

    @silence_print
    def _compare_raw_data(self):
        raw_data = self.raw_data
        data_matrix = raw_data.as_matrix()
        reference_values = data_matrix[:,0]
        change_values = data_matrix[:,1:]

        comparison_names = []
        all_results = []
        for i, change_col in enumerate(change_values.T):
            comparison_name = '{}_{}'.format(self.mmap_list[0].model_name,
                                             self.mmap_list[i+1].model_name)

            comparison_names.append(comparison_name)
            comparison_result = ResultsGenerator.percentage_change(reference_values,
                                                                   change_col)
            all_results.append(comparison_result)

        all_results = np.array(all_results).T
        self.comparison = pd.DataFrame(data=all_results,
                                       columns=comparison_names,
                                       index=raw_data.index)


class ParameterScanComparer(BaseModelComparer):
    @silence_print
    def do_compare(self, scan_in, scan_range, output_list=None, custom_init=None,
                   uniform_init=True, par_scan=False, par_engine='multiproc'):
        """
        Performs the comparison of the models.

        Results are stored in `self.raw_data` and `self.comparison`.

        Parameters
        ----------
        scan_in : str
            A string that specifies the parameter to be varied
        scan_range : array-like
            An array that specifies the range of values over which
            `scan_in` should be varied
        output_list : list of str, optional (Default : None)
            A list of model attributes to compare. Valid options are:
            species, reactions, parameters, and mca coefficients.
        custom_init : dict or list of dict, optional (Default : None)
            A dictionary specifying the initial conditions of the models.
            Keys specify model attributes (in str) and values are float
            values of these attributes. A list of dictionaries can also
            be supplied in order to give each model a different set of
            initial conditions. The list follows the same order as
            the `model_list` supplied during object instantiation.
        uniform_init : boolean, optional (Default : True)
            If set to True, the attributes of each model will be set to
            that of the base model prior to comparison. `custom_inits`
            are applied after making model attributes uniform.
        par_scan : boolean, optional (Default : False)
            If True the parameter scan will be executed using parallel
            processing.
        par_enging: str, optional (Default : 'multiproc')
            The parallel engine to be used. Options are dictated by
            PySCeS's ParScanner.
        """
        if output_list is None:
            output_list = self._get_default_outputs()
        self._uniform_init(uniform_init)
        self._custom_init(custom_init)

        self._generate_raw_data(scan_in, output_list, scan_range, par_scan, par_engine)
        self._compare_raw_data()

    @silence_print
    def _generate_raw_data(self, scan_in, output_list, scan_range, par_scan, par_engine):
        output_list = self._output_to_ss(output_list)
        main_column_labels = [scan_in] + output_list
        start, end, points, is_log_range = scanner_range_setup(scan_range)

        all_results = DotDict()
        for i, mmap in enumerate(self.mmap_list):
            current_scan_in = mmap.getattrname(scan_in)
            current_scan_out = mmap.attr_names_from_base_names(output_list)
            current_col_labels = [scan_in] + mmap.base_names_from_attr_names(current_scan_out, add_ss=True)

            # parameter scan
            raw_result = ResultsGenerator.do_par_scan(model=mmap.model,
                                                      scan_in=current_scan_in,
                                                      scan_out=current_scan_out,
                                                      start=start,
                                                      end=end,
                                                      points=points,
                                                      is_log_range=is_log_range,
                                                      par_scan=par_scan,
                                                      par_engine=par_engine)

            complete_results = pd.DataFrame(data=raw_result,
                                            columns=current_col_labels)
            complete_results = complete_results.reindex(columns=main_column_labels)
            complete_results = complete_results.set_index(scan_in)
            all_results[mmap.model_name] = complete_results
        self.raw_data = all_results

    @silence_print
    def _compare_raw_data(self):
        raw_data = self.raw_data
        reference_model_name = self.mmap_list[0].model_name
        reference_matrix = raw_data[reference_model_name].reset_index().as_matrix()
        column_labels = raw_data[reference_model_name].reset_index().columns

        all_results = DotDict()
        for mmap in self.mmap_list[1:]:
            current_model_name = mmap.model_name
            comparison_name = '{}_{}'.format(reference_model_name,
                                             current_model_name)
            change_matrix = raw_data[current_model_name].reset_index().as_matrix()

            comparison_result = ResultsGenerator.percentage_change(reference_matrix[:,1:],change_matrix[:,1:])
            comparison_result = np.hstack([reference_matrix[:,0][:,np.newaxis],comparison_result])
            df = pd.DataFrame(data=comparison_result,
                              columns=column_labels)
            index = df.columns[0]
            df = df.set_index(index)
            all_results[comparison_name] = df
        self.comparison = all_results


    def plot(self,cols=3, width=None, height=None):
        """
        Produces a simple plot that allows for the visual comparison of
        results for each model.


        Parameters
        ----------
        cols : int, optional (Default : 3)
            The number of columns to use when plotting subplots.
        width : float, optional (Default : 15.0)
            The width of the figure in inches.
        height : float, optional (Default : 5.0*number of subplot rows)
            The height of the figure in inches. By default the height is
            dynamic in will be adjusted based on the number of rows of
            subplots where each row is assigned 5 inches.
        Returns
        -------
        f: matplotlib figure
            A matplotlib figure on which results are plotted.
        axxarr: 2-dimensional numpy array of AxesSubplots
            An array that contains the axes associate with the figure.
        """
        columns = self.raw_data.values()[0].columns
        index = self.raw_data.values()[0].index

        assert cols >= 2
        rows = int(np.ceil(len(columns)/float(cols)))

        if not height:
            height = 5.*rows
        if not width:
            width = 15.

        f, axarr = plt.subplots(rows,cols)
        f.set_size_inches(w=width, h=height)

        for i in xrange(cols*rows - len(columns)):
            f.delaxes(axarr.flat[-1-i])

        for column, ax in zip(columns,axarr.flat):
            for k, v in self.raw_data.iteritems():
                ax.plot(index, v[column], '-',label=k)
            ax.set_xlabel(index.name)
            ax.set_title(column)
            ax.legend()
        return f,axarr


class SimulationComparer(ParameterScanComparer):
    @silence_print
    def do_compare(self, time_range, output_list=None, custom_init=None,
                   uniform_init=True):
        """
        Performs the comparison of the models.

        Results are stored in `self.raw_data` and `self.comparison`.

        Parameters
        ----------
        time_range : array-like
            An array that specifies the range of values over which
            `Time` should be varied. It allows for starting points other
            than zero.
        output_list : list of str, optional (Default : None)
            A list of model attributes to compare. Valid options are:
            species, reactions, parameters, and mca coefficients.
        custom_init : dict or list of dict, optional (Default : None)
            A dictionary specifying the initial conditions of the models.
            Keys specify model attributes (in str) and values are float
            values of these attributes. A list of dictionaries can also
            be supplied in order to give each model a different set of
            initial conditions. The list follows the same order as
            the `model_list` supplied during object instantiation.
        uniform_init : boolean, optional (Default : True)
            If set to True, the attributes of each model will be set to
            that of the base model prior to comparison. `custom_inits`
            are applied after making model attributes uniform.
        """
        if output_list is None:
            output_list = self._get_default_outputs()
        self._uniform_init(uniform_init)
        self._custom_init(custom_init)

        self._generate_raw_data(output_list, time_range)
        self._compare_raw_data()

    @silence_print
    def _generate_raw_data(self, output_list, time_range):
        main_column_labels = ['Time'] + output_list
        all_results = DotDict()
        for i, mmap in enumerate(self.mmap_list):

            now_fixed_indicies = []
            for i,out in enumerate(output_list):
                if out in mmap.is_now_fixed:
                    now_fixed_indicies.append(i)
            new_output_list = copy.deepcopy(output_list)
            param_cols = []
            for ind in reversed(now_fixed_indicies):
                out_val = mmap.getattr(output_list[ind])
                new_output_list.pop(ind)
                param_cols.append([out_val for _ in xrange(time_range.shape[0])])
            param_cols = param_cols

            current_sim_out = mmap.attr_names_from_base_names(new_output_list)

            real_sim_out = mmap.attr_names_from_base_names(output_list)
            current_col_labels = ['Time'] + mmap.base_names_from_attr_names(real_sim_out )

            # parameter scan
            raw_result = ResultsGenerator.do_simulation(model=mmap.model,
                                                        time_range=time_range,
                                                        sim_out=current_sim_out)

            new_raw_result = [col for col in raw_result.T]
            for ind, col in zip(reversed(now_fixed_indicies), param_cols):
                new_raw_result.insert(ind, col)
            new_raw_result = np.array(new_raw_result).T

            complete_results = pd.DataFrame(data=new_raw_result,
                                            columns=current_col_labels)

            complete_results = complete_results.reindex(columns=main_column_labels)
            complete_results = complete_results.set_index('Time')
            all_results[mmap.model_name] = complete_results
        self.raw_data = all_results


class ClosedOpenComparer(SimulationComparer):
    @silence_print
    def do_compare(self, time_range, output_list=None, custom_init=None,
                   uniform_init=True):
        """
        Performs the comparison of the models.

        Results are stored in `self.raw_data` and `self.comparison`.

        Parameters
        ----------
        time_range : array-like
            An array that specifies the range of values over which
            `Time` should be varied. It allows for starting points other
            than zero.
        output_list : list of str, optional (Default : None)
            A list of model attributes to compare. Valid options are:
            species, reactions, parameters, and mca coefficients.
        custom_init : dict or list of dict, optional (Default : None)
            A dictionary specifying the initial conditions of the models.
            Keys specify model attributes (in str) and values are float
            values of these attributes. A list of dictionaries can also
            be supplied in order to give each model a different set of
            initial conditions. The list follows the same order as
            the `model_list` supplied during object instantiation.
        uniform_init : boolean, optional (Default : True)
            If set to True, the attributes of each model will be set to
            that of the base model prior to comparison. `custom_inits`
            are applied after making model attributes uniform.
        """
        if output_list is None:
            output_list = self._get_default_outputs()
        self._uniform_init(uniform_init)
        self._custom_init(custom_init)

        self._generate_raw_data(output_list, time_range)
        self._compare_raw_data()

    @silence_print
    def _generate_raw_data(self, output_list, time_range):
        base_mmap = self.mmap_list[0]
        full_scan_column_names = []
        for mmap in self.mmap_list:
            full_scan_column_names = full_scan_column_names + mmap.is_now_fixed
        full_scan_column_names = list(set(full_scan_column_names))
        base_sim_out_list = full_scan_column_names + [out for out in output_list \
                                                      if out not in full_scan_column_names]
        base_column_names = ['Time'] + base_sim_out_list

        all_results = DotDict()
        simulation_results = ResultsGenerator.do_simulation(model=base_mmap.model,
                                                            time_range=time_range,
                                                            sim_out=base_sim_out_list)
        base_complete_results = pd.DataFrame(data=simulation_results,
                                             columns=base_column_names)
        base_complete_results = base_complete_results.set_index('Time')
        all_results[base_mmap.model_name] = base_complete_results

        for i, mmap in enumerate(self.mmap_list[1:]):
            scan_column_names = mmap.is_now_fixed
            output_partial = [out for out in output_list if out not in scan_column_names]
            outputs = self._output_to_ss(output_partial)
            output_col_names = ['Time'] + scan_column_names + output_partial

            time_col = base_complete_results.reset_index()['Time'].as_matrix()
            input_val_list = [base_complete_results[col_name].as_matrix() for col_name in scan_column_names]
            raw_results = []
            for input_vals in zip(*input_val_list):
                current_row = [] + list(input_vals)
                dict_to_set = dict(zip(scan_column_names, input_vals))
                mmap.setattrs_from_dict(dict_to_set)
                mmap.model.doState()
                current_row = current_row + mmap.getattrs_from_list(outputs)
                raw_results.append(current_row)
            raw_results = np.hstack((time_col[:,np.newaxis],np.array(raw_results)))
            complete_results = pd.DataFrame(data=raw_results,
                                            columns=output_col_names)
            complete_results = complete_results.reindex(columns=base_column_names)
            complete_results = complete_results.set_index('Time')
            all_results[mmap.model_name] = complete_results
        self.raw_data = all_results


