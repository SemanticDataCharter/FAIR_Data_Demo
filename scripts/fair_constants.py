"""
FAIR Data Demo — Shared Constants

Single source of truth for reusable component ct_ids, study metadata,
and column-to-ct_id manual overrides.

Component ct_ids match the NIH-CDE catalog in SDCStudio.
After an initial pipeline run, update SHARED_COMPONENTS and
COLUMN_OVERRIDES with the newly minted ct_ids for future reuse.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Reusable components shared across all 3 studies (17 components)
# ---------------------------------------------------------------------------
# These will be populated after the first pipeline run mints them.
# The catalog-first discovery in sdc-agents 4.3.1 will find published
# components by semantic keyword matching, reducing the need for
# manual overrides.

SHARED_COMPONENTS: dict[str, dict] = {
    "participant_id":           {"ct_id": "", "type": "XdString",   "label": "Participant ID"},
    "age_in_years":             {"ct_id": "", "type": "XdCount",    "label": "Age in Years"},
    "birth_date":               {"ct_id": "", "type": "XdTemporal", "label": "Birth Date"},
    "sex":                      {"ct_id": "", "type": "XdToken",    "label": "Sex"},
    "race":                     {"ct_id": "", "type": "XdToken",    "label": "Race"},
    "ethnicity":                {"ct_id": "", "type": "XdToken",    "label": "Ethnicity"},
    "education_level":          {"ct_id": "", "type": "XdToken",    "label": "Education Level"},
    "marital_status":           {"ct_id": "", "type": "XdToken",    "label": "Marital Status"},
    "systolic_blood_pressure":  {"ct_id": "", "type": "XdQuantity", "label": "Systolic Blood Pressure"},
    "diastolic_blood_pressure": {"ct_id": "", "type": "XdQuantity", "label": "Diastolic Blood Pressure"},
    "heart_rate":               {"ct_id": "", "type": "XdQuantity", "label": "Heart Rate"},
    "respiratory_rate":         {"ct_id": "", "type": "XdQuantity", "label": "Respiratory Rate"},
    "body_temperature":         {"ct_id": "", "type": "XdQuantity", "label": "Body Temperature"},
    "bmi":                      {"ct_id": "", "type": "XdQuantity", "label": "BMI"},
    "person_weight":            {"ct_id": "", "type": "XdQuantity", "label": "Person Weight Value"},
    "person_height":            {"ct_id": "", "type": "XdQuantity", "label": "Person Height Value"},
    "smoking_status":           {"ct_id": "", "type": "XdToken",    "label": "Smoking Status"},
}

# All known reusable ct_ids (for quick lookup)
ALL_REUSABLE_CT_IDS: set[str] = {
    c["ct_id"] for c in SHARED_COMPONENTS.values() if c["ct_id"]
}


# ---------------------------------------------------------------------------
# Study metadata
# ---------------------------------------------------------------------------

STUDIES: dict[str, dict] = {
    "nhanes": {
        "label": "NHANES",
        "full_name": "National Health and Nutrition Examination Survey",
        "funder": "CDC/NCHS",
        "datasets": [
            "nhanes_demographics",
            "nhanes_blood_pressure",
            "nhanes_cbc",
            "nhanes_cholesterol",
            "nhanes_medications",
            "nhanes_medical_conditions",
            "nhanes_smoking",
            "nhanes_physical_functioning",
        ],
        "cde_domains": [
            "Demographics", "Vital Signs", "Lab Results",
            "Medications", "Medical History", "Biospecimens",
            "Substance Use", "SDOH", "Physical Function", "Pain",
        ],
    },
    "brfss": {
        "label": "BRFSS",
        "full_name": "Behavioral Risk Factor Surveillance System",
        "funder": "CDC",
        "datasets": [
            "brfss",
        ],
        "cde_domains": [
            "Demographics", "Vital Signs", "Medical History",
            "Substance Use", "Physical Function",
        ],
    },
    "cms": {
        "label": "CMS",
        "full_name": "CMS DE-SynPUF (Medicare Claims Synthetic Data)",
        "funder": "CMS",
        "datasets": [
            "cms_beneficiary",
            "cms_inpatient",
            "cms_outpatient",
            "cms_prescriptions",
        ],
        "cde_domains": [
            "Demographics", "Medical History", "Medications",
        ],
    },
}


# ---------------------------------------------------------------------------
# Column-to-ct_id manual overrides per study
# ---------------------------------------------------------------------------
# NHANES and BRFSS use coded column names that won't auto-match.
# CMS uses short coded names for beneficiary demographics.
# These overrides tell the pipeline which catalog component to reuse
# for specific source columns.
#
# After the first pipeline run with catalog-first discovery (4.3.1+),
# populate these with the ct_ids of newly minted/matched components
# to ensure consistent reuse on subsequent runs.

COLUMN_OVERRIDES: dict[str, dict[str, str]] = {
    # Will be populated after first run with new ct_ids
}
