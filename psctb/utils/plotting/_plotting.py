from os import path, mkdir
from collections import OrderedDict

from IPython.display import display, clear_output
from matplotlib import pyplot as plt
from matplotlib import transforms
from matplotlib import rcParams
from numpy import linspace
from IPython.html import widgets
from pysces import ModelMap
from pysces import output_dir as psc_out_dir
import pysces

from ..misc import *
from ...latextools import LatexExpr
from ... import modeltools


exportLAWH = silence_print(pysces.write.exportLabelledArrayWithHeader)

"""
This whole module is fd in the a
"""
__all__ = ['LineData',
           'ScanFig',
           'Data2D']


def _add_legend_viewlim(ax, **kwargs):
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
        return ax.legend(label_objs, label_texts, **kwargs)

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

    def add_property(self, key, value):
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
    """
    An object that wraps results from a PySCeS parameter scan.

    Results from a parameter scan used to initialise this object which in turn
    is used to create a ``ScanFig`` object.

    Parameters
    ----------
    mod : PysMod
        The model for which the parameter scan was performed.
    column_names : list of str
        The names of each column in the data_array. Columns should be arranged
        with the input values (scan_in) in the first column and the output
        values (scan_out) in the columns that follow.
    data_array : ndarray
        An array containing results from a parameter scan. Arranged as
        described above.
    ltxe : LatexExpr, optional (Default : None)
        A LatexExpr object that is used to convert PySCeS compatible
        expressions to LaTeX math. If None is supplied a new LatexExpr object
        will be instantiated, but when working with multiple objects that make
        use of the LatexExpr class, it saves memory to share a single
        instance between them.
    analysis_method : str, Optional (Default : None)
        A string that indicates the name of the analysis method used to
        generate the results that populate ``Data2D``. This will determine
        where results are saved by ``Data2D`` as well as any ``ScanFig``
        objects that are produced by it.
    ax_properties : dict, Optional (Default : None)
        A dictionary of properties that will be used by ``ScanFig`` to adjust
        the appearance of plots. These properties should compatible with
        ``matplotlib.axes.AxesSubplot'' object in a way that its ``set``
        method can be used to change its properties. If none, a default
        ``ScanFig`` object is produced by the ``plot`` method.
    file_name : str, Optional (Default : None)
        The name that should be prepended to files produced any ``ScanFig``
        objects produced by ``Data2D``. If None, defaults to 'scan_fig'.

    See Also
    --------
    ScanFig
    Data2D
    RateChar
    """

    def __init__(self,
                 mod,
                 column_names,
                 data_array,
                 ltxe=None,
                 analysis_method=None,
                 ax_properties=None,
                 file_name=None,
                 additional_cat_classes=None,
                 additional_cats=None):
        self.plot_data = DotDict()
        self.plot_data['scan_in'] = column_names[0]
        self.plot_data['scan_out'] = column_names[1:]
        self.plot_data['scan_range'] = data_array[:, 0]
        self.plot_data['scan_results'] = data_array[:, 1:]
        self.plot_data['scan_points'] = len(self.plot_data.scan_range)

        self._column_names = column_names
        self._scan_results = data_array

        # self.column_names = column_names
        #self.column_names_in = column_names[0]
        #.column_names_out = column_names[1:]

        #self.data = data_array
        #self.data_in = data_array[:, 0]
        #self.data_out = data_array[:, 1:]

        self._mod = mod
        if not ltxe:
            ltxe = LatexExpr(mod)
        self._ltxe = ltxe

        self._mod.doMcaRC()

        if not analysis_method:
            self._analysis_method = 'parameter_scan'
        else:
            self._analysis_method = analysis_method

        self._fname_specified = False

        if not file_name:
            self._fname = 'scan_data'
        else:
            self._fname = file_name
            self._fname_specified = True

        self._working_dir = modeltools.make_path(self._mod,
                                                 self._analysis_method)
        if not ax_properties:
            self._ax_properties_ = None
        else:
            self._ax_properties_ = ax_properties

        # So in order for ScanFig to have all those nice buttons that are
        # organised so well we need to set it up beforehand. Basically
        # each different line has different categories of lines that it falls
        # into. Then each each of these categories falls into a category class.
        # Each ``_category_classes`` key represents a category class and the
        # value is a list of categories that fall into a class.
        #
        # The dictionary ``_scan_types`` contains the different categories that
        # a line can fall into (in addition to the category containing itself).
        # Here a keys is a category and value is a list of lines in this
        # category.
        #
        # Buttons will be arranged so that a category class is a label under
        # which all the buttons that toggle a certain category is arranged
        # under. For instance under the lable 'All Coefficients' will be the
        # buttons 'Elasticity Coefficients', 'Control Coefficients',
        # 'Response Coefficients etc.
        #
        # We also add _scan_types to the ``_category_classes`` so that each
        # individual line has its own button.
        # There will therefore be a button called 'Control Coefficients' that
        # fall under the 'All Coefficients' category class label as well as a
        # label for the category class called 'Control Coefficients' under
        # which all the  different control coefficient buttons will be
        # arranged.

        self._category_classes = \
            OrderedDict([('All Coefficients',
                          ['Elasticity Coefficients',
                           'Control Coefficients',
                           'Response Coefficients',
                           'Partial Response Coefficients',
                           'Control Patterns']),
                         ('All Fluxes/Reactions/Species',
                          ['Flux Rates',
                           'Reaction Rates',
                           'Species Concentrations',
                           'Steady-State Species Concentrations'])])

        if additional_cat_classes:
            for k,v in additional_cat_classes.iteritems():
                if k in self._category_classes:
                    lst = self._category_classes[k]
                    new_lst = list(set(lst + v))
                    self._category_classes[k] = new_lst
                else:
                    self._category_classes[k] = v

        self._scan_types = \
            OrderedDict([
                ('Flux Rates',
                 ['J_' + reaction for reaction in mod.reactions]),
                ('Reaction Rates', [reaction for reaction in mod.reactions]),
                ('Species Concentrations', mod.species),
                ('Steady-State Species Concentrations',
                 [sp + '_ss' for sp in mod.species]),
                ('Elasticity Coefficients', ec_list(mod)),
                ('Control Coefficients', cc_list(mod)),
                ('Response Coefficients', rc_list(mod)),
                ('Partial Response Coefficients', prc_list(mod)),
                ('Control Patterns', ['CP' + str(n)
                                      for n in
                                      range(1, len(self._column_names))])
            ])

        if additional_cats:
            for k,v in additional_cats.iteritems():
                if k in self._scan_types:
                    lst = self._scan_types[k]
                    new_lst = list(set(lst + v))
                    self._scan_types[k] = new_lst
                else:
                    self._scan_types[k] = v

        self._setup_categories()
        self._setup_lines()
        self._category_classes.update(self._scan_types)

    def _setup_categories(self):
        """
        This method sets up the categories for each data column stored by this
        object. These categories are stored in a dictionary as
        ``self._column_categories``.

        Each line falls into its own category as well as another category
        depending on what type of data it represents. So 'Species1' will
        fall into the category 'Species1' as well as 'Species Concentrations'
        Therefore the ``ScanFig`` buttons labelled 'Species1' and 'Species
        Concentrations' need to be toggled on for the line representing
        the parameter scan results of Species1 to be visible on the
        ``ScanFig`` figure.
        """
        scan_types = self._scan_types
        column_categories = {}
        for column in self.plot_data.scan_out:
            column_categories[column] = [column]
            for k, v in scan_types.iteritems():
                if column in v:
                    column_categories[column].append(k)
                    break

        self._column_categories = column_categories

    def _setup_lines(self):
        """
        Sets up ``LineData`` objects that will be used to populate ``ScanFig``
        objects created by the ``plot`` method of ``Data2D``. These objects
        are stored in a list: ``self._lines``

        ``ScanFig`` takes a list of ``LineData`` objects as an argument and
        this method sets up that list. The ``self._column_categories``
        dictionary is used here.
        """
        lines = []
        for i, each in enumerate(self.plot_data.scan_out):
            line = LineData(name=each,
                            x_data=self.plot_data.scan_range,
                            y_data=self.plot_data.scan_results[:, i],
                            categories=self._column_categories[each],
                            properties={'label':
                                            '$%s$' %
                                            (self._ltxe.expression_to_latex(
                                                each)),
                                        'linewidth': 1.6})
            lines.append(line)
        self._lines = lines

    @property
    def _ax_properties(self):
        """
        Internal property of ``Data2D``. If no ``ax_properties`` argument is
        specified in __init__ this property defines the xlabel of the
        ``ScanFig`` object depending on the value of ``self.scan_in``.

        """
        if not self._ax_properties_:
            self._ax_properties_ = {'xlabel': self._x_name}
        return self._ax_properties_

    @property
    def _x_name(self):
        mm = ModelMap(self._mod)
        species = mm.hasSpecies()
        x_name = ''
        if self.plot_data.scan_in == 'Time':
            x_name = 'Time (s)'
        elif self.plot_data.scan_in in species:
            x_name = '[%s]' % self.plot_data.scan_in
        elif self.plot_data.scan_in in self._mod.parameters:
            x_name = self.plot_data.scan_in
        return x_name

    def plot(self):
        """
        Creates a ``ScanFig`` object using the data stored in the current
        instance of ``Data2D``

        Returns
        -------
        ``ScanFig``
            A `ScanFig`` object that is used to visualise results.
        """
        if self._fname_specified:
            base_name = self._fname
        else:
            base_name = 'scan_fig'
        scan_fig = ScanFig(self._lines,
                           category_classes=self._category_classes,
                           ax_properties=self._ax_properties,
                           working_dir=path.join(self._working_dir,
                                           self.plot_data.scan_in,),
                           base_name=base_name,)
        return scan_fig

    def save_data(self, file_name=None, separator=','):
        """
        Saves data stores in current instance of ``Data2D`` as a comma
        separated file.

        Parameters
        ----------
        file_name : str, Optional (Default : None)
            The file name, extension and path under which data should be saved.
            If None the name will default to scan_data.csv and will be saved
            either under the directory specified under the directory specified
            in ``folder``.
        separator : str, Optional (Default : ',')
            The symbol which should be used to separate values in the output
            file.
        folder : str, Optional (Default : None)
            The folder under which the file should be saved. Only comes into
            consideration if file_name is None. If None the file will be saved
            under the the folder specified in the ``self._working_dir`` field,
            which itself is determined by the ``analysis_method`` parameter of
            __init__.
        """
        file_name = modeltools.get_file_path(working_dir = self._working_dir,
                                             internal_filename = self._fname,
                                             fmt = 'csv',
                                             fixed = self.plot_data.scan_in,
                                             file_name = file_name)

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
    """
    Uses data in the form of a list of LineData objects to display interactive
    plots.

    Interactive plots can be customised in terms of which data is visible at
    any one time by simply clicking a button to toggle a line. Matplotlib
    figures are used internally, therefore ScanFig figures can be altered
    by changing the properties of the internal figure.

    Parameters
    ----------
    line_data_list : list of LineData objects
        A LineData object contains the information needed to draw a single
        curve on a matplotlib figure. Here a list of these objects are used
        to populate the internal matplotlib figure with the various curves
        that represent the results of a parameter scan or simulation.
    category_classes : dict, Optional (Default : None)
        Each line on a ScanFig plot falls into a different category. Each of
        these categories in turn fall into a different class. Each category
        represents a button which toggles the lines which fall into the
        category while the button is arranged under a label which is
        represented by a category class. Each key in this dict is a category
        class and the value is a list of categories that fall into this class.
        If None all categories will fall into the same class.
    fig_properties : dict, Optional (Default : None)
        A dictionary of properties that will be used to adjust the appearance
        of the figure. These properties should compatible with
        ``matplotlib.figure.Figure'' object in a way that its ``set``
        method can be used to change its properties. If None, default
        matplotlib figure properties will be used.
    ax_properties : dict, Optional (Default : None)
        A dictionary of properties that will be used to adjust the appearance
        of plot axes. These properties should compatible with
        ``matplotlib.axes.AxesSubplot'' object in a way that its ``set``
        method can be used to change its properties. If None default matplotlib
        axes properties will be used.
    fname : str, Optional (Default : None)
        The file name under which figures should be saved. If None, the name
        "ScanFig" will be used when save is used with default parameters.

    See Also
    --------
    LineData
    Data2D
    """
    def __init__(self, line_data_list,
                 category_classes=None,
                 fig_properties=None,
                 ax_properties=None,
                 base_name=None,
                 working_dir=None):

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

        if base_name:
            self._base_name = base_name
        else:
            self._base_name =  'scan_fig'

        if working_dir:
            self._working_dir = working_dir
        else:
            self._working_dir = psc_out_dir

        self._save_counter = 0

        self.lines
        if rcParams['backend'] == \
                'module://IPython.kernel.zmq.pylab.backend_inline':
            plt.close()
        self._save_button_ = None

    @property
    def _save_button(self):
        if not self._save_button_:
            def save(clicked):
                self.save()

            self._save_button_ = widgets.Button()
            self._save_button_.description = 'Save'
            self._save_button_.on_click(save)
        return self._save_button_

    def show(self):
        """
        Displays the figure.

        Depending on the matplotlib backend this function will either display
        the figure inline if running in an ``IPython`` notebook with the
        ``--pylab=inline`` switch or with the %matplotlib inline IPython line
        magic, alternately it will display the figure as determined by the
        ``rcParams['backend']`` option of ``matplotlib``. Either the inline or
        nbagg backends are recommended.

        See Also
        --------
        interact
        adjust_figure
        """

        _add_legend_viewlim(
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

    def save(self, file_name=None, dpi=None, fmt=None):
        """


        """
        if not fmt:
            fmt = 'svg'

        if not dpi:
            dpi = 180

        file_name = modeltools.get_file_path(working_dir = self._working_dir,
                                             internal_filename= self._base_name,
                                             fmt = fmt,
                                             file_name = file_name)
        fmt = modeltools.get_fmt(file_name)

        self.fig.savefig(file_name,
                         format=fmt,
                         dpi=dpi,
                         bbox_extra_artists=(self.ax.get_legend(),),
                         bbox_inches='tight')

    @property
    def _widgets(self):
        if not self._widgets_:
            widget_classes = OrderedDict()
            for k in self.category_classes.iterkeys():
                widget_classes[k] = widgets.HBox()

            def oc(cat):
                def on_change(name, value):
                    self.toggle_category(cat, value)
                    self.show()

                return on_change

            for each in self.categories:
                w = widgets.ToggleButton()
                w.description = each
                w.value = self.categories_status[each]
                on_change = oc(each)
                w.on_trait_change(on_change, 'value')
                for k, v in self.category_classes.iteritems():
                    if each in v:
                        widget_classes[k].children += (w),

            # this is needed to sort widgets according to alphabetical order
            for k, v in widget_classes.iteritems():
                children_list = list(v.children)
                names = [getattr(widg, 'description')
                         for widg in children_list]
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
            else:
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
            min_x = widgets.FloatText()
            max_x = widgets.FloatText()
            min_x.value, max_x.value = self.ax.get_xlim()
            min_x.description = 'min'
            max_x.description = 'max'

            min_y = widgets.FloatText()
            max_y = widgets.FloatText()
            min_y.value, max_y.value = self.ax.get_ylim()
            min_y.description = 'min'
            max_y.description = 'max'

            log_x = widgets.Checkbox()
            log_y = widgets.Checkbox()
            log_x.value = convert_scale(self.ax.get_xscale())
            log_y.value = convert_scale(self.ax.get_yscale())
            log_x.description = 'x_log'
            log_y.description = 'y_log'

            apply_btn = widgets.Button()
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

            x_lims = widgets.HBox(children=[min_x, max_x])
            y_lims = widgets.HBox(children=[min_y, max_y])
            lin_log = widgets.HBox(children=[log_x, log_y])
            apply_con = widgets.HBox(children=[apply_btn])

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

                # set width to a default width of 2
                # bc the default value of one is too low
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
                head = widgets.Latex(value=k)
                display(head)
                display(v)
                # v.remove_class('vbox')
                # v.add_class('hbox')
                # v.set_css({'flex-wrap': 'wrap'})
        display(widgets.Latex(value='$~$'))
        display(self._save_button)
        # self._save_button.remove_class('vbox')
        # self._save_button.add_class('hbox')

    def adjust_figure(self):
        self.show()
        for k, v in self._figure_widgets.iteritems():
            if len(v.children) > 0:
                head = widgets.Latex(value=k)
                display(head)
                display(v)
                # v.remove_class('vbox')
                # v.add_class('hbox')
                # v.set_css({'flex-wrap': 'wrap'})
        display(widgets.Latex(value='$~$'))
        display(self._save_button)
        # self._save_button.remove_class('vbox')
        # self._save_button.add_class('hbox')
