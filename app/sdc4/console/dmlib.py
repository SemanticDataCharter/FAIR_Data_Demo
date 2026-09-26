"""
What a component was permitted to assert.

A resource view in a triple store shows what a node asserts. This reads the
published data model instead, and reports what the schema allowed: the reference
model type it restricts, the facets on its value, whether an absence may be
stated, and what the component is bound to in the wider world.

The library is already on disk. SDCStudio writes an .xsd, .shacl.ttl, .rdf, .ttl
and .jsonld per data model, so nothing new has to be recorded to answer this.
"""
import re
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from django.conf import settings
from lxml import etree

XS = 'http://www.w3.org/2001/XMLSchema'
RDFS = 'http://www.w3.org/2000/01/rdf-schema#'
RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
META = 'https://semanticdatacharter.com/ns/sdc4-meta/'

DMLIB = Path(settings.BASE_DIR) / 'mediafiles' / 'dmlib'

_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
_lock = threading.Lock()

# Facets worth showing, in the order a reader wants them.
_FACETS = (
    'minInclusive', 'maxInclusive', 'minExclusive', 'maxExclusive',
    'minLength', 'maxLength', 'length', 'pattern', 'totalDigits',
    'fractionDigits', 'enumeration',
)


def _local(tag) -> str:
    return tag.split('}', 1)[1] if isinstance(tag, str) and '}' in tag else str(tag)


def _short(uri: str) -> str:
    if not uri:
        return ''
    return uri.replace('sdc4:', '').replace(
        'https://semanticdatacharter.com/ns/sdc4/', '')


def _parse_model(ct_id: str) -> Dict[str, Dict[str, Any]]:
    """Read one data model schema into {component_ct_id: facts}."""
    path = DMLIB / f'dm-{ct_id}.xsd'
    if not path.exists():
        return {}
    try:
        root = etree.parse(str(path)).getroot()
    except Exception:
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    for ctype in root.iter(f'{{{XS}}}complexType'):
        name = ctype.get('name') or ''
        if not name.startswith('mc-'):
            continue
        comp: Dict[str, Any] = {
            'component': name[3:],
            'label': '', 'definition': '', 'rm_type': '',
            'defined_by': '', 'value_element': '', 'value_required': None,
            'facets': [], 'ev_allowed': False, 'units': '', 'units_ct': '',
        }

        for el in ctype.iter():
            tag = _local(el.tag)
            if tag == 'label' and el.text and not comp['label']:
                comp['label'] = el.text.strip()
            elif tag == 'comment' and el.text and not comp['definition']:
                comp['definition'] = el.text.strip()
            elif tag == 'isConstrainedByRmComponent':
                comp['rm_type'] = _short(el.get(f'{{{RDF}}}resource', ''))
            elif tag == 'isDefinedBy':
                comp['defined_by'] = el.get(f'{{{RDF}}}resource', '')

        # The value element, its optionality and its facets.
        for el in ctype.iter(f'{{{XS}}}element'):
            ename = el.get('name') or ''
            if el.get('ref') == 'sdc4:ExceptionalValue':
                comp['ev_allowed'] = True
                continue
            if ename.endswith('-value') and not ename.startswith('xdstring-value') or \
               re.match(r'^xd\w+-value$', ename) or ename.startswith('xdtemporal-'):
                if comp['value_element']:
                    continue
                comp['value_element'] = ename
                comp['value_required'] = el.get('minOccurs', '1') == '1'
                for facet in el.iter():
                    ftag = _local(facet.tag)
                    if ftag in _FACETS:
                        comp['facets'].append((ftag, facet.get('value', '')))

        # Units are a component in their own right, referenced by type, so the
        # link is resolved after every component in the model has been read.
        for el in ctype.iter(f'{{{XS}}}element'):
            if (el.get('name') or '').endswith('-units'):
                comp['units_ct'] = _short(el.get('type', ''))[3:]
                break

        if comp['label']:
            out[comp['component']] = comp

    for comp in out.values():
        ref = comp.pop('units_ct', '')
        if ref and ref in out:
            comp['units'] = out[ref]['label']
    return out


def model_components(dm_ct_id: str) -> Dict[str, Dict[str, Any]]:
    """Cached: every component in one data model, keyed by its CT_ID."""
    with _lock:
        if dm_ct_id not in _cache:
            _cache[dm_ct_id] = _parse_model(dm_ct_id)
        return _cache[dm_ct_id]


def governed_by(dm_ct_id: str, component_ct_id: str) -> Optional[Dict[str, Any]]:
    """Facts for one component, or None when the model is not on disk."""
    if not component_ct_id:
        return None
    return model_components(dm_ct_id).get(component_ct_id)
