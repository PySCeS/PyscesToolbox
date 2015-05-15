import json
from os import path
from time import sleep

from IPython.display import display
from IPython.html import widgets
from numpy import floor
from pysces import ModelMap
from sympy import Symbol

from ... import modeltools
from d3networkx_psctb import ForceDirectedGraph
from d3networkx_psctb import EventfulGraph


RGB_RGB_RGB_ = {0: "rgb(94,79,162)", 1: "rgb(50,136,189)",
                2: "rgb(102,194,165)", 3: "rgb(171,221,164)",
                4: "rgb(230,245,152)", 5: "rgb(254,224,139)",
                6: "rgb(253,174,97)", 7: "rgb(244,109,67)",
                8: "rgb(213,62,79)", 9: "rgb(158,1,66)", 10: "rgb(158,1,66)"}

__author__ = 'carl'

__all__ = ['ModelGraph']


class ModelGraph(object):
    def __init__(self, mod, pos_dic=None, analysis_method=None,
                 base_name=None):
        super(ModelGraph, self).__init__()
        self._eventful_graph = EventfulGraph(sleep=0.05)
        self._force_directed_graph = ForceDirectedGraph(self._eventful_graph)
        self._force_directed_graph.height = 1000
        self._force_directed_graph.width = 900
        self.mod = mod
        self._model_map = ModelMap(mod)
        self._nodes_fixed = True
        if not analysis_method:
            analysis_method = 'modelgraph'
        self._analysis_method = analysis_method
        self._working_dir = modeltools.make_path(self.mod,
                                                 self._analysis_method)


        self._default_base_name = 'model_scheme'
        if not base_name:
            base_name = self._default_base_name
        self._base_name = base_name

        self._top_box = widgets.VBox()
        self._big_box = widgets.VBox()
        self._big_box.children = (
            self._top_box, widgets.HTML('<hr>'), self._force_directed_graph)

        if not pos_dic:
            try:
                with open(path.join(self._working_dir,
                                    'graph_layout.dict'), 'r') as f:
                    self._pos_dic = json.load(f)
            except:
                self._clear_pos_dic()
        else:
            if pos_dic == 'clear':
                self._clear_pos_dic()
            else:
                with open(pos_dic,'r') as f:
                    self._pos_dic = json.load(f)

        self._elas_dic = {}
        self._pos_change_setup()
        self._save_image_setup()

    def _clear_pos_dic(self):
        self._pos_dic = {}
        for sp in self._model_map.species:
            self._pos_dic[sp.name] = ('none', 'none')
        for rx in self._model_map.reactions:
            self._pos_dic[rx.name] = ('none', 'none')


    # TODO Change d3networkx_psctb so that dumping json and dumping svg work in the same way
    def _pos_change_setup(self):
        def make_pos_dic(nodes_json):
            raw_json = json.loads(nodes_json)
            pos_dic = {}
            for each in raw_json:
                pos_dic[str(each['id'])] = (each['x'], each['y'])
            return pos_dic

        def save_json(sender):
            pos_dic = make_pos_dic(self._force_directed_graph.gnode_json)
            self._pos_dic = pos_dic
            with open(path.join(self._working_dir, 'graph_layout.dict'),
                      'w') as f:
                json.dump(pos_dic, f)

        self._force_directed_graph.on_trait_change(save_json, 'gnode_json')

    def _save_image_setup(self):
        def save_image(sender, content):
            if 'button_click' in content:
                if content['button_click'] == 'save_image':
                    self.save()

        self._force_directed_graph.on_msg(save_image)


    def _make_species_nodes(self):
        for species in self._model_map.species:
            pos = self._pos_dic.get(species.name)
            if pos:
                x, y = pos
            else:
                x, y = "none", "none"
            self._eventful_graph.add_node(species.name,
                                          fill="#FF6138",
                                          stroke="#FF6138",
                                          color='black',
                                          shape='circle',
                                          label=species.name,
                                          dx=15,
                                          dy=7,
                                          font_size=20,
                                          x=x,
                                          y=y,
                                          fixed=True,
                                          r=11,
                                          )

    def _make_reaction_nodes(self):
        for reaction in self._model_map.reactions:
            pos = self._pos_dic.get(reaction.name)
            if pos:
                x, y = pos
            else:
                x, y = "none", "none"
            self._eventful_graph.add_node(reaction.name,
                                          fill="#00A388",
                                          stroke="#00A388",
                                          color='black',
                                          shape='rect',
                                          label=reaction.name,
                                          dx=15,
                                          dy=7,
                                          font_size=20,
                                          x=x,
                                          y=y,
                                          fixed=True,
                                          r=8,
                                          )

    def _make_substrate_links(self):
        for species in self._model_map.species:
            for reaction in species.isSubstrateOf():
                elas = 'ec%s_%s' % (reaction, species.name)
                self._eventful_graph.add_edge(reaction,
                                              species.name,
                                              name=elas,
                                              strokewidth="0px",
                                              distance=200,
                                              stroke='black')
                self._eventful_graph.adj[reaction][species.name][
                    'strokewidth'] = '2px'
                self._elas_dic[elas] = (reaction, species.name)
                del self._eventful_graph.adj[species.name][reaction]

    def _make_product_links(self):
        for species in self._model_map.species:
            for reaction in species.isProductOf():
                elas = 'ec%s_%s' % (reaction, species.name)
                self._eventful_graph.add_edge(species.name,
                                              reaction,
                                              name=elas,
                                              strokewidth="0px",
                                              distance=200,
                                              stroke='black',
                                              marker_end='arrowhead')
                self._eventful_graph.adj[reaction][species.name][
                    'strokewidth'] = '2px'
                del self._eventful_graph.adj[species.name][reaction]
                self._elas_dic[elas] = (reaction, species.name)

    def _make_modifier_links(self):
        for species in self._model_map.species:
            for reaction in species.isModifierOf():
                elas = 'ec%s_%s' % (reaction, species.name)
                self._eventful_graph.add_edge(reaction,
                                              species.name,
                                              name=elas,
                                              strokewidth="0px",
                                              distance=200,
                                              stroke='gray',
                                              marker_end='dagger', )
                self._eventful_graph.adj[species.name][reaction][
                    'strokewidth'] = '2px'
                del self._eventful_graph.adj[reaction][species.name]
                self._elas_dic[elas] = (species.name, reaction)

    def remove_external_modifier_links(self):
        for species in self._model_map.species:
            for reaction in species.isModifierOf():
                if species.name in self.mod.parameters:
                    self._eventful_graph.adj[species.name][reaction][
                        'strokewidth'] = '0px'

    def remove_sinks(self):
        for each in ['dummy', 'sink']:
            if each in self._eventful_graph.node:
                del self._eventful_graph.node[each]

    def change_link_properties(self, elas, prop_dic=None,
                               only_overwrite=False):
        if not prop_dic:
            prop_dic = {}
        s_t = self._elas_dic.get(elas)
        if s_t:
            source, target = s_t
            dic_to_change = self._eventful_graph.adj[source][target]
            for k, v in prop_dic.iteritems():
                if only_overwrite and k in dic_to_change or not only_overwrite:
                    dic_to_change[k] = v

    def change_node_properties(self, node_name, prop_dic=None):
        if not prop_dic:
            prop_dic = {}
        dic = self._eventful_graph.node.get(node_name)
        if dic:
            for k, v in prop_dic.iteritems():
                dic[k] = v

    def draw_all_links(self):
        self._make_substrate_links()
        self._make_product_links()
        self._make_modifier_links()

    @property
    def nodes_fixed(self):
        return self._nodes_fixed

    @nodes_fixed.setter
    def nodes_fixed(self, value):
        self._nodes_fixed = value
        for node in self._model_map.reactions + self._model_map.species:
            self.change_node_properties(node.name,
                                        {'fixed': self._nodes_fixed})


    @property
    def straight_links(self):
        return self._force_directed_graph.straight_links

    @straight_links.setter
    def straight_links(self, value):
        self._force_directed_graph.straight_links = value

    @property
    def height(self):
        return self._force_directed_graph.height

    @height.setter
    def height(self, value):
        self._force_directed_graph.height = value

    @property
    def width(self):
        return self._force_directed_graph.height

    @width.setter
    def width(self, value):
        self._force_directed_graph.width = value

    def save(self, file_name=None):
        """Saves the image.

        Saves the image to either the default working directory or to an a
        specified location.
        Parameters
        ----------
        file_name : str, Optional (default : None)
            An optional path to which the image will be saved.

        Returns
        -------
        None
        """

        svg = self._force_directed_graph.svg_image

        file_name = modeltools.get_file_path(working_dir=self._working_dir,
                                             internal_filename=self._base_name,
                                             fmt='svg',
                                             file_name=file_name)
        with open(file_name, 'w') as f:
            f.write(svg)


    def show(self, no_links=False, clear_top_box=True):
        if clear_top_box:
            self._top_box.children = ()
        self._base_name = self._default_base_name
        display(self._big_box)
        self._eventful_graph.node.clear()
        self._make_species_nodes()
        self._make_reaction_nodes()
        self.nodes_fixed = self._nodes_fixed
        if not no_links:
            self.draw_all_links()


    def highlight_cp(self, cp):
        colors = RGB_RGB_RGB_
        symbols = cp.numerator.atoms(Symbol)
        title = widgets.Latex('Control Patterns for $' + cp.parent.latex_name + '$')
        CP_repr = widgets.Latex('$~$')


        cat = floor(cp.percentage / 10)

        CP_repr.value = cp._repr_latex_()

        hr = widgets.HTML('<hr>')

        titles = widgets.VBox()
        titles.children = (title, hr, CP_repr, hr)
        self._top_box.children = (titles,)
        self.show(clear_top_box=False)
        self._make_product_links()
        self._make_substrate_links()
        self._make_modifier_links()
        self._force_directed_graph.show_color_legend = False
        self._force_directed_graph.show_color_legend = True
        for sym in symbols:
            self.change_link_properties(str(sym),
                                        {'strokewidth': '20px',
                                         'marker_end': 'arrowheadlarge',
                                         'stroke': colors[cat]},
                                        only_overwrite=True)

        self._base_name = cp.parent.name + '_' + cp.name


    def highlight_cc(self, cc):
        colors = RGB_RGB_RGB_
        title = widgets.Latex('Control Patterns for $' + cc.latex_name + '$')
        CP_repr = widgets.Latex('$~$')

        def onclick_maker(cp):
            symbols = cp.numerator.atoms(Symbol)

            def click(sender):
                self._base_name = cc.name + '_' + cp.name
                cat = floor(cp.percentage / 10)
                self._make_product_links()
                self._make_substrate_links()
                self._make_modifier_links()
                self._force_directed_graph.show_color_legend = False
                self._force_directed_graph.show_color_legend = True
                for sym in symbols:
                    self.change_link_properties(str(sym),
                                                {'strokewidth': '20px',
                                                 'marker_end': 'arrowheadlarge',
                                                 'stroke': colors[cat]},
                                                only_overwrite=True)


                CP_repr.value = cp._repr_latex_()

            return click

        button_list = []
        for k, v in cc.control_patterns.iteritems():
            but = widgets.Button()
            but.description = k
            click = onclick_maker(v)
            but.on_click(click)
            button_list.append(but)

        hr = widgets.HTML('<hr>')

        titles = widgets.VBox()
        titles.children = (title, hr, CP_repr, hr)
        buttons = widgets.HBox()
        buttons.children = tuple(button_list)
        self._top_box.children = (titles, buttons)
        self.show(clear_top_box=False)