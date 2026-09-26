"""
The neighbourhood of one instance in the triple store.

Deliberately one hop and deliberately plain. Every graph product draws a canvas;
the argument this console makes is not that we can draw one, it is that the
nodes on it were generated from a governed model and resolve back to a validated
record. So this asks the triple store what is actually there rather than
illustrating what might be.
"""
import math
from typing import Any, Dict, List

from sdc4_shared.utils.graphdb_client import GraphDBClient

SDC4 = 'https://semanticdatacharter.com/ns/sdc4/'

# Fields, and the model they belong to, one hop from the instance node.
NEIGHBOURS = """
PREFIX sdc4: <https://semanticdatacharter.com/ns/sdc4/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?field ?label ?cluster WHERE {{
  GRAPH <{graph}> {{
    ?field sdc4:inInstance <{instance}> ;
           rdfs:label ?label .
    OPTIONAL {{ ?field sdc4:inCluster ?cluster }}
  }}
}} ORDER BY ?label
"""


def _short(uri: str) -> str:
    return uri.replace(SDC4, 'sdc4:') if uri else ''


def neighbourhood(model, instance, limit: int = 12) -> Dict[str, Any]:
    """
    Return laid-out nodes and edges, or a plain reason there are none.

    Never raises: a triple store that is down should leave the projection
    saying so, not break the record page around it.
    """
    graph_uri = instance.fuseki_graph_uri
    if instance.rdf_sync_status != 'synced' or not graph_uri:
        return {'unavailable': (
            'This instance was not projected into the triple store '
            f'(sync status: {instance.rdf_sync_status}), so there is nothing '
            'to draw. Validity is not the reason: every instance is projected, '
            'invalid ones included, carrying sdc4:validationStatus so a query '
            'can decide what to do with them.'
        )}

    instance_uri = f'{SDC4}{instance.instance_id}'
    query = NEIGHBOURS.format(graph=graph_uri, instance=instance_uri)

    try:
        result = GraphDBClient().query_sparql(query)
    except Exception:
        result = None
    if not result:
        return {'unavailable': 'The triple store did not answer. The other two '
                               'projections are unaffected.'}

    rows = result.get('results', {}).get('bindings', [])
    if not rows:
        return {'unavailable': 'No triples found in this instance graph.'}

    fields = [
        {'label': r['label']['value'], 'uri': r['field']['value'],
         'cluster': r.get('cluster', {}).get('value', '')}
        for r in rows
    ]
    shown, hidden = fields[:limit], max(0, len(fields) - limit)

    # Radial layout, computed here so the template stays markup. Deterministic:
    # the same record draws the same picture every time, which matters when the
    # point being made is that nothing here is generated on a whim.
    w, h = 760, 380
    cx, cy = w / 2, h / 2
    rx, ry = 250, 132
    nodes: List[Dict[str, Any]] = []
    for i, f in enumerate(shown):
        angle = (2 * math.pi * i / len(shown)) - math.pi / 2
        nodes.append({
            'label': f['label'],
            'x': round(cx + rx * math.cos(angle), 1),
            'y': round(cy + ry * math.sin(angle), 1),
            'anchor': 'start' if math.cos(angle) > 0.2 else ('end' if math.cos(angle) < -0.2 else 'middle'),
        })

    return {
        'width': w, 'height': h, 'cx': cx, 'cy': cy,
        'centre': {
            'label': getattr(model, 'DM_LABEL', model.__name__),
            'instance_id': instance.instance_id,
        },
        'model_uri': _short(f'{SDC4}dm-{getattr(model, "DM_CT_ID", "")}'),
        'nodes': nodes,
        'shown': len(shown),
        'total': len(fields),
        'hidden': hidden,
        'graph_uri': graph_uri,
        'cluster': _short(fields[0]['cluster']) if fields[0]['cluster'] else '',
    }
