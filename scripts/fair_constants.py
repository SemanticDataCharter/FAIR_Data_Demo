"""
FAIR Data Demo — Shared Constants

Single source of truth for reusable component ct_ids, study metadata,
and column-to-ct_id manual overrides.

Component ct_ids match the NIH-CDE catalog in SDCStudio.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Reusable components shared across all 3 studies (17 components)
# ---------------------------------------------------------------------------

SHARED_COMPONENTS: dict[str, dict] = {
    "participant_id":           {"ct_id": "sdt9aiqjdbjjaafgjzzwygf8", "type": "XdString",   "label": "Participant ID"},
    "age_in_years":             {"ct_id": "c1nr0ykdr4w99ss7dty1iaug", "type": "XdCount",    "label": "Age in Years"},
    "birth_date":               {"ct_id": "g3k6bj8su3rvkszg2700dhyh", "type": "XdTemporal", "label": "Birth Date"},
    "sex":                      {"ct_id": "mw9qdn71urog8egjbp5t3y00", "type": "XdToken",    "label": "Sex"},
    "race":                     {"ct_id": "iiwx1rakgy3wfytyskre0v3x", "type": "XdToken",    "label": "Race"},
    "ethnicity":                {"ct_id": "ltobu9ek54hcnrjxk16jk8qk", "type": "XdToken",    "label": "Ethnicity"},
    "education_level":          {"ct_id": "dbv7fgfi67iztx00lgv1vxni", "type": "XdToken",    "label": "Education Level"},
    "marital_status":           {"ct_id": "w3bw02ebbrrs7mzu3ztkb8od", "type": "XdToken",    "label": "Marital Status"},
    "systolic_blood_pressure":  {"ct_id": "v15kv8dnd9th63hmccqetmki", "type": "XdQuantity", "label": "Systolic Blood Pressure"},
    "diastolic_blood_pressure": {"ct_id": "b0qfvgagjyebeuizpe900a93", "type": "XdQuantity", "label": "Diastolic Blood Pressure"},
    "heart_rate":               {"ct_id": "wmjt38l5le7u3ro7qjmkaaz7", "type": "XdQuantity", "label": "Heart Rate"},
    "respiratory_rate":         {"ct_id": "zseky2lf0pcuc7rsjtj49dm9", "type": "XdQuantity", "label": "Respiratory Rate"},
    "body_temperature":         {"ct_id": "s0yyyjcuu3l4ra93p5lktzig", "type": "XdQuantity", "label": "Body Temperature"},
    "bmi":                      {"ct_id": "wpojnsuwae37rfsnj9xpbcun", "type": "XdQuantity", "label": "BMI"},
    "person_weight":            {"ct_id": "scjotdd5kp3yovkvjgsc5a7v", "type": "XdQuantity", "label": "Person Weight Value"},
    "person_height":            {"ct_id": "mkelab9gci43xj7akjy8w7h3", "type": "XdQuantity", "label": "Person Height Value"},
    "smoking_status":           {"ct_id": "pcqb6t8q1g9e0fagm55fkhf2", "type": "XdToken",    "label": "Smoking Status"},
}

# All known reusable ct_ids (for quick lookup)
ALL_REUSABLE_CT_IDS: set[str] = {
    c["ct_id"] for c in SHARED_COMPONENTS.values()
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

COLUMN_OVERRIDES: dict[str, dict[str, str]] = {
    # NHANES coded names -> component ct_id
    "nhanes_demographics": {
        "SEQN":     "sdt9aiqjdbjjaafgjzzwygf8",  # Participant ID
        "RIDAGEYR": "c1nr0ykdr4w99ss7dty1iaug",  # Age in Years
        "RIAGENDR": "mw9qdn71urog8egjbp5t3y00",  # Sex
        "RIDRETH3": "iiwx1rakgy3wfytyskre0v3x",  # Race
        "DMDEDUC2": "dbv7fgfi67iztx00lgv1vxni",  # Education Level
        "DMDMARTZ": "w3bw02ebbrrs7mzu3ztkb8od",  # Marital Status
    },
    "nhanes_blood_pressure": {
        "BPXSY1":  "v15kv8dnd9th63hmccqetmki",   # Systolic Blood Pressure
        "BPXDI1":  "b0qfvgagjyebeuizpe900a93",   # Diastolic Blood Pressure
        "BPXPLS":  "wmjt38l5le7u3ro7qjmkaaz7",   # Heart Rate
    },
    "nhanes_smoking": {
        "SMQ020":  "pcqb6t8q1g9e0fagm55fkhf2",   # Smoking Status
    },

    # BRFSS coded names -> component ct_id
    "brfss": {
        "_AGE80":   "c1nr0ykdr4w99ss7dty1iaug",  # Age in Years (top-coded at 80)
        "_SEX":     "mw9qdn71urog8egjbp5t3y00",  # Sex
        "_RACE":    "iiwx1rakgy3wfytyskre0v3x",  # Race
        "_EDUCAG":  "dbv7fgfi67iztx00lgv1vxni",  # Education Level
        "MARITAL":  "w3bw02ebbrrs7mzu3ztkb8od",  # Marital Status
        "_SMOKER3": "pcqb6t8q1g9e0fagm55fkhf2",  # Smoking Status
        "_BMI5":    "wpojnsuwae37rfsnj9xpbcun",  # BMI (implied 1 decimal)
        "HTM4":     "mkelab9gci43xj7akjy8w7h3",  # Person Height Value
        "WTK3":     "scjotdd5kp3yovkvjgsc5a7v",  # Person Weight Value
        "BPHIGH6":  "v15kv8dnd9th63hmccqetmki",  # High Blood Pressure (systolic proxy)
    },

    # CMS coded names -> component ct_id
    "cms_beneficiary": {
        "DESYNPUF_ID":       "sdt9aiqjdbjjaafgjzzwygf8",  # Participant ID
        "BENE_SEX_IDENT_CD": "mw9qdn71urog8egjbp5t3y00",  # Sex
        "BENE_RACE_CD":      "iiwx1rakgy3wfytyskre0v3x",  # Race
        "BENE_BIRTH_DT":     "g3k6bj8su3rvkszg2700dhyh",  # Birth Date
    },
}
