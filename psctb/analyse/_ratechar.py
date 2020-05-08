from os import path
from colorsys import hsv_to_rgb, rgb_to_hsv
from collections import OrderedDict
from random import shuffle

import numpy
from pysces.PyscesModelMap import ModelMap
from pysces import Scanner
import pysces
from matplotlib.pyplot import get_cmap

from .. import modeltools
from ..latextools import LatexExpr
from ..utils.plotting import ScanFig, LineData, Data2D
from ..utils.misc import silence_print
from ..utils.misc import DotDict
from ..utils.misc import formatter_factory


exportLAWH = silence_print(pysces.write.exportLabelledArrayWithHeader)

__all__ = ['RateChar']


def strip_nan_from_scan(array_like):
    # this function assumes that column
    # zero contains valid data (the scan input)
    t_f = list(numpy.isnan(array_like[:, 1]))
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
            self.load_session()

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
            self.save_session()

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
        # (calls psctb.modeltools.fix_metabolite)
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

    def save_session(self, file_name=None):
        file_name = modeltools.get_file_path(working_dir=self._working_dir,
                                             internal_filename='save_data',
                                             fmt='npz',
                                             file_name=file_name,
                                             write_suffix=False)

        to_save = {}
        for species in self.mod.species:
            species_object = getattr(self, species)
            try:
                column_array = numpy.array(species_object._column_names)
                scan_results = species_object._scan_results

                to_save['col_{0}'.format(species)] = column_array
                to_save['res_{0}'.format(species)] = scan_results
            except:
                pass
        numpy.savez(file_name, **to_save)


    def save_results(self, folder=None, separator=',',format='%f'):
        base_folder = folder
        for species in self.mod.species:
            if folder:
                folder = path.join(base_folder, species)
            getattr(self, species).save_all_results(folder=folder,
                                                    separator=separator)

    def load_session(self, file_name=None):
        file_name = modeltools.get_file_path(working_dir=self._working_dir,
                                             internal_filename='save_data',
                                             fmt='npz',
                                             file_name=file_name,
                                             write_suffix=False)

        loaded_data = {}
        try:
            with numpy.load(file_name) as data_file:
                for k, v in data_file.iteritems():
                    loaded_data[k] = v
        except IOError as e:
            raise e

        for species in self.mod.species:
            try:
                column_names = [str(each) for each in
                                list(loaded_data['col_{0}'.format(species)])]
                scan_results = loaded_data['res_{0}'.format(species)]
                fixed_species = species
                fixed_mod, fixed_ss = self._fix_at_ss(fixed_species)
                rcd = RateCharData(fixed_ss=fixed_ss,
                                   fixed_mod=fixed_mod,
                                   basemod=self.mod, column_names=column_names,
                                   scan_results=scan_results,
                                   model_map=self._model_map, ltxe=self._ltxe)
                setattr(self, fixed_species, rcd)
            except:
                pass


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

        self.scan_results = DotDict()
        self.mca_results = DotDict()

        self._slope_range_factor = 3.0

        self.scan_results['fixed'] = column_names[0]
        self.scan_results['fixed_ss'] = fixed_ss

        self.scan_results['scan_range'] = scan_results[:, 0]
        self.scan_results['flux_names'] = column_names[1:]
        self.scan_results['flux_data'] = scan_results[:, 1:]
        self.scan_results['scan_points'] = len(self.scan_results.scan_range)
        self.scan_results['flux_max'] = None
        self.scan_results['flux_min'] = None
        self.scan_results['scan_max'] = None
        self.scan_results['scan_min'] = None
        self.scan_results['ec_names'] = None
        self.scan_results['ec_data'] = None
        self.scan_results['rc_names'] = None
        self.scan_results['rc_data'] = None
        self.scan_results['prc_names'] = None
        self.scan_results['prc_data'] = None

        self._column_names = column_names
        self._scan_results = scan_results
        self._model_map = model_map

        self._analysis_method = 'ratechar'
        self._basemod = basemod
        self._working_dir = modeltools.make_path(self._basemod,
                                                 self._analysis_method,
                                                 [self.scan_results.fixed])
        self._ltxe = ltxe

        self._color_dict_ = None
        self._data_setup()
        self.mca_results._ltxe = ltxe
        self.mca_results._make_repr(
            '"$" + self._ltxe.expression_to_latex(k) + "$"', 'v',
            formatter_factory())
        # del self.scan_results
        # del self.mca_results

    def _data_setup(self):
        # reset value to do mcarc
        setattr(self.mod, self.scan_results.fixed, self.scan_results.fixed_ss)
        self.mod.doMcaRC()
        self._make_attach_total_fluxes()
        self._min_max_setup()
        self._attach_fluxes_to_self()
        self._make_all_coefficient_lines()
        self._attach_all_coefficients_to_self()
        self._make_all_summary()
        self._make_all_line_data()

    def _change_colour_order(self, order=None):
        if not order:
            order = self._color_dict_.keys()
            shuffle(order)
        self._color_dict_ = dict(zip(order, self._color_dict_.values()))
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

        self.mca_results.update(self._ec_summary)
        self.mca_results.update(self._cc_summary)
        self.mca_results.update(self._rc_summary)
        self.mca_results.update(self._prc_summary)

        del self._ec_summary
        del self._cc_summary
        del self._rc_summary
        del self._prc_summary

    def _make_ec_summary(self):
        ecs = {}
        reagent_of = [each[2:] for each in self.scan_results.flux_names]
        modifier_of = getattr(
            self._model_map, self.scan_results.fixed).isModifierOf()
        all_reactions = reagent_of + modifier_of
        for reaction in all_reactions:
            name = 'ec%s_%s' % (reaction, self.scan_results.fixed)
            val = getattr(self.mod, name)
            ecs[name] = val

        self._ec_summary = ecs

    def _make_rc_summary(self):
        rcs = {}
        for flux in self.scan_results.flux_names:
            reaction = flux[2:]
            name = '%s_%s' % (reaction, self.scan_results.fixed)
            val = getattr(self.mod.rc, name)
            name = 'rcJ' + name
            rcs[name] = val

        self._rc_summary = rcs

    def _make_cc_summary(self):

        ccs = {}
        reagent_of = [each[2:] for each in self.scan_results.flux_names]
        modifier_of = getattr(
            self._model_map, self.scan_results.fixed).isModifierOf()
        all_reactions = reagent_of + modifier_of

        for flux_reaction in reagent_of:
            for reaction in all_reactions:
                name = 'ccJ%s_%s' % (flux_reaction, reaction)
                val = getattr(self.mod, name)
                ccs[name] = val

        self._cc_summary = ccs

    def _make_prc_summary(self):

        prcs = {}

        reagent_of = [each[2:] for each in self.scan_results.flux_names]
        modifier_of = getattr(
            self._model_map, self.scan_results.fixed).isModifierOf()
        all_reactions = reagent_of + modifier_of

        for flux_reaction in reagent_of:
            for route_reaction in all_reactions:
                ec = getattr(self.mod,
                             'ec%s_%s' % (
                                 route_reaction, self.scan_results.fixed))

                cc = getattr(self.mod,
                             'ccJ%s_%s' % (flux_reaction, route_reaction))
                val = ec * cc
                name = 'prcJ%s_%s_%s' % (flux_reaction,
                                         self.scan_results.fixed,
                                         route_reaction)

                prcs[name] = val

        self._prc_summary = prcs

    def save_summary(self, file_name=None, separator=',',fmt='%f'):
        file_name = modeltools.get_file_path(working_dir=self._working_dir,
                                             internal_filename='mca_summary',
                                             fmt='csv',
                                             file_name=file_name, )

        keys = self.mca_results.keys()
        keys.sort()
        values = numpy.array([self.mca_results[k]
                              for k in keys]).reshape(len(keys), 1)

        try:
            exportLAWH(values,
                       names=keys,
                       header=['Value'],
                       fname=file_name,
                       sep=separator,
                       format=fmt)
        except IOError as e:
            print e.strerror

    def save_flux_results(self, file_name=None, separator=',',fmt='%f'):
        file_name = modeltools.get_file_path(working_dir=self._working_dir,
                                             internal_filename='flux_results',
                                             fmt='csv',
                                             file_name=file_name, )

        scan_points = self.scan_results.scan_points
        all_cols = numpy.hstack([
            self._scan_results,
            self.scan_results.total_supply.reshape(scan_points, 1),
            self.scan_results.total_demand.reshape(scan_points, 1)])
        column_names = self._column_names + ['Total Supply', 'Total Demand']

        try:
            exportLAWH(all_cols,
                       names=None,
                       header=column_names,
                       fname=file_name,
                       sep=separator,
                       format=fmt)
        except IOError as e:
            print e.strerror

    def save_coefficient_results(self,
                                 coefficient,
                                 file_name=None,
                                 separator=',',
                                 folder=None,
                                 fmt='%f'):
        assert_message = 'coefficient must be one of "ec", "rc" or "prc"'

        assert coefficient in ['rc', 'ec', 'prc'], assert_message

        base_name = coefficient + '_results'
        file_name = modeltools.get_file_path(working_dir=self._working_dir,
                                             internal_filename=base_name,
                                             fmt='csv',
                                             file_name=file_name, )

        results = getattr(self.scan_results, coefficient + '_data')
        names = getattr(self.scan_results, coefficient + '_names')
        new_names = []
        for each in names:
            new_names.append('x_vals')
            new_names.append(each)

        try:
            exportLAWH(results,
                       names=None,
                       header=new_names,
                       fname=file_name,
                       sep=separator,
                       format=fmt)
        except IOError as e:
            print e.strerror

    # TODO fix this method so that folder is a parameter only her
    def save_all_results(self, folder=None, separator=',',fmt='%f'):
        if not folder:
            folder = self._working_dir

        file_name = modeltools.get_file_path(working_dir=folder,
                                             internal_filename='flux_results',
                                             fmt='csv')
        self.save_flux_results(separator=separator, file_name=file_name,fmt=fmt)

        file_name = modeltools.get_file_path(working_dir=folder,
                                             internal_filename='mca_summary',
                                             fmt='csv')
        self.save_summary(separator=separator, file_name=file_name, fmt=fmt)
        for each in ['ec', 'rc', 'prc']:
            base_name = each + '_results'
            file_name = modeltools.get_file_path(working_dir=folder,
                                                 internal_filename=base_name,
                                                 fmt='csv')
            self.save_coefficient_results(coefficient=each,
                                          separator=separator,
                                          file_name=file_name,
                                          fmt=fmt)

    def _min_max_setup(self):
        # Negative minimum linear values mean nothing
        # because they don't translate to a log space
        # therefore we want the minimum non-negative/non-zero values.

        # lets make sure there are no zeros
        n_z_f = self.scan_results.flux_data[
            numpy.nonzero(self.scan_results.flux_data)]
        n_z_s = self.scan_results.scan_range[
            numpy.nonzero(self.scan_results.scan_range)]

        totals = numpy.vstack([self.scan_results.total_demand,
                               self.scan_results.total_supply])
        n_z_t = totals[numpy.nonzero(totals)]
        # and that the array is not now somehow empty
        # although if this happens-you have bigger problems
        if len(n_z_f) == 0:
            n_z_f = numpy.array([0.01, 1])
        if len(n_z_s) == 0:
            n_z_s = numpy.array([0.01, 1])

        # lets also (clumsily) find the non-negative mins and maxes
        # by converting to logspace (to get NaNs) and back
        # and then getting the min/max non-NaN
        # PS flux max is the max of the totals

        with numpy.errstate(all='ignore'):

            self.scan_results.flux_max = numpy.nanmax(10 ** numpy.log10(n_z_t))
            self.scan_results.flux_min = numpy.nanmin(10 ** numpy.log10(n_z_f))
            self.scan_results.scan_max = numpy.nanmax(10 ** numpy.log10(n_z_s))
            self.scan_results.scan_min = numpy.nanmin(10 ** numpy.log10(n_z_s))

    def _attach_fluxes_to_self(self):
        for i, each in enumerate(self.scan_results.flux_names):
            # setattr(self, each, self.scan_results.flux_data[:, i])
            self.scan_results[each] = self.scan_results.flux_data[:, i]

    def _attach_all_coefficients_to_self(self):
        setup_for = ['ec', 'rc', 'prc']
        for each in setup_for:
            eval('self._attach_coefficients_to_self(self.scan_results.' + each + '_names,\
                                                self.scan_results.' + each + '_data)')

    def _make_all_coefficient_lines(self):
        setup_for = ['ec', 'rc', 'prc']
        for each in setup_for:
            eval('self._make_' + each + '_lines()')

    def _make_attach_total_fluxes(self):
        demand_blocks = getattr(
            self._model_map, self.scan_results.fixed).isSubstrateOf()
        supply_blocks = getattr(
            self._model_map, self.scan_results.fixed).isProductOf()

        dem_pos = [self.scan_results.flux_names.index('J_' + flux)
                   for flux in demand_blocks]
        sup_pos = [self.scan_results.flux_names.index('J_' + flux)
                   for flux in supply_blocks]

        self.scan_results['total_demand'] = numpy.sum(
            [self.scan_results.flux_data[:, i]
             for i in dem_pos],
            axis=0)
        self.scan_results['total_supply'] = numpy.sum(
            [self.scan_results.flux_data[:, i]
             for i in sup_pos],
            axis=0)

    def _make_rc_lines(self):
        names = []
        resps = []

        for each in self.scan_results.flux_names:
            reaction = each[2:]
            name = reaction + '_' + self.scan_results.fixed

            J_ss = getattr(self.mod, each)
            slope = getattr(self.mod.rc, name)
            resp = self._tangent_line(J_ss, slope)

            name = 'rcJ' + name
            names.append(name)
            resps.append(resp)

        resps = numpy.hstack(resps)

        self.scan_results.rc_names = names
        self.scan_results.rc_data = resps

    def _make_prc_lines(self):
        names = []
        prcs = []

        reagent_of = [each[2:] for each in self.scan_results.flux_names]
        all_reactions = reagent_of + \
                        getattr(self._model_map,
                                self.scan_results.fixed).isModifierOf()

        for flux_reaction in self.scan_results.flux_names:

            J_ss = getattr(self.mod, flux_reaction)
            reaction = flux_reaction[2:]

            for route_reaction in all_reactions:
                ec = getattr(
                    self.mod,
                    'ec' + route_reaction + '_' + self.scan_results.fixed)
                cc = getattr(self.mod, 'ccJ' + reaction + '_' + route_reaction)
                slope = ec * cc

                prc = self._tangent_line(J_ss, slope)
                name = 'prcJ%s_%s_%s' % (reaction,
                                         self.scan_results.fixed,
                                         route_reaction)

                names.append(name)
                prcs.append(prc)

        prcs = numpy.hstack(prcs)

        self.scan_results.prc_names = names
        self.scan_results.prc_data = prcs

    def _make_ec_lines(self):
        names = []
        elasts = []

        for each in self.scan_results.flux_names:
            reaction = each[2:]
            name = 'ec' + reaction + '_' + self.scan_results.fixed

            J_ss = getattr(self.mod, each)
            slope = getattr(self.mod, name)
            elast = self._tangent_line(J_ss, slope)

            names.append(name)
            elasts.append(elast)

        elasts = numpy.hstack(elasts)

        self.scan_results.ec_names = names
        self.scan_results.ec_data = elasts

    def _attach_coefficients_to_self(self, names, tangent_lines):
        sp = 0
        ep = 2
        for name in names:
            # setattr(self, name, tangent_lines[:, sp:ep])
            self.scan_results[name] = tangent_lines[:, sp:ep]
            sp = ep
            ep += 2

    def _tangent_line(self, J_ss, slope):

        fix_ss = self.scan_results.fixed_ss

        constant = J_ss / (fix_ss ** slope)

        ydist = numpy.log10(self.scan_results.flux_max / self.scan_results.flux_min)
        xdist = numpy.log10(self.scan_results.scan_max / self.scan_results.scan_min)
        golden_ratio = (1 + numpy.sqrt(5)) / 2
        xyscale = xdist / (ydist * golden_ratio * 1.5)

        scale_factor = numpy.cos(numpy.arctan(slope * xyscale))
        distance = numpy.log10(self._slope_range_factor) * scale_factor

        range_min = fix_ss / (10 ** distance)
        range_max = fix_ss * (10 ** distance)
        scan_range = numpy.linspace(range_min, range_max, num=2)

        rate = constant * scan_range ** (slope)

        return numpy.vstack((scan_range, rate)).transpose()

    @property
    def _color_dict(self):
        if not self._color_dict_:
            fix_map = getattr(self._model_map, self.scan_results.fixed)
            relavent_reactions = fix_map.isProductOf() + \
                                 fix_map.isSubstrateOf() + \
                                 fix_map.isModifierOf()
            num_of_cols = len(relavent_reactions) + 3
            cmap = get_cmap('Set2')(
                numpy.linspace(0, 1.0, num_of_cols))[:, :3]
            color_list = [rgb_to_hsv(*cmap[i, :]) for i in range(num_of_cols)]

            relavent_reactions.sort()
            color_dict = dict(
                zip(['Total Supply'] +
                    ['J_' + reaction for reaction in relavent_reactions] +
                    ['Total Demand'],
                    color_list))
            # just to darken the colors a bit
            for k, v in color_dict.iteritems():
                color_dict[k] = [v[0], 1, v[2]]

            self._color_dict_ = color_dict

        return self._color_dict_

    def _make_flux_ld(self):
        color_dict = self._color_dict

        flux_ld_dict = {}

        demand_blocks = ['J_' + dem_reac for dem_reac in getattr(
            self._model_map, self.scan_results.fixed).isSubstrateOf()]
        supply_blocks = ['J_' + sup_reac for sup_reac in getattr(
            self._model_map, self.scan_results.fixed).isProductOf()]

        for flux in self.scan_results.flux_names:
            flux_col = self.scan_results.flux_names.index(flux)
            x_data = self.scan_results.scan_range
            y_data = self.scan_results.flux_data[:, flux_col]
            latex_expr = self._ltxe.expression_to_latex(flux)
            flux_color = self._color_dict[flux]
            color = hsv_to_rgb(flux_color[0],
                               flux_color[1],
                               flux_color[2] * 0.9)
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

        for ec_name in self.scan_results.ec_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                ec_reaction = flux[2:]
                if 'ec' + ec_reaction + '_' + self.scan_results.fixed in ec_name:
                    flux_color = self._color_dict[flux]
                    color = hsv_to_rgb(flux_color[0],
                                       flux_color[1] * 0.5,
                                       flux_color[2])
                    ec_data = self.scan_results[ec_name]
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

        for rc_name in self.scan_results.rc_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                rc_flux = 'J' + flux[2:]
                if 'rc' + rc_flux + '_' in rc_name:
                    flux_color = self._color_dict[flux]
                    color = hsv_to_rgb(flux_color[0],
                                       flux_color[1],
                                       flux_color[2] * 0.7)
                    rc_data = self.scan_results[rc_name]
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

        for prc_name in self.scan_results.prc_names:
            for flux, flux_ld in self._flux_ld_dict.iteritems():
                prc_flux = 'J' + flux[2:]
                if 'prc' + prc_flux + '_' + self.scan_results.fixed in prc_name:
                    route_reaction = get_prc_route(prc_name,
                                                   prc_flux,
                                                   self.scan_results.fixed)
                    flux_color = self._color_dict['J_' + route_reaction]
                    color = hsv_to_rgb(flux_color[0],
                                       flux_color[1] * 0.5,
                                       flux_color[2])
                    prc_data = self.scan_results[prc_name]
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
                     x_data=self.scan_results.scan_range,
                     y_data=self.scan_results.total_supply,
                     categories=['Fluxes',
                                 'Supply',
                                 'Total Supply'],
                     properties={'label': '$%s$' % 'Total\,Supply',
                                 'color': hsv_to_rgb(col[0], col[1],
                                                     col[2] * 0.9),
                                 'ls': '--'})

        col = self._color_dict['Total Demand']
        total_flux_ld_dict['Total Demand'] = \
            LineData(name='Total Demand',
                     x_data=self.scan_results.scan_range,
                     y_data=self.scan_results.total_demand,
                     categories=['Fluxes',
                                 'Demand',
                                 'Total Demand'],
                     properties={'label': '$%s$' % 'Total\,Demand',
                                 'color': hsv_to_rgb(col[0], col[1],
                                                     col[2] * 0.9),
                                 'ls': '--'})

        self._total_flux_ld_dict = total_flux_ld_dict

    def plot(self):

        category_classes = OrderedDict([
            ('Supply/Demand', [
                'Supply',
                'Demand']),
            ('Reaction Blocks',
             self.scan_results.flux_names +
             ['Total Supply', 'Total Demand']),
            ('Lines', [
                'Fluxes',
                'Elasticity Coefficients',
                'Response Coefficients',
                'Partial Response Coefficients'])])

        line_data_list = [v for v in self._line_data_dict.itervalues()]

        scan_fig = ScanFig(line_data_list,
                           ax_properties={'xlabel': '[%s]' %
                                                    self.scan_results.fixed.replace(
                                                        '_', ' '),
                                          'ylabel': 'Rate',
                                          'xscale': 'log',
                                          'yscale': 'log',
                                          'xlim': [self.scan_results.scan_min,
                                                   self.scan_results.scan_max],
                                          'ylim': [self.scan_results.flux_min,
                                                   self.scan_results.flux_max * 2
                                                   ]},
                           category_classes=category_classes,
                           base_name=self._analysis_method,
                           working_dir=self._working_dir)

        scan_fig.toggle_category('Supply', True)
        scan_fig.toggle_category('Demand', True)
        scan_fig.toggle_category('Fluxes', True)
        scan_fig.ax.axvline(self.scan_results.fixed_ss, ls=':', color='gray')

        return scan_fig

    def plot_decompose(self):
        from warnings import warn, simplefilter
        simplefilter('always', DeprecationWarning)
        warn('plot_decompose has been renamed to `do_mca_scan, use that '
             'method in the future`', DeprecationWarning, stacklevel=1)
        simplefilter('default', DeprecationWarning)
        return self.do_mca_scan()


    @silence_print
    def do_mca_scan(self):
        ecs = []
        ccs = []
        prc_names = []
        rc_names = []
        rc_pos = []

        reagent_of = [each[2:] for each in self.scan_results.flux_names]
        all_reactions = reagent_of + \
                        getattr(self._model_map,
                                self.scan_results.fixed).isModifierOf()

        arl = len(all_reactions)
        strt = 0
        stp = arl
        for flux_reaction in self.scan_results.flux_names:
            reaction = flux_reaction[2:]
            rc_names.append('rcJ%s_%s' % (reaction, self.scan_results.fixed))

            rc_pos.append(range(strt, stp))
            strt += arl
            stp += arl

            for route_reaction in all_reactions:
                ec = 'ec' + route_reaction + '_' + self.scan_results.fixed
                cc = 'ccJ' + reaction + '_' + route_reaction

                name = 'prcJ%s_%s_%s' % (reaction,
                                         self.scan_results.fixed,
                                         route_reaction)

                # ecs.append(ec)
                if ec not in ecs:
                    ecs.append(ec)
                ccs.append(cc)
                prc_names.append(name)

        ec_len = len(ecs)

        user_output = [self.scan_results.fixed] + ecs + ccs


        scanner = pysces.Scanner(self.mod)
        scanner.quietRun = True
        scanner.addScanParameter(self.scan_results.fixed,
                                 self.scan_results.scan_min,
                                 self.scan_results.scan_max,
                                 self.scan_results.scan_points,
                                 log=True)
        scanner.addUserOutput(*user_output)
        scanner.Run()

        ax_properties = {'ylabel': 'Coefficient Value',
                         'xlabel': '[%s]' %
                                   self.scan_results.fixed.replace('_', ' '),
                         'xscale': 'log',
                         'yscale': 'linear',
                         'xlim': [self.scan_results.scan_min,
                                  self.scan_results.scan_max]}

        cc_ec_data_obj = Data2D(mod=self.mod,
                                column_names=user_output,
                                data_array=scanner.UserOutputResults,
                                ltxe=self._ltxe,
                                analysis_method=self._analysis_method,
                                ax_properties=ax_properties,
                                file_name='cc_ec_scan',
                                num_of_groups=ec_len,
                                working_dir=path.split(self._working_dir)[0])

        rc_data = []

        all_outs = scanner.UserOutputResults[:, 1:]

        ec_outs = all_outs[:, :ec_len]
        cc_outs = all_outs[:, ec_len:]
        ec_positions = range(ec_len) * (len(prc_names)/ec_len)


        for i, prc_name in enumerate(prc_names):

            ec_col_data = ec_outs[:, ec_positions[i]]

            cc_col_data = cc_outs[:, i]
            # ec_col_data = outs[:, i]
            # cc_col_data = outs[:, i + cc_s_pos]
            col = ec_col_data * cc_col_data
            rc_data.append(col)

        temp = numpy.vstack(rc_data).transpose()
        rc_data += [numpy.sum(temp[:, rc_pos[i]], axis=1) for i in
                    range(len(rc_names))]

        rc_out_arr = [scanner.UserOutputResults[:, 0]] + rc_data
        rc_out_arr = numpy.vstack(rc_out_arr).transpose()
        rc_data_obj = Data2D(mod=self.mod,
                             column_names=[self.scan_results.fixed] + prc_names + rc_names,
                             data_array=rc_out_arr,
                             ltxe=self._ltxe,
                             analysis_method=self._analysis_method,
                             ax_properties=ax_properties,
                             file_name='prc_scan',
                             num_of_groups=ec_len,
                             working_dir=path.split(self._working_dir)[0])
        #rc_data_obj._working_dir = path.split(self._working_dir)[0]
        #cc_ec_data_obj._working_dir = path.split(self._working_dir)[0]

        return rc_data_obj, cc_ec_data_obj

