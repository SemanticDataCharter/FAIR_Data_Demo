"""
BRFSS Respondent 4.2.0: one record per respondent of the 2022 LLCP file.

The columns this demonstration carries (docs/design/FAIR-Demo-2-PRD.md section 3)
are named by their label path in the published model. Harmonized values (the
Default administrative gender, the NIH CDE age, race/ethnicity, education,
marital status, employment, insurance category, pregnancy; the shared smoking
status and chronic condition indicators) are written beside the agency's own
codes, and the mapping is in this file where a reader can check it.

Refused (7, 77, 777, 9x) and don't-know answers are left out: every leaf is
optional, and a stated absence would make a record invalid on purpose where the
row states nothing false. The counts of what was left out are printed at the end.

A seeded sample of SAMPLE["brfss"] respondents (FAIR_FULL=1 takes every row).
"""
from __future__ import annotations

import collections
import hashlib
import time

from engine import EV, Quantity
from shared import DEMO_SCALE, SAMPLE, code, import_dir, number, qty, read_csv, record, seeded_sample, write_record

TITLE = "BRFSS Respondent"
AGENCY = "Centers for Disease Control and Prevention"
SOURCE = "LLCP2022"
OUTPUT_DIR = import_dir("brfss_respondent")

DEMO = "BRFSS Demographics/"
DESIGN = "BRFSS Survey Design/"
HEALTH = "BRFSS Health Status and Access/"
COND = "Chronic Condition Indicators/"
BODY = "BRFSS Body Measures/"
VITALS = "Vital Signs Panel/"
TOBACCO = "BRFSS Tobacco and Alcohol Use/"
DIS = "BRFSS Disability/"

YESNO = {"1": "Yes", "2": "No"}
SEXVAR = {"1": "Male", "2": "Female"}
GENDER = {"1": "male", "2": "female"}
GENHLTH = {"1": "Excellent", "2": "Very good", "3": "Good", "4": "Fair", "5": "Poor"}
CHECKUP1 = {"1": "Within past year", "2": "Within past 2 years", "3": "Within past 5 years", "4": "5 or more years ago", "8": "Never"}
PRIMINSR = {"1": "A plan purchased through an employer or union", "2": "A private nongovernmental plan that you or another family member buys on your own", "3": "Medicare", "4": "Medigap",
            "5": "Medicaid", "6": "CHIP", "7": "Military related health care", "8": "Indian Health Service", "9": "State sponsored health plan", "10": "Other government program", "88": "No coverage of any type"}
# NIH CDE Category of Health Insurance from the primary source: employer or own plan private; every government program public; none uninsured.
INSURANCE_CATEGORY = {"1": "Private (purchased directly or through Employment)", "2": "Private (purchased directly or through Employment)", "88": "Uninsured"}
for _k in ("3", "4", "5", "6", "7", "8", "9", "10"):
    INSURANCE_CATEGORY[_k] = "Public (Medicare, Medicaid, Tricare)"
MARITAL = {"1": "Married", "2": "Divorced", "3": "Widowed", "4": "Separated", "5": "Never married", "6": "A member of an unmarried couple"}
# NIH CDE Marital Status: the same words where the CDE has them; never married is the CDE's single value; an unmarried couple is living as married.
MARITAL_CDE = {"1": "Married", "2": "Divorced", "3": "Widowed", "4": "Separated", "5": "Single, never been married-not living with romantic partner", "6": "Living as married or living with a romantic partner"}
EDUCA = {"1": "Never attended school or only kindergarten", "2": "Grades 1 through 8 (Elementary)", "3": "Grades 9 through 11 (Some high school)", "4": "Grade 12 or GED (High school graduate)",
         "5": "College 1 year to 3 years (Some college or technical school)", "6": "College 4 years or more (College graduate)"}
