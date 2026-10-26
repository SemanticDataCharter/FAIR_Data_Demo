# One-off for production, at the 4.2.5 release: retires NHANES Medication (4.2.0), superseded by NHANES Medication 4.2.5.
# Retired is not deleted: it stays published and resolvable.
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/retire_models_p05_oneoff.py)\""
#   (or: bash run_oneoff.sh build/retire_models_p05_oneoff.py)
from django.utils import timezone
from dmgen.models import DM
MODELS = {
    'epbdfmvxc3gbh5f66hhb3o2m': 'NHANES Medication 4.2.5',
}
done = skipped = 0
for old_ct, title in MODELS.items():
    old = DM.objects.get(ct_id=old_ct); new = DM.objects.get(project__name='FAIR Data Demo', title=title)
    assert old.project.name == 'FAIR Data Demo' and new.published and not new.retired and new.zip_file, (old_ct, title)
    if old.retired: skipped += 1; continue
    old.retired = True; old.retired_at = timezone.now()
    old.retired_reason = (f'superseded by {new.title} ({new.ct_id}) in FAIR Data Demo 4.2.5: NHANES prevention reason '
                          'codes carried as their own code system, not ICD-10-CM')[:300]
    old.save(update_fields=['retired', 'retired_at', 'retired_reason']); done += 1
    print('RETIRED', old.title, old_ct, '->', new.title, new.ct_id)
print('DONE', done, 'SKIPPED', skipped)
