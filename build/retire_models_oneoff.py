# One-off for production, at the 4.2.0 release (PRD section 2: supersede, never unpublish):
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/retire_models_oneoff.py)\""
# Retires the first build's eight models with the reason naming the 4.2.0 model that supersedes each. Retired is not
# deleted: the eight stay published and resolvable, and every 4.2.0 model records prov:wasRevisionOf its predecessor
# (models-4.2.0.json). Two of the NHANES models fold into one participant record, so two rows name the same successor.
from django.utils import timezone
from dmgen.models import DM
MODELS = {
    'r3gyip9ebl7ockdpj4kwabjo': 'xy8upneajsb8vdcmnve01g6g',   # NHANES Blood Pressure -> NHANES Participant
    's70cbgpe2gqfmpund4vvwyi5': 'xy8upneajsb8vdcmnve01g6g',   # NHANES Cholesterol -> NHANES Participant
    'g72xhdxvd7q53qnxx6dsczg5': 'epbdfmvxc3gbh5f66hhb3o2m',   # NHANES Medications -> NHANES Medication
    'ffq1c2tkbzexmxqnrxg48oqj': 'iymux9kjv8ndbkoi36xzx17i',   # BRFSS Brfss -> BRFSS Respondent
    'q9xk7y13y2115tr4sn2c7m39': 'fnv3zi2btk3s0sfodjsc25eb',   # CMS Beneficiary -> CMS Beneficiary
    'ra4tn4wzsu2rlbk5dineab5g': 'ji1eccop92mlmikwq5gwp7cr',   # CMS Inpatient -> CMS Inpatient Claim
    'k6f8kugg359vc6ew75ulojg9': 'mllwhe842wtnim4ms48qonio',   # CMS Outpatient -> CMS Outpatient Claim
    'dg6lyhgvz9wd9cuqxqdc5g4p': 'nvemvhvdkctdlm9alwwgcay7',   # CMS Prescriptions -> CMS Prescription Drug Event
}
done = skipped = 0
for old_ct, new_ct in MODELS.items():
    old = DM.objects.get(ct_id=old_ct); new = DM.objects.get(ct_id=new_ct)
    assert old.project.name == new.project.name == 'FAIR Data Demo' and new.published and not new.retired, (old_ct, new_ct)
    if old.retired: skipped += 1; continue
    old.retired = True; old.retired_at = timezone.now(); old.retired_reason = f'superseded by {new.title} ({new_ct}) in FAIR Data Demo 4.2.0'[:300]
    old.save(update_fields=['retired', 'retired_at', 'retired_reason']); done += 1
    print('RETIRED', old.title, old_ct, '->', new.title, new_ct)
print('DONE', done, 'SKIPPED', skipped)