# Education is not harmonized: the NIH CDE Current Educational Attainment has 24 values by grade and degree, and BRFSS's six bands do not nest with
# them (a band spans several grades or degrees), so the CDE is left out and the agency's coding stands, as with income.
EMPLOY1 = {"1": "Employed for wages", "2": "Self-employed", "3": "Out of work for 1 year or more", "4": "Out of work for less than 1 year", "5": "A homemaker", "6": "A student", "7": "Retired", "8": "Unable to work"}
# NIH CDE Employment Status from BRFSS's eight: wages and self-employed are full-time working now (BRFSS does not ask hours); out of work is looking for
# work; a homemaker is raising children or keeping house; a student, retired and unable to work (the CDE's disabled) map one to one.
EMPLOY1_CDE = {"1": "Full-time working now or paid sick leave/parental leave/family leave/administrative leave", "2": "Full-time working now or paid sick leave/parental leave/family leave/administrative leave",
               "3": "Looking for work, unemployed", "4": "Looking for work, unemployed", "5": "Raising children full-time, full-time caregiver, or keeping house", "6": "Student", "7": "Retired", "8": "Disabled, permanently or temporarily"}
IMPRACE = {"1": "White, Non-Hispanic", "2": "Black, Non-Hispanic", "3": "Asian, Non-Hispanic", "4": "American Indian/Alaskan Native, Non-Hispanic", "5": "Hispanic", "6": "Other race, Non-Hispanic"}
# NIH CDE Race/Ethnicity Self-Identification from the agency's imputed value; other race, non-Hispanic has no CDE value and the CDE is left out.
IMPRACE_CDE = {"1": "White", "2": "Black or African American", "3": "Asian or Asian American", "4": "American Indian or Alaska Native", "5": "Hispanic, Latino, or Spanish"}
INCOME3 = {"1": "Less than $10,000", "2": "$10,000 to less than $15,000", "3": "$15,000 to less than $20,000", "4": "$20,000 to less than $25,000", "5": "$25,000 to less than $35,000",
           "6": "$35,000 to less than $50,000", "7": "$50,000 to less than $75,000", "8": "$75,000 to less than $100,000", "9": "$100,000 to less than $150,000", "10": "$150,000 to less than $200,000", "11": "$200,000 or more"}
SMOKDAY2 = {"1": "Every day", "2": "Some days", "3": "Not at all"}
SMOKER3 = {"1": "Current smoker - now smokes every day", "2": "Current smoker - now smokes some days", "3": "Former smoker", "4": "Never smoked"}
ECIGNOW2 = {"1": "Never used e-cigarettes in your entire life", "2": "Use them every day", "3": "Use them some days", "4": "Not at all (right now)"}
BMI5CAT = {"1": "Underweight", "2": "Normal Weight", "3": "Overweight", "4": "Obese"}
# Diabetes: yes, and yes only during pregnancy, are Yes; no, and pre-diabetes or borderline, are No.
DIABETE4 = {"1": "Yes", "2": "Yes", "3": "No", "4": "No"}
# The condition indicators the 2022 questionnaire asks, in the order of the section, each the shared component.
CONDITIONS = [("ASTHMA3", "Asthma", YESNO), ("HAVARTH4", "Arthritis", YESNO), ("CVDCRHD4", "Coronary Heart Disease", YESNO), ("CVDINFR4", "Heart Attack", YESNO), ("CVDSTRK3", "Stroke", YESNO),
              ("CHCCOPD3", "COPD", YESNO), ("CHCOCNC1", "Cancer", YESNO), ("CHCSCNC1", "Skin Cancer", YESNO), ("ADDEPEV3", "Depression", YESNO), ("CHCKDNY2", "Kidney Disease", YESNO), ("DIABETE4", "Diabetes", DIABETE4)]
# BPHIGH6 and TOLDHI3 are not in the 2022 core file (the hypertension and cholesterol module runs in odd years), so High Blood Pressure and High
# Cholesterol are not carried by this study in this release.

DROPPED = collections.Counter()   # variable -> refused or don't-know answers left out


