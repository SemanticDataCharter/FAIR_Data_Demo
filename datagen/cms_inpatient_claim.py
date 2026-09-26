"""
CMS Inpatient Claim 4.2.0: one record per DE-SynPUF inpatient claim row (2008-2010) of a sampled beneficiary.

The stay is the FHIR encounter by identifier; diagnoses and procedures are ICD-9-CM coded values as the
claims carry them (not mapped to ICD-10-CM), HCPCS codes the first ten line slots; amounts in US dollars.
"""
import time

from cms_common import AGENCY, SUBJECT, Left, claim_values, sample_ids, usd
from shared import Quantity, cms_date, import_dir, read_csv, record, write_record

TITLE = "CMS Inpatient Claim"
OUTPUT_DIR = import_dir("cms_inpatient_claim")


def build_instance(row: dict, left: Left) -> str:
    values = claim_values(row, "IMP", left)
    values.update({
        "Claim Admission Date (CLM_ADMSN_DT)": cms_date(row["CLM_ADMSN_DT"]),
        "Beneficiary Discharge Date (NCH_BENE_DSCHRG_DT)": cms_date(row["NCH_BENE_DSCHRG_DT"]),
        "Claim Pass-Through Per Diem Amount": usd(row["CLM_PASS_THRU_PER_DIEM_AMT"]),
        "Inpatient Deductible Amount": usd(row["NCH_BENE_IP_DDCTBL_AMT"]),
        "Part A Coinsurance Liability Amount": usd(row["NCH_BENE_PTA_COINSRNC_LBLTY_AM"]),
        "Claim Utilization Day Count (CLM_UTLZTN_DAY_CNT)": Quantity(row["CLM_UTLZTN_DAY_CNT"], "days") if row["CLM_UTLZTN_DAY_CNT"].isdigit() else None,
        "Diagnosis Related Group Code (CLM_DRG_CD)": row["CLM_DRG_CD"] if len(row["CLM_DRG_CD"]) == 3 and row["CLM_DRG_CD"].isdigit() else None,
    })
    return record(TITLE, values, study="CMS", agency=AGENCY, source_key="CMS_IP", subject=(SUBJECT, row["DESYNPUF_ID"]), row_ref=f"CLM_ID={row['CLM_ID']}")


def generate():
    t0 = time.time()
    keep = sample_ids()
    left = Left()
    count = 0
    for row in read_csv("CMS_IP"):
        if row["DESYNPUF_ID"] not in keep:
            continue
        write_record(OUTPUT_DIR, "ci", build_instance(row, left))
        count += 1
    print(f"CMS Inpatient Claim: generated {count} XML files in {OUTPUT_DIR} ({time.time() - t0:.1f}s); codes left out: {left.counts}")
    return count


if __name__ == "__main__":
    generate()
