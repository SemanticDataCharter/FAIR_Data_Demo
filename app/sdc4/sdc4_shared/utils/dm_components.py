"""
The components each published model composes, read from the library schemas.

Every ``dm-<ct_id>.xsd`` in the library carries one block per component it
composes, introduced by ``<!-- Schema for component <label> (<ct_id>) -->``.
That is enough to know, without asking the store, which component a label
names in a model and which models compose a component. The store is asked
about records; the schema is asked about composition.

Why this matters for the queries: a field reifier in the store is
``https://semanticdatacharter.com/ns/dm/v_<component ct_id>_<instance id>``
and reifies ``<<sdc4:mc-<ct_id> ?p ?value>>``. A query that binds the
component (a constant, a VALUES list, or the reifier IRI built from the
component and the instance) answers in a fraction of a second; one that leaves
the component unbound in the triple term scans every reifier in the store.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, List

from django.conf import settings

_BLOCK = re.compile(r'<!-- Schema for component (.+?) \(([a-z0-9]{24})\) -->')
REIFIER_BASE = 'https://semanticdatacharter.com/ns/dm/v_'


@lru_cache(maxsize=None)
def components() -> Dict[str, Dict[str, str]]:
    """{model ct_id: {component ct_id: label}} for every model schema in the library."""
    out: Dict[str, Dict[str, str]] = {}
    dmlib = settings.MEDIA_ROOT / 'dmlib'
    try:
        paths = sorted(dmlib.glob('dm-*.xsd'))
    except OSError:
        return out
    for path in paths:
        dm_ct = path.stem[3:]
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        out[dm_ct] = {ct: label.strip() for label, ct in _BLOCK.findall(text)}
    return out


def by_label(dm_ct: str) -> Dict[str, str]:
    """{label: component ct_id} for one model (the first component wins when a label repeats)."""
    seen: Dict[str, str] = {}
    for ct, label in components().get(dm_ct, {}).items():
        seen.setdefault(label, ct)
    return seen


def with_label_prefix(prefix: str) -> List[str]:
    """Component ct_ids, across every model, whose label starts with the prefix; sorted, distinct."""
    return sorted({ct for comps in components().values() for ct, label in comps.items() if label.startswith(prefix)})


def reifier_iri(component_ct: str, instance_iri: str) -> str:
    """The reifier of one component in one record, from the instance IRI ``.../i-<id>``."""
    return f'{REIFIER_BASE}{component_ct}_{instance_iri.rsplit("/i-", 1)[-1]}'
