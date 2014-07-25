import pysces
import numpy as np
import os
import sys
import cPickle as pickle

from pysces.PyscesModelMap import ModelMap

from collections import OrderedDict
from matplotlib.pyplot import get_cmap
from colorsys import hsv_to_rgb, rgb_to_hsv

from .. import modeltools
from ..latextools import LatexExpr
from ..utils.plotting import ScanFig, LineData
from ..utils.misc import silence_print

__all__ = ['RateChar']


# def silence_print(func):
#     def wrapper(*args, **kwargs):
#         stdout = sys.stdout
#         sys.stdout = open(os.devnull, 'w')
#         returns = func(*args, **kwargs)
#         sys.stdout = stdout
#         return returns
#     return wrapper


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
        self._working_dir = modeltools.make_path(
            self.mod, self._analysis_method)

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
    def _do_scan(self, fixed_mod, fixed, scan_min, scan_max, scan_points, solver=0):
        # do scan is a simplified interface to pysces.Scanner
        # waaay more intuitive than Scan1 (functional vs OO??)
        # returns the names of the scanned blocks together with
        # the results of the scan

        assert solver in (0, 1, 2), 'Solver mode can only be one of 0, 1 or 2'

        fixed_mod.mode_solver = solver

        demand_blocks = [
            'J_' + r for r in getattr(self._model_map, fixed).isSubstrateOf()]
        supply_blocks = [
            'J_' + r for r in getattr(self._model_map, fixed).isProductOf()]
        user_output = [fixed] + demand_blocks + supply_blocks

        scanner = pysces.Scanner(fixed_mod)
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
        #setattr(fixed_mod, fixed, fixed_ss)
        #setattr(fixed_mod, 'fixed', fixed)
        #setattr(fixed_mod, 'fixed_ss', fixed_ss)
        fixed_mod.doState()
        return fixed_mod, fixed_ss

    def save(self, file_name=None):
        if not file_name:
            file_name = self._working_dir + 'save_data.pickle'

        save_data = []
        temp_mod_list = []

        # remove all PyscesModel object instances before saving
        for species in self.mod.species:
            rcd = getattr(self, species)
            if rcd:
                temp_mod_list.append(rcd.mod)
                rcd.mod = None
                rcd._ltxe = None
                rcd._basemod = None
            else:
                temp_mod_list.append(None)

            save_data.append(rcd)

        try:
            with open(file_name, 'w') as f:
                pickle.dump(save_data, f)
        except IOError as e:
            print e.strerror

        # add everything back
        for i, species in enumerate(self.mod.species):
            rcd = getattr(self, species)
            if rcd:
                rcd.mod = temp_mod_list[i]
                rcd._ltxe = self._ltxe
                rcd._basemod = self.mod

    def load(self, file_name=None):
        if not file_name:
            file_name = self._working_dir + 'save_data.pickle'

        try:
            with open(file_name) as f:
                save_data = pickle.load(f)

            for rcd in save_data:
                if rcd:
                    rcd._basemod = self.mod
                    rcd.mod = self._fix_at_ss(rcd.fixed)[0]
                    rcd._ltxe = self._ltxe
                    setattr(self, rcd.fixed, rcd)
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

        self._slope_range_factor = 3.0

        self.fixed = column_names[0]
        self.fixed_ss = fixed_ss

        self.scan_range = scan_results[:, 0]
        self.flux_names = column_names[1:]
        self.flux_data = scan_results[:, 1:]
        self.scan_points = len(self.scan_range)

        self._column_names = column_names
        self._scan_results = scan_results
        self._model_map = model_map

        self._analysis_method = 'ratechar'
        self._basemod = basemod
        self._working_dir = modeltools.make_path(self._basemod,
                                                 self._analysis_method,
                                                 [self.fixed])
        self._ltxe = ltxe

        self._color_dict_ = None
        self._data_setup()

    def _data_setup(self):
        # reset value to do mcarc
        setattr(self.mod, self.fixed, self.fixed_ss)
        self.mod.doMcaRC()
        self._min_max_setup()
        self._attach_fluxes_to_self()
        self._make_attach_total_fluxes()
        self._make_all_coefficient_lines()
        self._attach_all_coefficients_to_self()
        self._make_all_summary()
        self._make_all_line_data()

    def save_summary(self):
        pass

    def _make_all_line_data(self):
        self._make_flux_ld()
        self._make_ec_ld()
        self._make_rc_ld()
        self._make_prc_ld()
        self._make_total_flux_ld()

        self._line_data_dict = {}
        self._line_data_dict.update(self._flux_ld_dict)
        self._line_data_dict.update(self._ec_ld_dict)
        self._line_data_dict.update(self._rc_ld_dict)
        self._line_data_dict.update(self._prc_ld_dict)
        self._line_data_dict.update(self._total_flux_ld_dict)

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
        self._summary = {}
        self._summary.update(self._ec_summary)
        self._summary.update(self._cc_summary)
        self._summary.update(self._rc_summary)
        self._summary.update(self._prc_summary)
        del self._ec_summary
        del self._cc_summary
        del self._rc_summary
        del self._prc_summary

    def _make_ec_summary(self):
        ecs = {}
        for flux in self.flux_names:
            reaction = flux[2:]
            name = 'ec%s_%s' % (reaction, self.fixed)
            val = getattr(self.mod, name)
            ecs[name] = val

        self._ec_summary = ecs

    def _make_rc_summary(self):
        rcs = {}
        for flux in self.flux_names:
            reaction = flux[2:]
            name = '%s_%s' % (reaction, self.fixed)
            val = getattr(self.mod.rc, name)
            name = 'rcJ' + name
            rcs[name] = val

        self._rc_summary = rcs

    def _make_cc_summary(self):

        ccs = {}
        reagent_of = [each[2:] for each in self.flux_names]
        modifier_of = getattr(self._model_map, self.fixed).isModifierOf()
        all_reactions = reagent_of + modifier_of

        for flux_reaction in reagent_of:
            for reaction in all_reactions:
                name = 'ccJ%s_%s' % (flux_reaction, reaction)
                val = getattr(self.mod, name)
                ccs[name] = val

        self._cc_summary = ccs

    def _make_prc_summary(self):

        prcs = {}

        reagent_of = [each[2:] for each in self.flux_names]
        modifier_of = getattr(self._model_map, self.fixed).isModifierOf()
        all_reactions = reagent_of + modifier_of

        for flux_reaction in reagent_of:
            for route_reaction in all_reactions:
                ec = getattr(self.mod,
                             'ec%s_%s' % (route_reaction, self.fixed))

                cc = getattr(self.mod,
                             'ccJ%s_%s' % (flux_reaction, route_reaction))
                val = ec * cc
                name = 'prcJ%s_%s_%s' % (flux_reaction,
                                         self.fixed,
                                         route_reaction)

                prcs[name] = val

        self._prc_summary = prcs

    @silence_print
    def save_flux_data(self, file_name=None, separator=','):
        if not file_name:
            file_name = self._working_dir + 'flux_data.csv'

        scan_points = self.scan_points
        all_cols = np.hstack([
            self._scan_results,
            self.total_supply.reshape(scan_points, 1),
            self.total_demand.reshape(scan_points, 1)])
        column_names = self._column_names + ['Total Supply', 'Total Demand']

        try:
            pysces.write.exportLabelledArrayWithHeader(all_cols,
                                                       names=None,
                                                       header=column_names,
                                                       fname=file_name,
                                                       sep=separator)
        except IOError as e:
            print e.strerror

    @silence_print
    def save_coefficient_data(self, coefficient, file_name=None, separator=','):
        assert_message = 'coefficient must be one of "ec", "rc" or "prc"'

        assert coefficient in ['rc', 'ec', 'prc'], assert_message
        if not file_name:
            file_name = self._working_dir + coefficient + '_data.csv'

        results = getattr(self, coefficient + '_data')
        names = getattr(self, coefficient + '_names')
        new_names = []
        for each in names:
            new_names.append('x_vals')
            new_names.append(each)

        try:
            pysces.write.exportLabelledArrayWithHeader(results,
                                                       names=None,
                                                       header=new_names,
                                                       fname=file_name,
                                                       sep=separator)
        except IOError as e:
            print e.strerror

    def save_data(self, separator=','):
        self.save_flux_data(separator=separator)
        for each in ['ec', 'rc', 'prc']:
            self.save_coefficient_data(coefficient=each,
                                       separator=separator)

    def _min_max_setup(self):
        # Negative minimum linear values mean nothing
        # because they don't translate to a log space
        # therefore we want the minimum non-negative/non-zero values.

        # lets make sure there are no zeros
        n_z_f = self.flux_data[np.nonzero(self.flux_data)]
        n_z_s = self.scan_range[np.nonzero(self.scan_range)]
        # and that the array is not now somehow empty
        # although if this happens-you have bigger problems
        if len(n_z_f) == 0:
            n_z_f = np.array([0.01, 1])
        if len(n_z_s) == 0:
            n_z_s = np.array([0.01, 1])

        # lets also (clumsily) find the non-negative mins and maxes
        # by converting to logspace (to get NaNs) and back
        # and then getting the min/max non-NaN
        with np.errstate(invalid='ignore'):
            self.flux_max = np.nanmax(10 ** np.log10(n_z_f))
            self.flux_min = np.nanmin(10 ** np.log10(n_z_f))
            self.scan_max = np.nanmax(10 ** np.log10(n_z_s))
            self.scan_min = np.nanmin(10 ** np.log10(n_z_s))

    def _attach_fluxes_to_self(self):
        for i, each in enumerate(self.flux_names):
            setattr(self, each, self.flux_data[:, i])

    def _attach_all_coefficients_to_self(self):
        setup_for = ['ec', 'rc', 'prc']
        for each in setup_for:
            eval('self._attach_coefficients_to_self(self.' + each + '_names,\
                                                self.' + each + '_data)')

    def _make_all_coefficient_lines(self):
        setup_for = ['ec', 'rc', 'prc']
        for each in setup_for:
            eval('self._make_' + each + '_lines()')

    def _make_attach_total_fluxes(self):
        demand_blocks = getattr(self._model_map, self.fixed).isSubstrateOf()
        supply_blocks = getattr(self._model_map, self.fixed).isProductOf()

        dem_pos = [self.flux_names.index('J_' + flux)
                   for flux in demand_blocks]
        sup_pos = [self.flux_names.index('J_' + flux)
                   for flux in supply_blocks]

        self.total_demand = np.sum([self.flux_data[:, i] for i in dem_pos],
                                   axis=0)
        self.total_supply = np.sum([self.flux_data[:, i] for i in sup_pos],
                                   axis=0)

    def _make_rc_lines(self):
        names = []
        resps = []

        for each in self.flux_names:
            reaction = each[2:]
            name = reaction + '_' + self.fixed

            J_ss = getattr(self.mod, each)
            slope = getattr(self.mod.rc, name)
            resp = self._tangent_line(J_ss, slope)

            name = 'rcJ' + name
            names.append(name)
            resps.append(resp)

        resps = np.hstack(resps)

        self.rc_names = names
        self.rc_data = resps

    def _make_prc_lines(self):
        names = []
        prcs = []

        reagent_of = [each[2:] for each in self.flux_names]
        all_reactions = reagent_of + \
            getattr(self._model_map, self.fixed).isModifierOf()

        for flux_reaction in self.flux_names:

            J_ss = getattr(self.mod, flux_reaction)
            reaction = flux_reaction[2:]

            for route_reaction in all_reactions:

                ec = getattr(
                    self.mod, 'ec' + route_reaction + '_' + self.fixed)
                cc = getattr(self.mod, 'ccJ' + reaction + '_' + route_reaction)
                slope = ec * cc

                prc = self._tangent_line(J_ss, slope)
                name = 'prcJ%s_%s_%s' % (reaction,
                                         self.fixed,
                                         route_reaction)

                names.append(name)
                prcs.append(prc)

        prcs = np.hstack(prcs)

        self.prc_names = names
        self.prc_data = prcs

    def _make_ec_lines(self):
        names = []
        elasts = []

        for each in self.flux_names:

            reaction = each[2:]
            name = 'ec' + reaction + '_' + self.fixed

            J_ss = getattr(self.mod, each)
            slope = getattr(self.mod, name)
            elast = self._tangent_line(J_ss, slope)

            names.append(name)
            elasts.append(elast)

        elasts = np.hstack(elasts)

        self.ec_names = names
        self.ec_data = elasts

    def _attach_coefficients_to_self(self, names, tangent_lines):
        sp = 0
        ep = 2
        for name in names:
            setattr(self, name, tangent_lines[:, sp:ep])
            sp = ep
            ep += 2

    def _tangent_line(self, J_ss, slope):

        fix_ss = self.fixed_ss

        constant = J_ss / (fix_ss ** slope)

        ydist = np.log10(self.flux_max / self.flux_min)
        xdist = np.log10(self.scan_max / self.scan_min)
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
            color_dict = dict(
                zip(['Total Supply'] +
                    ['J_' + reaction for reaction in self.mod.reactions] +
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

        demand_blocks = getattr(self._model_map, self.fixed).isSubstrateOf()
        supply_blocks = getattr(self._model_map, self.fixed).isProductOf()

        for flux in self.flux_names:
            flux_col = self.flux_names.index(flux)
            x_data = self.scan_range
            y_data = self.flux_data[:, flux_col]
            latex_expr = self._ltxe.expression_to_latex(flux)
            color = hsv_to_rgb(*color_dict[flux])
            for dem in demand_blocks:
                if dem in flux:
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
                if sup in flux:
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

        for ec_name in self.ec_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                ec_reaction = flux[2:]
                if ec_reaction in ec_name:
                    flux_color = self._color_dict[flux]
                    color = hsv_to_rgb(flux_color[0],
                                       flux_color[1] * 0.65,
                                       flux_color[2])
                    ec_data = getattr(self, ec_name)
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

        for rc_name in self.rc_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                rc_flux = 'J' + flux[2:]
                if rc_flux in rc_name:
                    flux_color = self._color_dict[flux]
                    color = hsv_to_rgb(flux_color[0],
                                       flux_color[1],
                                       flux_color[2] * 0.65)
                    rc_data = getattr(self, rc_name)
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

        for prc_name in self.prc_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                prc_flux = 'J' + flux[2:]
                if prc_flux in prc_name:

                    route_reaction = get_prc_route(prc_name,
                                                   prc_flux,
                                                   self.fixed)
                    flux_color = self._color_dict['J_' + route_reaction]
                    color = hsv_to_rgb(flux_color[0],
                                       flux_color[1] * 0.75,
                                       flux_color[2])
                    prc_data = getattr(self, prc_name)
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

        total_flux_ld_dict['Total Supply'] = \
            LineData(name='Total Supply',
                     x_data=self.scan_range,
                     y_data=self.total_supply,
                     categories=['Fluxes',
                                 'Supply',
                                 'Total Supply'],
                     properties={'label': '$%s$' % 'Total\,Supply',
                                 'color': self._color_dict['Total Supply']})

        total_flux_ld_dict['Total Demand'] = \
            LineData(name='Total Demand',
                     x_data=self.scan_range,
                     y_data=self.total_demand,
                     categories=['Fluxes',
                                 'Demand',
                                 'Total Demand'],
                     properties={'label': '$%s$' % 'Total\,Demand',
                                 'color': self._color_dict['Total Demand']})

        self._total_flux_ld_dict = total_flux_ld_dict

    def plot(self):

        category_classes = OrderedDict([
            ('Supply/Demand', [
                'Supply',
                'Demand']),
            ('Reaction Blocks',
             self.flux_names +
             ['Total Supply', 'Total Demand']),
            ('Lines', [
                'Fluxes',
                'Elasticity Coefficients',
                'Response Coefficients',
                'Partial Response Coefficients'])])

        line_data_list = [v for v in self._line_data_dict.itervalues()]

        scan_fig = ScanFig(line_data_list,
                           ax_properties={'xlabel': '[%s]' %
                                          self.fixed.replace('_', ' '),
                                          'ylabel': 'Rate',
                                          'xscale': 'log',
                                          'yscale': 'log',
                                          'xlim':  [self.scan_min,
                                                    self.scan_max],
                                          'ylim':  [self.flux_min,
                                                    self.flux_max]},
                           category_classes=category_classes)

        scan_fig.toggle_category('Supply', True)
        scan_fig.toggle_category('Demand', True)
        scan_fig.toggle_category('Fluxes', True)

        return scan_fig


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
