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

# Components shared by ADNI + SPRINT only (Adverse Events, 4 components)
AE_COMPONENTS: dict[str, dict] = {
    "ae_description": {"ct_id": "pp5v32ipc0xbva1hi5l3r91g", "type": "XdString",   "label": "AE Description"},
    "ae_term":        {"ct_id": "fbfqzhm0es37p5rtrtw2wh0n", "type": "XdString",   "label": "AE Term"},
    "ae_start_date":  {"ct_id": "w0qi4triqgeeg0oodhy75p8h", "type": "XdTemporal", "label": "AE Start Date"},
    "ae_end_date":    {"ct_id": "andj4gpkessj3z0koheyc7gj", "type": "XdTemporal", "label": "AE End Date"},
}

# All known reusable ct_ids (for quick lookup)
ALL_REUSABLE_CT_IDS: set[str] = {
    c["ct_id"] for c in {**SHARED_COMPONENTS, **AE_COMPONENTS}.values()
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
    "adni": {
        "label": "ADNI",
        "full_name": "Alzheimer's Disease Neuroimaging Initiative",
        "funder": "NIA",
        "datasets": [
            "adni_demographics",
            "adni_vitals",
            "adni_labs",
            "adni_biospecimens",
            "adni_medications",
            "adni_adverse_events",
            "adni_cognitive",
            "adni_medical_history",
        ],
        "cde_domains": [
            "Demographics", "Vital Signs", "Lab Results",
            "Medications", "Medical History", "Biospecimens",
            "Adverse Events", "Cognitive Assessment",
        ],
    },
    "sprint": {
        "label": "SPRINT",
        "full_name": "Systolic Blood Pressure Intervention Trial",
        "funder": "NHLBI",
        "datasets": [
            "sprint_baseline",
            "sprint_blood_pressure",
            "sprint_labs",
            "sprint_medications",
            "sprint_adverse_events",
            "sprint_cognitive",
            "sprint_medical_history",
        ],
        "cde_domains": [
            "Demographics", "Vital Signs", "Lab Results",
            "Medications", "Medical History",
            "Adverse Events", "Cognitive Assessment",
        ],
    },
}


# ---------------------------------------------------------------------------
# Column-to-ct_id manual overrides per study
# ---------------------------------------------------------------------------
# NHANES uses coded column names (e.g. BPXSY1) that won't auto-match.
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

    # ADNI — column names are more descriptive, fewer overrides needed
    "adni_adverse_events": {
        "AETERM":     "fbfqzhm0es37p5rtrtw2wh0n", # AE Term
        "AESTDTC":    "w0qi4triqgeeg0oodhy75p8h",  # AE Start Date
        "AEENDTC":    "andj4gpkessj3z0koheyc7gj",  # AE End Date
    },

    # SPRINT — column names are fairly descriptive
    "sprint_adverse_events": {
        "AETERM":     "fbfqzhm0es37p5rtrtw2wh0n", # AE Term
        "AESTDT":     "w0qi4triqgeeg0oodhy75p8h",  # AE Start Date
        "AEENDT":     "andj4gpkessj3z0koheyc7gj",  # AE End Date
    },
}
