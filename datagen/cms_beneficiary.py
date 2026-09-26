"""
CMS Beneficiary 4.2.0: one record per DE-SynPUF beneficiary summary row (2008).

Composes the Default date of birth and administrative gender, the FHIR patient's deceased fields
and insurance coverage, the NIH CDE race/ethnicity, the shared chronic condition indicators on a
claims basis, and the CMS-local codes and amounts. The seeded sample of beneficiaries this
generator writes is the sample every other CMS generator carries.
"""
import time

from cms_common import AGENCY, SUBJECT, sample_ids, usd
from shared import Quantity, cms_date, import_dir, read_csv, record, write_record

TITLE = "CMS Beneficiary"
OUTPUT_DIR = import_dir("cms_beneficiary")

SEX = {"1": "Male", "2": "Female"}
GENDER = {"1": "male", "2": "female"}
RACE = {"1": "White", "2": "Black", "3": "Others", "5": "Hispanic"}
RACE_CDE = {"1": "White", "2": "Black or African American", "5": "Hispanic, Latino, or Spanish"}   # Others has no CDE value
YESNO = {"1": "Yes", "2": "No"}
CONDITIONS = {   # CMS chronic conditions flag -> the shared indicator
    "SP_ALZHDMTA": "Condition: Alzheimer", "SP_CHF": "Condition: Congestive Heart Failure", "SP_CHRNKIDN": "Condition: Kidney Disease",
    "SP_CNCR": "Condition: Cancer", "SP_COPD": "Condition: COPD", "SP_DEPRESSN": "Condition: Depression", "SP_DIABETES": "Condition: Diabetes",
    "SP_ISCHMCHT": "Condition: Coronary Heart Disease", "SP_OSTEOPRS": "Condition: Osteoporosis", "SP_RA_OA": "Condition: Arthritis", "SP_STRKETIA": "Condition: Stroke",
}
ANNUAL = {
    "MEDREIMB_IP": "Inpatient Annual Medicare Reimbursement", "BENRES_IP": "Inpatient Annual Beneficiary Responsibility", "PPPYMT_IP": "Inpatient Annual Primary Payer Reimbursement",
    "MEDREIMB_OP": "Outpatient Annual Medicare Reimbursement", "BENRES_OP": "Outpatient Annual Beneficiary Responsibility", "PPPYMT_OP": "Outpatient Annual Primary Payer Reimbursement",
    "MEDREIMB_CAR": "Carrier Annual Medicare Reimbursement", "BENRES_CAR": "Carrier Annual Beneficiary Responsibility", "PPPYMT_CAR": "Carrier Annual Primary Payer Reimbursement",
}


def months(v: str):
    return Quantity(v, "months") if v.isdigit() else None


def build_instance(row: dict) -> str:
    death = cms_date(row["BENE_DEATH_DT"])
    values = {
        "Beneficiary Code (DESYNPUF_ID)": row["DESYNPUF_ID"],
        "End-Stage Renal Disease Indicator (BENE_ESRD_IND)": {"Y": "Yes", "0": "No"}.get(row["BENE_ESRD_IND"]),
        "CMS Beneficiary Demographics/Date of Birth": cms_date(row["BENE_BIRTH_DT"]),
        "CMS Beneficiary Demographics/Administrative Gender": GENDER.get(row["BENE_SEX_IDENT_CD"]),
        "Sex (BENE_SEX_IDENT_CD)": SEX.get(row["BENE_SEX_IDENT_CD"]),
        "Deceased Indicator": death is not None,
        "Deceased Date": f"{death}T00:00:00" if death else None,
        ("CMS Beneficiary Demographics", "Race/Ethnicity Self-Identification"): RACE_CDE.get(row["BENE_RACE_CD"]),
        "Race (BENE_RACE_CD)": RACE.get(row["BENE_RACE_CD"]),
        "State Code (SP_STATE_CODE)": row["SP_STATE_CODE"] or None,
        "County Code (BENE_COUNTY_CD)": row["BENE_COUNTY_CD"] or None,
        # Medicare in the reference year: the FHIR coverage as a public policy, active, held by the beneficiary
        "Insurance Coverage/Coverage Type": "PUBLICPOL",
        "Insurance Coverage/Coverage Status": "active",
        "Insurance Coverage/Subscriber Relationship": "self",
        "Insurance Coverage/Member ID": row["DESYNPUF_ID"],
        "Insurance Coverage/Coverage Period Start": "2008-01-01",
        "Insurance Coverage/Coverage Period End": "2008-12-31",
        "Hospital Insurance (Part A) Coverage Months": months(row["BENE_HI_CVRAGE_TOT_MONS"]),
        "Supplementary Medical Insurance (Part B) Coverage Months": months(row["BENE_SMI_CVRAGE_TOT_MONS"]),
        "HMO Coverage Months": months(row["BENE_HMO_CVRAGE_TOT_MONS"]),
        "Part D Plan Coverage Months": months(row["PLAN_CVRG_MOS_NUM"]),
        "Condition Indicator Basis": "Claims-based algorithm",
    }
    for col, label in CONDITIONS.items():
        values[label] = YESNO.get(row[col])
    for col, label in ANNUAL.items():
        values[label] = usd(row[col])
    xml = record(TITLE, values, study="CMS", agency=AGENCY, source_key="CMS_BENE", subject=(SUBJECT, row["DESYNPUF_ID"]), row_ref=f"DESYNPUF_ID={row['DESYNPUF_ID']}")
    # SDCStudio's instance template cuts a label at an apostrophe ("Condition: Alzheimer") while the schema fixes the full
    # label; the template is addressed by the cut label and the record carries the label the schema fixes.
    return xml.replace("<label>Condition: Alzheimer</label>", "<label>Condition: Alzheimer's Disease or Related Disorder</label>")


def generate():
    t0 = time.time()
    keep = sample_ids()
    count = 0
    for row in read_csv("CMS_BENE"):
        if row["DESYNPUF_ID"] not in keep:
            continue
        write_record(OUTPUT_DIR, "cb", build_instance(row))
        count += 1
    print(f"CMS Beneficiary: generated {count} XML files in {OUTPUT_DIR} ({time.time() - t0:.1f}s)")
    return count


if __name__ == "__main__":
    generate()
