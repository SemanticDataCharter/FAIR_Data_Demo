# One-off for production, after the 4.3.1 load: makes its 9 revisions public.
#   bash run_oneoff.sh build/publicize_431_oneoff.py
from dmgen.management.commands.load_component_records import Command as Loader
SLOT = 'https://axius-sdc.com/library/fair/'
ORIGINALS = {
    'brfss-demographics': 'orywhiwtxp7meups9u64b0vp',
    'brfss-respondent': 'ekby0xlvhn8kxkkczk6z3wm4',
    'brfss-respondent-governed-record': 'nmsbjxjd2n2thv3wy1c0gz1i',
    'cms-beneficiary': 'ce5aqr7g21uqtbidjv14i1t0',
    'cms-beneficiary-demographics': 'frvayvpr4jkzykc8ykchaev6',
    'cms-beneficiary-governed-record': 'ovmmbdy2c30qbjopzbdhtuje',
    'nhanes-demographics': 'sbzj7kpa1ew9aj60to9wjegm',
    'nhanes-participant': 'mp7s7y891cu2qsvp2d1sztbb',
    'nhanes-participant-governed-record': 'rpwfemq2mts42x09nn050hi4',
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
