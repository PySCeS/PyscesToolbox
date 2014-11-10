import numpy as np
import cPickle as pickle

from os import path, mkdir

from pysces.PyscesModelMap import ModelMap
from pysces import Scanner
import pysces
from collections import OrderedDict
from matplotlib.pyplot import get_cmap
from colorsys import hsv_to_rgb, rgb_to_hsv

from .. import modeltools
from ..latextools import LatexExpr
from ..utils.plotting import ScanFig, LineData, Data2D
from ..utils.misc import silence_print
from ..utils.misc import DotDict
from ..utils.misc import formatter_factory
from collections import OrderedDict


exportLAWH = silence_print(pysces.write.exportLabelledArrayWithHeader)


__all__ = ['RateChar']


def strip_nan_from_scan(array_like):
    # this function assumes that column
    # zero contains valid data (the scan input)
    t_f = list(np.isnan(array_like[:, 1]))
    start = t_f.index(False)
    end = len(t_f) - t_f[::-1].index(False)

    return array_like[start:end, :]


class RateChar(object):

    def __init__(self, mod, min_concrange_factor=100,
                 max_concrange_factor=100,
                 scan_points=256,
                 auto_load=False):
        super(RateChar, self).__init__()

        self.mod = mod
        self.mod.SetQuiet()
        self._model_map = ModelMap(mod)
        self.mod.doState()

        self._analysis_method = 'ratechar'
        self._working_dir = modeltools.make_path(self.mod,
                                                 self._analysis_method)

        self._min_concrange_factor = min_concrange_factor
        self._max_concrange_factor = max_concrange_factor
        self._scan_points = scan_points

        self._ltxe = LatexExpr(self.mod)
        for species in self.mod.species:
            setattr(self, species, None)
        if auto_load:
            self.load()

    def do_ratechar(self, fixed='all',
                    scan_min=None,
                    scan_max=None,
                    min_concrange_factor=None,
                    max_concrange_factor=None,
                    scan_points=None,
                    solver=0,
                    auto_save=False):

        # this function wraps _do_scan functionality in a user friendly bubble
        if fixed == 'all':
            to_scan = self.mod.species
        elif type(fixed) is list or type(fixed) is tuple:
            for each in fixed:
                assert each in self.mod.species, 'Invalid species'
            to_scan = fixed
        else:
            assert fixed in self.mod.species, 'Invalid species'
            to_scan = [fixed]

        for each in to_scan:
            fixed_mod, fixed_ss = self._fix_at_ss(each)

            scan_start = self._min_max_chooser(fixed_ss,
                                               scan_min,
                                               min_concrange_factor,
                                               'min')

            scan_end = self._min_max_chooser(fixed_ss,
                                             scan_max,
                                             max_concrange_factor,
                                             'max')
            # here there could be a situation where a scan_min > scan_max
            # I wonder what will happen....

            if not scan_points:
                scan_points = self._scan_points

            column_names, results = self._do_scan(fixed_mod,
                                                  each,
                                                  scan_start,
                                                  scan_end,
                                                  scan_points)

            cleaned_results = strip_nan_from_scan(results)

            rcd = RateCharData(fixed_ss,
                               fixed_mod,
                               self.mod,
                               column_names,
                               cleaned_results,
                               self._model_map,
                               self._ltxe)
            setattr(self, each, rcd)
        if auto_save:
            self.save()

    def _min_max_chooser(self, ss, point, concrange, min_max):
        # chooses a minimum or maximum point based
        # on the information given by a user
        # ie if a specific min/max point is given - use that
        # if only concentration range is given -use that
        # if nothing is given - use the defualt conc_range_factor
        # pretty simple stuff
        if point:
            the_point = point
        if not point and concrange:
            if min_max == 'min':
                the_point = ss / concrange
            elif min_max == 'max':
                the_point = ss * concrange
        if not point and not concrange:
            if min_max == 'min':
                the_point = ss / self._min_concrange_factor
            elif min_max == 'max':
                the_point = ss * self._max_concrange_factor

        return the_point

    @silence_print
    def _do_scan(self,
                 fixed_mod,
                 fixed,
                 scan_min,
                 scan_max,
                 scan_points,
                 solver=0):
        # do scan is a simplified interface to pysces.Scanner
        # more intuitive than Scan1 (functional vs OO??)
        # returns the names of the scanned blocks together with
        # the results of the scan

        assert solver in (0, 1, 2), 'Solver mode can only be one of 0, 1 or 2'

        fixed_mod.mode_solver = solver

        demand_blocks = [
            'J_' + r for r in getattr(self._model_map, fixed).isSubstrateOf()]
        supply_blocks = [
            'J_' + r for r in getattr(self._model_map, fixed).isProductOf()]
        user_output = [fixed] + demand_blocks + supply_blocks

        scanner = Scanner(fixed_mod)
        scanner.quietRun = True
        scanner.addScanParameter(
            fixed, scan_min, scan_max, scan_points, log=True)
        scanner.addUserOutput(*user_output)
        scanner.Run()
        return user_output, scanner.UserOutputResults

    @silence_print
    def _fix_at_ss(self, fixed):
        # fixes the metabolite at the steady_state
        #(calls psctb.modeltools.fix_metabolite)
        # and returns both the ss value and the fixed model
        self.mod.doState()
        fixed_ss = getattr(self.mod, fixed + '_ss')
        fixed_mod = modeltools.fix_metabolite(self.mod, fixed)
        fixed_mod.SetQuiet()
        # i don't like this approach at all, too many possible unintended side
        # effects
        # setattr(fixed_mod, fixed, fixed_ss)
        # setattr(fixed_mod, 'fixed', fixed)
        # setattr(fixed_mod, 'fixed_ss', fixed_ss)
        fixed_mod.doState()
        return fixed_mod, fixed_ss

    def save(self, file_name=None):
        if not file_name:
            file_name = self._working_dir + 'save_data.pickle'

        rcd_data_list = []

        for species in self.mod.species:
            rcd = getattr(self, species)
            if rcd:
                rcd_data = [rcd._column_names,
                            rcd._scan_results]
                rcd_data_list.append(rcd_data)

        try:
            with open(file_name, 'w') as f:
                pickle.dump(rcd_data_list, f)
        except IOError as e:
            print e.strerror


    def save_results(self, folder=None, separator=',', ):
        for species in self.mod.species:
            getattr(self, species).save_results(folder=folder,
                                                separator=separator)

    def load(self, file_name=None):
        if not file_name:
            file_name = self._working_dir + 'save_data.pickle'

        try:
            with open(file_name) as f:
                rcd_data_list = pickle.load(f)

            for rcd_data in rcd_data_list:
                fixed_species = rcd_data[0][0]
                fixed_mod, fixed_ss = self._fix_at_ss(fixed_species)
                rcd = RateCharData(fixed_ss,
                                   fixed_mod,
                                   self.mod,
                                   rcd_data[0],
                                   rcd_data[1],
                                   self._model_map,
                                   self._ltxe)
                setattr(self, fixed_species, rcd)

        except IOError as e:
            print e.strerror


