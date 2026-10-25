# One-off for production, after the E-2026-10-01 cluster revisions are loaded: makes the six revisions public (the loader
# publishes but does not make public; a public model's members must be public). Each is found by its slot (the newest
# unretired holder), must be published and not one of the six originals; nothing else is touched.
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/publicize_errata_oneoff.py)\""
from dmgen.management.commands.load_component_records import Command as Loader
SLOT = 'https://axius-sdc.com/library/fair/'
ORIGINALS = {'nhanes-demographics': 'b6bz6qun3frba85kw1a539h2', 'nhanes-participant': 'e3gwv95m8jjx7578urmx8ppz',
             'nhanes-participant-governed-record': 'l6t9agg233vswxyv60quiu6w', 'brfss-demographics': 'oqw3pnwhf8knpgsfo8k3xojn',
             'brfss-respondent': 'rdoj4o216s33ymezyefwb8ia', 'brfss-respondent-governed-record': 'hnf5st6e6ulzvbiafx4310g7'}
loader = Loader()
found = {k: loader._member_by_slot(SLOT + k) for k in ORIGINALS}
bad = [k for k, c in found.items() if c is None or not c.published or c.retired or c.ct_id == ORIGINALS[k]]
if bad:
    print('REFUSED', bad, [(k, c.ct_id if c else None) for k, c in found.items()])
else:
    for k, c in found.items():
        was = c.public
        if not was:
            c.public = True; c.save(update_fields=['public'])
        print('PUBLIC' if not was else 'ALREADY', k, c.ct_id)
