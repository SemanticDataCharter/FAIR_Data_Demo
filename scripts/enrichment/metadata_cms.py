"""
CMS DE-SynPUF column metadata.

Hardcoded definitions from the CMS DE-SynPUF codebook covering:
- Beneficiary Summary (~30 columns)
- Inpatient Claims (~81 columns incl. repeated ICD9/HCPCS)
- Outpatient Claims (~78 columns incl. repeated ICD9/HCPCS)
- Prescription Drug Events (~8 columns)

Column names are self-documenting but terse. This module provides
human-readable labels, descriptions, and enumeration values.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Common enumerations across CMS datasets
CMS_SEX_CODES = {
    "1": "Male",
    "2": "Female",
}

CMS_RACE_CODES = {
    "1": "White",
    "2": "Black",
    "3": "Others",
    "5": "Hispanic",
}

CMS_CHRONIC_INDICATOR = {
    "1": "Yes, patient has condition",
    "2": "No, patient does not have condition",
}

CMS_ESRD_INDICATOR = {
    "Y": "Beneficiary has ESRD",
    "0": "No ESRD",
}


@dataclass
class CMSColumnMeta:
    """Metadata for a single CMS column."""
    label: str
    description: str
    enums: dict[str, str] | None = None


# ---------------------------------------------------------------------------
# Beneficiary Summary File columns
# ---------------------------------------------------------------------------
_BENEFICIARY: dict[str, CMSColumnMeta] = {
    "DESYNPUF_ID": CMSColumnMeta(
        label="Beneficiary Code",
        description="Unique identifier for each beneficiary in the DE-SynPUF dataset. Synthetic, not traceable to real Medicare beneficiaries.",
    ),
    "BENE_BIRTH_DT": CMSColumnMeta(
        label="Date of Birth",
        description="Beneficiary date of birth in YYYYMMDD integer format.",
    ),
    "BENE_DEATH_DT": CMSColumnMeta(
        label="Date of Death",
        description="Beneficiary date of death in YYYYMMDD format. Blank if beneficiary is alive.",
    ),
    "BENE_SEX_IDENT_CD": CMSColumnMeta(
        label="Sex",
        description="Beneficiary sex/gender code.",
        enums=CMS_SEX_CODES,
    ),
    "BENE_RACE_CD": CMSColumnMeta(
        label="Race",
        description="Beneficiary race code.",
        enums=CMS_RACE_CODES,
    ),
    "BENE_ESRD_IND": CMSColumnMeta(
        label="End-Stage Renal Disease Indicator",
        description="Indicator of whether the beneficiary has end-stage renal disease (ESRD).",
        enums=CMS_ESRD_INDICATOR,
    ),
    "SP_STATE_CODE": CMSColumnMeta(
        label="State Code",
        description="SSA state code for the beneficiary's mailing address.",
    ),
    "BENE_COUNTY_CD": CMSColumnMeta(
        label="County Code",
        description="SSA county code for the beneficiary's mailing address.",
    ),
    "BENE_HI_CVRAGE_TOT_MONS": CMSColumnMeta(
        label="Hospital Insurance Coverage Months",
        description="Total number of months of Part A (Hospital Insurance) coverage for the beneficiary in the reference year.",
    ),
    "BENE_SMI_CVRAGE_TOT_MONS": CMSColumnMeta(
        label="Supplementary Medical Insurance Coverage Months",
        description="Total number of months of Part B (Supplementary Medical Insurance) coverage for the beneficiary in the reference year.",
    ),
    "BENE_HMO_CVRAGE_TOT_MONS": CMSColumnMeta(
        label="HMO Coverage Months",
        description="Total number of months of HMO coverage for the beneficiary in the reference year.",
    ),
    "PLAN_CVRG_MOS_NUM": CMSColumnMeta(
        label="Part D Plan Coverage Months",
        description="Total number of months of Part D (prescription drug) plan coverage for the beneficiary in the reference year.",
    ),
    # Chronic condition indicators
    "SP_ALZHDMTA": CMSColumnMeta(
        label="Alzheimer's Disease or Related Disorders",
        description="Indicates whether the beneficiary has been diagnosed with Alzheimer's disease or related disorders/senile dementia.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_CHF": CMSColumnMeta(
        label="Congestive Heart Failure",
        description="Indicates whether the beneficiary has been diagnosed with heart failure.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_CHRNKIDN": CMSColumnMeta(
        label="Chronic Kidney Disease",
        description="Indicates whether the beneficiary has been diagnosed with chronic kidney disease.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_CNCR": CMSColumnMeta(
        label="Cancer",
        description="Indicates whether the beneficiary has been diagnosed with cancer (excluding skin cancer).",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_COPD": CMSColumnMeta(
        label="Chronic Obstructive Pulmonary Disease",
        description="Indicates whether the beneficiary has been diagnosed with COPD.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_DEPRESSN": CMSColumnMeta(
        label="Depression",
        description="Indicates whether the beneficiary has been diagnosed with depression.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_DIABETES": CMSColumnMeta(
        label="Diabetes",
        description="Indicates whether the beneficiary has been diagnosed with diabetes.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_ISCHMCHT": CMSColumnMeta(
        label="Ischemic Heart Disease",
        description="Indicates whether the beneficiary has been diagnosed with ischemic heart disease.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_OSTEOPRS": CMSColumnMeta(
        label="Osteoporosis",
        description="Indicates whether the beneficiary has been diagnosed with osteoporosis.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_RA_OA": CMSColumnMeta(
        label="Rheumatoid Arthritis / Osteoarthritis",
        description="Indicates whether the beneficiary has been diagnosed with rheumatoid arthritis or osteoarthritis.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    "SP_STRKETIA": CMSColumnMeta(
        label="Stroke / Transient Ischemic Attack",
        description="Indicates whether the beneficiary has been diagnosed with stroke or transient ischemic attack.",
        enums=CMS_CHRONIC_INDICATOR,
    ),
    # Financial summary fields
    "MEDREIMB_IP": CMSColumnMeta(
        label="Inpatient Annual Medicare Reimbursement",
        description="Total Medicare reimbursement amount for inpatient services during the reference year (USD).",
    ),
    "BENRES_IP": CMSColumnMeta(
        label="Inpatient Annual Beneficiary Responsibility",
        description="Total beneficiary responsibility amount for inpatient services during the reference year (USD).",
    ),
    "PPPYMT_IP": CMSColumnMeta(
        label="Inpatient Annual Primary Payer Reimbursement",
        description="Total amount paid by the primary payer for inpatient services during the reference year (USD).",
    ),
    "MEDREIMB_OP": CMSColumnMeta(
        label="Outpatient Annual Medicare Reimbursement",
        description="Total Medicare reimbursement amount for outpatient services during the reference year (USD).",
    ),
    "BENRES_OP": CMSColumnMeta(
        label="Outpatient Annual Beneficiary Responsibility",
        description="Total beneficiary responsibility amount for outpatient services during the reference year (USD).",
    ),
    "PPPYMT_OP": CMSColumnMeta(
        label="Outpatient Annual Primary Payer Reimbursement",
        description="Total amount paid by the primary payer for outpatient services during the reference year (USD).",
    ),
    "MEDREIMB_CAR": CMSColumnMeta(
        label="Carrier Annual Medicare Reimbursement",
        description="Total Medicare reimbursement amount for carrier (physician/supplier Part B) services during the reference year (USD).",
    ),
    "BENRES_CAR": CMSColumnMeta(
        label="Carrier Annual Beneficiary Responsibility",
        description="Total beneficiary responsibility amount for carrier services during the reference year (USD).",
    ),
    "PPPYMT_CAR": CMSColumnMeta(
        label="Carrier Annual Primary Payer Reimbursement",
        description="Total amount paid by the primary payer for carrier services during the reference year (USD).",
    ),
}

# ---------------------------------------------------------------------------
# Claims columns shared between Inpatient and Outpatient
# ---------------------------------------------------------------------------
_CLAIMS_COMMON: dict[str, CMSColumnMeta] = {
    "DESYNPUF_ID": CMSColumnMeta(
        label="Beneficiary Code",
        description="Unique identifier linking the claim to a beneficiary in the DE-SynPUF dataset.",
    ),
    "CLM_ID": CMSColumnMeta(
        label="Claim ID",
        description="Unique identifier for the claim.",
    ),
    "SEGMENT": CMSColumnMeta(
        label="Claim Line Segment",
        description="Segment number within the claim.",
    ),
    "CLM_FROM_DT": CMSColumnMeta(
        label="Claims Start Date",
        description="Start date of the claim period in YYYYMMDD integer format.",
    ),
    "CLM_THRU_DT": CMSColumnMeta(
        label="Claims End Date",
        description="End date of the claim period in YYYYMMDD integer format.",
    ),
    "PRVDR_NUM": CMSColumnMeta(
        label="Provider Institution Number",
        description="CMS Certification Number (CCN) of the institutional provider.",
    ),
    "CLM_PMT_AMT": CMSColumnMeta(
        label="Claim Payment Amount",
        description="Total amount paid for the claim by Medicare (USD).",
    ),
    "NCH_PRMRY_PYR_CLM_PD_AMT": CMSColumnMeta(
        label="Primary Payer Claim Paid Amount",
        description="Amount paid by the primary payer (other than Medicare) for the claim (USD).",
    ),
    "AT_PHYSN_NPI": CMSColumnMeta(
        label="Attending Physician NPI",
        description="National Provider Identifier of the attending physician.",
    ),
    "OP_PHYSN_NPI": CMSColumnMeta(
        label="Operating Physician NPI",
        description="National Provider Identifier of the operating physician.",
    ),
    "OT_PHYSN_NPI": CMSColumnMeta(
        label="Other Physician NPI",
        description="National Provider Identifier of another physician involved in the claim.",
    ),
    "NCH_BENE_BLOOD_DDCTBL_LBLTY_AM": CMSColumnMeta(
        label="Blood Deductible Liability Amount",
        description="Beneficiary liability amount for blood deductible (USD).",
    ),
    "ADMTNG_ICD9_DGNS_CD": CMSColumnMeta(
        label="Admitting Diagnosis Code (ICD-9-CM)",
        description="ICD-9-CM diagnosis code for the principal reason for admission.",
    ),
}

# Inpatient-only fields
_INPATIENT_SPECIFIC: dict[str, CMSColumnMeta] = {
    "CLM_ADMSN_DT": CMSColumnMeta(
        label="Claim Admission Date",
        description="Date the beneficiary was admitted to the inpatient facility in YYYYMMDD integer format.",
    ),
    "CLM_PASS_THRU_PER_DIEM_AMT": CMSColumnMeta(
        label="Claim Pass-Through Per Diem Amount",
        description="Per diem pass-through payment amount for the claim (USD).",
    ),
    "NCH_BENE_IP_DDCTBL_AMT": CMSColumnMeta(
        label="Inpatient Deductible Amount",
        description="Beneficiary inpatient deductible liability amount (USD).",
    ),
    "NCH_BENE_PTA_COINSRNC_LBLTY_AM": CMSColumnMeta(
        label="Part A Coinsurance Liability Amount",
        description="Beneficiary Part A coinsurance liability amount (USD).",
    ),
    "CLM_UTLZTN_DAY_CNT": CMSColumnMeta(
        label="Claim Utilization Day Count",
        description="Number of covered utilization days for the inpatient stay.",
    ),
    "NCH_BENE_DSCHRG_DT": CMSColumnMeta(
        label="Beneficiary Discharge Date",
        description="Date the beneficiary was discharged from the inpatient facility in YYYYMMDD format.",
    ),
    "CLM_DRG_CD": CMSColumnMeta(
        label="Diagnosis Related Group Code",
        description="DRG code assigned to the inpatient claim for prospective payment.",
    ),
}

# Outpatient-only fields
_OUTPATIENT_SPECIFIC: dict[str, CMSColumnMeta] = {
    "NCH_BENE_PTB_DDCTBL_AMT": CMSColumnMeta(
        label="Part B Deductible Amount",
        description="Beneficiary Part B deductible liability amount (USD).",
    ),
    "NCH_BENE_PTB_COINSRNC_AMT": CMSColumnMeta(
        label="Part B Coinsurance Amount",
        description="Beneficiary Part B coinsurance liability amount (USD).",
    ),
}

# ---------------------------------------------------------------------------
# Repeated (indexed) columns: ICD9 diagnosis, ICD9 procedure, HCPCS
# ---------------------------------------------------------------------------

def _generate_indexed_columns(
    prefix: str,
    count: int,
    label_template: str,
    description_template: str,
) -> dict[str, CMSColumnMeta]:
    """Generate metadata for indexed column families (e.g., ICD9_DGNS_CD_1..10)."""
    result = {}
    for i in range(1, count + 1):
        col_name = f"{prefix}_{i}"
        result[col_name] = CMSColumnMeta(
            label=label_template.format(i=i),
            description=description_template.format(i=i),
        )
    return result


# ICD-9 diagnosis codes (1-10 for both inpatient and outpatient)
_ICD9_DGNS = _generate_indexed_columns(
    "ICD9_DGNS_CD", 10,
    "ICD-9-CM Diagnosis Code {i}",
    "ICD-9-CM diagnosis code #{i} associated with the claim.",
)

# ICD-9 procedure codes (1-6 for both inpatient and outpatient)
_ICD9_PRCDR = _generate_indexed_columns(
    "ICD9_PRCDR_CD", 6,
    "ICD-9-CM Procedure Code {i}",
    "ICD-9-CM procedure code #{i} performed during the claim.",
)

# HCPCS codes — inpatient has up to 45, outpatient has up to 45
_HCPCS = _generate_indexed_columns(
    "HCPCS_CD", 45,
    "HCPCS Code {i}",
    "Healthcare Common Procedure Coding System (HCPCS) code #{i} for services rendered.",
)

# ---------------------------------------------------------------------------
# Prescription Drug Events columns
# ---------------------------------------------------------------------------
_PRESCRIPTIONS: dict[str, CMSColumnMeta] = {
    "DESYNPUF_ID": CMSColumnMeta(
        label="Beneficiary Code",
        description="Unique identifier linking the prescription drug event to a beneficiary.",
    ),
    "PDE_ID": CMSColumnMeta(
        label="Prescription Drug Event ID",
        description="Unique identifier for the prescription drug event.",
    ),
    "SRVC_DT": CMSColumnMeta(
        label="Service Date",
        description="Date the prescription was filled in YYYYMMDD integer format.",
    ),
    "PROD_SRVC_ID": CMSColumnMeta(
        label="Product/Service ID (NDC)",
        description="National Drug Code (NDC) identifying the drug product dispensed.",
    ),
    "QTY_DSPNSD_NUM": CMSColumnMeta(
        label="Quantity Dispensed",
        description="Number of units of the drug dispensed.",
    ),
    "DAYS_SUPLY_NUM": CMSColumnMeta(
        label="Days Supply",
        description="Number of days the dispensed drug supply is intended to last.",
    ),
    "PTNT_PAY_AMT": CMSColumnMeta(
        label="Patient Payment Amount",
        description="Amount paid by the patient/beneficiary for the prescription (USD).",
    ),
    "TOT_RX_CST_AMT": CMSColumnMeta(
        label="Total Prescription Cost",
        description="Total cost of the prescription drug event (USD).",
    ),
}


def _build_dataset_metadata(dataset: str) -> dict[str, CMSColumnMeta]:
    """Build the column metadata dict for a specific CMS dataset."""
    if dataset == "cms_beneficiary":
        return dict(_BENEFICIARY)
    elif dataset == "cms_inpatient":
        result = {}
        result.update(_CLAIMS_COMMON)
        result.update(_INPATIENT_SPECIFIC)
        result.update(_ICD9_DGNS)
        result.update(_ICD9_PRCDR)
        result.update(_HCPCS)
        return result
    elif dataset == "cms_outpatient":
        result = {}
        result.update(_CLAIMS_COMMON)
        result.update(_OUTPATIENT_SPECIFIC)
        result.update(_ICD9_DGNS)
        result.update(_ICD9_PRCDR)
        result.update(_HCPCS)
        return result
    elif dataset == "cms_prescriptions":
        return dict(_PRESCRIPTIONS)
    else:
        logger.warning("Unknown CMS dataset: %s", dataset)
        return {}


# Pre-built unified lookup: column_name → CMSColumnMeta
# Note: columns shared across datasets (DESYNPUF_ID, CLM_ID, etc.)
# will have the last dataset's version, which is fine since metadata is identical.
CMS_COLUMN_METADATA: dict[str, CMSColumnMeta] = {}
for _ds in ("cms_beneficiary", "cms_inpatient", "cms_outpatient", "cms_prescriptions"):
    CMS_COLUMN_METADATA.update(_build_dataset_metadata(_ds))


def load_cms_metadata() -> dict[str, CMSColumnMeta]:
    """Return the CMS column metadata dictionary.

    This is pre-built from hardcoded definitions, so no file I/O needed.
    """
    logger.info("CMS metadata: %d column definitions", len(CMS_COLUMN_METADATA))
    return CMS_COLUMN_METADATA
