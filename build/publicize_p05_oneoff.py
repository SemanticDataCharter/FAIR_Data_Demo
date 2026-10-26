# One-off for production, after the 4.2.5 load: makes public the five revisions and three new records it published
# (the loader publishes but does not make public). Each is found by its slot (the newest unretired holder).
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/publicize_p05_oneoff.py)\""
#   (or: bash run_oneoff.sh build/publicize_p05_oneoff.py)
from dmgen.management.commands.load_component_records import Command as Loader
SLOT = 'https://axius-sdc.com/library/fair/'
ORIGINALS = {  # slot -> its original (None: new in 4.2.5)
    'nhanes-medication': 'ncudsi2t2ij3rd2pmnnfr2j9',
    'nhanes-medication-governed-record': 'jo2kw48cijwgg64s6cud2el1',
    'nhanes-medication-reason-1': 'i213d6dp9r4c0nmzxkgc0tja',
    'nhanes-medication-reason-2': 'u3qz0js9emqn2i7s5nyynmgt',
    'nhanes-medication-reason-3': 'rozfpmwczk4yuw4c2vom4gyx',
    'nhanes-prevention-reason': None,
    'nhanes-prevention-reason-code': None,
    'system-nhanes-rx-reason': None,
}
loader = Loader()
found = {k: loader._member_by_slot(SLOT + k) for k in ORIGINALS}
bad = [k for k, c in found.items() if c is None or not c.published or c.retired or c.ct_id == ORIGINALS[k]]
if bad:
    print('REFUSED', bad, [(k, c.ct_id if c else None) for k, c in found.items() if k in bad])
else:
    n = 0
    for k, c in found.items():
        if not c.public:
            c.public = True; c.save(update_fields=['public']); n += 1
    print('PUBLIC', n, 'ALREADY', len(found) - n)
