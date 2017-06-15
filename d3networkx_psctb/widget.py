import ipywidgets as widgets # Widget definitions
from traitlets import Unicode, CInt, CFloat, Bool # Import the base Widget class and the traitlets Unicode class.

# Define our ForceDirectedGraph and its target model and default view.
class ForceDirectedGraph(widgets.DOMWidget):
    _view_module = Unicode('nbextensions/d3networkx_psctb/widget', sync=True)
    _view_name = Unicode('D3ForceDirectedGraphView', sync=True)

    width = CInt(500).tag(sync=True)
    height = CInt(500).tag(sync=True)
    charge = CFloat(270.).tag(sync=True)
    distance = CInt(30.).tag(sync=True)
    strength = CInt(0.3).tag(sync=True)
    gnode_json = Unicode(sync=True)
    straight_links = Bool(False).tag(sync=True)
    show_color_legend = Bool(False).tag(sync=True)

    svg_image = Unicode().tag(sync=True)

    def __init__(self, eventful_graph, *pargs, **kwargs):
        widgets.DOMWidget.__init__(self, *pargs, **kwargs)

        self._eventful_graph = eventful_graph
        self._send_dict_changes(eventful_graph.graph, 'graph')
        self._send_dict_changes(eventful_graph.node, 'node')
        self._send_dict_changes(eventful_graph.adj, 'adj')

    # def _dump_svg(self):
    #     self.send({'dict':'save_svg', 'action':None, 'key':None})

    def _ipython_display_(self, *pargs, **kwargs):

        # Show the widget, then send the current state
        widgets.DOMWidget._ipython_display_(self, *pargs, **kwargs)
        for (key, value) in self._eventful_graph.graph.items():
            self.send({'dict': 'graph', 'action': 'add', 'key': key, 'value': value})
        for (key, value) in self._eventful_graph.node.items():
            self.send({'dict': 'node', 'action': 'add', 'key': key, 'value': value})
        for (key, value) in self._eventful_graph.adj.items():
            self.send({'dict': 'adj', 'action': 'add', 'key': key, 'value': value})

    def _send_dict_changes(self, eventful_dict, dict_name):
        def key_add(key, value):
            self.send({'dict': dict_name, 'action': 'add', 'key': key, 'value': value})
        def key_set(key, value):
            self.send({'dict': dict_name, 'action': 'set', 'key': key, 'value': value})
        def key_del(key):
            self.send({'dict': dict_name, 'action': 'del', 'key': key})
        eventful_dict.on_add(key_add)
        eventful_dict.on_set(key_set)
        eventful_dict.on_del(key_del)
