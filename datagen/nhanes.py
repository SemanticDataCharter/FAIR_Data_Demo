"""
NHANES 2017-2018: one Participant record per DEMO_J row, joined on SEQN across BPX_J, TCHOL_J,
CBC_J, MCQ_J, SMQ_J and PFQ_J; one Medication record per RXQ_RX_J row that names a medicine.

Every value is the agency's, by label path in the published model. A refusal (7) or a don't-know
(9) is left out and counted, since every leaf is optional and a stated absence would make the
record invalid on purpose where nothing is required. Harmonized values (the Default gender, the
NIH CDE race/ethnicity, marital status, pregnancy) are written beside the agency's own
codes, and the mapping is in this file where a reader can check it.
"""
import collections
import sys
import time

from schema import Schema
from shared import EV, Quantity, read_csv, code, number, qty, record, write_record, import_dir, model_ct, DEMO_SCALE

PARTICIPANT = "NHANES Participant"
MEDICATION = "NHANES Medication"
AGENCY = "National Center for Health Statistics, Centers for Disease Control and Prevention"
DROPPED = collections.Counter()   # variable -> refused / don't-know answers left out

YN = {"1": "Yes", "2": "No"}
GENDER = {"1": "Male", "2": "Female"}
ADMIN_GENDER = {"1": "male", "2": "female"}
RACE = {"1": "Mexican American", "2": "Other Hispanic", "3": "Non-Hispanic White", "4": "Non-Hispanic Black", "6": "Non-Hispanic Asian", "7": "Other Race - Including Multi-Racial"}
RACE_CDE = {"1": "Hispanic, Latino, or Spanish", "2": "Hispanic, Latino, or Spanish", "3": "White", "4": "Black or African American", "6": "Asian or Asian American"}   # 7 has no CDE value
BORN = {"1": "Born in 50 US states or Washington, DC", "2": "Others"}
CITIZEN = {"1": "Citizen by birth or naturalization", "2": "Not a citizen of the US"}
EDUC = {"1": "Less than 9th grade", "2": "9-11th grade (includes 12th grade with no diploma)", "3": "High school graduate/GED or equivalent", "4": "Some college or AA degree", "5": "College graduate or above"}
MARITAL = {"1": "Married", "2": "Widowed", "3": "Divorced", "4": "Separated", "5": "Never married", "6": "Living with partner"}
MARITAL_CDE = {"1": "Married", "2": "Widowed", "3": "Divorced", "4": "Separated", "5": "Single, never been married-not living with romantic partner", "6": "Living as married or living with a romantic partner"}
PREG = {"1": "Yes, positive lab pregnancy test or self-reported pregnant at exam", "2": "Not pregnant at exam", "3": "Cannot ascertain if pregnant at exam"}
PREG_CDE = {"1": "Yes", "2": "No", "3": "Unknown"}
INCOME = {"1": "$0 to $4,999", "2": "$5,000 to $9,999", "3": "$10,000 to $14,999", "4": "$15,000 to $19,999", "5": "$20,000 to $24,999", "6": "$25,000 to $34,999", "7": "$35,000 to $44,999",
          "8": "$45,000 to $54,999", "9": "$55,000 to $64,999", "10": "$65,000 to $74,999", "12": "$20,000 and Over", "13": "Under $20,000", "14": "$75,000 to $99,999", "15": "$100,000 and Over"}
STATUS = {"1": "Interviewed only", "2": "Both interviewed and MEC examined"}
ARM = {"1": "Right", "2": "Left"}
ARM_SITE = {"1": ("368209003", "Right upper arm"), "2": ("368208006", "Left upper arm")}
CUFF = {"1": "Infant (9 x 18 cm)", "2": "Child (12 x 22 cm)", "3": "Adult (15 x 32 cm)", "4": "Large (17 x 36 cm)", "5": "Thigh (23 x 38 cm)"}
PULSE = {"1": "Regular", "2": "Irregular"}
SMOKE_NOW = {"1": "Every day", "2": "Some days", "3": "Not at all"}
DIFFICULTY = {"1": "No difficulty", "2": "Some difficulty", "3": "Much difficulty", "4": "Unable to do", "5": "Do not do this activity"}
CONDITIONS = {"MCQ010": "Asthma", "MCQ160A": "Arthritis", "MCQ160B": "Congestive Heart Failure", "MCQ160C": "Coronary Heart Disease", "MCQ160D": "Angina", "MCQ160E": "Heart Attack",
              "MCQ160F": "Stroke", "MCQ160G": "Emphysema", "MCQ160K": "Chronic Bronchitis", "MCQ160O": "COPD", "MCQ160L": "Liver Condition", "MCQ160M": "Thyroid Problem", "MCQ220": "Cancer"}
