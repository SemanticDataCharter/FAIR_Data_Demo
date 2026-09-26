"""
CMS Outpatient Claim 4.2.0: one record per DE-SynPUF outpatient claim row (2008-2010) of a sampled beneficiary.

The visit is the FHIR encounter by identifier; diagnoses and procedures are ICD-9-CM coded values as the
claims carry them, HCPCS codes the first ten line slots; the Part B amounts in US dollars.
"""
import time

from cms_common import AGENCY, SUBJECT, Left, claim_values, sample_ids, usd
from shared import import_dir, read_csv, record, write_record

TITLE = "CMS Outpatient Claim"
OUTPUT_DIR = import_dir("cms_outpatient_claim")


def build_instance(row: dict, left: Left) -> str:
    values = claim_values(row, "AMB", left)
    values.update({
        "Part B Deductible Amount": usd(row["NCH_BENE_PTB_DDCTBL_AMT"]),
        "Part B Coinsurance Amount": usd(row["NCH_BENE_PTB_COINSRNC_AMT"]),
    })
    return record(TITLE, values, study="CMS", agency=AGENCY, source_key="CMS_OP", subject=(SUBJECT, row["DESYNPUF_ID"]), row_ref=f"CLM_ID={row['CLM_ID']}")


def generate():
    t0 = time.time()
    keep = sample_ids()
    left = Left()
    count = 0
    for row in read_csv("CMS_OP"):
        if row["DESYNPUF_ID"] not in keep:
            continue
        write_record(OUTPUT_DIR, "co", build_instance(row, left))
        count += 1
    print(f"CMS Outpatient Claim: generated {count} XML files in {OUTPUT_DIR} ({time.time() - t0:.1f}s); codes left out: {left.counts}")
    return count


if __name__ == "__main__":
    generate()
