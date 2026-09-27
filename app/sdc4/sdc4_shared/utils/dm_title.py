"""
The published title of a data model, read from its schema in the library.

The generated app carries the model's label as a CamelCase identifier
(``DM_LABEL = 'BrfssRespondent'``); the published model carries the title a
person gave it (``BRFSS Respondent``) in the ``dc:title`` of ``dm-<ct_id>.xsd``.
The console and the demo pages show the published title and fall back to the
label when the schema is not in the library.
"""
from __future__ import annotations

import re
from functools import lru_cache

from django.conf import settings

_TITLE = re.compile(r'<dc:title[^>]*>([^<]+)</dc:title>')


@lru_cache(maxsize=None)
def _title_for(ct_id: str) -> str:
    try:
        text = (settings.MEDIA_ROOT / 'dmlib' / f'dm-{ct_id}.xsd').read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''
    for m in _TITLE.finditer(text):
        title = m.group(1).strip()
        if title:
            return title
    return ''


def dm_title(model) -> str:
    """The published title of a generated model class, else its DM_LABEL, else its class name."""
    ct_id = getattr(model, 'DM_CT_ID', '')
    return (_title_for(ct_id) if ct_id else '') or getattr(model, 'DM_LABEL', model.__name__)