PF_ITEMS = {"PFQ061B": "Difficulty Walking a Quarter Mile", "PFQ061C": "Difficulty Walking Up Ten Stairs", "PFQ061D": "Difficulty Stooping, Crouching or Kneeling", "PFQ061E": "Difficulty Lifting or Carrying",
            "PFQ061H": "Difficulty Walking Between Rooms", "PFQ061I": "Difficulty Standing Up from an Armless Chair", "PFQ061J": "Difficulty Getting In and Out of Bed", "PFQ061L": "Difficulty Dressing Yourself", "PFQ061M": "Difficulty Standing for Long Periods"}
LABS = [("LBXTC", "Total Cholesterol", "mg/dL"), ("LBDTCSI", "Total Cholesterol (SI)", "mmol/L"), ("LBXWBCSI", "White Blood Cell Count", "10*3/uL"), ("LBXLYPCT", "Lymphocyte Percent", "%"),
        ("LBXMOPCT", "Monocyte Percent", "%"), ("LBXNEPCT", "Segmented Neutrophils Percent", "%"), ("LBXEOPCT", "Eosinophils Percent", "%"), ("LBXBAPCT", "Basophils Percent", "%"),
        ("LBDLYMNO", "Lymphocyte Number", "10*3/uL"), ("LBDMONO", "Monocyte Number", "10*3/uL"), ("LBDNENO", "Segmented Neutrophils Number", "10*3/uL"), ("LBDEONO", "Eosinophils Number", "10*3/uL"),
        ("LBDBANO", "Basophils Number", "10*3/uL"), ("LBXRBCSI", "Red Blood Cell Count", "10*6/uL"), ("LBXHGB", "Hemoglobin", "g/dL"), ("LBXHCT", "Hematocrit", "%"), ("LBXMCVSI", "Mean Cell Volume", "fL"),
        ("LBXMCHSI", "Mean Cell Hemoglobin", "pg"), ("LBXMC", "Mean Cell Hemoglobin Concentration", "g/dL"), ("LBXRDW", "Red Cell Distribution Width", "%"), ("LBXPLTSI", "Platelet Count", "10*3/uL"),
        ("LBXMPSI", "Mean Platelet Volume", "fL"), ("LBXNRBC", "Nucleated Red Blood Cells", "/100{WBCs}")]


# Education is not harmonized: the NIH CDE's attainment values are per grade and per degree, and NHANES's five adult
# ranges ("Less than 9th grade", "9-11th grade", ...) do not nest with them. The agency's coding is carried; the CDE is left out,
# as it is for income. BRFSS is treated the same way.

def ans(var, v, table, **kw):
    """A coded answer, with a refusal or don't-know left out and counted."""
    out = code(v, table, **kw)
    if isinstance(out, EV):
        DROPPED[var] += 1
        return None
    return out


def num(var, v, missing):
    if v in missing:
        DROPPED[var] += 1
        return None
    return number(v)


def by_seqn(key):
    return {r["SEQN"]: r for r in read_csv(key)}


def smoking_status(smq020, smq040):
    if smq020 == "2":
        return "Never smoker"
    if smq020 != "1":
        return None
    return {"1": "Current every day smoker", "2": "Current some day smoker", "3": "Former smoker"}.get(smq040, "Smoker, current status unknown")


