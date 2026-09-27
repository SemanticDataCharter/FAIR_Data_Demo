# One-off verification on production after the load (python manage.py shell -c "$(grep -v '^#' build/verify_oneoff.py)").
import collections
from dmgen.models import Project, Cluster, XdQuantity, XdCount, DM
from dmgen.derivation import component_models
p = Project.objects.get(name='FAIR Data Demo')
active = retired = 0; reasons = collections.Counter(); labels = collections.Counter(); unpublished = 0
for m in component_models():
    for c in m.objects.filter(project=p):
        if c.retired:
            retired += 1; reasons[' '.join(c.retired_reason.split(' ')[:2])] += 1
        else:
            active += 1; labels[getattr(c, 'label', getattr(c, 'title', ''))] += 1; unpublished += (not c.published)
print('ACTIVE', active, 'RETIRED', retired, 'UNPUBLISHED_ACTIVE', unpublished)
print('REASONS', dict(reasons))
print('DUP_LABELS', [l for l, n in labels.items() if n > 1][:10])
cross = collections.Counter(); xu = collections.Counter()
for c in Cluster.objects.filter(project=p, retired=False):
    for rel in ('clusters', 'xdstring', 'xdtoken', 'xdquantity', 'xdcount', 'xdtemporal', 'xdboolean', 'xdlink', 'xdfile', 'xdordinal'):
        for mobj in getattr(c, rel).all():
            if mobj.project_id != p.id: cross[mobj.project.name] += 1
for q in list(XdQuantity.objects.filter(project=p, retired=False)) + list(XdCount.objects.filter(project=p, retired=False)):
    if q.units_id and q.units.project_id != p.id: xu[q.units.project.name] += 1
print('CROSS_MEMBERS', dict(cross), 'CROSS_UNITS', dict(xu))
print('DMS', [(d.title, d.published, d.retired, bool(d.zip_file)) for d in DM.objects.filter(project=p).order_by('title')])
