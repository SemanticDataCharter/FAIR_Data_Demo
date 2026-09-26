"""
Two cross-study questions, answered from the triple store.

The first build of this demonstration could not answer either: each study minted
its own components, and a query that joined on a shared component returned
nothing. The second build composes the three study models from the same
libraries, so the store can be asked which components the studies share and
what each study says on a shared one, and it answers from the records.
"""
import time
from typing import Any, Dict, List

from django.core.cache import cache

from sdc4_shared.utils.dm_registry import get_dm_registry
from sdc4_shared.utils.graphdb_client import GraphDBClient

CACHE_SECONDS = 24 * 3600   # the answers are keyed by the record count, so a reload invalidates them


def _loaded() -> tuple:
    """Records and models in PostgreSQL: the totals the page states, and the cache key for the store's answers."""
    counts = {ct: m.objects.count() for ct, m in get_dm_registry().items()}
    return sum(counts.values()), sum(1 for c in counts.values() if c)

PREFIXES = """PREFIX sdc4: <https://semanticdatacharter.com/ns/sdc4/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc:   <http://purl.org/dc/elements/1.1/>
"""

# Every component records of more than one model carry, with how many models and records.
GOV = ("Audit ", "Activity ", "Agent ", "Was ", "Software ")
GOV_EXACT = ("Started At", "Ended At", "Purpose of Use", "Confidentiality", "Provenance Agent Type", "PROV Agent Type", "System Identifier", "System Location Name",
             "Data Subject Reference", "Used Entity Reference", "Had Plan Reference", "On Behalf Of Reference", "Acted On Behalf Of Reference", "Error Message")
_GOV_FILTER = " && ".join(f'!STRSTARTS(?label, "{g}")' for g in GOV) + " && ?label NOT IN (" + ", ".join(f'"{g}"' for g in GOV_EXACT) + ")"
SHARED = PREFIXES + """
SELECT ?label ?mc (COUNT(DISTINCT ?dm) AS ?models) (COUNT(DISTINCT ?i) AS ?records) (GROUP_CONCAT(DISTINCT ?title; separator=", ") AS ?studies)
WHERE {
  ?f sdc4:inInstance ?i ; sdc4:inDataModel ?dm ; rdfs:label ?label ; rdf:reifies <<?mc ?vp ?v>> .
  ?dm dc:title ?title . FILTER(CONTAINS(?title, " "))
  FILTER(%s)
}
GROUP BY ?label ?mc
HAVING (COUNT(DISTINCT ?dm) > 1)
ORDER BY DESC(?models) DESC(?records) ?label
LIMIT %%d
""" % _GOV_FILTER

# One record per shared component per model, so a row can open in the console.
SAMPLES = PREFIXES + """
SELECT ?mc ?dm (SAMPLE(?i) AS ?inst) WHERE {
  ?f sdc4:inInstance ?i ; sdc4:inDataModel ?dm ; rdf:reifies <<?mc ?vp ?v>> .
  FILTER(?mc IN (%s))
} GROUP BY ?mc ?dm
"""

# Chronic conditions: one component per condition, the basis stated per record.
CONDITIONS = PREFIXES + """
SELECT ?condition ?study ?basis (COUNT(DISTINCT ?i) AS ?records) (SUM(IF(?v = "Yes", 1, 0)) AS ?yes) (SAMPLE(?i) AS ?inst) (SAMPLE(?dm) AS ?dmid)
WHERE {
  ?f sdc4:inInstance ?i ; sdc4:inDataModel ?dm ; rdfs:label ?condition ; rdf:reifies <<?mc ?vp ?v>> .
  FILTER(STRSTARTS(?condition, "Condition: "))
  ?b sdc4:inInstance ?i ; rdfs:label "Condition Indicator Basis" ; rdf:reifies <<?mcb ?vpb ?basis>> .
  ?dm dc:title ?study . FILTER(CONTAINS(?study, " "))
}
GROUP BY ?condition ?study ?basis
ORDER BY ?condition ?study
"""


