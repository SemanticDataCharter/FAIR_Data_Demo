# One-off for production, at the 4.3.1 release: retires the three 4.3.0 models 4.3.1 revises.
#   bash run_oneoff.sh build/retire_models_431_oneoff.py
from django.utils import timezone
from dmgen.models import DM
MODELS = {
    'drjvqb171q9pqwcdq6nxxrr4': 'NHANES Participant 4.3.1',
    'zmlfrxyorqbb1e2id0cwhjyy': 'BRFSS Respondent 4.3.1',
    'n7y449kzry6ax839d9g3oecd': 'CMS Beneficiary 4.3.1',
}
done = skipped = 0
for old_ct, title in MODELS.items():
    old = DM.objects.get(ct_id=old_ct); new = DM.objects.get(project__name='FAIR Data Demo', title=title)
    assert old.project.name == 'FAIR Data Demo' and new.published and not new.retired and new.zip_file, (old_ct, title)
    if old.retired: skipped += 1; continue
    old.retired = True; old.retired_at = timezone.now()
    old.retired_reason = (f'superseded by {new.title} ({new.ct_id}) in FAIR Data Demo 4.3.1: the NIH CDE answers claim '
                          'no exact match for a compound concept (R-2026-10-27)')[:300]
    old.save(update_fields=['retired', 'retired_at', 'retired_reason']); done += 1
    print('RETIRED', old.title, old_ct, '->', new.title, new.ct_id)
print('DONE', done, 'SKIPPED', skipped)
