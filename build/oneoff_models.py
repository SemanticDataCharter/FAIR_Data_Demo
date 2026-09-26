# One-off for production, after the bundle is loaded and published into project Cordova (PRD §4 steps 4):
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/oneoff_models.py)\""
# Creates the Cordova-owned Audit (decision 4) and the ten 4.4.0 models (titled '<Domain> 4.4.0': titles are unique per project and a published one cannot change), each prov:wasRevisionOf its 4.3.1 model,
# with the ProvGov workflow bound, then publishes them. Idempotent: a model whose title already exists is skipped.
import json
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from dmgen.models import Project, Modeler, DM, Cluster, Party, Audit, XdString, XdLink, Attestation, PredObj
from dmgen.derivation import record_derivation, resolve_component, WAS_REVISION_OF
from dmgen.management.commands.load_component_records import Command as Loader

SLOT = 'https://axius-sdc.com/library/'
project = Project.objects.get(ct_id='gpmelx4n5fvx3giwubza1etc')
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


# 1. the Cordova-owned Audit: system id (record), system user (Party), location (record cluster)
system_id = by_slot('cordova/cordova-system-identifier')
location = by_slot('cordova/cordova-system-location')
system_user, created = Party.objects.get_or_create(project=project, label='Cordova System User', defaults=dict(creator=modeler, edited_by=modeler,
    description='The user or service account of the Cordova government system that handled the record (PROV agent).'))
publish(system_user)
audit, created = Audit.objects.get_or_create(project=project, label='Cordova System Audit', defaults=dict(creator=modeler, edited_by=modeler,
    description='The audit of a Cordova government record: the system that handled it, the system user, and where (Default geolocation, Cordova city and province). Replaces the June ProvGov System Audit in every Cordova model.',
    system_id=system_id, system_user=system_user, location=location))
publish(audit)
print('AUDIT', audit.ct_id, 'published', audit.published)

# 2. the ten models
MODELS = [
    # title, governed record slot, ProvGov workflow, 4.3.1 DM ct_id, attestation ct, acs ct, protocol ct
    ('Civil Registry', 'civil-registry-governed-record', 'activity-lifecycle', 'uika42uwtj3ijdbegzw2kcwq', 'pf1mrtzd9ld1939qanem0olk', 'fdwlhbher1gm91zfmf8mno6c', 'azmp0vkmkmtne1goba54qubu'),
    ('Vital Statistics Record', 'vital-statistics-governed-record', 'document-publishing', 'ulzd6pe8072mwkqf7i313bov', 'vh5jbumsfax6iw9vez68om83', 'rqeuaeoe81e9siuma9cu7zz1', 'bzj79tikzsv5s4qu83f7qx3m'),
    ('Business Registry', 'business-registry-governed-record', 'asset-status', 'x250838l7oi6l3yavg9twc1i', 'sxtoz5f7z2jbvckaczaetrto', 'ksvt73kzyktevaumrh5djpe7', 'dr8983b4k8ngg02x78lrw560'),
    ('Property Registry', 'property-registry-governed-record', 'asset-status', 'x44vt69qqri2bl7vwxb8ck7n', 'wwgpl34lymlbjbnrkf9srbho', 'sl027mwr4zjo3ht4yeslb0ti', 'fpn6il0cnly7pv2haetuqfu5'),
    ('Education Record', 'education-governed-record', 'activity-lifecycle', 'upq7w1bqbix5v5ss0mu3kq5n', 'qwy0t84c1zzo68vm770xhx51', 'rw24p8yjm8dmdnvw7egxi2uv', 'vdwqv3o1qf00yjq9cv7kcpos'),
    ('Employment Record', 'employment-governed-record', 'activity-lifecycle', 'pm5cks82lnrvyna1xbwpfxic', 'dqjp4dd4kgj2e2hg8kiw3qfw', 'tw8mn0vv8z8v3w533gfu9j92', 'f37y1r2uqdu9kkrdptbm803d'),
    ('Tax and Revenue Record', 'tax-and-revenue-governed-record', 'payment', 'vaw4g2kusit5z0kox5mog54g', 'a4xeuo9t72trcpyzsmc144ze', 'n4fhdacb4d2nu14s79t2pnq2', 'z8bsecpgj1lsk4bjoiwaqn40'),
    ('Healthcare Record', 'healthcare-governed-record', 'encounter-lifecycle', 'ftluo2nybgxmn7mawttoos20', 'q8x2nc8i8ud3tqo42g850vwz', 'hbk1xmzqefk2lchmd7jooz7a', 'emov6wuhen2tuyjlppqmmjjl'),
    ('Law Enforcement Record', 'law-enforcement-governed-record', 'act-lifecycle', 'yh0opq0bnu6y9y56oukg92uf', 'i8g57yrmdthdj1k5tcmj3ecx', 'bkuhivi6ot6nxll6vam7yobp', 'rhu2opcioifbl83m7ph3rbhw'),
    ('Maritime Port Authority', 'maritime-governed-record', 'reservation', 'md2451x882z5j89g66zb50rw', 'kmd0ncqu6c70mt5ri4bxucgg', 'wqs7c6hl5vgq6f4ub25th5tr', 'c75jy9i3wmcbaewdoeivt2v5'),
]
out = {}
for base_title, data_slot, wf, old_ct, att_ct, acs_ct, proto_ct in MODELS:
    old = DM.objects.get(ct_id=old_ct)
    title = base_title + ' 4.4.0'   # a published title cannot change and titles are unique per project
    existing = DM.objects.filter(project=project, title=title, retired=False).exclude(ct_id=old_ct).first()
    if existing:
        print('EXISTS', title, existing.ct_id); out[title] = existing.ct_id; continue
    dm = DM.objects.create(project=project, title=title, creator=modeler, edited_by=modeler, author=modeler,
                           description=old.description, about=old.about, dc_subject=old.dc_subject, rights=old.rights, publisher=old.publisher, dc_language=old.dc_language, language=old.language, encoding=old.encoding,
                           data=by_slot('cordova/' + data_slot), workflow=by_slot('provgov/' + wf),
                           attestation=Attestation.objects.get(ct_id=att_ct), acs=XdLink.objects.get(ct_id=acs_ct), protocol=XdString.objects.get(ct_id=proto_ct))
    dm.audit.add(audit)
    for po in old.pred_obj.all():
        dm.pred_obj.add(po)
    record_derivation(dm, old_ct, WAS_REVISION_OF)
    publish(dm)
    out[title] = dm.ct_id
    print('MODEL', title, dm.ct_id, 'wasRevisionOf', old_ct, 'workflow', wf)
print('DONE', json.dumps(out))
