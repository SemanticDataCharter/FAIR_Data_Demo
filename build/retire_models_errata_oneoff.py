# One-off for production, at the 4.2.3 release (supersede, never unpublish): retires the two 4.2.0 models that composed
# the NIH CDE "Are you pregnant now?" with its LOINC answer codes one off (E-2026-10-01, SOURCE-ERRATA.md), each with the
# reason naming its 4.2.3 revision. Retired is not deleted: both stay published and resolvable.
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/retire_models_errata_oneoff.py)\""
from django.utils import timezone
from dmgen.models import DM
MODELS = {
    'xy8upneajsb8vdcmnve01g6g': 'eehpfapwgvxtzdrofgstdcfs',   # NHANES Participant -> NHANES Participant 4.2.3
    'iymux9kjv8ndbkoi36xzx17i': 'w9ozx00idgs5k8tw4359skvn',   # BRFSS Respondent -> BRFSS Respondent 4.2.3
}
done = skipped = 0
for old_ct, new_ct in MODELS.items():
    old = DM.objects.get(ct_id=old_ct); new = DM.objects.get(ct_id=new_ct)
    assert old.project.name == new.project.name == 'FAIR Data Demo' and new.published and not new.retired and new.zip_file, (old_ct, new_ct)
    if old.retired: skipped += 1; continue
    old.retired = True; old.retired_at = timezone.now()
    old.retired_reason = (f'superseded by {new.title} ({new_ct}) in FAIR Data Demo 4.2.3: the NIH CDE pregnancy answers '
                          'were bound to the wrong LOINC codes (E-2026-10-01)')[:300]
    old.save(update_fields=['retired', 'retired_at', 'retired_reason']); done += 1
    print('RETIRED', old.title, old_ct, '->', new.title, new_ct)
print('DONE', done, 'SKIPPED', skipped)