def ans(var: str, v: str, table: dict, **kw):
    """The coded answer, or None; a refusal or don't-know is counted and left out."""
    x = code(v, table, **kw)
    if isinstance(x, EV):
        DROPPED[var] += 1
        return None
    return x


def count(var: str, v: str, none_code: str | None = None, missing=("77", "99", "777", "999")):
    """A count answer: none_code (88) means zero; refused and don't-know are counted and left out."""
    if v == "":
        return None
    if none_code is not None and v == none_code:
        return "0"
    if v in missing:
        DROPPED[var] += 1
        return None
    return v


def height_cm(v: str):
    """HEIGHT3: 0FII feet and inches, or 9xxx metres and centimetres; 7777 and 9999 are missing."""
    if v in ("", "7777", "9999"):
        if v:
            DROPPED["HEIGHT3"] += 1
        return None
    n = int(v)
    if 200 <= n <= 711:
        feet, inches = divmod(n, 100)
        return f"{feet * 30.48 + inches * 2.54:.1f}"
    if 9000 < n < 9999:
        return f"{n - 9000:d}"
    return None


def weight_kg(v: str):
    """WEIGHT2: pounds (50-776) or 9xxx kilograms; returns (kilograms, pounds or None)."""
    if v in ("", "7777", "9999"):
        if v:
            DROPPED["WEIGHT2"] += 1
        return None, None
    n = int(v)
    if 50 <= n <= 776:
        return f"{n * 0.45359237:.1f}", str(n)
    if 9000 < n < 9999:
        return f"{n - 9000:d}", None
    return None, None


def alcohol_days(v: str):
    """ALCDAY4: 1xx days per week (scaled to 30 days), 2xx days in the past 30, 888 none."""
    if v == "":
        return None
    if v == "888":
        return "0"
    if v in ("777", "999"):
        DROPPED["ALCDAY4"] += 1
        return None
    n = int(v)
    if 101 <= n <= 199:
        return str(round((n - 100) * 30 / 7))
    if 201 <= n <= 299:
        return str(n - 200)
    return None


def smoking_status(smoke100: str, smokday2: str):
    """The shared Smoking Status on the LOINC answer list, from the two questions that establish it."""
    if smoke100 == "2":
        return "Never smoker"
    if smoke100 != "1":
        return None
    return {"1": "Current every day smoker", "2": "Current some day smoker", "3": "Former smoker"}.get(smokday2, "Smoker, current status unknown")


def interview_date(idate: str):
    """IDATE is MMDDYYYY."""
    if len(idate) != 8:
        return None
    return f"{idate[4:8]}-{idate[0:2]}-{idate[2:4]}"


