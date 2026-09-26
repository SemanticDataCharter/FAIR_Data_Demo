"""
Demo views for C-Suite presentation.

Read-only presentation layer over the loaded study records and GraphDB.
"""
import hashlib
import json
import time
import logging

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from sdc4_shared.utils.dm_registry import get_dm_registry
from sdc4_shared.utils.graphdb_client import GraphDBClient

from . import entity_graph
from .narrative import BEATS
from .sparql_loader import load_query, load_all_queries, QUERY_CATALOG, SPARQL_DIR

logger = logging.getLogger(__name__)


def dashboard(request):
    """Domain cards with instance counts and GraphDB stats."""
    registry = get_dm_registry()

    # Build domain card data
    domains = []
    total_instances = 0
    for dm_ct_id, model_class in sorted(registry.items(), key=lambda x: getattr(x[1], 'DM_LABEL', '')):
        count = model_class.objects.count()
        total_instances += count
        domains.append({
            'label': getattr(model_class, 'DM_LABEL', model_class.__name__),
            'app_label': model_class._meta.app_label,
            'count': count,
        })

    # GraphDB health and triple count (cached for 1 hour)
    client = GraphDBClient()
    graphdb_healthy = client.health_check()
    triple_count = cache.get('dashboard_triple_count', 0)
    if triple_count == 0 and graphdb_healthy:
        result = client.query_sparql('SELECT (COUNT(*) AS ?cnt) WHERE { ?s ?p ?o }')
        if result and 'results' in result:
            bindings = result['results'].get('bindings', [])
            if bindings:
                triple_count = int(bindings[0]['cnt']['value'])
                cache.set('dashboard_triple_count', triple_count, 30)

    context = {
        'domains': domains,
        'total_instances': total_instances,
        'triple_count': triple_count,
        'graphdb_healthy': graphdb_healthy,
        'query_count': len(QUERY_CATALOG),
    }
    return render(request, 'demo/dashboard.html', context)


def narrative(request):
    """7-beat Contagion walkthrough."""
    return render(request, 'demo/narrative.html', {'beats': BEATS})


def explorer(request):
    """SPARQL query editor with pre-loaded queries."""
    queries = load_all_queries()
    # Serialize for JS consumption via json_script
    queries_json = {str(k): v['sparql'] for k, v in queries.items()}
    context = {
        'queries': queries,
        'queries_json': queries_json,
    }
    return render(request, 'demo/explorer.html', context)


@require_POST
def run_query(request):
    """HTMX endpoint: execute a SPARQL query and return results partial."""
    query_number = request.POST.get('query_number')
    raw_sparql = request.POST.get('sparql', '').strip()
    source = request.POST.get('source', 'explorer')

    # Determine SPARQL text
    if query_number:
        sparql = load_query(int(query_number))
        if not sparql:
            entry = QUERY_CATALOG.get(int(query_number))
            if entry:
                expected = SPARQL_DIR / entry['file']
                detail = f'File: {expected} (dir exists: {SPARQL_DIR.exists()}, file exists: {expected.exists()})'
            else:
                detail = f'No catalog entry for query {query_number}'
            logger.error('SPARQL load failed: %s', detail)
            return HttpResponse(
                f'<div class="alert alert-danger">Query file not found. {detail}</div>'
            )
    elif raw_sparql:
        sparql = raw_sparql
    else:
        return HttpResponse(
            '<div class="alert alert-warning">No query provided.</div>'
        )

    # Check cache first. The key prefix names the row shape; bump it when the
    # shape changes or a deploy renders stale rows into a new template.
    cache_key = f"sparql3:{hashlib.sha256(sparql.encode()).hexdigest()[:16]}"
    cached = cache.get(cache_key)

    if cached:
        context = dict(cached, elapsed='0.000')
    else:
        # Execute against GraphDB
        client = GraphDBClient()
        start = time.monotonic()
        result = client.query_sparql(sparql)
        elapsed = time.monotonic() - start

        if result is None:
            return HttpResponse(
                '<div class="alert alert-danger">'
                'Query execution failed. Check GraphDB connection and query syntax.'
                '</div>'
            )

        # Parse SPARQL JSON results. Variables that carry a record IRI (?inst,
        # ?inst_2, ...) are not columns: they address the record behind the row,
        # and they are what the entity graph is drawn from.
        all_vars = result.get('head', {}).get('vars', [])
        bindings = result.get('results', {}).get('bindings', [])
        variables = [v for v in all_vars if not entity_graph.RECORD_VAR.fullmatch(v)]
        record_iris = entity_graph.record_iris_from_bindings(all_vars, bindings)
        graph = entity_graph.build(record_iris, client) if record_iris else None
        by_iri = {n['iri']: n for n in graph['nodes'] if n.get('type') == 'record'} if graph else {}
        rows = []
        for binding in bindings:
            cells = [binding.get(v, {}).get('value', '') for v in variables]
            links = []
            for v in all_vars:
                cell = binding.get(v)
                if v not in variables and cell and cell.get('type') == 'uri' and cell['value'] in by_iri:
                    n = by_iri[cell['value']]
                    links.append({'url': n['console_url'], 'title': n['title'], 'domain': n['domain']})
            rows.append({'cells': cells, 'links': links})

        context = {
            'variables': variables,
            'rows': rows,
            'row_count': len(rows),
            'graph': graph,
            'node_count': sum(1 for n in graph['nodes'] if n.get('type') == 'record') if graph else 0,
            'edge_count': len(graph['edges']) if graph else 0,
        }
        cache.set(cache_key, context)
        context = dict(context, elapsed=f'{elapsed:.3f}')

    context['uid'] = f"{source}-{query_number or cache_key[-8:]}"
    context['graph_script_id'] = f"graph-data-{context['uid']}"
    template = 'demo/_beat_results.html' if source == 'narrative' else 'demo/_query_results.html'
    return render(request, template, context)