def _rows(client, query):
    result = client.query_sparql(query)
    return (result or {}).get('results', {}).get('bindings', [])


def _v(binding, key, default=''):
    return binding.get(key, {}).get('value', default)


def coverage(limit: int = 200) -> Dict[str, Any]:
    """Which components do the studies share, and how many records carry each."""
    records, models = _loaded()
    key = f'console:coverage:{records}:{limit}'
    hit = cache.get(key)
    if hit:
        return hit
    client = GraphDBClient()
    started = time.monotonic()
    try:
        shared = _rows(client, SHARED % limit)
    except Exception:
        return {'unavailable': 'The triple store did not answer.'}
    if not shared:
        return {'unavailable': 'No records carrying a shared component were found.'}
    mcs = [_v(b, 'mc') for b in shared]
    samples = _rows(client, SAMPLES % ", ".join(f"<{m}>" for m in mcs)) if mcs else []
    elapsed = time.monotonic() - started
    first: Dict[str, Dict[str, str]] = {}
    for smp in samples:
        mc = _v(smp, 'mc')
        if mc not in first:
            first[mc] = {'ct_id': _v(smp, 'dm').rsplit('/', 1)[-1].replace('dm-', ''), 'instance_id': _v(smp, 'inst').rsplit('/', 1)[-1]}
    rows: List[Dict[str, Any]] = []
    for b in shared:
        studies = _v(b, 'studies')
        study_count = len({t.strip().split(' ')[0] for t in studies.split(',') if t.strip()})   # the study is the title's first word
        rows.append({'label': _v(b, 'label'), 'ct_id': _v(b, 'mc').rsplit('/', 1)[-1].replace('mc-', ''), 'models': int(_v(b, 'models', '0')),
                     'records': int(_v(b, 'records', '0')), 'studies': studies, 'study_count': study_count, 'open': first.get(_v(b, 'mc'))})
    rows.sort(key=lambda r: (-r['study_count'], -r['models'], -r['records'], r['label']))
    out = {
        'records': records, 'models': models,
        'shared': len(rows), 'multi_study': sum(1 for r in rows if r['study_count'] > 1), 'all_three': sum(1 for r in rows if r['study_count'] >= 3),
        'rows': [r for r in rows if r['study_count'] > 1], 'within_only': sum(1 for r in rows if r['study_count'] == 1),
        'elapsed': f'{elapsed:.2f}', 'query': SHARED % limit,
    }
    cache.set(key, out, CACHE_SECONDS)
    return out


def conditions() -> dict:
    """What each study says on each chronic condition, and the basis it says it on."""
    records, _ = _loaded()
    key = f'console:conditions:{records}'
    hit = cache.get(key)
    if hit:
        return hit
    client = GraphDBClient()
    started = time.monotonic()
    try:
        rows = _rows(client, CONDITIONS)
    except Exception:
        return {'unavailable': 'The triple store did not answer.'}
    if not rows:
        return {'unavailable': 'No records carrying a chronic condition indicator were found.'}
    elapsed = time.monotonic() - started
    out = []
    for r in rows:
        inst = _v(r, 'inst')
        out.append({'condition': _v(r, 'condition').replace('Condition: ', ''), 'study': _v(r, 'study'), 'basis': _v(r, 'basis'),
                    'records': int(_v(r, 'records', '0')), 'yes': int(_v(r, 'yes', '0')),
                    'open': {'ct_id': _v(r, 'dmid').rsplit('/', 1)[-1].replace('dm-', ''), 'instance_id': inst.rsplit('/', 1)[-1]} if inst else None})
    result = {'rows': out, 'conditions': len({r['condition'] for r in out}), 'elapsed': f'{elapsed:.2f}', 'query': CONDITIONS}
    cache.set(key, result, CACHE_SECONDS)
    return result
