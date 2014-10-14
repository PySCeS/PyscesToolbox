#TODO:
#There are cases where path.join would be more appropriate (for cross platform
#compatability)
from IPython.display import display, clear_output
from matplotlib import pyplot as plt
from matplotlib import transforms
from matplotlib import rcParams
from os import path, mkdir
from numpy import linspace
from IPython.html import widgets
from pysces import ModelMap
from pysces import output_dir as psc_out_dir
import pysces

from ..misc import *
from ...latextools import LatexExpr
from collections import OrderedDict
from ... import modeltools


exportLAWH = silence_print(pysces.write.exportLabelledArrayWithHeader)


"""
This whole module is fd in the a
"""
__all__ = ['LineData',
           'ScanFig',
           'Data2D']


def add_legend_viewlim(ax, **kwargs):
    """ Reset the legend in ax to only display lines that are
    currently visible in plot area """
    # THIS FUNCTION COMES FROM
    # http://matplotlib.1069221.n5.nabble.com/
    # Re-Limit-legend-to-visible-data-td18335.html
    label_objs = []
    label_texts = []
    # print "viewLim:", ax.viewLim
    for line in ax.lines:
        line_label = line.get_label()
        cond = line.get_visible() and \
            line_label and not line_label.startswith("_")
        if cond:
            line_bbox = transforms.Bbox.unit()
            line_bbox.update_from_data_xy(line.get_xydata())
            if ax.viewLim.overlaps(line_bbox):
                # print line_label, line_bbox
                label_objs.append(line)
                label_texts.append(line_label)
    if label_objs:
        return ax.legend(label_objs, label_texts,  **kwargs)

    elif ax.get_legend():
        ax.get_legend().set_visible(False)
    else:
        ax.legend().set_visible(False)


class LineData(object):

    """
    An object that contains data that can be used to draw a matplotlib line.

    This object is used to initialise a ``ScanFig`` object together with a
    ``Data2D`` object. Once a ``ScanFig`` instance is initialised, the
    ``LineData`` objects are saved in a list ``_raw_line_data``. Changing
    any values there will have no effect on the output of the ``ScanFig``
    instance.

    Parameters
    ----------
    name : str
        The name of the line. Will be used as a label if none is specified.
    x_data : array_like
        The x data.
    y_data : array_like
        The y data.
    categories : list, optional
        A list of categories that a line falls into. This will be used by
        ScanFig to draw buttons that enable/disable the line.
    properties : dict, optional
        A dictionary of properties of the line to be drawn. This dictionary
        will be used by the generic ``set()`` function of
        ``matplotlib.Lines.Line2D`` to set the properties of the line.

    See Also
    --------
    ScanFig
    Data2D
    RateChar
    """

    def __init__(self, name, x_data, y_data, categories=None, properties=None):
        super(LineData, self).__init__()
        self.name = name
        self.x = x_data
        self.y = y_data

        if categories:
            self.categories = categories
        else:
            self.categories = [self.name]
        if properties:
            self.properties = properties
        else:
            self.properties = {}

        self._update_attach_properties()

    def _update_attach_properties(self):
        """
        Attaches all properties in ``self.properties`` to the ``self``
        namespace.
        """
        for k, v in self.properties.iteritems():
            setattr(self, k, v)

    def add_property(key, value):
        """
        Adds a property to the ``properties`` dictionary of the
        ``LineData`` object.

        The ``properties`` dictionary of ``LineData`` will be used by the
        generic ``set()`` function of ``matplotlib.Lines.Line2D``
        to set the properties of the line.

        Parameters
        ----------
        key : str
            The name of the ``matplotlib.Lines.Line2D`` property to be set.
        value : sting, int, bool
            The value of the property to be set. The type depends on the
            property.
        """

        self.properties.update({key, value})
        self._update_attach_properties()


