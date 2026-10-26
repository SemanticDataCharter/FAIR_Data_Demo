# One-off for production, after the 4.3.0 load is published and public: the four models whose records compose a
# revised component, each a revision of the published model on the revised governed record cluster.
#   bash run_oneoff.sh build/oneoff_models_430.py   (or: gcloud run jobs execute sdcstudio-migrate ... shell -c "$(grep -v '^#' build/oneoff_models_430.py)")
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from dmgen.models import Project, Modeler, DM
from dmgen.derivation import record_derivation, DERIVATION_PREDICATES, WAS_REVISION_OF
from dmgen.management.commands.load_component_records import Command as Loader

SLOT = 'https://axius-sdc.com/library/fair/'
project = Project.objects.get(name='FAIR Data Demo')
user = get_user_model().objects.get(email='twcook@axius-sdc.com')
modeler = Modeler.objects.filter(user=user).first(); assert modeler
request = RequestFactory().get('/'); request.user = user
loader = Loader()
MODELS = [
    # title, governed record slot, the published model it revises (models-4.2.4.json)
    ('NHANES Participant 4.3.0', 'nhanes-participant-governed-record', 'tp5pg0u4dasqarie0b3ujn2u'),
    ('BRFSS Respondent 4.3.0', 'brfss-respondent-governed-record', 'j6wmvhr46irxht2ls90nry8k'),
    ('NHANES Medication 4.3.0', 'nhanes-medication-governed-record', 'epbdfmvxc3gbh5f66hhb3o2m'),
    ('CMS Beneficiary 4.3.0', 'cms-beneficiary-governed-record', 'vj0hr75146j0pbedvc0iaqrz'),
]
out = {}
for title, data_slot, old_ct in MODELS:
    old = DM.objects.get(ct_id=old_ct)
    data = loader._member_by_slot(SLOT + data_slot)
    assert data is not None and data.pk != old.data.pk, (title, 'the governed record slot still resolves to the old root')
    existing = DM.objects.filter(project=project, title=title).first()
    if existing:
        print('EXISTS', title, existing.ct_id); out[title] = existing.ct_id; continue
    dm = DM.objects.create(project=project, title=title, creator=modeler, edited_by=modeler, author=modeler,
                           description=old.description, about=old.about, dc_subject=old.dc_subject, rights=old.rights, publisher=old.publisher,
                           dc_language=old.dc_language, language=old.language, encoding=old.encoding,
                           data=data, attestation=old.attestation, acs=old.acs, protocol=old.protocol)
    for a in old.audit.all():
        dm.audit.add(a)
    for po in old.pred_obj.exclude(predicate__class_name__in=DERIVATION_PREDICATES):   # its own lineage, not old's
        dm.pred_obj.add(po)
    record_derivation(dm, old_ct, WAS_REVISION_OF)
    if not dm.published:
        result = dm.publish(request); dm.refresh_from_db(); assert dm.published, (title, result)
    out[title] = dm.ct_id
    print('MODEL', title, dm.ct_id, 'wasRevisionOf', old_ct, 'data', data.ct_id)
print('DONE', __import__('json').dumps(out))