def build_instance(row: dict) -> str:
    seqno = row["SEQNO"]
    date = interview_date(row["IDATE"])
    h = height_cm(row["HEIGHT3"])
    kg, lb = weight_kg(row["WEIGHT2"])
    bmi = number(row["_BMI5"])
    values = {
        "BRFSS Respondent/Annual Sequence Number (SEQNO)": seqno,
        DESIGN + "State FIPS Code (_STATE)": number(row["_STATE"]),
        DESIGN + "Interview Date (IDATE)": date,
        DESIGN + "Primary Sampling Unit (_PSU)": number(row["_PSU"]),
        DESIGN + "Sample Design Stratification Variable (_STSTR)": number(row["_STSTR"]),
        DESIGN + "Final Weight: Land-line and Cell-phone Data (_LLCPWT)": qty(row["_LLCPWT"], "1"),
        # demographics: the Default gender and the NIH CDEs beside the agency's codes
        DEMO + "Administrative Gender": GENDER.get(row["SEXVAR"]),
        DEMO + "Sex of Respondent (SEXVAR)": SEXVAR.get(row["SEXVAR"]),
        DEMO + "Age": qty(row["_AGE80"], "years"),
        DEMO + "Imputed Age Value Collapsed Above 80 (_AGE80)": qty(row["_AGE80"], "years"),
        (DEMO[:-1], "Race/Ethnicity Self-Identification"): IMPRACE_CDE.get(row["_IMPRACE"]),
        (DEMO[:-1], "Imputed Race/Ethnicity Value (_IMPRACE)"): IMPRACE.get(row["_IMPRACE"]),
        DEMO + "Education Level (EDUCA)": ans("EDUCA", row["EDUCA"], EDUCA),
        DEMO + "Marital Status": ans("MARITAL", row["MARITAL"], MARITAL_CDE),
        DEMO + "Marital Status (MARITAL)": ans("MARITAL", row["MARITAL"], MARITAL),
        DEMO + "Employment Status": ans("EMPLOY1", row["EMPLOY1"], EMPLOY1_CDE),
        DEMO + "Employment Status (EMPLOY1)": ans("EMPLOY1", row["EMPLOY1"], EMPLOY1),
        DEMO + "Category of Health Insurance": ans("PRIMINSR", row["PRIMINSR"], INSURANCE_CATEGORY),
        DEMO + "Primary Source of Health Insurance (PRIMINSR)": ans("PRIMINSR", row["PRIMINSR"], PRIMINSR),
        DEMO + "Veteran Status": ans("VETERAN3", row["VETERAN3"], YESNO),
        DEMO + "Are you pregnant now?": ans("PREGNANT", row["PREGNANT"], YESNO),
        DEMO + "Pregnancy Status (PREGNANT)": ans("PREGNANT", row["PREGNANT"], YESNO),
        DEMO + "Number of Children in Household (CHILDREN)": qty(count("CHILDREN", row["CHILDREN"], "88", ("99",)) or "", "items") if count("CHILDREN", row["CHILDREN"], "88", ("99",)) else None,
        DEMO + "Income Level (INCOME3)": ans("INCOME3", row["INCOME3"], INCOME3),
        # health status and access
        HEALTH + "General Health Status": ans("GENHLTH", row["GENHLTH"], GENHLTH),
        HEALTH + "Days Physical Health Not Good, Past 30 (PHYSHLTH)": qty(count("PHYSHLTH", row["PHYSHLTH"], "88") or "", "days") if count("PHYSHLTH", row["PHYSHLTH"], "88") else None,
        HEALTH + "Days Mental Health Not Good, Past 30 (MENTHLTH)": qty(count("MENTHLTH", row["MENTHLTH"], "88") or "", "days") if count("MENTHLTH", row["MENTHLTH"], "88") else None,
        HEALTH + "Length of Time Since Last Routine Checkup (CHECKUP1)": ans("CHECKUP1", row["CHECKUP1"], CHECKUP1),
        HEALTH + "Exercise in Past 30 Days (EXERANY2)": ans("EXERANY2", row["EXERANY2"], YESNO),
        # chronic conditions: the shared indicators on a self-report basis
        COND + "Condition Indicator Basis": "Self-report of a professional diagnosis",
        "BRFSS Chronic Conditions/Still Have Asthma (ASTHNOW)": ans("ASTHNOW", row["ASTHNOW"], YESNO),
        # body measures: the agency's codes and the FHIR vital signs panel
        BODY + "Reported Height in Feet and Inches (HEIGHT3)": row["HEIGHT3"] if row["HEIGHT3"] not in ("", "7777", "9999") else None,
        BODY + "Reported Weight in Pounds (WEIGHT2)": Quantity(lb, "lb") if lb else None,
        BODY + "Computed Body Mass Index Category (_BMI5CAT)": BMI5CAT.get(row["_BMI5CAT"]),
        VITALS + "Body Height": Quantity(h, "cm") if h else None,
        VITALS + "Body Weight": Quantity(kg, "kg") if kg else None,
        VITALS + "Body Mass Index": Quantity(f"{int(bmi) / 100:.2f}", "kg/m2") if bmi else None,
        VITALS + "Observation Status": "final" if (h or kg or bmi) else None,
        VITALS + "Observation Date Time": f"{date}T00:00:00" if date and (h or kg or bmi) else None,
        # tobacco and alcohol
        TOBACCO + "Smoked at Least 100 Cigarettes (SMOKE100)": ans("SMOKE100", row["SMOKE100"], YESNO),
        TOBACCO + "Frequency of Days Now Smoking (SMOKDAY2)": ans("SMOKDAY2", row["SMOKDAY2"], SMOKDAY2),
        TOBACCO + "Smoking Status": smoking_status(row["SMOKE100"], row["SMOKDAY2"]),
        TOBACCO + "Computed Smoking Status (_SMOKER3)": SMOKER3.get(row["_SMOKER3"]),
        TOBACCO + "Current E-cigarette Use (ECIGNOW2)": ans("ECIGNOW2", row["ECIGNOW2"], ECIGNOW2),
        TOBACCO + "Days in Past 30 Had Alcoholic Beverage (ALCDAY4)": qty(alcohol_days(row["ALCDAY4"]) or "", "days") if alcohol_days(row["ALCDAY4"]) is not None else None,
        TOBACCO + "Average Alcoholic Drinks per Day in Past 30 (AVEDRNK3)": qty(count("AVEDRNK3", row["AVEDRNK3"], None) or "", "drinks") if row["AVEDRNK3"] not in ("", "88", "77", "99") else (DROPPED.update({"AVEDRNK3": 1}) if row["AVEDRNK3"] in ("77", "99") else None),
        TOBACCO + "Binge Drinking Occasions in Past 30 (DRNK3GE5)": qty(count("DRNK3GE5", row["DRNK3GE5"], "88") or "", "items") if count("DRNK3GE5", row["DRNK3GE5"], "88") else None,
    }
    for var, label, table in CONDITIONS:
        values[COND + f"Condition: {label}"] = ans(var, row[var], table)
    for var, label in (("DEAF", "Deaf or Serious Difficulty Hearing (DEAF)"), ("BLIND", "Blind or Serious Difficulty Seeing (BLIND)"), ("DECIDE", "Serious Difficulty Concentrating, Remembering or Deciding (DECIDE)"),
                       ("DIFFWALK", "Serious Difficulty Walking or Climbing Stairs (DIFFWALK)"), ("DIFFDRES", "Difficulty Dressing or Bathing (DIFFDRES)"), ("DIFFALON", "Difficulty Doing Errands Alone (DIFFALON)")):
        values[DIS + label] = ans(var, row[var], YESNO)
    return record(TITLE, values, study="BRFSS", agency=AGENCY, source_key=SOURCE, subject=("BRFSS Respondent", f"{row['_STATE']}-{seqno}"), row_ref=f"_STATE={row['_STATE']};SEQNO={seqno}")


