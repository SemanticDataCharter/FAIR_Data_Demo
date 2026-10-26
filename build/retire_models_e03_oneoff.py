# One-off for production, at the 4.2.4 release (supersede, never unpublish): retires the three models whose value
# bindings named codes their terminologies do not confirm (E-2026-10-03, SOURCE-ERRATA.md), each with the reason naming
# its 4.2.4 revision. Retired is not deleted: each stays published and resolvable.
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/retire_models_e03_oneoff.py)\""
from django.utils import timezone
from dmgen.models import DM
MODELS = {
    'eehpfapwgvxtzdrofgstdcfs': 'NHANES Participant 4.2.4',
    'w9ozx00idgs5k8tw4359skvn': 'BRFSS Respondent 4.2.4',
    'fnv3zi2btk3s0sfodjsc25eb': 'CMS Beneficiary 4.2.4',
}
done = skipped = 0
for old_ct, title in MODELS.items():
    old = DM.objects.get(ct_id=old_ct); new = DM.objects.get(project__name='FAIR Data Demo', title=title)
    assert old.project.name == 'FAIR Data Demo' and new.published and not new.retired and new.zip_file, (old_ct, title)
    if old.retired: skipped += 1; continue
    old.retired = True; old.retired_at = timezone.now()
    old.retired_reason = (f'superseded by {new.title} ({new.ct_id}) in FAIR Data Demo 4.2.4: value bindings corrected to '
                          'codes their terminologies confirm (E-2026-10-03)')[:300]
    old.save(update_fields=['retired', 'retired_at', 'retired_reason']); done += 1
    print('RETIRED', old.title, old_ct, '->', new.title, new.ct_id)
print('DONE', done, 'SKIPPED', skipped)