def participant_values(seqn, demo, bpx, tchol, cbc, mcq, smq, pfq):
    v = {
        "NHANES Participant/Respondent Sequence Number (SEQN)": seqn,
        "NHANES Survey Design/Data Release Cycle (SDDSRVYR)": "NHANES 2017-2018 public release" if demo.get("SDDSRVYR") == "10" else None,
        ("NHANES Survey Design", "Interview/Examination Status (RIDSTATR)"): STATUS.get(demo.get("RIDSTATR")),
        "NHANES Survey Design/Full Sample 2 Year Interview Weight (WTINT2YR)": qty(demo.get("WTINT2YR", ""), "1"),
        "NHANES Survey Design/Full Sample 2 Year MEC Exam Weight (WTMEC2YR)": qty(demo.get("WTMEC2YR", ""), "1"),
        "NHANES Survey Design/Masked Variance Pseudo-PSU (SDMVPSU)": qty(demo.get("SDMVPSU", ""), "items"),
        "NHANES Survey Design/Masked Variance Pseudo-Stratum (SDMVSTRA)": qty(demo.get("SDMVSTRA", ""), "items"),
        "NHANES Demographics/Administrative Gender": ADMIN_GENDER.get(demo.get("RIAGENDR")),
        "NHANES Demographics/Gender (RIAGENDR)": GENDER.get(demo.get("RIAGENDR")),
        "NHANES Demographics/Age": qty(demo.get("RIDAGEYR", ""), "years"),
        "NHANES Demographics/Age in Months at Screening (RIDAGEMN)": qty(demo.get("RIDAGEMN", ""), "months"),
        ("NHANES Demographics", "Race/Ethnicity Self-Identification"): RACE_CDE.get(demo.get("RIDRETH3")),
        ("NHANES Demographics", "Race/Hispanic Origin with NH Asian (RIDRETH3)"): RACE.get(demo.get("RIDRETH3")),
        "NHANES Demographics/Country of Birth (DMDBORN4)": ans("DMDBORN4", demo.get("DMDBORN4", ""), BORN, refused=("77",), dont_know=("99",)),
        "NHANES Demographics/Citizenship Status (DMDCITZN)": ans("DMDCITZN", demo.get("DMDCITZN", ""), CITIZEN),
        "NHANES Demographics/Education Level - Adults 20+ (DMDEDUC2)": ans("DMDEDUC2", demo.get("DMDEDUC2", ""), EDUC),
        "NHANES Demographics/Marital Status": MARITAL_CDE.get(demo.get("DMDMARTL")),
        "NHANES Demographics/Marital Status (DMDMARTL)": ans("DMDMARTL", demo.get("DMDMARTL", ""), MARITAL, refused=("77",), dont_know=("99",)),
        "NHANES Demographics/Are you pregnant now?": PREG_CDE.get(demo.get("RIDEXPRG")),
        "NHANES Demographics/Pregnancy Status at Exam (RIDEXPRG)": PREG.get(demo.get("RIDEXPRG")),
        "NHANES Demographics/Veteran Status": ans("DMQMILIZ", demo.get("DMQMILIZ", ""), YN),
        "NHANES Demographics/Total Number of People in the Household (DMDHHSIZ)": qty(demo.get("DMDHHSIZ", ""), "items"),
        "NHANES Demographics/Annual Household Income (INDHHIN2)": ans("INDHHIN2", demo.get("INDHHIN2", ""), INCOME, refused=("77",), dont_know=("99",)),
        "NHANES Demographics/Ratio of Family Income to Poverty (INDFMPIR)": qty(demo.get("INDFMPIR", ""), "1"),
    }
    if bpx:
        v.update({
            "NHANES Blood Pressure/Arm Selected (BPAARM)": ARM.get(bpx.get("BPAARM")),
            "NHANES Blood Pressure/Coded Cuff Size (BPACSZ)": CUFF.get(bpx.get("BPACSZ")),
            "NHANES Blood Pressure/Heart Rate": qty(bpx.get("BPXPLS", ""), "/min"),
            "NHANES Blood Pressure/Pulse Regular or Irregular (BPXPULS)": PULSE.get(bpx.get("BPXPULS")),
            "NHANES Blood Pressure/Maximum Inflation Level (BPXML1)": qty(bpx.get("BPXML1", ""), "mmHg"),
        })
        site = ARM_SITE.get(bpx.get("BPAARM"))
        for n in (1, 2, 3):
            sy, di = bpx.get(f"BPXSY{n}", ""), bpx.get(f"BPXDI{n}", "")
            if sy or di:
                p = f"Blood Pressure Reading {n}/Blood Pressure"
                v[f"{p}/Systolic Blood Pressure"] = qty(sy, "mmHg")
                v[f"{p}/Diastolic Blood Pressure"] = qty(di, "mmHg") if di not in ("", "0") else None
                v[f"{p}/Observation Status"] = "final"
                if site:
                    v[f"{p}/Body Site (SNOMED CT)/Body Site Code (SNOMED CT)"] = site[0]
                    v[f"{p}/Body Site (SNOMED CT)/Code Display Text"] = site[1]
    for var, label, unit in LABS:
        src = tchol if var in ("LBXTC", "LBDTCSI") else cbc
        if src and src.get(var, ""):
            v[f"NHANES Laboratory Results/{label}"] = Quantity(src[var], unit)
    if smq:
        v.update({
            "NHANES Smoking/Smoked at Least 100 Cigarettes in Life (SMQ020)": ans("SMQ020", smq.get("SMQ020", ""), YN),
            "NHANES Smoking/Do You Now Smoke Cigarettes (SMQ040)": ans("SMQ040", smq.get("SMQ040", ""), SMOKE_NOW),
            "NHANES Smoking/Smoking Status": smoking_status(smq.get("SMQ020", ""), smq.get("SMQ040", "")),
            "NHANES Smoking/Age Started Smoking Cigarettes Regularly (SMD030)": qty(num("SMD030", smq.get("SMD030", ""), ("777", "999")) or "", "years"),
            "NHANES Smoking/Average Cigarettes per Day, Past 30 Days (SMD650)": qty(num("SMD650", smq.get("SMD650", ""), ("777", "999")) or "", "cigarettes"),
            "NHANES Smoking/Ever Used an E-cigarette (SMQ900)": ans("SMQ900", smq.get("SMQ900", ""), YN),
        })
    if mcq:
        v["NHANES Medical Conditions/Chronic Condition Indicators/Condition Indicator Basis"] = "Self-report of a professional diagnosis"
        for var, label in CONDITIONS.items():
            v[f"NHANES Medical Conditions/Chronic Condition Indicators/Condition: {label}"] = ans(var, mcq.get(var, ""), YN)
        v["NHANES Medical Conditions/Still Have Asthma (MCQ035)"] = ans("MCQ035", mcq.get("MCQ035", ""), YN)
        v["NHANES Medical Conditions/Doctor Ever Said You Were Overweight (MCQ080)"] = ans("MCQ080", mcq.get("MCQ080", ""), YN)
    if pfq:
        v["NHANES Physical Functioning/Limitations Keeping You from Working (PFQ049)"] = ans("PFQ049", pfq.get("PFQ049", ""), YN)
        v["NHANES Physical Functioning/Need Special Equipment to Walk (PFQ054)"] = ans("PFQ054", pfq.get("PFQ054", ""), YN)
        v["NHANES Physical Functioning/Experience Confusion or Memory Problems (PFQ057)"] = ans("PFQ057", pfq.get("PFQ057", ""), YN)
        for var, label in PF_ITEMS.items():
            v[f"NHANES Physical Functioning/{label} ({var})"] = ans(var, pfq.get(var, ""), DIFFICULTY)
    return v


