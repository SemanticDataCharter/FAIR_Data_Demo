# One-off for production, after the bundle is loaded and published into project FAIR Data Demo (PRD §4 step 4):
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/oneoff_models.py)\""
# Creates the FAIR System Audit (the pipeline as the system, a Party as its user, the source file as its location) and the seven
# 4.2.0 models, each prov:wasRevisionOf the first build's model it supersedes, then publishes them. Idempotent by title.
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from dmgen.models import Project, Modeler, DM, Party, Audit, XdString, XdLink, Attestation
from dmgen.derivation import record_derivation, WAS_REVISION_OF
from dmgen.management.commands.load_component_records import Command as Loader

SLOT = 'https://axius-sdc.com/library/fair/'
project = Project.objects.get(name='FAIR Data Demo')
user = get_user_model().objects.get(email='twcook@axius-sdc.com')
modeler = Modeler.objects.filter(user=user).first(); assert modeler
request = RequestFactory().get('/'); request.user = user
loader = Loader()


def by_slot(slot):
    obj = loader._member_by_slot(SLOT + slot)
    assert obj is not None, slot
    return obj


def publish(obj):
    if obj.published:
        return obj
    result = obj.publish(request); obj.refresh_from_db(); assert obj.published, (getattr(obj, 'label', None) or obj.title, result)
    return obj


system_id = by_slot('fair-system-identifier')
location = by_slot('fair-source-file')
system_user, created = Party.objects.get_or_create(project=project, label='FAIR Pipeline User', defaults=dict(creator=modeler, edited_by=modeler,
    description='The pipeline run that generated the record from a federal source file (PROV agent).'))
publish(system_user)
audit, created = Audit.objects.get_or_create(project=project, label='FAIR Pipeline Audit', defaults=dict(creator=modeler, edited_by=modeler,
    description='The audit of a record generated from a federal source file: the pipeline that generated it, its run, and the source file it read (the ProvGov PROV entity).',
    system_id=system_id, system_user=system_user, location=location))
publish(audit)
print('AUDIT', audit.ct_id, 'published', audit.published)

MODELS = [
    # title, governed record slot, first-build DM ct_id it revises
    ('NHANES Participant', 'nhanes-participant-governed-record', 'r3gyip9ebl7ockdpj4kwabjo'),
    ('NHANES Medication', 'nhanes-medication-governed-record', 'g72xhdxvd7q53qnxx6dsczg5'),
    ('BRFSS Respondent', 'brfss-respondent-governed-record', 'ffq1c2tkbzexmxqnrxg48oqj'),
    ('CMS Beneficiary', 'cms-beneficiary-governed-record', 'q9xk7y13y2115tr4sn2c7m39'),
    ('CMS Inpatient Claim', 'cms-inpatient-claim-governed-record', 'ra4tn4wzsu2rlbk5dineab5g'),
    ('CMS Outpatient Claim', 'cms-outpatient-claim-governed-record', 'k6f8kugg359vc6ew75ulojg9'),
    ('CMS Prescription Drug Event', 'cms-prescription-drug-event-governed-record', 'dg6lyhgvz9wd9cuqxqdc5g4p'),
]
out = {}
for title, data_slot, old_ct in MODELS:
    old = DM.objects.get(ct_id=old_ct)
    existing = DM.objects.filter(project=project, title=title, retired=False).exclude(ct_id=old_ct).first()
    if existing:
        print('EXISTS', title, existing.ct_id); out[title] = existing.ct_id; continue
    dm = DM.objects.create(project=project, title=title, creator=modeler, edited_by=modeler, author=modeler,
                           description=old.description, about=old.about, dc_subject=old.dc_subject, rights=old.rights, publisher=old.publisher, dc_language=old.dc_language, language=old.language, encoding=old.encoding,
                           data=by_slot(data_slot), attestation=old.attestation, acs=old.acs, protocol=old.protocol)
    dm.audit.add(audit)
    for po in old.pred_obj.all():
        dm.pred_obj.add(po)
    record_derivation(dm, old_ct, WAS_REVISION_OF)
    publish(dm)
    out[title] = dm.ct_id
    print('MODEL', title, dm.ct_id, 'wasRevisionOf', old_ct)
print('DONE', __import__('json').dumps(out))
