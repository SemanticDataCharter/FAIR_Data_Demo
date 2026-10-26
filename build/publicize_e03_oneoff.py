# One-off for production, after the E-2026-10-03 revisions are loaded (SOURCE-ERRATA.md): makes the 38 revisions public
# (the loader publishes but does not make public; a public model's members must be public). Each is found by its slot
# (the newest unretired holder), must be published and not its original; nothing else is touched.
#   gcloud run jobs execute sdcstudio-migrate --region us-central1 --project sdcstudio-prod --wait \
#     --args="^~^-c~cd /app/src && python manage.py shell -c \"$(grep -v '^#' build/publicize_e03_oneoff.py)\""
from dmgen.management.commands.load_component_records import Command as Loader
SLOT = 'https://axius-sdc.com/library/fair/'
ORIGINALS = {
    'brfss-bmi-category': 'ezewpvppvx8zjikutr53ppgz',
    'brfss-body-measures': 'gc3nb6hzobkzifswmzgt7w6t',
    'brfss-chronic-conditions': 'lahhb7fhnu75l1fxrv9f8fdv',
    'brfss-days-mental-health-not-good': 'k32effn0kp5a42ikkpvcva9j',
    'brfss-days-physical-health-not-good': 'fljkn7b19qtnj6rr3t8qcfg1',
    'brfss-demographics': 'tto2m72tul0hj0z7zyoco4yx',
    'brfss-education-level': 'fci5gajaodxc2ihq6nuz9l6y',
    'brfss-health-status': 'kmgw3rv02bipvaoxpvnh7fzk',
    'brfss-respondent': 'jxif4jju7k2rg3vokabzzj22',
    'brfss-respondent-governed-record': 'kb26is7epmdlc0lm1k9pdz9f',
    'brfss-survey-design': 'zauadmfc05ep5nf2kd9j8cwh',
    'chronic-condition-indicators': 'wa0mknvfo83hej635n48s0ig',
    'cms-beneficiary': 'kkdy1kjdruxvx8s1ra8eh231',
    'cms-beneficiary-governed-record': 'io2h28pi3yktedurk8ye3oq0',
    'condition-indicator-basis': 'hc79skkfionpgw87dsg5yrgw',
    'general-health-status': 'lth27h6towue4i9iq1cudogc',
    'nhanes-citizenship-status': 'm67ncwhc9s1j36f9w9qsrxfx',
    'nhanes-demographics': 'nzhi9t6qd9rhb5ojsaxtn8md',
    'nhanes-dressing': 'p4jxl2rur1agjhdpvj2g9u4k',
    'nhanes-education-level-adults': 'fqjd2lvp9jamdpf0f3kpkwnp',
    'nhanes-getting-in-and-out-of-bed': 'cy6k5rxvhvg2v27cfp7pjwyx',
    'nhanes-laboratory-results': 'c73687ou0pkc7qy6n2kksfc7',
    'nhanes-lifting-or-carrying': 'b1mxr233mgqvzr39c90ly8cv',
    'nhanes-medical-conditions': 'mc8by65nv7wa59lw4oj54e2w',
    'nhanes-participant': 'dawjwho8viq3hr0esb39dhb7',
    'nhanes-participant-governed-record': 'u9elnmjjpxdtxcxnqugqaowk',
    'nhanes-physical-functioning': 'ky7lvmote5jfn5gt6n89q79s',
    'nhanes-pregnancy-status-at-exam': 'r0j6yo8zvo4q8x0ovdr6j9yz',
    'nhanes-race-hispanic-origin': 'hs44ipuqgvc3azbt3mirxtsz',
    'nhanes-standing-for-long-periods': 'vp4ow7t3q8w2phcft0qvyj4u',
    'nhanes-standing-up-from-chair': 'y52y4mpq95zcknal0be1uc7v',
    'nhanes-stooping-crouching-kneeling': 'knrs4clih4pi26tm2zra1ai0',
    'nhanes-survey-design': 'mgqswj92qaeasqjjvfcyxon5',
    'nhanes-total-cholesterol-si': 'qp5mdgab3s37zwqzyfzq8rvi',
    'nhanes-walking-between-rooms': 'crr2z3b2l7hlq1kvevppt8kt',
    'nhanes-walking-quarter-mile': 'mktq5xr8slz67q85idl8bsky',
    'nhanes-walking-up-ten-stairs': 'rot4z5ny8gdkfmimedcjl1te',
    'veteran-status': 'eimlsgbawhm8aa4i6gbdrja0'
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