class Data2D(object):

    def __init__(self,
                 mod,
                 column_names,
                 data_array,
                 ltxe=None,
                 analysis_method=None,
                 ax_properties=None,
                 file_name=None):
        self.plot_data = DotDict()
        self.plot_data['scan_in'] = column_names[0]
        self.plot_data['scan_out'] = column_names[1:]
        self.plot_data['scan_range'] = data_array[:, 0]
        self.plot_data['scan_results'] = data_array[:, 1:]
        self.plot_data['scan_points'] = len(self.plot_data.scan_range)



        self._column_names = column_names
        self._scan_results = data_array


        self.column_names = column_names
        self.column_names_in = column_names[0]
        self.column_names_out = column_names[1:]

        self.data = data_array
        self.data_in = data_array[:, 0]
        self.data_out = data_array[:, 1:]

        self.mod = mod
        if not ltxe:
            ltxe = LatexExpr(mod)
        self.ltxe = ltxe

        self.mod.doMcaRC()

        if not analysis_method:
            self._analysis_method = 'DataScan'
        else:
            self._analysis_method = analysis_method

        if not file_name:
            self._fname = 'scan_fig'
        else:
            self._fname = file_name

        self._working_dir = modeltools.make_path(self.mod,
                                                 self._analysis_method)
        if not ax_properties:
            self._ax_properties = None
        else:
            self._ax_properties = ax_properties

        self.category_classes = \
            OrderedDict([('All Coefficients',
                          ['Elasticity Coefficients',
                           'Control Coefficients',
                           'Response Coefficients',
                           'Partial Response Coefficients',
                           'Control Patterns']),
                         ('All Fluxes/Reactions/Species',
                          ['Fluxes Rates',
                           'Reaction Rates',
                           'Species Concentrations'])])

        self.scan_types = \
        OrderedDict([
            ('Fluxes Rates',
                ['J_' + reaction for reaction in mod.reactions]),
            ('Reaction Rates', [reaction for reaction in mod.reactions]),
            ('Species Concentrations', mod.species),
            ('Steady-state Species Concentrations',
                [sp + '_ss' for sp in mod.species]),
            ('Elasticity Coefficients', ec_list(mod)),
            ('Control Coefficients', cc_list(mod)),
            ('Response Coefficients', rc_list(mod)),
            ('Partial Response Coefficients', prc_list(mod)),
            ('Control Patterns', ['CP' + str(n) for n in range(1,len(self.column_names))])
             ])

        self._setup_categories()
        self._setup_lines()
        self.category_classes.update(self.scan_types)

    def _setup_categories(self):
        scan_types = self.scan_types
        column_categories = {}
        for column in self.column_names_out:
            column_categories[column] = [column]
            for k, v in scan_types.iteritems():
                if column in v:
                    column_categories[column].append(k)
                    break

        self.column_categories = column_categories

    def _setup_lines(self):
        lines = []
        for i, each in enumerate(self.column_names_out):
            line = LineData(name=each,
                            x_data=self.data_in,
                            y_data=self.data_out[:, i],
                            categories=self.column_categories[each],
                            properties={'label':
                                        '$%s$' %
                                        (self.ltxe.expression_to_latex(each)),
                                        'linewidth': 1.6})
            lines.append(line)
        self.lines = lines

    @property
    def ax_properties(self):
        if not self._ax_properties:
            self._ax_properties = {'xlabel': self._x_name()}
        return self._ax_properties

    def _x_name(self):
        mm = ModelMap(self.mod)
        species = mm.hasSpecies()
        x_name = ''
        if self.column_names_in == 'Time':
            x_name = 'Time (s)'
        elif self.column_names_in in species:
            x_name = '[%s]' % self.column_names_in
        elif self.column_names_in in self.mod.parameters:
            x_name = self.column_names_in
        return x_name

    def plot(self):
        scan_fig = ScanFig(self.lines,
                           category_classes=self.category_classes,
                           ax_properties=self.ax_properties,
                           fname=path.join(self._working_dir,
                                           self.plot_data.scan_in,
                                           self._fname))
        return scan_fig


    def save_data(self, file_name=None, separator=',', folder=None):
        if not file_name:
            if folder:
                if not path.exists(path.join(folder, self.plot_data.scan_in)):
                    mkdir(path.join(folder, self.plot_data.scan_in))
                file_name = path.join(folder,
                                      self.plot_data.scan_in,
                                      'scan_data.csv')
            else:
                if not path.exists(path.join(self._working_dir, self.plot_data.scan_in)):
                    mkdir(path.join(self._working_dir, self.plot_data.scan_in))
                file_name = path.join(self._working_dir, self.plot_data.scan_in,'scan_data.csv')
        scan_results = self._scan_results
        column_names = self._column_names

        try:
            exportLAWH(scan_results,
                       names=None,
                       header=column_names,
                       fname=file_name,
                       sep=separator)
        except IOError as e:
            print e.strerror



