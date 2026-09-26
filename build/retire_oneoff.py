# One-off, run on production after the chunked load as:
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(cat build/retire_oneoff.py)\""
# Retires the 2026 NIEM components that have no successor (review/niem-retire.csv, uploaded as niem-rebuild/retire.csv),
# with the reason as text. Retired is not deleted: CordovaOS's compositions stay valid.
import csv, io
from django.core.files.storage import default_storage
from django.utils import timezone
from dmgen.derivation import resolve_component
rows = list(csv.DictReader(io.StringIO(default_storage.open('cordova/retire.csv', 'rb').read().decode('utf-8'))))
done = skipped = missing = 0
for r in rows:
    if r['decision'].strip().lower() != 'accept': skipped += 1; continue
    c = resolve_component(r['ct_id'])
    if c is None: missing += 1; print('MISSING', r['ct_id'], r['label']); continue
    if c.retired: skipped += 1; continue
    assert c.project.ct_id == 'gpmelx4n5fvx3giwubza1etc', (r['ct_id'], c.project.name)
    c.retired = True; c.retired_at = timezone.now(); c.retired_reason = ('not rebuilt: ' + r['reason'])[:255]
    c.save(update_fields=['retired', 'retired_at', 'retired_reason']); done += 1
print('RETIRED', done, 'SKIPPED', skipped, 'MISSING', missing)
