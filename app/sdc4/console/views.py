"""
Executive console views.

A read-only presentation layer beside /demo/. The demo is the engineer's view;
this is the view for the person who signs. Its one rule is that every figure on
screen resolves to a validated instance, so the console never renders anything it
cannot open.
"""
import logging

from django.http import Http404, HttpResponse
from django.shortcuts import render

from sdc4_shared.utils.dm_registry import get_dm_registry

from .dmlib import governed_by
from .graph import neighbourhood
from .question import coverage, conditions
from .instances import (
    field_rows,
    get_instance,
    instance_header,
    neighbours,
    stated_absences,
)

logger = logging.getLogger(__name__)

PANES = ('table', 'document', 'graph')


def question(request):
    """Two cross-study questions, and the evidence for the answers."""
    return render(request, 'console/question.html', {'q': coverage(), 't': conditions()})


def index(request):
    """
    The front door. Seven study models, and the records worth opening first.

    The refusal cases are surfaced deliberately rather than left to whoever
    knows an identifier: a console that only ever shows records that passed is
    the kind of dashboard this one exists to argue against.
    """
    domains = []
    refused = []

    for ct_id, model in sorted(get_dm_registry().items(),
                               key=lambda kv: getattr(kv[1], 'DM_LABEL', '')):
        qs = model.objects.all()
        total = qs.count()
        if not total:
            continue

        latest = qs.order_by('-created_at').values_list('instance_id', flat=True).first()
        invalid = qs.filter(validation_status='invalid').count()
        domains.append({
            'label': getattr(model, 'DM_LABEL', model.__name__),
            'ct_id': ct_id,
            'count': total,
            'invalid': invalid,
            'latest': latest,
        })

        # An instance that states an absence carries the i-ev- prefix, so the
        # fact is in the identifier and this needs no extra column to find.
        for obj in qs.filter(instance_id__startswith='i-ev-')[:4]:
            refused.append({
                'ct_id': ct_id,
                'label': getattr(model, 'DM_LABEL', model.__name__),
                'instance_id': obj.instance_id,
                'status': obj.validation_status,
                'absences': stated_absences(obj),
            })

    return render(request, 'console/index.html', {
        'domains': domains,
        'refused': refused,
        'total_records': sum(d['count'] for d in domains),
        'total_invalid': sum(d['invalid'] for d in domains),
    })


def _load(ct_id, instance_id):
    model, obj = get_instance(ct_id, instance_id)
    if model is None:
        raise Http404(f'No data model registered for CT_ID {ct_id}')
    if obj is None:
        raise Http404(f'No instance {instance_id} in {model.DM_LABEL}')
    return model, obj


def _pane_context(model, obj, pane):
    """Build only the projection being asked for."""
    if pane == 'document':
        # The authoritative format, rendered verbatim. Nothing is reformatted:
        # what the reader sees is the bytes that were validated.
        return {'xml_content': obj.xml_content}
    if pane == 'table':
        return {'rows': field_rows(obj)}
    # graph
    return {'g': neighbourhood(model, obj)}


def instance(request, ct_id, instance_id):
    """One record, shown three ways."""
    model, obj = _load(ct_id, instance_id)
    # The table is the default because it is the projection a reader can act
    # on. Document and Graph are one click away for anyone who wants them.
    pane = request.GET.get('pane', 'table')
    if pane not in PANES:
        pane = 'table'

    rows = field_rows(obj)
    # Which component the governance pane describes. Defaults to the first
    # field so the pane is never empty on arrival.
    selected = request.GET.get('field') or (rows[0]['component'] if rows else '')

    context = {
        'h': instance_header(model, obj),
        'pane': pane,
        'panes': PANES,
        'nav': neighbours(model, obj),
        'selected': selected,
        'governed': governed_by(getattr(model, 'DM_CT_ID', ''), selected),
    }
    context.update(_pane_context(model, obj, pane))
    return render(request, 'console/instance.html', context)


def pane(request, ct_id, instance_id, pane):
    """HTMX endpoint: swap one projection without reloading the record."""
    if pane not in PANES:
        return HttpResponse('<p class="hint">Unknown projection.</p>', status=400)
    model, obj = _load(ct_id, instance_id)
    context = _pane_context(model, obj, pane)
    context['h'] = instance_header(model, obj)
    return render(request, f'console/_pane_{pane}.html', context)