class ScanFig(object):

    def __init__(self, line_data_list,
                 category_classes=None,
                 fig_properties=None,
                 ax_properties=None,
                 fname=None,):

        super(ScanFig, self).__init__()

        rcParams.update({'font.size': 16})

        self._categories = None
        self._categories_status = None
        self._lines = None
        self._widgets_ = None
        self._figure_widgets_ = None
        self._raw_line_data = line_data_list

        # figure setup
        plt.ioff()
        self.fig = plt.figure(figsize=(10, 5.72))
        if fig_properties:
            self.fig.set(**fig_properties)

        # axis setup
        self.ax = self.fig.add_subplot(111)
        if ax_properties:
            self.ax.set(**ax_properties)

        # colourmap_setup
        # at the moment this is very basic and could be expanded
        # it would be useful to set it up based on category somehow
        cmap = plt.get_cmap('Set1')(
            linspace(0, 1.0, len(line_data_list)))
        self.ax.set_color_cycle(cmap)

        if category_classes:
            self.category_classes = category_classes
        else:
            self.category_classes = {'': [k for k in self.categories]}

        if fname:
            self.fname = fname
        else:
            self.fname = path.join(psc_out_dir,'ScanFig')

        self._save_counter = 0

        self.lines
        plt.close()
        self._save_button_ = None
    @property
    def _save_button(self):
        if not self._save_button_:
            def save(clicked):
                self.save()
            self._save_button_ = widgets.ButtonWidget()
            self._save_button_.description = 'Save'
            self._save_button_.on_click(save)
        return self._save_button_


    def show(self):
        """
        Shows the figure.

        Depending on the matplotlib backend this function will either display
        the figure inline if running in an ``IPython`` notebook with the
        ``--pylab=inline`` switch or it will display the figure as determined
        by the ``rcParams['backend']`` option of ``matplotlib``.

        See Also
        --------
        interact
        adjust_figure
        """

        add_legend_viewlim(
            self.ax,
            bbox_to_anchor=(0, -0.17),
            ncol=3,
            loc=2,
            borderaxespad=0.)

        if rcParams['backend'] == \
                'module://IPython.kernel.zmq.pylab.backend_inline':
            clear_output(wait=True)
            display(self.fig)
        else:
            self.fig.show()

    def save(self, fname=None, dpi=None, fmt=None):
        if not fmt:
            fmt = 'svg'

        if not dpi:
            dpi = 180

        if not fname:
            name_string = '_' + str(self._save_counter) + '.' + fmt
            fname = self.fname + name_string
        else:
            fname = fname + '.' + fmt
        if not path.exists(path.split(self.fname)[0]):
            mkdir(path.split(self.fname)[0])
        self._save_counter += 1

        self.fig.savefig(fname,
                         format=fmt,
                         dpi=dpi,
                         bbox_extra_artists=(self.ax.get_legend(),),
                         bbox_inches='tight')


    @property
    def _widgets(self):
        if not self._widgets_:
            widget_classes = OrderedDict()
            for k in self.category_classes.iterkeys():
                widget_classes[k] = widgets.ContainerWidget()

            def oc(cat):
                def on_change(name, value):
                    self.toggle_category(cat, value)
                    self.show()
                return on_change

            for each in self.categories:
                w = widgets.ToggleButtonWidget()
                w.description = each
                w.value = self.categories_status[each]
                on_change = oc(each)
                w.on_trait_change(on_change, 'value')
                for k, v in self.category_classes.iteritems():
                    if each in v:
                        widget_classes[k].children += (w),

            #this is needed to sort widgets according to alphabetical order
            for k, v in widget_classes.iteritems():
                children_list = list(v.children)
                names = [getattr(widg,'description') for widg in children_list]
                names.sort()

                new_children_list = []
                for name in names:
                    for child in children_list:
                        if child.description == name:
                            new_children_list.append(child)
                v.children = tuple(new_children_list)

            self._widgets_ = widget_classes
        return self._widgets_

    @property
    def _figure_widgets(self):
        """
        Instantiates the widgets that will be used to adjust the figure.

        At the moment widgets for manipulating the following paramers
        are available:

            minimum and maximum x values on the x axis
            minimum and maximum y values on the y axis
            the scale of the x and y axis i.e. log vs linear

        The following are possible TODOs:

            figure size
            y label
            x label
            figure title
        """

        def convert_scale(val):
            """
            Converts between str and bool for the strings 'log' and 'linear'

            The string 'log' returns True, while True returns 'log'.
            The string 'linear' returns False, while False returns 'linear'

            Parameters
            ----------
            val : str, bool
                The value to convert.

            Returns
            -------
            value : str, bool
                The conversion of the parameter ``val``

            Examples
            --------
            >>> convert_scale('log')
            True
            >>> convert_scale(False)
            'linear'
            """

            if type(val) == bool:
                if val is True:
                    return 'log'
                elif val is False:
                    return 'linear'
            elif type(val) == str:
                if val == 'log':
                    return True
                elif val == 'linear':
                    return False

        def c_v(val):

            if val <= 0:
                return 0.001
            else:
                return val

        if not self._figure_widgets_:
            min_x = widgets.FloatTextWidget()
            max_x = widgets.FloatTextWidget()
            min_x.value, max_x.value = self.ax.get_xlim()
            min_x.description = 'min'
            max_x.description = 'max'

            min_y = widgets.FloatTextWidget()
            max_y = widgets.FloatTextWidget()
            min_y.value, max_y.value = self.ax.get_ylim()
            min_y.description = 'min'
            max_y.description = 'max'

            log_x = widgets.CheckboxWidget()
            log_y = widgets.CheckboxWidget()
            log_x.value = convert_scale(self.ax.get_xscale())
            log_y.value = convert_scale(self.ax.get_yscale())
            log_x.description = 'x_log'
            log_y.description = 'y_log'

            apply_btn = widgets.ButtonWidget()
            apply_btn.description = 'Apply'

            def set_values(clicked):
                if log_x.value is True:
                    min_x.value = c_v(min_x.value)
                    max_x.value = c_v(max_x.value)

                self.ax.set_xlim([min_x.value, max_x.value])

                if log_y.value is True:
                    min_y.value = c_v(min_y.value)
                    max_y.value = c_v(max_y.value)

                self.ax.set_ylim([min_y.value, max_y.value])

                self.ax.set_xscale(convert_scale(log_x.value))
                self.ax.set_yscale(convert_scale(log_y.value))

                self.show()

            apply_btn.on_click(set_values)

            x_lims = widgets.ContainerWidget(children=[min_x, max_x])
            y_lims = widgets.ContainerWidget(children=[min_y, max_y])
            lin_log = widgets.ContainerWidget(children=[log_x, log_y])
            apply_con = widgets.ContainerWidget(children=[apply_btn])

            _figure_widgets_ = OrderedDict()
            _figure_widgets_['X axis limits'] = x_lims
            _figure_widgets_['Y axis limits'] = y_lims
            _figure_widgets_['Axis scale'] = lin_log
            _figure_widgets_['    '] = apply_con

            self._figure_widgets_ = _figure_widgets_
        return self._figure_widgets_

    @property
    def categories(self):
        if not self._categories:
            main_cats = []
            cats = []
            for each in self._raw_line_data:
                cats += each.categories
                main_cats.append(each.categories[0])
            cats = list(set(cats))

            cat_dict = {}
            for each in cats:
                cat_dict[each] = []

            for each in self._raw_line_data:
                line = self.lines[each.name]
                for cat in each.categories:
                    cat_dict[cat].append(line)

            self._categories = cat_dict
        return self._categories

    @property
    def categories_status(self):
        if not self._categories_status:
            cat_stat_dict = {}
            for each in self.categories:
                cat_stat_dict[each] = False

            self._categories_status = cat_stat_dict
        return self._categories_status

    @property
    def lines(self):
        if not self._lines:
            lines = {}
            for i, each in enumerate(self._raw_line_data):
                line, = self.ax.plot(each.x, each.y)

                #set width to a default width of 2
                #bc the default value of one is too low
                line.set_linewidth(2)
                if each.properties:
                    line.set(**each.properties)
                else:
                    line.set_label(each.name)

                line.set_visible(False)

                lines[each.name] = line
            self._lines = lines
        return self._lines

    def toggle_line(self, name, value):
        self.lines[name].set_visible(value)

    def toggle_category(self, cat, value):
        # get the visibility status of the category eg. True/False
        self.categories_status[cat] = value
        # get all the other categories
        other_cats = self.categories.keys()
        other_cats.pop(other_cats.index(cat))
        # self.categories is a dict with categories as keys
        # and list of lines that fall within a category
        # as a value. So for each line that falls in a cat
        for line in self.categories[cat]:
            # The visibility for a line has not changed at the start of
            # the loop
            in_other_cats = False
            # A line can also fall within another category
            other_cat_stats = []

            for each in other_cats:
                if line in self.categories[each]:

                    other_cat_stats.append(self.categories_status[each])
                    in_other_cats = True
            # If a line is never in any other categories
            # just set its  visibility as it is dictated by
            # its category status.
            if in_other_cats:
                visibility = all([value] + other_cat_stats)
                line.set_visible(visibility)
            else:
                line.set_visible(value)

    def interact(self):
        self.show()
        for k, v in self._widgets.iteritems():
            if len(v.children) > 0:
                head = widgets.LatexWidget(value=k)
                display(head)
                display(v)
                v.remove_class('vbox')
                v.add_class('hbox')
                v.set_css({'flex-wrap': 'wrap'})
        display(widgets.LatexWidget(value='$~$'))
        display(self._save_button)
        self._save_button.remove_class('vbox')
        self._save_button.add_class('hbox')

    def adjust_figure(self):
        self.show()
        for k, v in self._figure_widgets.iteritems():
            if len(v.children) > 0:
                head = widgets.LatexWidget(value=k)
                display(head)
                display(v)
                v.remove_class('vbox')
                v.add_class('hbox')
                v.set_css({'flex-wrap': 'wrap'})
        display(widgets.LatexWidget(value='$~$'))
        display(self._save_button)
        self._save_button.remove_class('vbox')
        self._save_button.add_class('hbox')