def generate_participants():
    t0 = time.time()
    demo = by_seqn("DEMO_J"); bpx = by_seqn("BPX_J"); tchol = by_seqn("TCHOL_J"); cbc = by_seqn("CBC_J"); mcq = by_seqn("MCQ_J"); smq = by_seqn("SMQ_J"); pfq = by_seqn("PFQ_J")
    out = import_dir("nhanes_participant")
    n = 0
    for seqn, d in demo.items():
        values = participant_values(seqn, d, bpx.get(seqn), tchol.get(seqn), cbc.get(seqn), mcq.get(seqn), smq.get(seqn), pfq.get(seqn))
        xml = record(PARTICIPANT, values, study="NHANES", agency=AGENCY, source_key="DEMO_J", subject=("NHANES Participant", seqn), row_ref=f"SEQN={seqn}")
        write_record(out, "np", xml)
        n += 1
    print(f"NHANES Participant: generated {n} XML files in {out} ({time.time() - t0:.0f}s)")
    return n


ICD10 = __import__("re").compile(r"^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$")


def generate_medications():
    t0 = time.time()
    out = import_dir("nhanes_medication")
    n = skipped = 0
    for r in read_csv("RXQ_RX_J"):
        drug = r.get("RXDDRUG", "")
        if r.get("RXDUSE") != "1" or not drug or drug in ("55555", "77777", "99999"):
            skipped += 1
            continue
        seqn = r["SEQN"]
        v = {
            "NHANES Medication/Respondent Sequence Number (SEQN)": seqn,
            "NHANES Medication/Taken Prescription Medicine, Past Month (RXDUSE)": "Yes",
            "NHANES Medication/Generic Drug Name (RXDDRUG)": drug,
            "NHANES Medication/Generic Drug Code (RXDDRGID)": r.get("RXDDRGID") or None,
            "NHANES Medication/Number of Days Taken Medicine (RXDDAYS)": qty(num("RXDDAYS", r.get("RXDDAYS", ""), ("77777", "99999")) or "", "days"),
            "NHANES Medication/Number of Prescription Medicines Taken (RXDCOUNT)": qty(r.get("RXDCOUNT", ""), "items"),
        }
        for k in (1, 2, 3):
            c = r.get(f"RXDRSC{k}", "")
            if c and ICD10.match(c):
                v[f"Medication Reason {k}/Diagnosis (ICD-10-CM)/Diagnosis Code (ICD-10-CM)"] = c
                v[f"Medication Reason {k}/Diagnosis (ICD-10-CM)/Code Display Text"] = r.get(f"RXDRSD{k}") or None
            elif c:
                DROPPED[f"RXDRSC{k}"] += 1
        xml = record(MEDICATION, v, study="NHANES", agency=AGENCY, source_key="RXQ_RX_J", subject=("NHANES Participant", seqn), row_ref=f"SEQN={seqn};RXDDRGID={r.get('RXDDRGID', '')}")
        write_record(out, "nm", xml)
        n += 1
    print(f"NHANES Medication: generated {n} XML files in {out} ({skipped} rows without a medicine skipped; {time.time() - t0:.0f}s)")
    return n


def generate():
    generate_participants()
    generate_medications()
    print("NHANES answers left out as refused or don't know:", dict(DROPPED.most_common(12)))


if __name__ == "__main__":
    generate()
