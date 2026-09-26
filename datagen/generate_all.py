#!/usr/bin/env python
"""
Generate every FAIR Data Demo record from the federal source files.

NHANES: every participant and every medication row. BRFSS and CMS: the seeded samples
(5,000 respondents; 5,000 beneficiaries with all their claims and prescription events), or
every row with FAIR_FULL=1. Writes app/sdc4/import_data/<app>/*.xml, each validated by the
loader on the way in, and each already shaped by the model's own instance template.
"""
import glob
import os
import time

import nhanes
import brfss_respondent
import cms_beneficiary
import cms_inpatient_claim
import cms_outpatient_claim
import cms_prescription_drug_event
from shared import IMPORT_ROOT, DEMO_SCALE


def main():
    t0 = time.time()
    print("=" * 60)
    print("FAIR Data Demo generator, 4.2.0 models", "(seeded samples)" if DEMO_SCALE else "(every row)")
    print("=" * 60)
    os.makedirs(IMPORT_ROOT, exist_ok=True)
    removed = 0
    for sub in os.listdir(IMPORT_ROOT):
        d = os.path.join(IMPORT_ROOT, sub)
        if os.path.isdir(d):
            for f in glob.glob(os.path.join(d, "*.xml")):
                os.remove(f); removed += 1
    print(f"Removed {removed} existing files.\n")
    for name, module in (("NHANES", nhanes), ("BRFSS", brfss_respondent), ("CMS beneficiaries", cms_beneficiary), ("CMS inpatient claims", cms_inpatient_claim),
                         ("CMS outpatient claims", cms_outpatient_claim), ("CMS prescription drug events", cms_prescription_drug_event)):
        t = time.time()
        module.generate()
        print(f"  {name}: {time.time() - t:.0f}s\n")
    total = 0
    print("SUMMARY")
    for sub in sorted(os.listdir(IMPORT_ROOT)):
        n = len(glob.glob(os.path.join(IMPORT_ROOT, sub, "*.xml")))
        if n:
            total += n
            print(f"  {sub:<32} {n:>8,}")
    print(f"  {'TOTAL':<32} {total:>8,}")
    print(f"Completed in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