class RateCharData(object):

    def __init__(self,
                 fixed_ss,
                 fixed_mod,
                 basemod,
                 column_names,
                 scan_results,
                 model_map,
                 ltxe):

        super(RateCharData, self).__init__()
        self.mod = fixed_mod

        self.plot_data = DotDict()
        self.mca_data = DotDict()

        self._slope_range_factor = 3.0

        self.plot_data['fixed'] = column_names[0]
        self.plot_data['fixed_ss'] = fixed_ss

        self.plot_data['scan_range'] = scan_results[:, 0]
        self.plot_data['flux_names'] = column_names[1:]
        self.plot_data['flux_data'] = scan_results[:, 1:]
        self.plot_data['scan_points'] = len(self.plot_data.scan_range)
        self.plot_data['flux_max'] = None
        self.plot_data['flux_min'] = None
        self.plot_data['scan_max'] = None
        self.plot_data['scan_min'] = None
        self.plot_data['ec_names'] = None
        self.plot_data['ec_data'] = None
        self.plot_data['rc_names'] = None
        self.plot_data['rc_data'] = None
        self.plot_data['prc_names'] = None
        self.plot_data['prc_data'] = None

        self._column_names = column_names
        self._scan_results = scan_results
        self._model_map = model_map

        self._analysis_method = 'ratechar'
        self._basemod = basemod
        self._working_dir = modeltools.make_path(self._basemod,
                                                 self._analysis_method,
                                                 [self.plot_data.fixed])
        self._ltxe = ltxe

        self._color_dict_ = None
        self._data_setup()
        self.mca_data._ltxe = ltxe
        self.mca_data._make_repr('"$" + self._ltxe.expression_to_latex(k) + "$"', 'v', formatter_factory())
        #del self.plot_data
        #del self.mca_data

    def _data_setup(self):
        # reset value to do mcarc
        setattr(self.mod, self.plot_data.fixed, self.plot_data.fixed_ss)
        self.mod.doMcaRC()
        self._make_attach_total_fluxes()
        self._min_max_setup()
        self._attach_fluxes_to_self()
        self._make_all_coefficient_lines()
        self._attach_all_coefficients_to_self()
        self._make_all_summary()
        self._make_all_line_data()

    def _make_all_line_data(self):
        self._make_flux_ld()
        self._make_ec_ld()
        self._make_rc_ld()
        self._make_prc_ld()
        self._make_total_flux_ld()

        self._line_data_dict = OrderedDict()
        self._line_data_dict.update(self._prc_ld_dict)
        self._line_data_dict.update(self._flux_ld_dict)
        self._line_data_dict.update(self._total_flux_ld_dict)

        self._line_data_dict.update(self._ec_ld_dict)
        self._line_data_dict.update(self._rc_ld_dict)



        del self._flux_ld_dict
        del self._ec_ld_dict
        del self._rc_ld_dict
        del self._prc_ld_dict
        del self._total_flux_ld_dict

    def _make_all_summary(self):
        self._make_ec_summary()
        self._make_cc_summary()
        self._make_rc_summary()
        self._make_prc_summary()

        self.mca_data.update(self._ec_summary)
        self.mca_data.update(self._cc_summary)
        self.mca_data.update(self._rc_summary)
        self.mca_data.update(self._prc_summary)

        del self._ec_summary
        del self._cc_summary
        del self._rc_summary
        del self._prc_summary

    def _make_ec_summary(self):
        ecs = {}
        for flux in self.plot_data.flux_names:
            reaction = flux[2:]
            name = 'ec%s_%s' % (reaction, self.plot_data.fixed)
            val = getattr(self.mod, name)
            ecs[name] = val

        self._ec_summary = ecs

    def _make_rc_summary(self):
        rcs = {}
        for flux in self.plot_data.flux_names:
            reaction = flux[2:]
            name = '%s_%s' % (reaction, self.plot_data.fixed)
            val = getattr(self.mod.rc, name)
            name = 'rcJ' + name
            rcs[name] = val

        self._rc_summary = rcs

    def _make_cc_summary(self):

        ccs = {}
        reagent_of = [each[2:] for each in self.plot_data.flux_names]
        modifier_of = getattr(
            self._model_map, self.plot_data.fixed).isModifierOf()
        all_reactions = reagent_of + modifier_of

        for flux_reaction in reagent_of:
            for reaction in all_reactions:
                name = 'ccJ%s_%s' % (flux_reaction, reaction)
                val = getattr(self.mod, name)
                ccs[name] = val

        self._cc_summary = ccs

    def _make_prc_summary(self):

        prcs = {}

        reagent_of = [each[2:] for each in self.plot_data.flux_names]
        modifier_of = getattr(
            self._model_map, self.plot_data.fixed).isModifierOf()
        all_reactions = reagent_of + modifier_of

        for flux_reaction in reagent_of:
            for route_reaction in all_reactions:
                ec = getattr(self.mod,
                             'ec%s_%s' % (route_reaction, self.plot_data.fixed))

                cc = getattr(self.mod,
                             'ccJ%s_%s' % (flux_reaction, route_reaction))
                val = ec * cc
                name = 'prcJ%s_%s_%s' % (flux_reaction,
                                         self.plot_data.fixed,
                                         route_reaction)

                prcs[name] = val

        self._prc_summary = prcs

    def _save_summary(self, file_name=None, separator=',', folder=None):
        if not file_name:
            if folder:
                if not path.exists(path.join(folder, self.plot_data.fixed)):
                    mkdir(path.join(folder, self.plot_data.fixed))
                file_name = path.join(folder,
                                      self.plot_data.fixed,
                                      'mca_summary.cvs')
            else:
                file_name = path.join(self._working_dir, 'mca_summary.cvs')

        keys = self.mca_data.keys()
        keys.sort()
        values = np.array([self.mca_data[k]
                           for k in keys]).reshape(len(keys), 1)

        try:
            exportLAWH(values,
                       names=keys,
                       header=['Value'],
                       fname=file_name,
                       sep=separator)
        except IOError as e:
            print e.strerror

    def _save_flux_data(self, file_name=None, separator=',', folder=None):
        if not file_name:
            if folder:
                if not path.exists(path.join(folder, self.plot_data.fixed)):
                    mkdir(path.join(folder, self.plot_data.fixed))
                file_name = path.join(folder,
                                      self.plot_data.fixed,
                                      'flux_data.csv')
            else:
                file_name = path.join(self._working_dir,
                                      'flux_data.csv')

        scan_points = self.plot_data.scan_points
        all_cols = np.hstack([
            self._scan_results,
            self.plot_data.total_supply.reshape(scan_points, 1),
            self.plot_data.total_demand.reshape(scan_points, 1)])
        column_names = self._column_names + ['Total Supply', 'Total Demand']

        try:
            exportLAWH(all_cols,
                       names=None,
                       header=column_names,
                       fname=file_name,
                       sep=separator)
        except IOError as e:
            print e.strerror

    def _save_coefficient_data(self,
                               coefficient,
                               file_name=None,
                               separator=',',
                               folder=None):
        assert_message = 'coefficient must be one of "ec", "rc" or "prc"'

        assert coefficient in ['rc', 'ec', 'prc'], assert_message
        if not file_name:
            if folder:
                if not path.exists(path.join(folder, self.plot_data.fixed)):
                    mkdir(path.join(folder, self.plot_data.fixed))
                file_name = path.join(folder,
                                      self.plot_data.fixed,
                                      coefficient + '_data.csv')
            else:
                file_name = path.join(self._working_dir,
                                      coefficient + '_data.csv')

        results = getattr(self.plot_data, coefficient + '_data')
        names = getattr(self.plot_data, coefficient + '_names')
        new_names = []
        for each in names:
            new_names.append('x_vals')
            new_names.append(each)

        try:
            exportLAWH(results,
                       names=None,
                       header=new_names,
                       fname=file_name,
                       sep=separator)
        except IOError as e:
            print e.strerror

    def save_results(self, folder=None, separator=','):
        self._save_flux_data(separator=separator, folder=folder)
        self._save_summary(separator=separator, folder=folder)
        for each in ['ec', 'rc', 'prc']:
            self._save_coefficient_data(coefficient=each,
                                        separator=separator,
                                        folder=folder)

    def _min_max_setup(self):
        # Negative minimum linear values mean nothing
        # because they don't translate to a log space
        # therefore we want the minimum non-negative/non-zero values.

        # lets make sure there are no zeros
        n_z_f = self.plot_data.flux_data[np.nonzero(self.plot_data.flux_data)]
        n_z_s = self.plot_data.scan_range[
            np.nonzero(self.plot_data.scan_range)]

        totals = np.vstack([self.plot_data.total_demand,
                                self.plot_data.total_supply])
        n_z_t = totals[np.nonzero(totals)]
        # and that the array is not now somehow empty
        # although if this happens-you have bigger problems
        if len(n_z_f) == 0:
            n_z_f = np.array([0.01, 1])
        if len(n_z_s) == 0:
            n_z_s = np.array([0.01, 1])

        # lets also (clumsily) find the non-negative mins and maxes
        # by converting to logspace (to get NaNs) and back
        # and then getting the min/max non-NaN
        # PS flux max is the max of the totals

        with np.errstate(invalid='ignore'):

            self.plot_data.flux_max = np.nanmax(10 ** np.log10(totals))
            self.plot_data.flux_min = np.nanmin(10 ** np.log10(n_z_f))
            self.plot_data.scan_max = np.nanmax(10 ** np.log10(n_z_s))
            self.plot_data.scan_min = np.nanmin(10 ** np.log10(n_z_s))

    def _attach_fluxes_to_self(self):
        for i, each in enumerate(self.plot_data.flux_names):
            # setattr(self, each, self.plot_data.flux_data[:, i])
            self.plot_data[each] = self.plot_data.flux_data[:, i]

    def _attach_all_coefficients_to_self(self):
        setup_for = ['ec', 'rc', 'prc']
        for each in setup_for:
            eval('self._attach_coefficients_to_self(self.plot_data.' + each + '_names,\
                                                self.plot_data.' + each + '_data)')

    def _make_all_coefficient_lines(self):
        setup_for = ['ec', 'rc', 'prc']
        for each in setup_for:
            eval('self._make_' + each + '_lines()')

    def _make_attach_total_fluxes(self):
        demand_blocks = getattr(
            self._model_map, self.plot_data.fixed).isSubstrateOf()
        supply_blocks = getattr(
            self._model_map, self.plot_data.fixed).isProductOf()

        dem_pos = [self.plot_data.flux_names.index('J_' + flux)
                   for flux in demand_blocks]
        sup_pos = [self.plot_data.flux_names.index('J_' + flux)
                   for flux in supply_blocks]

        self.plot_data['total_demand'] = np.sum([self.plot_data.flux_data[:, i]
                                                 for i in dem_pos],
                                                axis=0)
        self.plot_data['total_supply'] = np.sum([self.plot_data.flux_data[:, i]
                                                 for i in sup_pos],
                                                axis=0)

    def _make_rc_lines(self):
        names = []
        resps = []

        for each in self.plot_data.flux_names:
            reaction = each[2:]
            name = reaction + '_' + self.plot_data.fixed

            J_ss = getattr(self.mod, each)
            slope = getattr(self.mod.rc, name)
            resp = self._tangent_line(J_ss, slope)

            name = 'rcJ' + name
            names.append(name)
            resps.append(resp)

        resps = np.hstack(resps)

        self.plot_data.rc_names = names
        self.plot_data.rc_data = resps

    def _make_prc_lines(self):
        names = []
        prcs = []

        reagent_of = [each[2:] for each in self.plot_data.flux_names]
        all_reactions = reagent_of + \
            getattr(self._model_map, self.plot_data.fixed).isModifierOf()

        for flux_reaction in self.plot_data.flux_names:

            J_ss = getattr(self.mod, flux_reaction)
            reaction = flux_reaction[2:]

            for route_reaction in all_reactions:

                ec = getattr(
                    self.mod, 'ec' + route_reaction + '_' + self.plot_data.fixed)
                cc = getattr(self.mod, 'ccJ' + reaction + '_' + route_reaction)
                slope = ec * cc

                prc = self._tangent_line(J_ss, slope)
                name = 'prcJ%s_%s_%s' % (reaction,
                                         self.plot_data.fixed,
                                         route_reaction)

                names.append(name)
                prcs.append(prc)

        prcs = np.hstack(prcs)

        self.plot_data.prc_names = names
        self.plot_data.prc_data = prcs

    def _make_ec_lines(self):
        names = []
        elasts = []

        for each in self.plot_data.flux_names:

            reaction = each[2:]
            name = 'ec' + reaction + '_' + self.plot_data.fixed

            J_ss = getattr(self.mod, each)
            slope = getattr(self.mod, name)
            elast = self._tangent_line(J_ss, slope)

            names.append(name)
            elasts.append(elast)

        elasts = np.hstack(elasts)

        self.plot_data.ec_names = names
        self.plot_data.ec_data = elasts

    def _attach_coefficients_to_self(self, names, tangent_lines):
        sp = 0
        ep = 2
        for name in names:
            # setattr(self, name, tangent_lines[:, sp:ep])
            self.plot_data[name] = tangent_lines[:, sp:ep]
            sp = ep
            ep += 2

    def _tangent_line(self, J_ss, slope):

        fix_ss = self.plot_data.fixed_ss

        constant = J_ss / (fix_ss ** slope)

        ydist = np.log10(self.plot_data.flux_max / self.plot_data.flux_min)
        xdist = np.log10(self.plot_data.scan_max / self.plot_data.scan_min)
        golden_ratio = (1 + np.sqrt(5)) / 2
        xyscale = xdist / (ydist * golden_ratio * 1.5)

        scale_factor = np.cos(np.arctan(slope * xyscale))
        distance = np.log10(self._slope_range_factor) * scale_factor

        range_min = fix_ss / (10 ** distance)
        range_max = fix_ss * (10 ** distance)
        scan_range = np.linspace(range_min, range_max, num=2)

        rate = constant * scan_range ** (slope)

        return np.vstack((scan_range, rate)).transpose()

    @property
    def _color_dict(self):
        if not self._color_dict_:
            num_of_cols = len(self.mod.reactions) + 2
            cmap = get_cmap('Set2')(
                np.linspace(0, 1.0, num_of_cols))[:, :3]
            color_list = [rgb_to_hsv(*cmap[i, :]) for i in range(num_of_cols)]
            fix_map = getattr(self._model_map, self.plot_data.fixed)
            relavent_reactions = fix_map.isProductOf() + \
                                 fix_map.isSubstrateOf() + \
                                 fix_map.isModifierOf()
            relavent_reactions.sort()
            color_dict = dict(
                zip(['Total Supply'] +
                    ['J_' + reaction for reaction in relavent_reactions] +
                    ['Total Demand'],
                    color_list))
            # just to darken the colors a bit
            for k, v in color_dict.iteritems():
                color_dict[k] = [v[0], v[1], v[2] * 0.9]

            self._color_dict_ = color_dict

        return self._color_dict_

    def _make_flux_ld(self):
        color_dict = self._color_dict

        flux_ld_dict = {}

        demand_blocks = ['J_' + dem_reac for dem_reac in getattr(
            self._model_map, self.plot_data.fixed).isSubstrateOf()]
        supply_blocks = ['J_' + sup_reac for sup_reac in getattr(
            self._model_map, self.plot_data.fixed).isProductOf()]

        for flux in self.plot_data.flux_names:
            flux_col = self.plot_data.flux_names.index(flux)
            x_data = self.plot_data.scan_range
            y_data = self.plot_data.flux_data[:, flux_col]
            latex_expr = self._ltxe.expression_to_latex(flux)
            flux_color = self._color_dict[flux]
            color = hsv_to_rgb(flux_color[0],
                               1,
                               flux_color[2])
            for dem in demand_blocks:
                if dem == flux:
                    flux_ld_dict[flux] = \
                        LineData(name=flux,
                                 x_data=x_data,
                                 y_data=y_data,
                                 categories=['Fluxes',
                                             'Demand',
                                             flux],
                                 properties={'label': '$%s$' % latex_expr,
                                             'color': color})
                    break
            for sup in supply_blocks:
                if sup == flux:
                    flux_ld_dict[flux] = \
                        LineData(name=flux,
                                 x_data=x_data,
                                 y_data=y_data,
                                 categories=['Fluxes',
                                             'Supply',
                                             flux],
                                 properties={'label': '$%s$' % latex_expr,
                                             'color': color})
                    break
        self._flux_ld_dict = flux_ld_dict

    def _make_ec_ld(self):
        ec_ld_dict = {}

        for ec_name in self.plot_data.ec_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                ec_reaction = flux[2:]
                if ec_reaction in ec_name:
                    flux_color = self._color_dict[flux]
                    color = hsv_to_rgb(flux_color[0],
                                       flux_color[1],
                                       flux_color[2])
                    ec_data = self.plot_data[ec_name]
                    categories = ['Elasticity Coefficients'] + \
                        flux_ld.categories[1:]
                    latex_expr = self._ltxe.expression_to_latex(ec_name)

                    ec_ld_dict[ec_name] = \
                        LineData(name=ec_name,
                                 x_data=ec_data[:, 0],
                                 y_data=ec_data[:, 1],
                                 categories=categories,
                                 properties={'label': '$%s$' % latex_expr,
                                             'color': color})
        self._ec_ld_dict = ec_ld_dict

    def _make_rc_ld(self):
        rc_ld_dict = {}

        for rc_name in self.plot_data.rc_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                rc_flux = 'J' + flux[2:]
                if rc_flux in rc_name:
                    flux_color = self._color_dict[flux]
                    color = hsv_to_rgb(flux_color[0],
                                       flux_color[1],
                                       flux_color[2] * 0.7)
                    rc_data = self.plot_data[rc_name]
                    categories = ['Response Coefficients'] + \
                        flux_ld.categories[1:]
                    latex_expr = self._ltxe.expression_to_latex(rc_name)

                    rc_ld_dict[rc_name] = \
                        LineData(name=rc_name,
                                 x_data=rc_data[:, 0],
                                 y_data=rc_data[:, 1],
                                 categories=categories,
                                 properties={'label': '$%s$' % latex_expr,
                                             'color': color,
                                             'ls': '--'})
        self._rc_ld_dict = rc_ld_dict

    def _make_prc_ld(self):

        def get_prc_route(prc, flux, fixed):
            without_prefix = prc.split('prc')[1]
            without_flux = without_prefix.split(flux)[1][1:]
            route = without_flux.split(fixed)[1][1:]
            return route

        prc_ld_dict = {}

        for prc_name in self.plot_data.prc_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                prc_flux = 'J' + flux[2:]
                if prc_flux in prc_name:

                    route_reaction = get_prc_route(prc_name,
                                                   prc_flux,
                                                   self.plot_data.fixed)
                    flux_color = self._color_dict['J_' + route_reaction]
                    color = hsv_to_rgb(flux_color[0],
                                       1,
                                       flux_color[2] * 0.9)
                    prc_data = self.plot_data[prc_name]
                    categories = ['Partial Response Coefficients'] + \
                        flux_ld.categories[1:]
                    latex_expr = self._ltxe.expression_to_latex(prc_name)

                    prc_ld_dict[prc_name] = \
                        LineData(name=prc_name,
                                 x_data=prc_data[:, 0],
                                 y_data=prc_data[:, 1],
                                 categories=categories,
                                 properties={'label': '$%s$' % latex_expr,
                                             'color': color})
        self._prc_ld_dict = prc_ld_dict

    def _make_total_flux_ld(self):
        total_flux_ld_dict = {}
        col = self._color_dict['Total Supply']
        total_flux_ld_dict['Total Supply'] = \
            LineData(name='Total Supply',
                     x_data=self.plot_data.scan_range,
                     y_data=self.plot_data.total_supply,
                     categories=['Fluxes',
                                 'Supply',
                                 'Total Supply'],
                     properties={'label': '$%s$' % 'Total\,Supply',
                                 'color': hsv_to_rgb(col[0],col[1]*2,col[2])})

        col = self._color_dict['Total Demand']
        total_flux_ld_dict['Total Demand'] = \
            LineData(name='Total Demand',
                     x_data=self.plot_data.scan_range,
                     y_data=self.plot_data.total_demand,
                     categories=['Fluxes',
                                 'Demand',
                                 'Total Demand'],
                     properties={'label': '$%s$' % 'Total\,Demand',
                                 'color': hsv_to_rgb(col[0],col[1]*2,col[2])})

        self._total_flux_ld_dict = total_flux_ld_dict

    def plot(self):

        category_classes = OrderedDict([
            ('Supply/Demand', [
                'Supply',
                'Demand']),
            ('Reaction Blocks',
             self.plot_data.flux_names +
             ['Total Supply', 'Total Demand']),
            ('Lines', [
                'Fluxes',
                'Elasticity Coefficients',
                'Response Coefficients',
                'Partial Response Coefficients'])])

        line_data_list = [v for v in self._line_data_dict.itervalues()]

        scan_fig = ScanFig(line_data_list,
                           ax_properties={'xlabel': '[%s]' %
                                          self.plot_data.fixed.replace(
                                              '_', ' '),
                                          'ylabel': 'Rate',
                                          'xscale': 'log',
                                          'yscale': 'log',
                                          'xlim':  [self.plot_data.scan_min,
                                                    self.plot_data.scan_max],
                                          'ylim':  [self.plot_data.flux_min,
                                                    self.plot_data.flux_max * 2
                                                    ]},
                           category_classes=category_classes,
                           fname = path.join(self._working_dir,'rate_char'))

        scan_fig.toggle_category('Supply', True)
        scan_fig.toggle_category('Demand', True)
        scan_fig.toggle_category('Fluxes', True)
        scan_fig.ax.axvline(self.plot_data.fixed_ss, ls=':', color='gray')

        return scan_fig

    @silence_print
    def plot_decompose(self):
        ecs = []
        ccs = []
        prc_names = []
        rc_names = []
        rc_pos = []

        reagent_of = [each[2:] for each in self.plot_data.flux_names]
        all_reactions = reagent_of + \
            getattr(self._model_map, self.plot_data.fixed).isModifierOf()


        arl = len(all_reactions)
        strt = 0
        stp = arl
        for flux_reaction in self.plot_data.flux_names:
            reaction = flux_reaction[2:]
            rc_names.append('rcJ%s_%s' % (reaction, self.plot_data.fixed))

            rc_pos.append(range(strt,stp))
            strt += arl
            stp += arl

            for route_reaction in all_reactions:

                ec = 'ec' + route_reaction + '_' + self.plot_data.fixed
                cc = 'ccJ' + reaction + '_' + route_reaction

                name = 'prcJ%s_%s_%s' % (reaction,
                                         self.plot_data.fixed,
                                         route_reaction)

                ecs.append(ec)
                ccs.append(cc)
                prc_names.append(name)

        user_output = [self.plot_data.fixed] + ecs + ccs
        print user_output

        scanner = pysces.Scanner(self.mod)
        scanner.quietRun = True
        scanner.addScanParameter(self.plot_data.fixed,
                                 self.plot_data.scan_min,
                                 self.plot_data.scan_max,
                                 self.plot_data.scan_points,
                                 log=True)
        scanner.addUserOutput(*user_output)
        scanner.Run()

        ax_properties = {'ylabel':'Coefficient Value',
                         'xlabel': '[%s]' %
                         self.plot_data.fixed.replace('_', ' '),
                         'xscale': 'log',
                         'yscale': 'linear',
                         'xlim': [self.plot_data.scan_min,self.plot_data.scan_max]}

        cc_ec_data_obj = Data2D(self.mod,
                           user_output,
                           scanner.UserOutputResults,
                           self._ltxe,
                           self._analysis_method,
                           ax_properties,
                           'cc_ec_scan')

        rc_data = []
        for i, prc_name in enumerate(prc_names):
            outs = scanner.UserOutputResults[:, 1:]
            cc_s_pos = len(prc_names)
            ec_col_data = outs[:, i]
            cc_col_data = outs[:, i + cc_s_pos]
            col = ec_col_data * cc_col_data
            rc_data.append(col)

        temp = np.vstack(rc_data).transpose()
        rc_data += [np.sum(temp[:,rc_pos[i]],axis=1) for i in range(len(rc_names))]

        rc_out_arr = [scanner.UserOutputResults[:, 0]] + rc_data
        rc_out_arr = np.vstack(rc_out_arr).transpose()

        rc_data_obj = Data2D(self.mod,
                         [self.plot_data.fixed] + prc_names + rc_names,
                         rc_out_arr,
                         self._ltxe,
                         self._analysis_method,
                         ax_properties,
                         'prc_scan')
        rc_data_obj._working_dir = path.split(path.split(self._working_dir)[0])[0]
        cc_ec_data_obj._working_dir = path.split(path.split(self._working_dir)[0])[0]
        # for plot in [cc_ec_plt, prc_plt]:
        #     plot.ax.set_xscale('log')
        #     plot.ax.set_ylabel('Coefficient Value')
        #     plot.ax.set_xlim([self.plot_data.scan_min,
        #                       self.plot_data.scan_max])

        # prc_plt.ax.axvline(self.plot_data.fixed_ss, ls=':', color='gray')
        # #prc_plt.ax.set_ylim([-5,5])
        # cc_ec_plt.ax.axvline(self.plot_data.fixed_ss, ls=':', color='gray')
        # #cc_ec_plt.ax.set_ylim([-5,5])

        return rc_data_obj, cc_ec_data_obj

##########################################
'''
TODO:
fix this metadata story
and create LineData objects

idea:

setup linedata in one function.. setup colormap here as well
so something like:

cmap =  number of colors corresponding with number of fluxes
for each line that we should draw
    if line_type is flux:
        color = color out of cmap
    elif ec:
        darker
    etc

    line = LineData(bla bla bla)
    lines.append(line)


categories:

Supply demand

Flux, Elasticity coefficients, Partial Response coefficients, Response coefficients

Reaction Name




'''
