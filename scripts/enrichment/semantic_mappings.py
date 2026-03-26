"""
Semantic mappings for FAIR Data Demo component enrichment.

Defines:
- Namespaces to register (snomed, loinc, icd10)
- Predicates needed (skos:exactMatch, skos:closeMatch, dcterms:subject, rdfs:isDefinedBy)
- Curated semantic mappings: column_name → list of {predicate, object_uri, po_name}
- Domain subject URIs for broad categorization
"""
from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# New namespaces to register (if not already present)
# ---------------------------------------------------------------------------
NEW_NAMESPACES: dict[str, str] = {
    "snomed": "http://snomed.info/id/",
    "loinc": "https://loinc.org/",
    "icd10": "http://hl7.org/fhir/sid/icd-10-cm/",
}

# ---------------------------------------------------------------------------
# Predicates needed (namespace_abbrev, local_name)
# ---------------------------------------------------------------------------
# These may already exist; the enrichment script checks before creating.
PREDICATES_NEEDED: list[tuple[str, str]] = [
    ("skos", "exactMatch"),
    ("skos", "closeMatch"),
    ("dcterms", "subject"),
    ("rdfs", "isDefinedBy"),
]


@dataclass
class SemanticLink:
    """A single semantic link to apply to a component."""
    predicate_ns: str   # e.g., "skos"
    predicate_name: str  # e.g., "exactMatch"
    object_uri: str      # e.g., "https://loinc.org/8480-6"
    po_name: str         # Human-readable name, e.g., "LOINC 8480-6 Systolic BP"


# ---------------------------------------------------------------------------
# Domain subject URIs — broad categorization per dataset/domain
# ---------------------------------------------------------------------------
DOMAIN_SUBJECTS: dict[str, SemanticLink] = {
    # NHANES datasets
    "nhanes_demographics": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/15220000",
        "SNOMED CT: Laboratory test (procedure)",
    ),
    "nhanes_blood_pressure": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/46973005",
        "SNOMED CT: Blood pressure taking (procedure)",
    ),
    "nhanes_cbc": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/26604007",
        "SNOMED CT: Complete blood count (procedure)",
    ),
    "nhanes_cholesterol": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/77068002",
        "SNOMED CT: Cholesterol measurement (procedure)",
    ),
    "nhanes_medications": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/182832007",
        "SNOMED CT: Drug therapy (procedure)",
    ),
    "nhanes_medical_conditions": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/84100007",
        "SNOMED CT: History taking (procedure)",
    ),
    "nhanes_smoking": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/365981007",
        "SNOMED CT: Tobacco use and exposure (observable)",
    ),
    "nhanes_physical_functioning": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/301857004",
        "SNOMED CT: Ability to perform activities of daily living (observable)",
    ),
    # BRFSS
    "brfss": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/410188000",
        "SNOMED CT: Behavioral risk factor surveillance",
    ),
    # CMS datasets
    "cms_beneficiary": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/184102003",
        "SNOMED CT: Patient demographics (record artifact)",
    ),
    "cms_inpatient": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/32485007",
        "SNOMED CT: Hospital admission (procedure)",
    ),
    "cms_outpatient": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/281685003",
        "SNOMED CT: Outpatient care (regime/therapy)",
    ),
    "cms_prescriptions": SemanticLink(
        "dcterms", "subject",
        "http://snomed.info/id/182832007",
        "SNOMED CT: Drug therapy (procedure)",
    ),
}

# ---------------------------------------------------------------------------
# Source codebook reference links (rdfs:isDefinedBy)
# ---------------------------------------------------------------------------
SOURCE_REFERENCES: dict[str, SemanticLink] = {
    "nhanes": SemanticLink(
        "rdfs", "isDefinedBy",
        "https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017",
        "NHANES 2017-2018 Survey Documentation",
    ),
    "brfss": SemanticLink(
        "rdfs", "isDefinedBy",
        "https://www.cdc.gov/brfss/annual_data/annual_2022.html",
        "BRFSS 2022 Survey Data Documentation",
    ),
    "cms": SemanticLink(
        "rdfs", "isDefinedBy",
        "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf",
        "CMS DE-SynPUF Codebook Documentation",
    ),
}

# ---------------------------------------------------------------------------
# Curated per-column semantic mappings
# ---------------------------------------------------------------------------
# High-value columns mapped to LOINC and SNOMED CT codes.
# Format: column_name → list of SemanticLink

