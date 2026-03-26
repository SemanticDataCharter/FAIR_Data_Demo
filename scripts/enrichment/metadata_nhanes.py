"""
NHANES metadata loader.

Loads per-column metadata from JSON sidecar files extracted from SAS XPT files.
Supplements with hardcoded enumerations for well-known coded variables.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SOURCE_DIR = Path(__file__).resolve().parent.parent.parent / "source_data" / "nhanes"

# Sidecar files to load
SIDECAR_FILES = [
    "DEMO_J.json",
    "BPX_J.json",
    "CBC_J.json",
    "TCHOL_J.json",
    "RXQ_RX_J.json",
    "MCQ_J.json",
    "SMQ_J.json",
    "PFQ_J.json",
]

# ---------------------------------------------------------------------------
# Hardcoded enumerations for common NHANES coded variables
# ---------------------------------------------------------------------------
# NHANES uses a consistent coding pattern across survey questionnaires:
#   1 = Yes, 2 = No, 7 = Refused, 9 = Don't know

YES_NO_REFUSED_DK = {
    "1": "Yes",
    "2": "No",
    "7": "Refused",
    "9": "Don't know",
}

YES_NO_ONLY = {
    "1": "Yes",
    "2": "No",
}

GENDER_CODES = {
    "1": "Male",
    "2": "Female",
}

RACE_ETHNICITY_RIDRETH1 = {
    "1": "Mexican American",
    "2": "Other Hispanic",
    "3": "Non-Hispanic White",
    "4": "Non-Hispanic Black",
    "5": "Other Race - Including Multi-Racial",
}

RACE_ETHNICITY_RIDRETH3 = {
    "1": "Mexican American",
    "2": "Other Hispanic",
    "3": "Non-Hispanic White",
    "4": "Non-Hispanic Black",
    "6": "Non-Hispanic Asian",
    "7": "Other Race - Including Multi-Racial",
}

EDUCATION_CHILD = {
    "0": "Never attended / kindergarten only",
    "1": "1st grade",
    "2": "2nd grade",
    "3": "3rd grade",
    "4": "4th grade",
    "5": "5th grade",
    "6": "6th grade",
    "7": "7th grade",
    "8": "8th grade",
    "9": "9th grade",
    "10": "10th grade",
    "11": "11th grade",
    "12": "12th grade, no diploma",
    "13": "High school graduate",
    "14": "GED or equivalent",
    "15": "More than high school",
    "55": "Less than 5th grade",
    "66": "Less than 9th grade",
    "77": "Refused",
    "99": "Don't know",
}

EDUCATION_ADULT = {
    "1": "Less than 9th grade",
    "2": "9-11th grade (includes 12th grade with no diploma)",
    "3": "High school graduate/GED or equivalent",
    "4": "Some college or AA degree",
    "5": "College graduate or above",
    "7": "Refused",
    "9": "Don't know",
}

MARITAL_STATUS = {
    "1": "Married",
    "2": "Widowed",
    "3": "Divorced",
    "4": "Separated",
    "5": "Never married",
    "6": "Living with partner",
    "77": "Refused",
    "99": "Don't know",
}

PREGNANCY_STATUS = {
    "1": "Yes, positive lab pregnancy test or self-reported",
    "2": "The participant was not pregnant at exam",
    "3": "Cannot ascertain if the participant is pregnant at exam",
}

COUNTRY_BORN = {
    "1": "Born in 50 US states or Washington, DC",
    "2": "Others",
    "77": "Refused",
    "99": "Don't know",
}

CITIZENSHIP = {
    "1": "Citizen by birth or naturalization",
    "2": "Not a citizen of the US",
    "7": "Refused",
    "9": "Don't know",
}

LANGUAGE_CODES = {
    "1": "English",
    "2": "Spanish",
}

PROXY_CODES = {
    "1": "Yes",
    "2": "No",
}

INTERPRETER_CODES = {
    "1": "Yes",
    "2": "No",
}

SIX_MONTH_PERIOD = {
    "1": "November 1 through April 30",
    "2": "May 1 through October 31",
}

INTERVIEW_EXAM_STATUS = {
    "1": "Interviewed only",
    "2": "Both interviewed and MEC examined",
}

ARM_SELECTED = {
    "1": "Right",
    "2": "Left",
}

CUFF_SIZE = {
    "1": "Pediatric",
    "2": "Child",
    "3": "Adult",
    "4": "Large adult",
    "5": "Thigh",
}

PULSE_REGULARITY = {
    "1": "Regular",
    "2": "Irregular",
}

PULSE_TYPE = {
    "0": "Radial",
}

BP_STATUS_COMMENT = {
    "1": "Safety exclusion",
    "2": "SP refusal",
    "3": "No time",
    "4": "Physical limitation",
    "5": "Communication problem",
    "6": "Equipment failure",
    "7": "SP ill/emergency",
    "14": "Interrupted",
    "56": "Came acutely ill to lab",
    "99": "Other",
}

ENHANCEMENT_CODES = {
    "1": "Yes",
    "2": "No",
}

# Smoking frequency
SMOKE_NOW = {
    "1": "Every day",
    "2": "Some days",
    "3": "Not at all",
    "7": "Refused",
    "9": "Don't know",
}

HOW_SOON_AFTER_WAKING = {
    "1": "Within 5 minutes",
    "2": "From 6 to 30 minutes",
    "3": "From more than 30 minutes to one hour",
    "4": "More than one hour",
    "7": "Refused",
    "9": "Don't know",
}

CIGARETTES_IN_LIFE = {
    "1": "1 or more puffs but never a whole cigarette",
    "2": "1 cigarette",
    "3": "2 to 5 cigarettes",
    "4": "6 to 15 cigarettes (about 1/2 a pack)",
    "5": "16 to 25 cigarettes (about 1 pack)",
    "6": "26 to 49 cigarettes (about 2 packs)",
    "7": "50 to 99 cigarettes (about 3-4 packs)",
    "8": "100 or more cigarettes (5 or more packs)",
    "77": "Refused",
    "99": "Don't know",
}

CIGARETTE_BRAND_30DAY = {
    "1": "Marlboro",
    "2": "Camel",
    "3": "Newport",
    "8": "Other",
    "77": "Refused",
    "99": "Don't know",
}

FILTER_TYPE = {
    "0": "Non-filter",
    "1": "Filter",
    "2": "Filter - Loss not published",
}

MENTHOL_INDICATOR = {
    "1": "Menthol",
    "2": "Non-menthol",
}

CIGARETTE_LENGTH = {
    "1": "Regular (68-72 mm)",
    "2": "King (79-88 mm)",
    "3": "Long (94-101 mm)",
    "4": "Ultra long (110-121 mm)",
}

UNIT_OF_MEASURE_TIME = {
    "1": "Days",
    "2": "Weeks",
    "3": "Months",
    "4": "Years",
}

QUESTIONNAIRE_MODE = {
    "1": "Home Interview (20+)",
    "2": "ACASI (12-19)",
}

# Container seen
CONTAINER_SEEN = {
    "1": "Yes",
    "2": "No",
}

# Prescription use
PRESCRIPTION_USE = {
    "1": "Yes",
    "2": "No",
}

# Difficulty levels for PFQ061* series
DIFFICULTY_5POINT = {
    "1": "No difficulty",
    "2": "Some difficulty",
    "3": "Much difficulty",
    "4": "Unable to do",
    "7": "Refused",
    "9": "Don't know",
}

# Health problems causing difficulty (PFQ063*)
HEALTH_PROBLEM_CAUSING = {
    "10": "Arthritis/rheumatism",
    "11": "Back or neck problem",
    "12": "Birth defect",
    "13": "Cancer",
    "14": "Depression/anxiety/emotional problem",
    "15": "Other developmental problem",
    "16": "Diabetes",
    "17": "Fractures, bone/joint injury",
    "18": "Hearing problem",
    "19": "Heart problem",
    "20": "Hypertension/high blood pressure",
    "21": "Lung/breathing problem",
    "22": "Mental retardation",
    "23": "Other injury",
    "24": "Senility",
    "25": "Stroke problem",
    "26": "Vision/problem seeing",
    "27": "Weight problem",
    "28": "Other impairment/problem",
}

ARTHRITIS_TYPE = {
    "1": "Osteoarthritis or degenerative arthritis",
    "2": "Rheumatoid arthritis",
    "3": "Psoriatic arthritis",
    "9": "Don't know",
}

ABDOMINAL_PAIN_LOCATION = {
    "1": "Right upper abdomen",
    "2": "Right lower abdomen",
    "3": "Left upper abdomen",
    "4": "Left lower abdomen",
    "5": "Upper abdomen",
    "6": "Lower abdomen",
    "7": "Entire abdomen",
    "77": "Refused",
    "99": "Don't know",
}

# Map column_name → enumeration dict for well-known coded variables
NHANES_ENUMERATIONS: dict[str, dict[str, str]] = {
    # Demographics
    "RIAGENDR": GENDER_CODES,
    "RIDRETH1": RACE_ETHNICITY_RIDRETH1,
    "RIDRETH3": RACE_ETHNICITY_RIDRETH3,
    "RIDSTATR": INTERVIEW_EXAM_STATUS,
    "RIDEXMON": SIX_MONTH_PERIOD,
    "RIDEXPRG": PREGNANCY_STATUS,
    "DMDBORN4": COUNTRY_BORN,
    "DMDCITZN": CITIZENSHIP,
    "DMDEDUC3": EDUCATION_CHILD,
    "DMDEDUC2": EDUCATION_ADULT,
    "DMDMARTL": MARITAL_STATUS,
    "DMDHRGND": GENDER_CODES,
    "SIALANG": LANGUAGE_CODES,
    "FIALANG": LANGUAGE_CODES,
    "MIALANG": LANGUAGE_CODES,
    "SIAPROXY": PROXY_CODES,
    "FIAPROXY": PROXY_CODES,
    "MIAPROXY": PROXY_CODES,
    "SIAINTRP": INTERPRETER_CODES,
    "FIAINTRP": INTERPRETER_CODES,
    "MIAINTRP": INTERPRETER_CODES,
    "AIALANGA": LANGUAGE_CODES,
    "DMQMILIZ": YES_NO_REFUSED_DK,
    "DMQADFC": YES_NO_REFUSED_DK,
    # Blood pressure
    "PEASCCT1": BP_STATUS_COMMENT,
    "BPAARM": ARM_SELECTED,
    "BPACSZ": CUFF_SIZE,
    "BPXPULS": PULSE_REGULARITY,
    "BPXPTY": PULSE_TYPE,
    "BPAEN1": ENHANCEMENT_CODES,
    "BPAEN2": ENHANCEMENT_CODES,
    "BPAEN3": ENHANCEMENT_CODES,
    "BPAEN4": ENHANCEMENT_CODES,
    # Medical conditions — Yes/No/Refused/DK pattern
    "MCQ010": YES_NO_REFUSED_DK,
    "MCQ035": YES_NO_REFUSED_DK,
    "MCQ040": YES_NO_REFUSED_DK,
    "MCQ050": YES_NO_REFUSED_DK,
    "AGQ030": YES_NO_REFUSED_DK,
    "MCQ053": YES_NO_REFUSED_DK,
    "MCQ080": YES_NO_REFUSED_DK,
    "MCQ092": YES_NO_REFUSED_DK,
    "MCQ149": YES_NO_REFUSED_DK,
    "MCQ160A": YES_NO_REFUSED_DK,
    "MCQ160B": YES_NO_REFUSED_DK,
    "MCQ160C": YES_NO_REFUSED_DK,
    "MCQ160D": YES_NO_REFUSED_DK,
    "MCQ160E": YES_NO_REFUSED_DK,
    "MCQ160F": YES_NO_REFUSED_DK,
    "MCQ160G": YES_NO_REFUSED_DK,
    "MCQ160K": YES_NO_REFUSED_DK,
    "MCQ160L": YES_NO_REFUSED_DK,
    "MCQ160M": YES_NO_REFUSED_DK,
    "MCQ160N": YES_NO_REFUSED_DK,
    "MCQ160O": YES_NO_REFUSED_DK,
    "MCQ170K": YES_NO_REFUSED_DK,
    "MCQ170L": YES_NO_REFUSED_DK,
    "MCQ170M": YES_NO_REFUSED_DK,
    "MCQ195": ARTHRITIS_TYPE,
    "MCQ203": YES_NO_REFUSED_DK,
    "MCQ220": YES_NO_REFUSED_DK,
    "MCQ300A": YES_NO_REFUSED_DK,
    "MCQ300B": YES_NO_REFUSED_DK,
    "MCQ300C": YES_NO_REFUSED_DK,
    "MCQ366A": YES_NO_REFUSED_DK,
    "MCQ366B": YES_NO_REFUSED_DK,
    "MCQ366C": YES_NO_REFUSED_DK,
    "MCQ366D": YES_NO_REFUSED_DK,
    "MCQ371A": YES_NO_REFUSED_DK,
    "MCQ371B": YES_NO_REFUSED_DK,
    "MCQ371C": YES_NO_REFUSED_DK,
    "MCQ371D": YES_NO_REFUSED_DK,
    "MCQ500": YES_NO_REFUSED_DK,
    "MCQ510A": YES_NO_ONLY,
    "MCQ510B": YES_NO_ONLY,
    "MCQ510C": YES_NO_ONLY,
    "MCQ510D": YES_NO_ONLY,
    "MCQ510E": YES_NO_ONLY,
    "MCQ510F": YES_NO_ONLY,
    "MCQ520": YES_NO_REFUSED_DK,
    "MCQ530": ABDOMINAL_PAIN_LOCATION,
    "MCQ540": YES_NO_REFUSED_DK,
    "MCQ550": YES_NO_REFUSED_DK,
    "MCQ560": YES_NO_REFUSED_DK,
    "OSQ230": YES_NO_REFUSED_DK,
    # Smoking
    "SMQ020": YES_NO_REFUSED_DK,
    "SMQ040": SMOKE_NOW,
    "SMQ050U": UNIT_OF_MEASURE_TIME,
    "SMQ078": HOW_SOON_AFTER_WAKING,
    "SMD093": CONTAINER_SEEN,
    "SMD100FL": FILTER_TYPE,
    "SMD100MN": MENTHOL_INDICATOR,
    "SMD100LN": CIGARETTE_LENGTH,
    "SMQ621": CIGARETTES_IN_LIFE,
    "SMQ661": CIGARETTE_BRAND_30DAY,
    "SMQ670": YES_NO_REFUSED_DK,
    "SMQ852U": UNIT_OF_MEASURE_TIME,
    "SMQ890": YES_NO_REFUSED_DK,
    "SMQ900": YES_NO_REFUSED_DK,
    "SMQ910": YES_NO_REFUSED_DK,
    "SMAQUEX2": QUESTIONNAIRE_MODE,
    # Physical functioning — Yes/No/Refused/DK
    "PFQ020": YES_NO_REFUSED_DK,
    "PFQ030": YES_NO_REFUSED_DK,
    "PFQ033": YES_NO_REFUSED_DK,
    "PFQ041": YES_NO_REFUSED_DK,
    "PFQ049": YES_NO_REFUSED_DK,
    "PFQ051": YES_NO_REFUSED_DK,
    "PFQ054": YES_NO_REFUSED_DK,
    "PFQ057": YES_NO_REFUSED_DK,
    "PFQ059": YES_NO_REFUSED_DK,
    "PFQ090": YES_NO_REFUSED_DK,
    # PFQ061 series - difficulty levels
    "PFQ061A": DIFFICULTY_5POINT,
    "PFQ061B": DIFFICULTY_5POINT,
    "PFQ061C": DIFFICULTY_5POINT,
    "PFQ061D": DIFFICULTY_5POINT,
    "PFQ061E": DIFFICULTY_5POINT,
    "PFQ061F": DIFFICULTY_5POINT,
    "PFQ061G": DIFFICULTY_5POINT,
    "PFQ061H": DIFFICULTY_5POINT,
    "PFQ061I": DIFFICULTY_5POINT,
    "PFQ061J": DIFFICULTY_5POINT,
    "PFQ061K": DIFFICULTY_5POINT,
    "PFQ061L": DIFFICULTY_5POINT,
    "PFQ061M": DIFFICULTY_5POINT,
    "PFQ061N": DIFFICULTY_5POINT,
    "PFQ061O": DIFFICULTY_5POINT,
    "PFQ061P": DIFFICULTY_5POINT,
    "PFQ061Q": DIFFICULTY_5POINT,
    "PFQ061R": DIFFICULTY_5POINT,
    "PFQ061S": DIFFICULTY_5POINT,
    "PFQ061T": DIFFICULTY_5POINT,
    # PFQ063 series - health problems
    "PFQ063A": HEALTH_PROBLEM_CAUSING,
    "PFQ063B": HEALTH_PROBLEM_CAUSING,
    "PFQ063C": HEALTH_PROBLEM_CAUSING,
    "PFQ063D": HEALTH_PROBLEM_CAUSING,
    "PFQ063E": HEALTH_PROBLEM_CAUSING,
    # Medications
    "RXDUSE": PRESCRIPTION_USE,
    "RXQSEEN": CONTAINER_SEEN,
}


@dataclass
class NHANESColumnMeta:
    """Metadata for a single NHANES column."""
    label: str
    description: str
    enums: dict[str, str] | None = None
    enum_descriptions: dict[str, str] | None = None


def load_nhanes_metadata() -> dict[str, NHANESColumnMeta]:
    """Load all NHANES sidecar metadata and enumerations.

    Returns:
        Dict mapping column_name → NHANESColumnMeta.
    """
    result: dict[str, NHANESColumnMeta] = {}

    for filename in SIDECAR_FILES:
        filepath = SOURCE_DIR / filename
        if not filepath.exists():
            logger.warning("NHANES sidecar not found: %s", filepath)
            continue

        with open(filepath) as f:
            data = json.load(f)

        columns = data.get("columns", {})
        for col_name, col_info in columns.items():
            label = col_info.get("label", "")
            description = col_info.get("description", "")

            # Get enumerations from sidecar value_labels or hardcoded
            value_labels = col_info.get("value_labels")
            enums = None
            if value_labels and isinstance(value_labels, dict):
                # Convert numeric keys to strings
                enums = {str(k).rstrip(".0"): v for k, v in value_labels.items()}
            elif col_name in NHANES_ENUMERATIONS:
                enums = NHANES_ENUMERATIONS[col_name]

            # If no sidecar enums but hardcoded exists, use hardcoded
            if enums is None and col_name in NHANES_ENUMERATIONS:
                enums = NHANES_ENUMERATIONS[col_name]

            result[col_name] = NHANESColumnMeta(
                label=label,
                description=description,
                enums=enums,
            )

    # Add any hardcoded enums for columns not in sidecars
    for col_name, enum_dict in NHANES_ENUMERATIONS.items():
        if col_name not in result:
            result[col_name] = NHANESColumnMeta(
                label="",
                description="",
                enums=enum_dict,
            )

    logger.info("Loaded NHANES metadata for %d columns", len(result))
    return result
