# One-off for production, at the 4.3.0 release: retires the four models 4.3.0 revises, each with the reason naming
# its revision. Retired is not deleted: each stays published and resolvable.
#   bash run_oneoff.sh build/retire_models_430_oneoff.py   (or: gcloud run jobs execute sdcstudio-migrate ... shell -c "$(grep -v '^#' build/retire_models_430_oneoff.py)")
from django.utils import timezone
from dmgen.models import DM
MODELS = {
    'tp5pg0u4dasqarie0b3ujn2u': 'NHANES Participant 4.3.0',
    'j6wmvhr46irxht2ls90nry8k': 'BRFSS Respondent 4.3.0',
    'epbdfmvxc3gbh5f66hhb3o2m': 'NHANES Medication 4.3.0',
    'vj0hr75146j0pbedvc0iaqrz': 'CMS Beneficiary 4.3.0',
}
done = skipped = 0
for old_ct, title in MODELS.items():
    old = DM.objects.get(ct_id=old_ct); new = DM.objects.get(project__name='FAIR Data Demo', title=title)
    assert old.project.name == 'FAIR Data Demo' and new.published and not new.retired and new.zip_file, (old_ct, title)
    if old.retired: skipped += 1; continue
    old.retired = True; old.retired_at = timezone.now()
    old.retired_reason = (f'superseded by {new.title} ({new.ct_id}) in FAIR Data Demo 4.3.0: refusals and unknowns as '
                          'Exceptional Values; NHANES prevention codes as their own')[:300]
    old.save(update_fields=['retired', 'retired_at', 'retired_reason']); done += 1
    print('RETIRED', old.title, old_ct, '->', new.title, new.ct_id)
print('DONE', done, 'SKIPPED', skipped)