def _key(row: dict) -> str:
    """SEQNO repeats across states (it numbers the interviews within a state and year), so the row's key is state and sequence number."""
    return f"{row['_STATE']}-{row['SEQNO']}"


def _in_sample(key: str, n: int) -> bool:
    """A deterministic pre-sample of about 1.2 n of the 445,132 respondents by a hash of the key; generate() trims it to exactly n."""
    return int(hashlib.sha256(f"fair:brfss:{key}".encode()).hexdigest(), 16) % 445132 < n * 1.2


def generate():
    t0 = time.time()
    n = SAMPLE["brfss"]
    rows = []
    for row in read_csv(SOURCE):
        if row["SEQNO"] and (not DEMO_SCALE or _in_sample(_key(row), n)):
            rows.append(row)
    if DEMO_SCALE:
        keep = seeded_sample([_key(r) for r in rows], n, "fair:brfss")
        rows = [r for r in rows if _key(r) in keep]
    count_ = 0
    for row in rows:
        write_record(OUTPUT_DIR, "br", build_instance(row))
        count_ += 1
    print(f"BRFSS Respondent: generated {count_} XML files in {OUTPUT_DIR} in {time.time() - t0:.0f}s")
    print("BRFSS Respondent: refused or don't-know answers left out, by variable:", dict(sorted(DROPPED.items())))


if __name__ == "__main__":
    generate()
