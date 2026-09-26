"""What the four CMS DE-SynPUF generators share: the sample of beneficiaries, code patterns, and the claim shape."""
from __future__ import annotations

import re

from shared import DEMO_SCALE, SAMPLE, Quantity, cms_date, qty, read_csv, seeded_sample

AGENCY = "Centers for Medicare & Medicaid Services"
SUBJECT = "Medicare Beneficiary"
DX_RE = re.compile(r"^[0-9EV][0-9]{2,4}$")
PX_RE = re.compile(r"^[0-9]{2,4}$")
HCPCS_RE = re.compile(r"^[0-9A-Z][0-9]{3}[0-9A-Z]$")
NPI_RE = re.compile(r"^[0-9]{10}$")
_sample: set | None = None


def sample_ids() -> set:
    """The beneficiaries every CMS generator carries: the seeded sample of SAMPLE['cms'], or every beneficiary with FAIR_FULL=1."""
    global _sample
    if _sample is None:
        ids = {row["DESYNPUF_ID"] for row in read_csv("CMS_BENE")}
        _sample = seeded_sample(ids, SAMPLE["cms"], "fair:cms") if DEMO_SCALE else ids
    return _sample


def usd(v: str):
    return qty(v, "USD")


def datetime_of(v: str):
    d = cms_date(v)
    return f"{d}T00:00:00" if d else None


def npi(v: str):
    return v if NPI_RE.match(v or "") else None


class Left:
    """Counts of codes a file carried that do not match the code system's pattern and were left out."""

    def __init__(self):
        self.counts = {}

    def take(self, kind: str, v: str, rx: re.Pattern):
        if not v:
            return None
        if rx.match(v):
            return v
        self.counts[kind] = self.counts.get(kind, 0) + 1
        return None


def claim_values(row: dict, encounter_class: str, left: Left) -> dict:
    """The values every claim carries: identifiers, the encounter, provider and physicians, the common amounts, the coded values."""
    values = {
        "Beneficiary Code (DESYNPUF_ID)": row["DESYNPUF_ID"],
        "Claim ID (CLM_ID)": row["CLM_ID"] if row["CLM_ID"].isdigit() else None,
        "Claim Line Segment (SEGMENT)": Quantity(row["SEGMENT"], "items") if row["SEGMENT"].isdigit() else None,
        "Encounter/Encounter Status": "finished",
        "Encounter/Encounter Class": encounter_class,
        "Encounter/Encounter Start": datetime_of(row["CLM_FROM_DT"]),
        "Encounter/Encounter End": datetime_of(row["CLM_THRU_DT"]),
        "Provider Institution (PRVDR_NUM)": row["PRVDR_NUM"] or None,
        "Claim Payment Amount": usd(row["CLM_PMT_AMT"]),
        "Primary Payer Claim Paid Amount": usd(row["NCH_PRMRY_PYR_CLM_PD_AMT"]),
        "Attending Physician NPI (AT_PHYSN_NPI)": npi(row["AT_PHYSN_NPI"]),
        "Operating Physician NPI (OP_PHYSN_NPI)": npi(row["OP_PHYSN_NPI"]),
        "Other Physician NPI (OT_PHYSN_NPI)": npi(row["OT_PHYSN_NPI"]),
        "Blood Deductible Liability Amount": usd(row["NCH_BENE_BLOOD_DDCTBL_LBLTY_AM"]),
        "Admitting Diagnosis/Diagnosis (ICD-9-CM)/Diagnosis Code (ICD-9-CM)": left.take("ICD-9-CM diagnosis", row["ADMTNG_ICD9_DGNS_CD"], DX_RE),
    }
    for n in range(1, 11):
        values[f"Claim Diagnosis {n}/Diagnosis (ICD-9-CM)/Diagnosis Code (ICD-9-CM)"] = left.take("ICD-9-CM diagnosis", row.get(f"ICD9_DGNS_CD_{n}", ""), DX_RE)
        values[f"Claim HCPCS {n}/Procedure (HCPCS)/HCPCS Code"] = left.take("HCPCS", row.get(f"HCPCS_CD_{n}", ""), HCPCS_RE)
    for n in range(1, 7):
        values[f"Claim Procedure {n}/Procedure (ICD-9-CM)/Procedure Code (ICD-9-CM)"] = left.take("ICD-9-CM procedure", row.get(f"ICD9_PRCDR_CD_{n}", ""), PX_RE)
    return values