COLUMN_SEMANTIC_MAPPINGS: dict[str, list[SemanticLink]] = {
    # ── NHANES Blood Pressure ────────────────────────────────────────
    "BPXSY1": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8480-6", "LOINC 8480-6: Systolic blood pressure"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/271649006", "SNOMED CT: Systolic blood pressure"),
    ],
    "BPXSY2": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8480-6", "LOINC 8480-6: Systolic blood pressure"),
    ],
    "BPXSY3": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8480-6", "LOINC 8480-6: Systolic blood pressure"),
    ],
    "BPXSY4": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8480-6", "LOINC 8480-6: Systolic blood pressure"),
    ],
    "BPXDI1": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8462-4", "LOINC 8462-4: Diastolic blood pressure"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/271650006", "SNOMED CT: Diastolic blood pressure"),
    ],
    "BPXDI2": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8462-4", "LOINC 8462-4: Diastolic blood pressure"),
    ],
    "BPXDI3": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8462-4", "LOINC 8462-4: Diastolic blood pressure"),
    ],
    "BPXDI4": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8462-4", "LOINC 8462-4: Diastolic blood pressure"),
    ],
    "BPXCHR": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8867-4", "LOINC 8867-4: Heart rate"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/364075005", "SNOMED CT: Heart rate"),
    ],
    "BPXPLS": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8867-4", "LOINC 8867-4: Heart rate"),
    ],
    "BPXML1": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/46973005", "SNOMED CT: Blood pressure taking"),
    ],

    # ── NHANES CBC (Complete Blood Count) ────────────────────────────
    "LBXWBCSI": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/6690-2", "LOINC 6690-2: WBC count"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/767002", "SNOMED CT: White blood cell count"),
    ],
    "LBXLYPCT": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/736-9", "LOINC 736-9: Lymphocytes/100 leukocytes"),
    ],
    "LBXMOPCT": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/5905-5", "LOINC 5905-5: Monocytes/100 leukocytes"),
    ],
    "LBXNEPCT": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/770-8", "LOINC 770-8: Neutrophils/100 leukocytes"),
    ],
    "LBXEOPCT": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/713-8", "LOINC 713-8: Eosinophils/100 leukocytes"),
    ],
    "LBXBAPCT": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/706-2", "LOINC 706-2: Basophils/100 leukocytes"),
    ],
    "LBDLYMNO": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/731-0", "LOINC 731-0: Lymphocytes (#/volume)"),
    ],
    "LBDMONO": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/742-7", "LOINC 742-7: Monocytes (#/volume)"),
    ],
    "LBDNENO": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/751-8", "LOINC 751-8: Neutrophils (#/volume)"),
    ],
    "LBDEONO": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/711-2", "LOINC 711-2: Eosinophils (#/volume)"),
    ],
    "LBDBANO": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/704-7", "LOINC 704-7: Basophils (#/volume)"),
    ],
    "LBXRBCSI": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/789-8", "LOINC 789-8: RBC count"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/14089001", "SNOMED CT: Red blood cell count"),
    ],
    "LBXHGB": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/718-7", "LOINC 718-7: Hemoglobin"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/104142005", "SNOMED CT: Hemoglobin measurement"),
    ],
    "LBXHCT": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/4544-3", "LOINC 4544-3: Hematocrit"),
    ],
    "LBXMCVSI": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/787-2", "LOINC 787-2: Mean corpuscular volume"),
    ],
    "LBXMCHSI": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/785-6", "LOINC 785-6: Mean corpuscular hemoglobin"),
    ],
    "LBXMC": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/786-4", "LOINC 786-4: MCHC"),
    ],
    "LBXRDW": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/788-0", "LOINC 788-0: RBC distribution width"),
    ],
    "LBXPLTSI": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/777-3", "LOINC 777-3: Platelet count"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/61928009", "SNOMED CT: Platelet count"),
    ],
    "LBXMPSI": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/32623-1", "LOINC 32623-1: Mean platelet volume"),
    ],
    "LBXNRBC": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/19048-8", "LOINC 19048-8: Nucleated RBC/100 WBC"),
    ],

    # ── NHANES Cholesterol ───────────────────────────────────────────
    "LBXTC": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/2093-3", "LOINC 2093-3: Total cholesterol (mg/dL)"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/77068002", "SNOMED CT: Cholesterol measurement"),
    ],
    "LBDTCSI": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/2093-3", "LOINC 2093-3: Total cholesterol"),
    ],

    # ── NHANES Demographics ──────────────────────────────────────────
    "RIAGENDR": [
        SemanticLink("skos", "exactMatch", "http://snomed.info/id/263495000", "SNOMED CT: Gender"),
        SemanticLink("skos", "closeMatch", "https://loinc.org/46098-0", "LOINC 46098-0: Sex"),
    ],
    "RIDAGEYR": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/30525-0", "LOINC 30525-0: Age"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/424144002", "SNOMED CT: Current chronological age"),
    ],
    "RIDRETH1": [
        SemanticLink("skos", "closeMatch", "https://loinc.org/32624-9", "LOINC 32624-9: Race"),
    ],
    "DMDEDUC2": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/105421008", "SNOMED CT: Educational attainment"),
    ],
    "DMDMARTL": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/125680007", "SNOMED CT: Marital status"),
    ],

    # ── NHANES Medical Conditions ────────────────────────────────────
    "MCQ010": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/195967001", "SNOMED CT: Asthma"),
    ],
    "MCQ160A": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/3723001", "SNOMED CT: Arthritis"),
    ],
    "MCQ160B": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/42343007", "SNOMED CT: Congestive heart failure"),
    ],
    "MCQ160C": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/53741008", "SNOMED CT: Coronary heart disease"),
    ],
    "MCQ160E": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/22298006", "SNOMED CT: Myocardial infarction"),
    ],
    "MCQ160F": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/230690007", "SNOMED CT: Stroke"),
    ],
    "MCQ220": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/363346000", "SNOMED CT: Malignant neoplastic disease"),
    ],

    # ── NHANES Smoking ───────────────────────────────────────────────
    "SMQ020": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/77176002", "SNOMED CT: Smoker"),
        SemanticLink("skos", "closeMatch", "https://loinc.org/72166-2", "LOINC 72166-2: Tobacco smoking status"),
    ],
    "SMQ040": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/72166-2", "LOINC 72166-2: Tobacco smoking status"),
    ],

    # ── NHANES Medications ───────────────────────────────────────────
    "RXDDRUG": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/410942007", "SNOMED CT: Drug or medicament"),
    ],
    "RXDRSC1": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/439401001", "SNOMED CT: Diagnosis"),
    ],

    # ── CMS Beneficiary ──────────────────────────────────────────────
    "BENE_SEX_IDENT_CD": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/263495000", "SNOMED CT: Gender"),
    ],
    "BENE_RACE_CD": [
        SemanticLink("skos", "closeMatch", "https://loinc.org/32624-9", "LOINC 32624-9: Race"),
    ],
    "SP_ALZHDMTA": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/26929004", "SNOMED CT: Alzheimer's disease"),
    ],
    "SP_CHF": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/42343007", "SNOMED CT: Congestive heart failure"),
    ],
    "SP_CHRNKIDN": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/709044004", "SNOMED CT: Chronic kidney disease"),
    ],
    "SP_CNCR": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/363346000", "SNOMED CT: Malignant neoplastic disease"),
    ],
    "SP_COPD": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/13645005", "SNOMED CT: COPD"),
    ],
    "SP_DEPRESSN": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/35489007", "SNOMED CT: Depressive disorder"),
    ],
    "SP_DIABETES": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/73211009", "SNOMED CT: Diabetes mellitus"),
    ],
    "SP_ISCHMCHT": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/414545008", "SNOMED CT: Ischemic heart disease"),
    ],
    "SP_OSTEOPRS": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/64859006", "SNOMED CT: Osteoporosis"),
    ],
    "SP_RA_OA": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/3723001", "SNOMED CT: Arthritis"),
    ],
    "SP_STRKETIA": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/230690007", "SNOMED CT: Stroke"),
    ],

    # ── BRFSS key variables ──────────────────────────────────────────
    "GENHLTH": [
        SemanticLink("skos", "closeMatch", "https://loinc.org/11323-3", "LOINC 11323-3: Health status"),
    ],
    "PHYSHLTH": [
        SemanticLink("skos", "closeMatch", "https://loinc.org/77849-5", "LOINC: Days physical health not good"),
    ],
    "MENTHLTH": [
        SemanticLink("skos", "closeMatch", "https://loinc.org/77850-3", "LOINC: Days mental health not good"),
    ],
    "HLTHPLN1": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/224196002", "SNOMED CT: Health care coverage"),
    ],
    "DIABETE4": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/73211009", "SNOMED CT: Diabetes mellitus"),
    ],
    "BPHIGH6": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/38341003", "SNOMED CT: Hypertensive disorder"),
    ],
    "TOLDHI3": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/55822004", "SNOMED CT: Hyperlipidemia"),
    ],
    "CVDINFR4": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/22298006", "SNOMED CT: Myocardial infarction"),
    ],
    "CVDCRHD4": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/53741008", "SNOMED CT: Coronary heart disease"),
    ],
    "CVDSTRK3": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/230690007", "SNOMED CT: Stroke"),
    ],
    "ASTHMA3": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/195967001", "SNOMED CT: Asthma"),
    ],
    "CHCCOPD3": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/13645005", "SNOMED CT: COPD"),
    ],
    "HAVARTH5": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/3723001", "SNOMED CT: Arthritis"),
    ],
    "ADDEPEV3": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/35489007", "SNOMED CT: Depressive disorder"),
    ],
    "CHCKDNY2": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/709044004", "SNOMED CT: Chronic kidney disease"),
    ],
    "SMOKE100": [
        SemanticLink("skos", "closeMatch", "https://loinc.org/72166-2", "LOINC 72166-2: Tobacco smoking status"),
    ],
    "_BMI5": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/39156-5", "LOINC 39156-5: Body mass index"),
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/60621009", "SNOMED CT: Body mass index"),
    ],
    "WEIGHT2": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/29463-7", "LOINC 29463-7: Body weight"),
    ],
    "HEIGHT3": [
        SemanticLink("skos", "exactMatch", "https://loinc.org/8302-2", "LOINC 8302-2: Body height"),
    ],
    "EXERANY2": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/256235009", "SNOMED CT: Exercise"),
    ],
    "SLEPTIM1": [
        SemanticLink("skos", "closeMatch", "https://loinc.org/65968-0", "LOINC: Sleep duration"),
    ],
    "DRNKANY6": [
        SemanticLink("skos", "closeMatch", "http://snomed.info/id/160573003", "SNOMED CT: Alcohol intake"),
    ],
}
