from .widget import ForceDirectedGraph
from .eventful_graph import EventfulGraph, empty_eventfulgraph_hook

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': '.',
        'dest': 'd3networkx_psctb',
        'require': 'd3networkx_psctb/widget'
}]