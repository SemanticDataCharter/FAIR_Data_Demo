#!/usr/bin/env python3
"""
Author records/*.yaml for the FAIR Data Demo models (docs/design/FAIR-Demo-2-PRD.md §3).

Three kinds of member:
  a library component by identifier slot   https://axius-sdc.com/library/<default|provgov|fhir>/<key>
  a NIH CDE component by its ct_id          ct:<ct_id>  (that library carries no slot; CDE() checks the rebuilt lookup)
  a FAIR record                             a key in this file: shared across studies, or local to one

Every study-local record names the agency variable it carries (rdfs:seeAlso the codebook) and every harmonized
value keeps the agency's own coding beside it. The 976 components of the first build are retired with the
reason written (review/fair-retire.csv).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
D = "https://axius-sdc.com/library/default/"
PG = "https://axius-sdc.com/library/provgov/"
F = "https://axius-sdc.com/library/fhir/"
EXPORT = ROOT / "docs" / "design" / "inventory" / "export-fair-data-demo-2026-09-26.csv"
CDES = json.loads((ROOT / "docs" / "design" / "inventory" / "nih-cde-rebuilt-lookup.json").read_text())
OLD = {r["ct_id"]: r for r in csv.DictReader(open(EXPORT, encoding="utf-8"))}
NHANES = "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/"
BRFSS = "https://www.cdc.gov/brfss/annual_data/2022/pdf/codebook22_llcp-v2-508.pdf"
CMS = "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf"

RECORDS: dict[str, dict] = {}
KEPT: dict[str, str] = {}        # ct_id -> label (NIH CDEs composed by ct_id)
COVERED: dict[str, str] = {}     # old ct_id -> what covers it


def CDE(tiny: str, label: str) -> str:
    r = CDES[tiny]
    assert r["label"] == label, (tiny, r["label"], label)
    KEPT[r["ct_id"]] = label
    return f"ct:{r['ct_id']}"


def put(rec: dict) -> str:
    assert rec["key"] not in RECORDS, rec["key"]
    RECORDS[rec["key"]] = rec
    return rec["key"]


def leaf(key, label, type_, description, links=(), constraints=None, enumeration=None, source="FAIR Data Demo", flags=None):
    rec = {"key": key, "label": label, "type": type_, "description": " ".join(description.split()), "source": {"name": source},
           "links": [{"predicate": p, "iri": i, "basis": b} for p, i, b in links]}
    if constraints:
        rec["constraints"] = constraints
    if enumeration is not None:
        rec["enumeration"] = enumeration
    if flags:
        rec["flags"] = flags
    return put(rec)


def member_label(m: str) -> str:
    if m.startswith("ct:"):
        return KEPT[m[3:]] + " (NIH CDE)"
    if m.startswith("http"):
        lib = m.split("/library/")[1].split("/")[0]
        return m.rsplit("/", 1)[1] + f" ({lib.upper() if lib == 'fhir' else lib.capitalize()})"
    return RECORDS[m]["label"]


def C(key, label, description, members, exact=None, source="FAIR Data Demo", flags=None):
    assert len(members) == len(set(members)), f"{key}: duplicate members"
    rec = {"key": key, "label": label, "type": "Cluster",
           "description": " ".join(description.split()) + " Members: " + "; ".join(member_label(m) for m in members) + ".",
           "source": {"name": source},
           "links": [{"predicate": "skos:exactMatch" if exact else "skos:closeMatch", "iri": exact or "https://schema.org/ItemList", "basis": "standard" if exact else "concept"}],
           "members": members}
    if flags:
        rec["flags"] = flags
    return put(rec)


def cover(ct_id: str, by: str):
    assert ct_id in OLD, ct_id
    COVERED[ct_id] = by


def yesno(*extra):
    """Yes / No with the LOINC answers, plus the survey's refusal and don't-know codes stated as absences at generation, not as values."""
    return [{"value": "Yes", "definition": "https://loinc.org/LA33-6/"}, {"value": "No", "definition": "https://loinc.org/LA32-8/"}] + list(extra)


def enum(*pairs):
    return [{"value": v, "definition": d} for v, d in pairs]


def see(url):
    return ("rdfs:seeAlso", url, "standard")


NCIT = "http://purl.obolibrary.org/obo/NCIT_"
SCT = "http://snomed.info/id/"
LOINC = "https://loinc.org/"
UCUM = "https://ucum.org/ucum"


# ================================================================ Units this project binds (the rest come from the Default library by slot)
def units(key, label, description, values):
    return leaf(key, label, "Units", description, links=[("skos:closeMatch", "http://qudt.org/schema/qudt/Unit", "concept")],
                enumeration=[{"value": v, "definition": d} for v, d in values], source="QUDT")


U_G_DL = units("units-gram-per-decilitre", "Grams per Decilitre", "Mass concentration in grams per decilitre.", [("g/dL", "http://qudt.org/vocab/unit/GM-PER-DeciL")])
U_MG_DL = units("units-milligram-per-decilitre", "Milligrams per Decilitre", "Mass concentration in milligrams per decilitre.", [("mg/dL", "http://qudt.org/vocab/unit/MilliGM-PER-DeciL")])
U_MMOL_L = units("units-millimole-per-litre", "Millimoles per Litre", "Substance concentration in millimoles per litre.", [("mmol/L", "http://qudt.org/vocab/unit/MilliMOL-PER-L")])
U_FL = units("units-femtolitre", "Femtolitres", "Cell volume in femtolitres.", [("fL", "http://qudt.org/vocab/unit/FemtoL")])
U_PG = units("units-picogram", "Picograms", "Mass in picograms.", [("pg", "http://qudt.org/vocab/unit/PicoGM")])
U_K_UL = units("units-thousand-per-microlitre", "Thousands per Microlitre", "Cell count in thousands of cells per microlitre (UCUM 10*3/uL).", [("10*3/uL", UCUM)])
U_M_UL = units("units-million-per-microlitre", "Millions per Microlitre", "Cell count in millions of cells per microlitre (UCUM 10*6/uL).", [("10*6/uL", UCUM)])
U_PER_100 = units("units-per-100-cells", "Per 100 Cells", "A count per 100 white blood cells (UCUM /100{WBCs}).", [("/100{WBCs}", UCUM)])
U_WEIGHT = units("units-sample-weight", "Sample Weight", "A dimensionless survey sample weight.", [("1", "http://qudt.org/vocab/unit/NUM")])
U_MONTHS = units("units-months", "Months", "A duration in months.", [("months", "http://qudt.org/vocab/unit/MO")])
U_DAYS = units("units-days", "Days", "A duration in days.", [("days", "http://qudt.org/vocab/unit/DAY")])
U_YEARS = units("units-years", "Years", "A duration in years.", [("years", "http://qudt.org/vocab/unit/YR")])
U_CIGS = units("units-cigarettes", "Cigarettes", "A count of cigarettes.", [("cigarettes", "http://qudt.org/vocab/unit/NUM")])
U_DRINKS = units("units-drinks", "Drinks", "A count of alcoholic drinks.", [("drinks", "http://qudt.org/vocab/unit/NUM")])


# ================================================================ shared FAIR components: measured by more than one study, held by no library
smoking = leaf("smoking-status", "Smoking Status", "XdToken",
               "Tobacco smoking status (LOINC 72166-2) as the survey establishes it: NHANES from SMQ020 and SMQ040, BRFSS from SMOKE100 and SMOKDAY2 (the agency's _SMOKER3 is kept beside it). The LOINC answer list LL2201-3.",
               links=[("skos:exactMatch", LOINC + "72166-2/", "standard")],
               enumeration=enum(("Current every day smoker", LOINC + "LA18976-3/"), ("Current some day smoker", LOINC + "LA18977-1/"), ("Former smoker", LOINC + "LA15920-4/"),
                                ("Never smoker", LOINC + "LA18978-9/"), ("Smoker, current status unknown", LOINC + "LA18979-7/")))
basis = leaf("condition-indicator-basis", "Condition Indicator Basis", "XdToken",
             "How a study established its chronic condition indicators: the person's report of what a health professional told them (NHANES, BRFSS) or the presence of qualifying diagnosis codes in claims (CMS). Stated once per record so the three studies compare on equal terms.",
             links=[("skos:closeMatch", NCIT + "C25596", "concept")],
             enumeration=enum(("Self-report of a professional diagnosis", NCIT + "C93409"), ("Claims-based algorithm", NCIT + "C25404")))

CONDITIONS = {   # key: (label, SNOMED CT disorder, NHANES variable, BRFSS variable, CMS variable)
    "asthma": ("Asthma", "195967001", "MCQ010", "ASTHMA3", None),
    "arthritis": ("Arthritis", "3723001", "MCQ160A", "HAVARTH4", "SP_RA_OA"),
    "congestive-heart-failure": ("Congestive Heart Failure", "42343007", "MCQ160B", None, "SP_CHF"),
    "coronary-heart-disease": ("Coronary Heart Disease", "53741008", "MCQ160C", "CVDCRHD4", "SP_ISCHMCHT"),
    "angina": ("Angina", "194828000", "MCQ160D", None, None),
    "heart-attack": ("Heart Attack", "22298006", "MCQ160E", "CVDINFR4", None),
    "stroke": ("Stroke", "230690007", "MCQ160F", "CVDSTRK3", "SP_STRKETIA"),
    "emphysema": ("Emphysema", "87433001", "MCQ160G", None, None),
    "chronic-bronchitis": ("Chronic Bronchitis", "63480004", "MCQ160K", None, None),
    "copd": ("COPD", "13645005", "MCQ160O", "CHCCOPD3", "SP_COPD"),
    "liver-condition": ("Liver Condition", "235856003", "MCQ160L", None, None),
    "thyroid-problem": ("Thyroid Problem", "14304000", "MCQ160M", None, None),
    "cancer": ("Cancer", "363346000", "MCQ220", "CHCOCNC1", "SP_CNCR"),
    "skin-cancer": ("Skin Cancer", "372130007", None, "CHCSCNC1", None),
    "depression": ("Depression", "35489007", None, "ADDEPEV3", "SP_DEPRESSN"),
    "kidney-disease": ("Kidney Disease", "709044004", None, "CHCKDNY2", "SP_CHRNKIDN"),
    "diabetes": ("Diabetes", "73211009", None, "DIABETE4", "SP_DIABETES"),
    "alzheimers-disease": ("Alzheimer's Disease or Related Disorder", "26929004", None, None, "SP_ALZHDMTA"),
    "osteoporosis": ("Osteoporosis", "64859006", None, None, "SP_OSTEOPRS"),
    "high-blood-pressure": ("High Blood Pressure", "38341003", None, "BPHIGH6", None),
    "high-cholesterol": ("High Cholesterol", "13644009", None, "TOLDHI3", None),
}
COND = {}
for key, (label, sct, nh, br, cm) in CONDITIONS.items():
    where = ", ".join(w for w in ((f"NHANES {nh}" if nh else ""), (f"BRFSS {br}" if br else ""), (f"CMS {cm}" if cm else "")) if w)
    COND[key] = leaf(f"condition-{key}", f"Condition: {label}", "XdToken",
                     f"Whether the person has {label.lower()} ({label}, SNOMED CT {sct}), on the basis the record states in its Condition Indicator Basis: told by a health professional, or found in claims. Carried by {where}.",
                     links=[("dcterms:subject", SCT + sct, "concept")], enumeration=yesno())
conditions_members = [basis] + list(COND.values())
conditions = C("chronic-condition-indicators", "Chronic Condition Indicators",
               "The chronic conditions a study records for a person, one indicator per condition, with the basis on which the study established them. NHANES and BRFSS carry the ones their questionnaires ask; CMS carries the eleven its chronic conditions flags define; every study that carries an indicator carries the same component.",
               conditions_members, exact=NCIT + "C2991")

pregnancy = CDE("LiUWCWluP", "Are you pregnant now?")
veteran = leaf("veteran-status", "Veteran Status", "XdToken", "Whether the person has ever served on active duty in the United States Armed Forces (NHANES DMQMILIZ; BRFSS VETERAN3).",
               links=[("skos:closeMatch", NCIT + "C17742", "concept"), see(NHANES + "DEMO_J.htm#DMQMILIZ")], enumeration=yesno())
general_health = leaf("general-health-status", "General Health Status", "XdToken", "The person's rating of their general health (BRFSS GENHLTH; the NHANES HSQ question is the same scale when that file is carried).",
                      links=[("skos:closeMatch", NCIT + "C16669", "concept"), see(BRFSS)],
                      enumeration=enum(("Excellent", NCIT + "C25184"), ("Very good", NCIT + "C42642"), ("Good", NCIT + "C25185"), ("Fair", NCIT + "C42633"), ("Poor", NCIT + "C25187")))
# harmonized demographics: the NIH CDE beside the agency's own coding (the agency coding is study-local, below)
RACE_ETH = CDE("LakF0YkywC", "Race/Ethnicity Self-Identification")
SEX = D + "administrative-gender"
AGE = CDE("PDjBiGXjO", "Age")
EDUCATION = CDE("Co2d1RyYS3", "Current Educational Attainment")
MARITAL = CDE("C6SezX_mKG", "Marital Status")
INSURANCE = CDE("cPiK4Amjn5", "Category of Health Insurance")
EMPLOYMENT = CDE("RME88_Wg_hV", "Employment Status")
BIRTH_DATE = D + "date-of-birth"

# ================================================================ NHANES 2017-2018
NH = "NHANES 2017-2018"
def nh(var, file):
    return see(NHANES + f"{file}.htm#{var}")

seqn = leaf("nhanes-respondent-sequence-number", "Respondent Sequence Number (SEQN)", "XdString", "The NHANES respondent sequence number, the identifier every NHANES file carries for a participant (SEQN).",
            links=[nh("SEQN", "DEMO_J")], constraints={"max_length": 8, "str_fmt": "[0-9]{5,6}"}, source=NH)
nh_cycle = leaf("nhanes-data-release-cycle", "Data Release Cycle (SDDSRVYR)", "XdToken", "The NHANES data release cycle (SDDSRVYR).", links=[nh("SDDSRVYR", "DEMO_J")],
                enumeration=enum(("NHANES 2017-2018 public release", NHANES + "DEMO_J.htm#SDDSRVYR")), source=NH)
nh_status = leaf("nhanes-interview-examination-status", "Interview/Examination Status (RIDSTATR)", "XdToken", "Whether the participant was interviewed only, or interviewed and examined at the mobile examination center (RIDSTATR).",
                 links=[nh("RIDSTATR", "DEMO_J")], enumeration=enum(("Interviewed only", NHANES + "DEMO_J.htm#RIDSTATR"), ("Both interviewed and MEC examined", NHANES + "DEMO_J.htm#RIDSTATR")), source=NH)
nh_gender = leaf("nhanes-gender-code", "Gender (RIAGENDR)", "XdToken", "The participant's gender as NHANES codes it (RIAGENDR). Kept beside the Default administrative gender it is mapped to.",
                 links=[nh("RIAGENDR", "DEMO_J")], enumeration=enum(("Male", NCIT + "C20197"), ("Female", NCIT + "C16576")), source=NH)
nh_age_months = leaf("nhanes-age-in-months-at-screening", "Age in Months at Screening (RIDAGEMN)", "XdCount", "Age in months at screening, reported for participants aged 0 to 24 months (RIDAGEMN).",
                     links=[nh("RIDAGEMN", "DEMO_J")], constraints={"units": U_MONTHS, "min_inclusive": 0, "max_inclusive": 24}, source=NH)
nh_race = leaf("nhanes-race-hispanic-origin", "Race/Hispanic Origin with NH Asian (RIDRETH3)", "XdToken", "Race and Hispanic origin as NHANES codes it (RIDRETH3). Kept beside the NIH CDE Race/Ethnicity Self-Identification it is mapped to; the mapping is in the generator and Other Race including multi-racial has no CDE value.",
               links=[nh("RIDRETH3", "DEMO_J")],
               enumeration=enum(("Mexican American", NCIT + "C67175"), ("Other Hispanic", NCIT + "C17459"), ("Non-Hispanic White", NCIT + "C41261"), ("Non-Hispanic Black", NCIT + "C16352"), ("Non-Hispanic Asian", NCIT + "C41260"), ("Other Race - Including Multi-Racial", NCIT + "C17649")), source=NH)
nh_born = leaf("nhanes-country-of-birth", "Country of Birth (DMDBORN4)", "XdToken", "Whether the participant was born in the 50 US states or Washington, DC, or elsewhere (DMDBORN4).",
               links=[nh("DMDBORN4", "DEMO_J")], enumeration=enum(("Born in 50 US states or Washington, DC", NCIT + "C17234"), ("Others", NCIT + "C17649")), source=NH)
nh_citizen = leaf("nhanes-citizenship-status", "Citizenship Status (DMDCITZN)", "XdToken", "Citizenship status (DMDCITZN).", links=[nh("DMDCITZN", "DEMO_J")],
                  enumeration=enum(("Citizen by birth or naturalization", NCIT + "C41130"), ("Not a citizen of the US", NCIT + "C41130")), source=NH)
nh_educ = leaf("nhanes-education-level-adults", "Education Level - Adults 20+ (DMDEDUC2)", "XdToken", "The highest grade or level of school completed, adults 20 and over (DMDEDUC2). Kept beside the NIH CDE Current Educational Attainment it is mapped to.",
               links=[nh("DMDEDUC2", "DEMO_J")],
               enumeration=enum(("Less than 9th grade", NCIT + "C17953"), ("9-11th grade (includes 12th grade with no diploma)", NCIT + "C17953"), ("High school graduate/GED or equivalent", NCIT + "C67136"),
                                ("Some college or AA degree", NCIT + "C67137"), ("College graduate or above", NCIT + "C39303")), source=NH)
nh_marital = leaf("nhanes-marital-status", "Marital Status (DMDMARTL)", "XdToken", "Marital status as NHANES codes it (DMDMARTL). Kept beside the NIH CDE Marital Status it is mapped to.",
                  links=[nh("DMDMARTL", "DEMO_J")],
                  enumeration=enum(("Married", NCIT + "C51773"), ("Widowed", NCIT + "C51775"), ("Divorced", NCIT + "C51776"), ("Separated", NCIT + "C51777"), ("Never married", NCIT + "C51774"), ("Living with partner", NCIT + "C53262")), source=NH)
nh_pregnancy = leaf("nhanes-pregnancy-status-at-exam", "Pregnancy Status at Exam (RIDEXPRG)", "XdToken", "Pregnancy status at the examination, females 20-44 (RIDEXPRG). Kept beside the NIH CDE pregnancy question it is mapped to.",
                    links=[nh("RIDEXPRG", "DEMO_J")], enumeration=enum(("Yes, positive lab pregnancy test or self-reported pregnant at exam", NCIT + "C25191"), ("Not pregnant at exam", NCIT + "C25191"), ("Cannot ascertain if pregnant at exam", NCIT + "C17998")), source=NH)
nh_hh_size = leaf("nhanes-household-size", "Total Number of People in the Household (DMDHHSIZ)", "XdCount", "Total number of people in the household (DMDHHSIZ; 7 means 7 or more).", links=[nh("DMDHHSIZ", "DEMO_J")], constraints={"units": D + "units-items", "min_inclusive": 1, "max_inclusive": 7}, source=NH)
nh_income = leaf("nhanes-annual-household-income", "Annual Household Income (INDHHIN2)", "XdToken", "Annual household income in the agency's ranges (INDHHIN2). Not harmonized: the NHANES, BRFSS and NIH CDE income ranges do not nest, so each study keeps its own.",
                 links=[nh("INDHHIN2", "DEMO_J")],
                 enumeration=enum(*[(v, NHANES + "DEMO_J.htm#INDHHIN2") for v in ("$0 to $4,999", "$5,000 to $9,999", "$10,000 to $14,999", "$15,000 to $19,999", "$20,000 to $24,999", "$25,000 to $34,999", "$35,000 to $44,999", "$45,000 to $54,999", "$55,000 to $64,999", "$65,000 to $74,999", "$20,000 and Over", "Under $20,000", "$75,000 to $99,999", "$100,000 and Over")]), source=NH)
nh_pir = leaf("nhanes-family-income-poverty-ratio", "Ratio of Family Income to Poverty (INDFMPIR)", "XdQuantity", "The ratio of family income to the poverty guideline (INDFMPIR; 5 means 5 or more).", links=[nh("INDFMPIR", "DEMO_J")],
              constraints={"units": U_WEIGHT, "total_digits": 4, "fraction_digits": 2, "min_inclusive": 0, "max_inclusive": 5}, source=NH)
nh_wtint = leaf("nhanes-interview-weight", "Full Sample 2 Year Interview Weight (WTINT2YR)", "XdQuantity", "The full-sample two-year interview weight (WTINT2YR), for weighted estimates of the interviewed sample.", links=[nh("WTINT2YR", "DEMO_J")], constraints={"units": U_WEIGHT, "total_digits": 12, "fraction_digits": 4, "min_inclusive": 0}, source=NH)
nh_wtmec = leaf("nhanes-mec-exam-weight", "Full Sample 2 Year MEC Exam Weight (WTMEC2YR)", "XdQuantity", "The full-sample two-year MEC examination weight (WTMEC2YR); zero for participants not examined.", links=[nh("WTMEC2YR", "DEMO_J")], constraints={"units": U_WEIGHT, "total_digits": 12, "fraction_digits": 4, "min_inclusive": 0}, source=NH)
nh_psu = leaf("nhanes-masked-variance-psu", "Masked Variance Pseudo-PSU (SDMVPSU)", "XdCount", "The masked variance pseudo primary sampling unit (SDMVPSU).", links=[nh("SDMVPSU", "DEMO_J")], constraints={"units": D + "units-items", "min_inclusive": 1, "max_inclusive": 2}, source=NH)
nh_stra = leaf("nhanes-masked-variance-stratum", "Masked Variance Pseudo-Stratum (SDMVSTRA)", "XdCount", "The masked variance pseudo stratum (SDMVSTRA).", links=[nh("SDMVSTRA", "DEMO_J")], constraints={"units": D + "units-items", "min_inclusive": 100, "max_inclusive": 200}, source=NH)
nh_design = C("nhanes-survey-design", "NHANES Survey Design", "The survey design fields a weighted estimate needs: the release cycle, interview and examination status, the interview and MEC weights, the pseudo-PSU and pseudo-stratum.",
              [nh_cycle, nh_status, nh_wtint, nh_wtmec, nh_psu, nh_stra], exact=NCIT + "C142700", source=NH)
nh_demo = C("nhanes-demographics", "NHANES Demographics", "The participant's demographics: the Default administrative gender and the NHANES gender code, the NIH CDE age with age in months for infants, race/ethnicity as the NIH CDE and as NHANES codes it, country of birth, citizenship, education and marital status as the NIH CDE and as NHANES codes them, pregnancy status, household size, the agency's income range and the income-to-poverty ratio.",
             [SEX, nh_gender, AGE, nh_age_months, RACE_ETH, nh_race, nh_born, nh_citizen, EDUCATION, nh_educ, MARITAL, nh_marital, pregnancy, nh_pregnancy, veteran, nh_hh_size, nh_income, nh_pir], exact=NCIT + "C16495", source=NH)

# blood pressure (BPX_J): the FHIR blood pressure cluster once per reading
nh_arm = leaf("nhanes-arm-selected", "Arm Selected (BPAARM)", "XdToken", "The arm the blood pressure was measured on (BPAARM).", links=[nh("BPAARM", "BPX_J")], enumeration=enum(("Right", SCT + "368209003"), ("Left", SCT + "368208006")), source=NH)
nh_cuff = leaf("nhanes-coded-cuff-size", "Coded Cuff Size (BPACSZ)", "XdToken", "The blood pressure cuff size used (BPACSZ).", links=[nh("BPACSZ", "BPX_J")],
               enumeration=enum(*[(v, NHANES + "BPX_J.htm#BPACSZ") for v in ("Infant (9 x 18 cm)", "Child (12 x 22 cm)", "Adult (15 x 32 cm)", "Large (17 x 36 cm)", "Thigh (23 x 38 cm)")]), source=NH)
nh_pulse_reg = leaf("nhanes-pulse-regularity", "Pulse Regular or Irregular (BPXPULS)", "XdToken", "Whether the pulse was regular or irregular (BPXPULS).", links=[nh("BPXPULS", "BPX_J")], enumeration=enum(("Regular", SCT + "271636001"), ("Irregular", SCT + "61086009")), source=NH)
nh_mil = leaf("nhanes-maximum-inflation-level", "Maximum Inflation Level (BPXML1)", "XdQuantity", "The maximum inflation level used, in mm Hg (BPXML1).", links=[nh("BPXML1", "BPX_J")], constraints={"units": D + "units-pressure", "total_digits": 3, "fraction_digits": 0, "min_inclusive": 0}, source=NH)
readings = [C(f"nhanes-blood-pressure-reading-{n}", f"Blood Pressure Reading {n}", f"The {['first', 'second', 'third'][n - 1]} of the seated blood pressure readings (BPXSY{n}, BPXDI{n}): the FHIR blood pressure cluster by identifier.", [F + "blood-pressure"], exact=LOINC + "85354-9/", source=NH) for n in (1, 2, 3)]
nh_bp = C("nhanes-blood-pressure", "NHANES Blood Pressure", "The blood pressure examination (BPX_J): the arm and cuff, the 60-second pulse as the FHIR heart rate by identifier and its regularity, the maximum inflation level, and up to three readings each as the FHIR blood pressure cluster.",
          [nh_arm, nh_cuff, F + "heart-rate", nh_pulse_reg, nh_mil] + readings, exact=LOINC + "85354-9/", source=NH)

# laboratory (TCHOL_J, CBC_J): a quantity per analyte, the LOINC code as its identity
def lab(key, label, var, file, loinc, u, digits, frac, desc=""):
    return leaf(key, label, "XdQuantity", f"{desc or label} ({var}, LOINC {loinc}).", links=[("skos:exactMatch", LOINC + loinc + "/", "standard"), nh(var, file)],
                constraints={"units": u, "total_digits": digits, "fraction_digits": frac, "min_inclusive": 0}, source=NH)
labs = [
    lab("nhanes-total-cholesterol", "Total Cholesterol", "LBXTC", "TCHOL_J", "2093-3", U_MG_DL, 4, 0, "Total cholesterol in serum, mg/dL"),
    lab("nhanes-total-cholesterol-si", "Total Cholesterol (SI)", "LBDTCSI", "TCHOL_J", "2093-3", U_MMOL_L, 5, 2, "Total cholesterol in serum, mmol/L (the agency's conversion of LBXTC)"),
    lab("nhanes-white-blood-cell-count", "White Blood Cell Count", "LBXWBCSI", "CBC_J", "6690-2", U_K_UL, 5, 1),
    lab("nhanes-lymphocyte-percent", "Lymphocyte Percent", "LBXLYPCT", "CBC_J", "736-9", D + "units-percentage", 4, 1),
    lab("nhanes-monocyte-percent", "Monocyte Percent", "LBXMOPCT", "CBC_J", "5905-5", D + "units-percentage", 4, 1),
    lab("nhanes-neutrophil-percent", "Segmented Neutrophils Percent", "LBXNEPCT", "CBC_J", "770-8", D + "units-percentage", 4, 1),
    lab("nhanes-eosinophil-percent", "Eosinophils Percent", "LBXEOPCT", "CBC_J", "713-8", D + "units-percentage", 4, 1),
    lab("nhanes-basophil-percent", "Basophils Percent", "LBXBAPCT", "CBC_J", "706-2", D + "units-percentage", 4, 1),
    lab("nhanes-lymphocyte-count", "Lymphocyte Number", "LBDLYMNO", "CBC_J", "731-0", U_K_UL, 4, 1),
    lab("nhanes-monocyte-count", "Monocyte Number", "LBDMONO", "CBC_J", "742-7", U_K_UL, 4, 1),
    lab("nhanes-neutrophil-count", "Segmented Neutrophils Number", "LBDNENO", "CBC_J", "751-8", U_K_UL, 4, 1),
    lab("nhanes-eosinophil-count", "Eosinophils Number", "LBDEONO", "CBC_J", "711-2", U_K_UL, 4, 1),
    lab("nhanes-basophil-count", "Basophils Number", "LBDBANO", "CBC_J", "704-7", U_K_UL, 4, 1),
    lab("nhanes-red-blood-cell-count", "Red Blood Cell Count", "LBXRBCSI", "CBC_J", "789-8", U_M_UL, 4, 2),
    lab("nhanes-hemoglobin", "Hemoglobin", "LBXHGB", "CBC_J", "718-7", U_G_DL, 4, 1),
    lab("nhanes-hematocrit", "Hematocrit", "LBXHCT", "CBC_J", "4544-3", D + "units-percentage", 4, 1),
    lab("nhanes-mean-cell-volume", "Mean Cell Volume", "LBXMCVSI", "CBC_J", "787-2", U_FL, 5, 1),
    lab("nhanes-mean-cell-hemoglobin", "Mean Cell Hemoglobin", "LBXMCHSI", "CBC_J", "785-6", U_PG, 4, 1),
    lab("nhanes-mean-cell-hemoglobin-concentration", "Mean Cell Hemoglobin Concentration", "LBXMC", "CBC_J", "786-4", U_G_DL, 4, 1),
    lab("nhanes-red-cell-distribution-width", "Red Cell Distribution Width", "LBXRDW", "CBC_J", "788-0", D + "units-percentage", 4, 1),
    lab("nhanes-platelet-count", "Platelet Count", "LBXPLTSI", "CBC_J", "777-3", U_K_UL, 4, 0),
    lab("nhanes-mean-platelet-volume", "Mean Platelet Volume", "LBXMPSI", "CBC_J", "32623-1", U_FL, 4, 1),
]
labs.append(leaf("nhanes-nucleated-red-blood-cells", "Nucleated Red Blood Cells", "XdQuantity", "Nucleated red blood cells per 100 white blood cells (LBXNRBC).", links=[nh("LBXNRBC", "CBC_J")],
                 constraints={"units": U_PER_100, "total_digits": 4, "fraction_digits": 1, "min_inclusive": 0}, source=NH))
nh_labs = C("nhanes-laboratory-results", "NHANES Laboratory Results", "The laboratory results carried: total cholesterol (TCHOL_J) and the complete blood count with differential (CBC_J), each analyte a quantity identified by its LOINC code.",
            labs, exact="http://hl7.org/fhir/StructureDefinition/Observation", source=NH)

# smoking (SMQ_J)
nh_smq020 = leaf("nhanes-smoked-100-cigarettes", "Smoked at Least 100 Cigarettes in Life (SMQ020)", "XdToken", "Whether the participant has smoked at least 100 cigarettes in their life (SMQ020).", links=[nh("SMQ020", "SMQ_J"), ("skos:closeMatch", LOINC + "63581-3/", "concept")], enumeration=yesno(), source=NH)
nh_smq040 = leaf("nhanes-now-smoke-cigarettes", "Do You Now Smoke Cigarettes (SMQ040)", "XdToken", "Whether the participant now smokes cigarettes every day, some days or not at all (SMQ040).", links=[nh("SMQ040", "SMQ_J")],
                 enumeration=enum(("Every day", LOINC + "LA18976-3/"), ("Some days", LOINC + "LA18977-1/"), ("Not at all", LOINC + "LA15920-4/")), source=NH)
nh_smd030 = leaf("nhanes-age-started-smoking", "Age Started Smoking Cigarettes Regularly (SMD030)", "XdCount", "The age the participant started smoking cigarettes regularly (SMD030).", links=[nh("SMD030", "SMQ_J")], constraints={"units": U_YEARS, "min_inclusive": 0, "max_inclusive": 100}, source=NH)
nh_smd650 = leaf("nhanes-cigarettes-per-day-past-30-days", "Average Cigarettes per Day, Past 30 Days (SMD650)", "XdCount", "The average number of cigarettes smoked per day during the past 30 days (SMD650).", links=[nh("SMD650", "SMQ_J")], constraints={"units": U_CIGS, "min_inclusive": 0, "max_inclusive": 100}, source=NH)
nh_smq900 = leaf("nhanes-ever-used-e-cigarette", "Ever Used an E-cigarette (SMQ900)", "XdToken", "Whether the participant has ever used an e-cigarette (SMQ900).", links=[nh("SMQ900", "SMQ_J")], enumeration=yesno(), source=NH)
nh_smoking = C("nhanes-smoking", "NHANES Smoking", "Cigarette use (SMQ_J): the two questions the smoking status derives from, the status itself as the shared component, the age started, the recent daily count and e-cigarette use.",
               [nh_smq020, nh_smq040, smoking, nh_smd030, nh_smd650, nh_smq900], exact=LOINC + "72166-2/", source=NH)

# medical conditions (MCQ_J)
nh_asthma_still = leaf("nhanes-still-have-asthma", "Still Have Asthma (MCQ035)", "XdToken", "Whether the participant still has asthma (MCQ035).", links=[nh("MCQ035", "MCQ_J")], enumeration=yesno(), source=NH)
nh_overweight = leaf("nhanes-doctor-said-overweight", "Doctor Ever Said You Were Overweight (MCQ080)", "XdToken", "Whether a doctor or health professional ever said the participant was overweight (MCQ080).", links=[nh("MCQ080", "MCQ_J")], enumeration=yesno(), source=NH)
nh_conditions = C("nhanes-medical-conditions", "NHANES Medical Conditions", "The medical conditions questionnaire (MCQ_J): the shared chronic condition indicators on a self-report basis, whether asthma persists, and whether a doctor said the participant was overweight.",
                  [conditions, nh_asthma_still, nh_overweight], exact=NCIT + "C2991", source=NH)

# physical functioning (PFQ_J)
DIFFICULTY = enum(("No difficulty", NCIT + "C17998"), ("Some difficulty", NCIT + "C17998"), ("Much difficulty", NCIT + "C17998"), ("Unable to do", NCIT + "C17998"), ("Do not do this activity", NCIT + "C17998"))
PF_ITEMS = {"PFQ061B": ("walking-quarter-mile", "Difficulty Walking a Quarter Mile"), "PFQ061C": ("walking-up-ten-stairs", "Difficulty Walking Up Ten Stairs"), "PFQ061D": ("stooping-crouching-kneeling", "Difficulty Stooping, Crouching or Kneeling"),
            "PFQ061E": ("lifting-or-carrying", "Difficulty Lifting or Carrying"), "PFQ061H": ("walking-between-rooms", "Difficulty Walking Between Rooms"), "PFQ061I": ("standing-up-from-chair", "Difficulty Standing Up from an Armless Chair"),
            "PFQ061J": ("getting-in-and-out-of-bed", "Difficulty Getting In and Out of Bed"), "PFQ061L": ("dressing", "Difficulty Dressing Yourself"), "PFQ061M": ("standing-for-long-periods", "Difficulty Standing for Long Periods")}
pf = [leaf(f"nhanes-{k}", f"{lab} ({var})", "XdToken", f"{lab} ({var}), on the four-point difficulty scale.", links=[nh(var, "PFQ_J")], enumeration=DIFFICULTY, source=NH) for var, (k, lab) in PF_ITEMS.items()]
nh_pfq049 = leaf("nhanes-limitations-keeping-from-working", "Limitations Keeping You from Working (PFQ049)", "XdToken", "Whether a physical, mental or emotional problem keeps the participant from working (PFQ049).", links=[nh("PFQ049", "PFQ_J")], enumeration=yesno(), source=NH)
nh_pfq054 = leaf("nhanes-need-special-equipment-to-walk", "Need Special Equipment to Walk (PFQ054)", "XdToken", "Whether the participant needs special equipment to walk (PFQ054).", links=[nh("PFQ054", "PFQ_J")], enumeration=yesno(), source=NH)
nh_pfq057 = leaf("nhanes-confusion-memory-problems", "Experience Confusion or Memory Problems (PFQ057)", "XdToken", "Whether the participant experiences confusion or memory problems (PFQ057).", links=[nh("PFQ057", "PFQ_J")], enumeration=yesno(), source=NH)
nh_pf = C("nhanes-physical-functioning", "NHANES Physical Functioning", "Physical functioning (PFQ_J): work limitation, equipment to walk, confusion or memory problems, and nine activity items on the four-point difficulty scale.",
          [nh_pfq049, nh_pfq054, nh_pfq057] + pf, exact=NCIT + "C20000", source=NH)

nh_participant = C("nhanes-participant", "NHANES Participant", "One NHANES 2017-2018 participant: the sequence number, the survey design, demographics, the blood pressure examination, laboratory results, smoking, medical conditions and physical functioning, joined on SEQN across the eight source files.",
                   [seqn, nh_design, nh_demo, nh_bp, nh_labs, nh_smoking, nh_conditions, nh_pf], exact=NCIT + "C41189", source=NH)

# medications (RXQ_RX_J): one record per medication row
nh_rxduse = leaf("nhanes-taken-prescription-past-month", "Taken Prescription Medicine, Past Month (RXDUSE)", "XdToken", "Whether the participant took prescription medicine in the past 30 days (RXDUSE).", links=[nh("RXDUSE", "RXQ_RX_J")], enumeration=yesno(), source=NH)
nh_drug = leaf("nhanes-generic-drug-name", "Generic Drug Name (RXDDRUG)", "XdString", "The generic drug name as NHANES records it (RXDDRUG).", links=[nh("RXDDRUG", "RXQ_RX_J")], constraints={"max_length": 200}, source=NH)
nh_drugid = leaf("nhanes-generic-drug-code", "Generic Drug Code (RXDDRGID)", "XdString", "The NHANES generic drug code (RXDDRGID), the agency's own identifier from the Lexicon Plus database; not an RxNorm code, so it is not presented as one.", links=[nh("RXDDRGID", "RXQ_RX_J")], constraints={"max_length": 12}, source=NH)
nh_days = leaf("nhanes-days-taken-medicine", "Number of Days Taken Medicine (RXDDAYS)", "XdCount", "The number of days the participant has taken the medicine (RXDDAYS; 99999 means more than that).", links=[nh("RXDDAYS", "RXQ_RX_J")], constraints={"units": U_DAYS, "min_inclusive": 0, "max_inclusive": 99999}, source=NH)
nh_rxcount = leaf("nhanes-number-of-prescription-medicines", "Number of Prescription Medicines Taken (RXDCOUNT)", "XdCount", "The number of prescription medicines the participant is taking (RXDCOUNT).", links=[nh("RXDCOUNT", "RXQ_RX_J")], constraints={"units": D + "units-items", "min_inclusive": 0, "max_inclusive": 50}, source=NH)
rx_reasons = [C(f"nhanes-medication-reason-{n}", f"Medication Reason {n}", f"The {['first', 'second', 'third'][n - 1]} reason the medicine is taken (RXDRSC{n}, RXDRSD{n}), as the FHIR ICD-10-CM diagnosis coded value by identifier.", [F + "diagnosis-icd10cm"], exact="http://hl7.org/fhir/R4/medicationrequest-definitions.html#MedicationRequest.reasonCode", source=NH) for n in (1, 2, 3)]
nh_medication = C("nhanes-medication", "NHANES Medication", "One prescription medicine a participant reported (RXQ_RX_J): the sequence number joining it to the participant, whether any was taken, the generic name and NHANES code, days taken, the count of medicines, and up to three reasons as ICD-10-CM coded values.",
                  [seqn, nh_rxduse, nh_drug, nh_drugid, nh_days, nh_rxcount] + rx_reasons, exact="http://hl7.org/fhir/StructureDefinition/MedicationStatement", source=NH)

# ================================================================ BRFSS 2022
BR = "BRFSS 2022"
def br(var):
    return see(BRFSS)

seqno = leaf("brfss-annual-sequence-number", "Annual Sequence Number (SEQNO)", "XdString", "The BRFSS annual sequence number identifying the respondent within the year (SEQNO).", links=[br("SEQNO")], constraints={"max_length": 12, "str_fmt": "[0-9]{10}"}, source=BR)
br_state = leaf("brfss-state-fips-code", "State FIPS Code (_STATE)", "XdString", "The FIPS code of the state or territory of residence (_STATE).", links=[br("_STATE")], constraints={"max_length": 2, "str_fmt": "[0-9]{1,2}"}, source=BR)
br_idate = leaf("brfss-interview-date", "Interview Date (IDATE)", "XdTemporal", "The interview date (IDATE).", links=[br("IDATE")], constraints={"allow": ["date"]}, source=BR)
br_psu = leaf("brfss-primary-sampling-unit", "Primary Sampling Unit (_PSU)", "XdString", "The primary sampling unit (_PSU), equal to the sequence number.", links=[br("_PSU")], constraints={"max_length": 12}, source=BR)
br_ststr = leaf("brfss-sample-design-stratum", "Sample Design Stratification Variable (_STSTR)", "XdString", "The sample design stratum (_STSTR).", links=[br("_STSTR")], constraints={"max_length": 8}, source=BR)
br_wt = leaf("brfss-final-weight", "Final Weight: Land-line and Cell-phone Data (_LLCPWT)", "XdQuantity", "The final raked weight for the combined landline and cellphone sample (_LLCPWT).", links=[br("_LLCPWT")], constraints={"units": U_WEIGHT, "total_digits": 12, "fraction_digits": 4, "min_inclusive": 0}, source=BR)
br_design = C("brfss-survey-design", "BRFSS Survey Design", "The survey design fields a weighted estimate needs: the state, interview date, PSU, stratum and final weight.", [br_state, br_idate, br_psu, br_ststr, br_wt], exact=NCIT + "C142700", source=BR)

br_sex = leaf("brfss-sex-of-respondent", "Sex of Respondent (SEXVAR)", "XdToken", "The sex of the respondent as BRFSS codes it (SEXVAR). Kept beside the Default administrative gender it is mapped to.", links=[br("SEXVAR")], enumeration=enum(("Male", NCIT + "C20197"), ("Female", NCIT + "C16576")), source=BR)
br_age = leaf("brfss-imputed-age-80", "Imputed Age Value Collapsed Above 80 (_AGE80)", "XdCount", "Imputed age in years, collapsed at 80 (_AGE80). The NIH CDE Age beside it carries the same value.", links=[br("_AGE80")], constraints={"units": U_YEARS, "min_inclusive": 18, "max_inclusive": 80}, source=BR)
br_race = leaf("brfss-imputed-race-ethnicity", "Imputed Race/Ethnicity Value (_IMPRACE)", "XdToken", "Race and ethnicity as BRFSS imputes and codes it (_IMPRACE). Kept beside the NIH CDE Race/Ethnicity Self-Identification it is mapped to.", links=[br("_IMPRACE")],
               enumeration=enum(("White, Non-Hispanic", NCIT + "C41261"), ("Black, Non-Hispanic", NCIT + "C16352"), ("Asian, Non-Hispanic", NCIT + "C41260"), ("American Indian/Alaskan Native, Non-Hispanic", NCIT + "C41259"), ("Hispanic", NCIT + "C17459"), ("Other race, Non-Hispanic", NCIT + "C17649")), source=BR)
br_educa = leaf("brfss-education-level", "Education Level (EDUCA)", "XdToken", "The highest grade or year of school completed (EDUCA). Kept beside the NIH CDE Current Educational Attainment it is mapped to.", links=[br("EDUCA")],
                enumeration=enum(("Never attended school or only kindergarten", NCIT + "C17953"), ("Grades 1 through 8 (Elementary)", NCIT + "C17953"), ("Grades 9 through 11 (Some high school)", NCIT + "C17953"), ("Grade 12 or GED (High school graduate)", NCIT + "C67136"), ("College 1 year to 3 years (Some college or technical school)", NCIT + "C67137"), ("College 4 years or more (College graduate)", NCIT + "C39303")), source=BR)
br_marital = leaf("brfss-marital-status", "Marital Status (MARITAL)", "XdToken", "Marital status as BRFSS codes it (MARITAL). Kept beside the NIH CDE Marital Status it is mapped to.", links=[br("MARITAL")],
                  enumeration=enum(("Married", NCIT + "C51773"), ("Divorced", NCIT + "C51776"), ("Widowed", NCIT + "C51775"), ("Separated", NCIT + "C51777"), ("Never married", NCIT + "C51774"), ("A member of an unmarried couple", NCIT + "C53262")), source=BR)
br_employ = leaf("brfss-employment-status", "Employment Status (EMPLOY1)", "XdToken", "Employment status as BRFSS codes it (EMPLOY1). Kept beside the NIH CDE Employment Status it is mapped to.", links=[br("EMPLOY1")],
                 enumeration=enum(*[(v, BRFSS) for v in ("Employed for wages", "Self-employed", "Out of work for 1 year or more", "Out of work for less than 1 year", "A homemaker", "A student", "Retired", "Unable to work")]), source=BR)
br_income = leaf("brfss-income-level", "Income Level (INCOME3)", "XdToken", "Annual household income from all sources in the agency's ranges (INCOME3). Not harmonized: the ranges do not nest with NHANES's or the NIH CDE's.", links=[br("INCOME3")],
                 enumeration=enum(*[(v, BRFSS) for v in ("Less than $10,000", "$10,000 to less than $15,000", "$15,000 to less than $20,000", "$20,000 to less than $25,000", "$25,000 to less than $35,000", "$35,000 to less than $50,000", "$50,000 to less than $75,000", "$75,000 to less than $100,000", "$100,000 to less than $150,000", "$150,000 to less than $200,000", "$200,000 or more")]), source=BR)
br_insurance = leaf("brfss-primary-source-of-insurance", "Primary Source of Health Insurance (PRIMINSR)", "XdToken", "The current primary source of health insurance coverage (PRIMINSR). Kept beside the NIH CDE Category of Health Insurance it is mapped to.", links=[br("PRIMINSR")],
                    enumeration=enum(*[(v, BRFSS) for v in ("A plan purchased through an employer or union", "A private nongovernmental plan that you or another family member buys on your own", "Medicare", "Medigap", "Medicaid", "CHIP", "Military related health care", "Indian Health Service", "State sponsored health plan", "Other government program", "No coverage of any type")]), source=BR)
br_children = leaf("brfss-number-of-children-in-household", "Number of Children in Household (CHILDREN)", "XdCount", "The number of children less than 18 years of age in the household (CHILDREN).", links=[br("CHILDREN")], constraints={"units": D + "units-items", "min_inclusive": 0, "max_inclusive": 87}, source=BR)
br_pregnant = leaf("brfss-pregnancy-status", "Pregnancy Status (PREGNANT)", "XdToken", "Whether the respondent is pregnant (PREGNANT). Kept beside the NIH CDE pregnancy question it is mapped to.", links=[br("PREGNANT")], enumeration=yesno(), source=BR)
br_demo = C("brfss-demographics", "BRFSS Demographics", "The respondent's demographics: the Default administrative gender and the BRFSS sex code, the NIH CDE age and the agency's imputed age, race/ethnicity as the NIH CDE and as BRFSS imputes it, education, marital status, employment and insurance as the NIH CDE and as BRFSS codes them, veteran status, pregnancy, children in the household and the agency's income range.",
            [SEX, br_sex, AGE, br_age, RACE_ETH, br_race, EDUCATION, br_educa, MARITAL, br_marital, EMPLOYMENT, br_employ, INSURANCE, br_insurance, veteran, pregnancy, br_pregnant, br_children, br_income], exact=NCIT + "C16495", source=BR)

DAYS30 = {"units": U_DAYS, "min_inclusive": 0, "max_inclusive": 30}
br_physhlth = leaf("brfss-days-physical-health-not-good", "Days Physical Health Not Good, Past 30 (PHYSHLTH)", "XdCount", "The number of days in the past 30 the respondent's physical health was not good (PHYSHLTH).", links=[br("PHYSHLTH"), ("skos:closeMatch", LOINC + "63580-5/", "concept")], constraints=DAYS30, source=BR)
br_menthlth = leaf("brfss-days-mental-health-not-good", "Days Mental Health Not Good, Past 30 (MENTHLTH)", "XdCount", "The number of days in the past 30 the respondent's mental health was not good (MENTHLTH).", links=[br("MENTHLTH"), ("skos:closeMatch", LOINC + "63579-7/", "concept")], constraints=DAYS30, source=BR)
br_checkup = leaf("brfss-length-since-last-checkup", "Length of Time Since Last Routine Checkup (CHECKUP1)", "XdToken", "How long since the respondent last visited a doctor for a routine checkup (CHECKUP1).", links=[br("CHECKUP1")],
                  enumeration=enum(*[(v, BRFSS) for v in ("Within past year", "Within past 2 years", "Within past 5 years", "5 or more years ago", "Never")]), source=BR)
br_exerany = leaf("brfss-exercise-in-past-30-days", "Exercise in Past 30 Days (EXERANY2)", "XdToken", "Whether the respondent took part in any physical activity or exercise in the past month other than their regular job (EXERANY2).", links=[br("EXERANY2")], enumeration=yesno(), source=BR)
br_health = C("brfss-health-status", "BRFSS Health Status and Access", "General health as the shared component, the days physical and mental health were not good, time since the last checkup, and exercise in the past 30 days.",
              [general_health, br_physhlth, br_menthlth, br_checkup, br_exerany], exact=NCIT + "C16669", source=BR)

br_asthnow = leaf("brfss-still-have-asthma", "Still Have Asthma (ASTHNOW)", "XdToken", "Whether the respondent still has asthma (ASTHNOW).", links=[br("ASTHNOW")], enumeration=yesno(), source=BR)
br_conditions = C("brfss-chronic-conditions", "BRFSS Chronic Conditions", "The chronic health conditions section: the shared chronic condition indicators on a self-report basis, and whether asthma persists.", [conditions, br_asthnow], exact=NCIT + "C2991", source=BR)

br_weight = leaf("brfss-reported-weight-in-pounds", "Reported Weight in Pounds (WEIGHT2)", "XdQuantity", "Self-reported weight without shoes, in pounds as reported (WEIGHT2; the agency's kilogram reports are converted). The FHIR body weight beside it carries the same value in kilograms.", links=[br("WEIGHT2")], constraints={"units": D + "units-mass-us", "total_digits": 4, "fraction_digits": 0, "min_inclusive": 50, "max_inclusive": 999}, source=BR)
br_height = leaf("brfss-reported-height", "Reported Height in Feet and Inches (HEIGHT3)", "XdString", "Self-reported height as coded (HEIGHT3: feet and inches as FII, or 9xxx for metres and centimetres). The FHIR body height beside it carries the value in centimetres.", links=[br("HEIGHT3")], constraints={"max_length": 4, "str_fmt": "[0-9]{3,4}"}, source=BR)
br_bmi5cat = leaf("brfss-bmi-category", "Computed Body Mass Index Category (_BMI5CAT)", "XdToken", "The agency's computed BMI category (_BMI5CAT).", links=[br("_BMI5CAT")], enumeration=enum(("Underweight", NCIT + "C17962"), ("Normal Weight", NCIT + "C17958"), ("Overweight", NCIT + "C94250"), ("Obese", NCIT + "C3283")), source=BR)
br_body = C("brfss-body-measures", "BRFSS Body Measures", "Self-reported height and weight as the agency codes them, and as the FHIR vital signs panel by identifier (body height, body weight, BMI), with the agency's computed BMI category.",
            [br_height, br_weight, F + "vital-signs-panel", br_bmi5cat], exact=LOINC + "39156-5/", source=BR)

br_smoke100 = leaf("brfss-smoked-100-cigarettes", "Smoked at Least 100 Cigarettes (SMOKE100)", "XdToken", "Whether the respondent has smoked at least 100 cigarettes in their entire life (SMOKE100).", links=[br("SMOKE100"), ("skos:closeMatch", LOINC + "63581-3/", "concept")], enumeration=yesno(), source=BR)
br_smokday = leaf("brfss-frequency-of-days-now-smoking", "Frequency of Days Now Smoking (SMOKDAY2)", "XdToken", "Whether the respondent now smokes cigarettes every day, some days or not at all (SMOKDAY2).", links=[br("SMOKDAY2")], enumeration=enum(("Every day", LOINC + "LA18976-3/"), ("Some days", LOINC + "LA18977-1/"), ("Not at all", LOINC + "LA15920-4/")), source=BR)
br_smoker3 = leaf("brfss-computed-smoking-status", "Computed Smoking Status (_SMOKER3)", "XdToken", "The agency's four-level computed smoking status (_SMOKER3). The shared Smoking Status beside it is derived from the same answers.", links=[br("_SMOKER3")],
                  enumeration=enum(("Current smoker - now smokes every day", LOINC + "LA18976-3/"), ("Current smoker - now smokes some days", LOINC + "LA18977-1/"), ("Former smoker", LOINC + "LA15920-4/"), ("Never smoked", LOINC + "LA18978-9/")), source=BR)
br_ecig = leaf("brfss-e-cigarette-use", "Current E-cigarette Use (ECIGNOW2)", "XdToken", "Whether the respondent now uses e-cigarettes every day, some days, or not at all, or never used them (ECIGNOW2).", links=[br("ECIGNOW2")], enumeration=enum(*[(v, BRFSS) for v in ("Never used e-cigarettes in your entire life", "Use them every day", "Use them some days", "Not at all (right now)")]), source=BR)
br_alcday = leaf("brfss-days-drank-alcohol", "Days in Past 30 Had Alcoholic Beverage (ALCDAY4)", "XdCount", "The number of days in the past 30 the respondent had at least one alcoholic drink (ALCDAY4; the agency's per-week code is converted to days).", links=[br("ALCDAY4")], constraints=DAYS30, source=BR)
br_avedrnk = leaf("brfss-average-drinks-per-day", "Average Alcoholic Drinks per Day in Past 30 (AVEDRNK3)", "XdCount", "The average number of drinks on the days the respondent drank (AVEDRNK3).", links=[br("AVEDRNK3"), ("skos:closeMatch", LOINC + "74013-4/", "concept")], constraints={"units": U_DRINKS, "min_inclusive": 1, "max_inclusive": 76}, source=BR)
br_binge = leaf("brfss-binge-drinking-occasions", "Binge Drinking Occasions in Past 30 (DRNK3GE5)", "XdCount", "The number of occasions in the past 30 days the respondent had five (men) or four (women) or more drinks (DRNK3GE5).", links=[br("DRNK3GE5")], constraints={"units": D + "units-items", "min_inclusive": 0, "max_inclusive": 76}, source=BR)
br_tobacco = C("brfss-tobacco-and-alcohol", "BRFSS Tobacco and Alcohol Use", "Cigarette use: the two questions the shared smoking status derives from, the status, the agency's computed status, e-cigarette use; alcohol: days drinking, average drinks and binge occasions in the past 30 days.",
               [br_smoke100, br_smokday, smoking, br_smoker3, br_ecig, br_alcday, br_avedrnk, br_binge], exact=LOINC + "72166-2/", source=BR)

DIS = {"DEAF": ("deaf-or-hard-of-hearing", "Deaf or Serious Difficulty Hearing"), "BLIND": ("blind-or-difficulty-seeing", "Blind or Serious Difficulty Seeing"), "DECIDE": ("difficulty-concentrating-or-remembering", "Serious Difficulty Concentrating, Remembering or Deciding"),
       "DIFFWALK": ("difficulty-walking-or-climbing-stairs", "Serious Difficulty Walking or Climbing Stairs"), "DIFFDRES": ("difficulty-dressing-or-bathing", "Difficulty Dressing or Bathing"), "DIFFALON": ("difficulty-doing-errands-alone", "Difficulty Doing Errands Alone")}
dis = [leaf(f"brfss-{k}", f"{lab} ({var})", "XdToken", f"{lab} ({var}), the American Community Survey disability question as BRFSS asks it.", links=[br(var)], enumeration=yesno(), source=BR) for var, (k, lab) in DIS.items()]
br_disability = C("brfss-disability", "BRFSS Disability", "The six disability questions: hearing, vision, cognition, mobility, self-care and independent living.", dis, exact=NCIT + "C21007", source=BR)

br_respondent = C("brfss-respondent", "BRFSS Respondent", "One BRFSS 2022 respondent: the sequence number, survey design, demographics, health status and access, chronic conditions, body measures, tobacco and alcohol, and disability, from the columns of the LLCP2022 file this demonstration carries.",
                  [seqno, br_design, br_demo, br_health, br_conditions, br_body, br_tobacco, br_disability], exact=NCIT + "C41189", source=BR)

# ================================================================ CMS DE-SynPUF
CM = "CMS DE-SynPUF"
def cm(var):
    return see(CMS)

bene_id = leaf("cms-beneficiary-code", "Beneficiary Code (DESYNPUF_ID)", "XdString", "The synthetic beneficiary identifier every DE-SynPUF file carries (DESYNPUF_ID); not traceable to a real Medicare beneficiary.", links=[cm("DESYNPUF_ID")], constraints={"max_length": 16, "str_fmt": "[0-9A-F]{16}"}, source=CM)
cms_sex = leaf("cms-sex-code", "Sex (BENE_SEX_IDENT_CD)", "XdToken", "The beneficiary's sex as CMS codes it (BENE_SEX_IDENT_CD). Kept beside the Default administrative gender it is mapped to.", links=[cm("BENE_SEX_IDENT_CD")], enumeration=enum(("Male", NCIT + "C20197"), ("Female", NCIT + "C16576")), source=CM)
cms_race = leaf("cms-race-code", "Race (BENE_RACE_CD)", "XdToken", "The beneficiary's race as CMS codes it (BENE_RACE_CD). Kept beside the NIH CDE Race/Ethnicity Self-Identification it is mapped to; Others has no CDE value.", links=[cm("BENE_RACE_CD")],
                enumeration=enum(("White", NCIT + "C41261"), ("Black", NCIT + "C16352"), ("Others", NCIT + "C17649"), ("Hispanic", NCIT + "C17459")), source=CM)
cms_esrd = leaf("cms-end-stage-renal-disease-indicator", "End-Stage Renal Disease Indicator (BENE_ESRD_IND)", "XdToken", "Whether the beneficiary has end-stage renal disease (BENE_ESRD_IND).", links=[cm("BENE_ESRD_IND"), ("dcterms:subject", SCT + "46177005", "concept")], enumeration=yesno(), source=CM)
cms_state = leaf("cms-state-code", "State Code (SP_STATE_CODE)", "XdString", "The SSA state code of the beneficiary's mailing address (SP_STATE_CODE).", links=[cm("SP_STATE_CODE")], constraints={"max_length": 2, "str_fmt": "[0-9]{1,2}"}, source=CM)
cms_county = leaf("cms-county-code", "County Code (BENE_COUNTY_CD)", "XdString", "The SSA county code of the beneficiary's mailing address (BENE_COUNTY_CD).", links=[cm("BENE_COUNTY_CD")], constraints={"max_length": 3, "str_fmt": "[0-9]{1,3}"}, source=CM)
MONTHS = {"units": U_MONTHS, "min_inclusive": 0, "max_inclusive": 12}
cms_hi = leaf("cms-part-a-coverage-months", "Hospital Insurance (Part A) Coverage Months", "XdCount", "Total months of Part A coverage in the reference year (BENE_HI_CVRAGE_TOT_MONS).", links=[cm("BENE_HI_CVRAGE_TOT_MONS")], constraints=MONTHS, source=CM)
cms_smi = leaf("cms-part-b-coverage-months", "Supplementary Medical Insurance (Part B) Coverage Months", "XdCount", "Total months of Part B coverage in the reference year (BENE_SMI_CVRAGE_TOT_MONS).", links=[cm("BENE_SMI_CVRAGE_TOT_MONS")], constraints=MONTHS, source=CM)
cms_hmo = leaf("cms-hmo-coverage-months", "HMO Coverage Months", "XdCount", "Total months of HMO coverage in the reference year (BENE_HMO_CVRAGE_TOT_MONS).", links=[cm("BENE_HMO_CVRAGE_TOT_MONS")], constraints=MONTHS, source=CM)
cms_partd = leaf("cms-part-d-coverage-months", "Part D Plan Coverage Months", "XdCount", "Total months of Part D plan coverage in the reference year (PLAN_CVRG_MOS_NUM).", links=[cm("PLAN_CVRG_MOS_NUM")], constraints=MONTHS, source=CM)
cms_coverage = C("cms-medicare-coverage", "CMS Medicare Coverage", "The beneficiary's Medicare coverage in the reference year: the FHIR insurance coverage by identifier (Medicare as the coverage type), and the months of Part A, Part B, HMO and Part D coverage.",
                 [F + "insurance-coverage", cms_hi, cms_smi, cms_hmo, cms_partd], exact="http://hl7.org/fhir/StructureDefinition/Coverage", source=CM)
AMOUNT = {"units": D + "units-currency", "total_digits": 12, "fraction_digits": 2}
def amount(key, label, var, desc):
    return leaf(key, label, "XdQuantity", f"{desc} ({var}), in US dollars.", links=[cm(var), ("skos:closeMatch", "https://schema.org/MonetaryAmount", "concept")], constraints=AMOUNT, source=CM)
annual = [amount(f"cms-annual-{k}", lab, var, desc) for k, lab, var, desc in (
    ("inpatient-medicare-reimbursement", "Inpatient Annual Medicare Reimbursement", "MEDREIMB_IP", "Medicare reimbursement for inpatient services in the year"),
    ("inpatient-beneficiary-responsibility", "Inpatient Annual Beneficiary Responsibility", "BENRES_IP", "The beneficiary's responsibility for inpatient services in the year"),
    ("inpatient-primary-payer-reimbursement", "Inpatient Annual Primary Payer Reimbursement", "PPPYMT_IP", "Primary payer reimbursement for inpatient services in the year"),
    ("outpatient-medicare-reimbursement", "Outpatient Annual Medicare Reimbursement", "MEDREIMB_OP", "Medicare reimbursement for outpatient services in the year"),
    ("outpatient-beneficiary-responsibility", "Outpatient Annual Beneficiary Responsibility", "BENRES_OP", "The beneficiary's responsibility for outpatient services in the year"),
    ("outpatient-primary-payer-reimbursement", "Outpatient Annual Primary Payer Reimbursement", "PPPYMT_OP", "Primary payer reimbursement for outpatient services in the year"),
    ("carrier-medicare-reimbursement", "Carrier Annual Medicare Reimbursement", "MEDREIMB_CAR", "Medicare reimbursement for carrier (physician and supplier) services in the year"),
    ("carrier-beneficiary-responsibility", "Carrier Annual Beneficiary Responsibility", "BENRES_CAR", "The beneficiary's responsibility for carrier services in the year"),
    ("carrier-primary-payer-reimbursement", "Carrier Annual Primary Payer Reimbursement", "PPPYMT_CAR", "Primary payer reimbursement for carrier services in the year"))]
cms_annual = C("cms-annual-amounts", "CMS Annual Amounts", "The year's Medicare reimbursement, beneficiary responsibility and primary payer reimbursement for inpatient, outpatient and carrier services.", annual, exact="https://schema.org/MonetaryAmount", source=CM)
cms_demo = C("cms-beneficiary-demographics", "CMS Beneficiary Demographics", "The beneficiary's demographics: the Default date of birth and administrative gender with the CMS sex code, the FHIR patient's deceased indicator and date by identifier, race as the NIH CDE and as CMS codes it, and the state and county of the mailing address.",
             [BIRTH_DATE, SEX, cms_sex, F + "deceased-indicator", F + "deceased-date", RACE_ETH, cms_race, cms_state, cms_county], exact=NCIT + "C16495", source=CM)
cms_beneficiary = C("cms-beneficiary", "CMS Beneficiary", "One DE-SynPUF beneficiary summary for the 2008 reference year: the beneficiary code, demographics, Medicare coverage, the eleven chronic condition indicators on a claims basis with the ESRD indicator, and the year's amounts.",
                    [bene_id, cms_demo, cms_coverage, conditions, cms_esrd, cms_annual], exact=NCIT + "C41189", source=CM)

# claims
claim_id = leaf("cms-claim-id", "Claim ID (CLM_ID)", "XdString", "The claim identifier (CLM_ID).", links=[cm("CLM_ID")], constraints={"max_length": 20, "str_fmt": "[0-9]{1,20}"}, source=CM)
segment = leaf("cms-claim-line-segment", "Claim Line Segment (SEGMENT)", "XdCount", "The claim line segment (SEGMENT).", links=[cm("SEGMENT")], constraints={"units": D + "units-items", "min_inclusive": 1, "max_inclusive": 9}, source=CM)
prvdr = leaf("cms-provider-institution", "Provider Institution (PRVDR_NUM)", "XdString", "The provider institution number (PRVDR_NUM).", links=[cm("PRVDR_NUM")], constraints={"max_length": 10}, source=CM)
npi = {k: leaf(f"cms-{k}-physician-npi", f"{lab} Physician NPI ({var})", "XdString", f"The {lab.lower()} physician's National Provider Identifier ({var}).", links=[cm(var)], constraints={"max_length": 10, "str_fmt": "[0-9]{10}"}, source=CM)
       for k, lab, var in (("attending", "Attending", "AT_PHYSN_NPI"), ("operating", "Operating", "OP_PHYSN_NPI"), ("other", "Other", "OT_PHYSN_NPI"))}
clm_pmt = amount("cms-claim-payment-amount", "Claim Payment Amount", "CLM_PMT_AMT", "The amount Medicare paid on the claim")
prmry_pyr = amount("cms-primary-payer-claim-paid-amount", "Primary Payer Claim Paid Amount", "NCH_PRMRY_PYR_CLM_PD_AMT", "The amount a primary payer paid on the claim")
blood_ddctbl = amount("cms-blood-deductible-liability-amount", "Blood Deductible Liability Amount", "NCH_BENE_BLOOD_DDCTBL_LBLTY_AM", "The beneficiary's blood deductible liability")
# ICD-9-CM, HCPCS: coded values this project owns, shaped as the FHIR library shapes a coded value
sys_icd9 = leaf("system-icd9cm", "Code System: ICD-9-CM", "XdLink", "The code system of a coded value, fixed: ICD-9-CM (http://hl7.org/fhir/sid/icd-9-cm). FHIR Coding.system.",
                links=[("skos:exactMatch", "http://hl7.org/fhir/sid/icd-9-cm", "standard")], constraints={"link": "http://hl7.org/fhir/sid/icd-9-cm", "relation": "codeSystem", "relation_uri": "http://hl7.org/fhir/R4/datatypes-definitions.html#Coding.system"}, source="ICD-9-CM")
sys_hcpcs = leaf("system-hcpcs", "Code System: HCPCS", "XdLink", "The code system of a coded value, fixed: HCPCS Level I (CPT) and Level II (http://www.ama-assn.org/go/cpt and https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system). FHIR Coding.system.",
                 links=[("skos:exactMatch", "http://www.ama-assn.org/go/cpt", "standard")], constraints={"link": "http://www.ama-assn.org/go/cpt", "relation": "codeSystem", "relation_uri": "http://hl7.org/fhir/R4/datatypes-definitions.html#Coding.system"}, source="HCPCS")
sys_ndc = leaf("system-ndc", "Code System: NDC", "XdLink", "The code system of a coded value, fixed: the National Drug Code (http://hl7.org/fhir/sid/ndc). FHIR Coding.system.",
               links=[("skos:exactMatch", "http://hl7.org/fhir/sid/ndc", "standard")], constraints={"link": "http://hl7.org/fhir/sid/ndc", "relation": "codeSystem", "relation_uri": "http://hl7.org/fhir/R4/datatypes-definitions.html#Coding.system"}, source="NDC")
icd9_dx_code = leaf("diagnosis-icd9cm-code", "Diagnosis Code (ICD-9-CM)", "XdString", "An ICD-9-CM diagnosis code as recorded on a 2008-2010 Medicare claim, without the decimal point as CMS files carry it.", links=[("skos:exactMatch", "http://hl7.org/fhir/sid/icd-9-cm", "standard")], constraints={"max_length": 5, "str_fmt": "[0-9EV][0-9]{2,4}"}, source="ICD-9-CM")
icd9_px_code = leaf("procedure-icd9cm-code", "Procedure Code (ICD-9-CM)", "XdString", "An ICD-9-CM volume 3 procedure code as recorded on a Medicare inpatient claim, without the decimal point.", links=[("skos:exactMatch", "http://hl7.org/fhir/sid/icd-9-cm", "standard")], constraints={"max_length": 4, "str_fmt": "[0-9]{2,4}"}, source="ICD-9-CM")
hcpcs_code = leaf("hcpcs-code", "HCPCS Code", "XdString", "A HCPCS code as recorded on a Medicare claim line: five characters, CPT (Level I) or Level II.", links=[("skos:exactMatch", "http://www.ama-assn.org/go/cpt", "standard")], constraints={"max_length": 5, "str_fmt": "[0-9A-Z][0-9]{3}[0-9A-Z]"}, source="HCPCS")
ndc_code = leaf("ndc-code", "Product Service ID (NDC)", "XdString", "The National Drug Code of the product dispensed (PROD_SRVC_ID), eleven digits.", links=[("skos:exactMatch", "http://hl7.org/fhir/sid/ndc", "standard"), cm("PROD_SRVC_ID")], constraints={"max_length": 11, "str_fmt": "[0-9]{11}"}, source="NDC")
dx9 = C("diagnosis-icd9cm", "Diagnosis (ICD-9-CM)", "A diagnosis coded in ICD-9-CM: the code, its display text and the fixed code system (FHIR Coding). What the 2008-2010 claims carry; not mapped to ICD-10-CM.", [icd9_dx_code, F + "code-display-text", sys_icd9], exact="http://hl7.org/fhir/R4/datatypes.html#Coding", source="ICD-9-CM")
px9 = C("procedure-icd9cm", "Procedure (ICD-9-CM)", "A procedure coded in ICD-9-CM volume 3: the code, its display text and the fixed code system (FHIR Coding).", [icd9_px_code, F + "code-display-text", sys_icd9], exact="http://hl7.org/fhir/R4/datatypes.html#Coding", source="ICD-9-CM")
hcpcs = C("procedure-hcpcs", "Procedure (HCPCS)", "A procedure or service coded in HCPCS: the code, its display text and the fixed code system (FHIR Coding).", [hcpcs_code, F + "code-display-text", sys_hcpcs], exact="http://hl7.org/fhir/R4/datatypes.html#Coding", source="HCPCS")
ndc = C("product-ndc", "Product (NDC)", "A dispensed product coded in the National Drug Code: the code, its display text and the fixed code system (FHIR Coding).", [ndc_code, F + "code-display-text", sys_ndc], exact="http://hl7.org/fhir/R4/datatypes.html#Coding", source="NDC")
admitting_dx = C("cms-admitting-diagnosis", "Admitting Diagnosis", "The admitting diagnosis (ADMTNG_ICD9_DGNS_CD) as an ICD-9-CM coded value.", [dx9], exact="http://hl7.org/fhir/R4/encounter-definitions.html#Encounter.diagnosis", source=CM)
dxs = [C(f"cms-claim-diagnosis-{n}", f"Claim Diagnosis {n}", f"Diagnosis code {n} on the claim (ICD9_DGNS_CD_{n}) as an ICD-9-CM coded value.", [dx9], exact="http://hl7.org/fhir/R4/claim-definitions.html#Claim.diagnosis", source=CM) for n in range(1, 11)]
pxs = [C(f"cms-claim-procedure-{n}", f"Claim Procedure {n}", f"Procedure code {n} on the claim (ICD9_PRCDR_CD_{n}) as an ICD-9-CM coded value.", [px9], exact="http://hl7.org/fhir/R4/claim-definitions.html#Claim.procedure", source=CM) for n in range(1, 7)]
hcs = [C(f"cms-claim-hcpcs-{n}", f"Claim HCPCS {n}", f"HCPCS code {n} on the claim (HCPCS_CD_{n}) as a coded value; the first ten of the file's forty-five line slots are carried.", [hcpcs], exact="http://hl7.org/fhir/R4/claim-definitions.html#Claim.item", source=CM) for n in range(1, 11)]
claim_common = [bene_id, claim_id, segment, F + "encounter", prvdr, clm_pmt, prmry_pyr, npi["attending"], npi["operating"], npi["other"], blood_ddctbl]
# inpatient
admsn_dt = leaf("cms-claim-admission-date", "Claim Admission Date (CLM_ADMSN_DT)", "XdTemporal", "The inpatient admission date (CLM_ADMSN_DT).", links=[cm("CLM_ADMSN_DT")], constraints={"allow": ["date"]}, source=CM)
dschrg_dt = leaf("cms-beneficiary-discharge-date", "Beneficiary Discharge Date (NCH_BENE_DSCHRG_DT)", "XdTemporal", "The inpatient discharge date (NCH_BENE_DSCHRG_DT).", links=[cm("NCH_BENE_DSCHRG_DT")], constraints={"allow": ["date"]}, source=CM)
drg = leaf("cms-diagnosis-related-group-code", "Diagnosis Related Group Code (CLM_DRG_CD)", "XdString", "The claim's diagnosis related group code (CLM_DRG_CD).", links=[cm("CLM_DRG_CD")], constraints={"max_length": 3, "str_fmt": "[0-9]{3}"}, source=CM)
per_diem = amount("cms-pass-through-per-diem-amount", "Claim Pass-Through Per Diem Amount", "CLM_PASS_THRU_PER_DIEM_AMT", "The pass-through per diem amount")
ip_ddctbl = amount("cms-inpatient-deductible-amount", "Inpatient Deductible Amount", "NCH_BENE_IP_DDCTBL_AMT", "The beneficiary's inpatient deductible")
pta_coins = amount("cms-part-a-coinsurance-liability-amount", "Part A Coinsurance Liability Amount", "NCH_BENE_PTA_COINSRNC_LBLTY_AM", "The beneficiary's Part A coinsurance liability")
util_days = leaf("cms-claim-utilization-day-count", "Claim Utilization Day Count (CLM_UTLZTN_DAY_CNT)", "XdCount", "The number of covered days on the claim (CLM_UTLZTN_DAY_CNT).", links=[cm("CLM_UTLZTN_DAY_CNT")], constraints={"units": U_DAYS, "min_inclusive": 0, "max_inclusive": 366}, source=CM)
cms_inpatient = C("cms-inpatient-claim", "CMS Inpatient Claim", "One DE-SynPUF inpatient claim (2008-2010): the beneficiary and claim identifiers, the stay as the FHIR encounter by identifier with admission and discharge dates, provider and physicians, the payment, per diem, deductible and coinsurance amounts, utilization days, the DRG, the admitting diagnosis, up to ten diagnoses, six procedures and ten HCPCS codes as ICD-9-CM and HCPCS coded values.",
                  claim_common + [admsn_dt, dschrg_dt, per_diem, ip_ddctbl, pta_coins, util_days, drg, admitting_dx] + dxs + pxs + hcs, exact="http://hl7.org/fhir/StructureDefinition/Claim", source=CM)
cms_outpatient = C("cms-outpatient-claim", "CMS Outpatient Claim", "One DE-SynPUF outpatient claim (2008-2010): the beneficiary and claim identifiers, the visit as the FHIR encounter by identifier, provider and physicians, the payment and blood deductible amounts, the Part B coinsurance and deductible, the admitting diagnosis, up to ten diagnoses, six procedures and ten HCPCS codes.",
                   claim_common + [amount("cms-part-b-coinsurance-amount", "Part B Coinsurance Amount", "NCH_BENE_PTB_COINSRNC_AMT", "The beneficiary's Part B coinsurance"), amount("cms-part-b-deductible-amount", "Part B Deductible Amount", "NCH_BENE_PTB_DDCTBL_AMT", "The beneficiary's Part B deductible"), admitting_dx] + dxs + pxs + hcs,
                   exact="http://hl7.org/fhir/StructureDefinition/Claim", source=CM)
# prescription drug events
pde_id = leaf("cms-prescription-drug-event-id", "Prescription Drug Event ID (PDE_ID)", "XdString", "The prescription drug event identifier (PDE_ID).", links=[cm("PDE_ID")], constraints={"max_length": 20, "str_fmt": "[0-9]{1,20}"}, source=CM)
srvc_dt = leaf("cms-service-date", "Service Date (SRVC_DT)", "XdTemporal", "The date the prescription was filled (SRVC_DT).", links=[cm("SRVC_DT")], constraints={"allow": ["date"]}, source=CM)
qty = leaf("cms-quantity-dispensed", "Quantity Dispensed (QTY_DSPNSD_NUM)", "XdQuantity", "The quantity dispensed (QTY_DSPNSD_NUM).", links=[cm("QTY_DSPNSD_NUM")], constraints={"units": D + "units-items", "total_digits": 8, "fraction_digits": 2, "min_inclusive": 0}, source=CM)
days_supply = leaf("cms-days-supply", "Days Supply (DAYS_SUPLY_NUM)", "XdCount", "The days' supply dispensed (DAYS_SUPLY_NUM).", links=[cm("DAYS_SUPLY_NUM")], constraints={"units": U_DAYS, "min_inclusive": 0, "max_inclusive": 365}, source=CM)
ptnt_pay = amount("cms-patient-pay-amount", "Patient Pay Amount", "PTNT_PAY_AMT", "The amount the patient paid")
tot_rx = amount("cms-total-prescription-cost", "Total Prescription Cost", "TOT_RX_CST_AMT", "The gross drug cost")
cms_pde = C("cms-prescription-drug-event", "CMS Prescription Drug Event", "One DE-SynPUF Part D prescription drug event (2008-2010): the beneficiary and event identifiers, the service date, the product as an NDC coded value, quantity, days supply, and the patient pay and total cost amounts.",
            [bene_id, pde_id, srvc_dt, ndc, qty, days_supply, ptnt_pay, tot_rx], exact="http://hl7.org/fhir/StructureDefinition/MedicationDispense", source=CM)

# ================================================================ the governed records and the audit's location
def governed(key, label, desc, data):
    return C(key, label, f"{desc} The governed record: the data cluster, the PROV activity and agent and the audit event from the ProvGov library by identifier.",
             [data, PG + "prov-activity", PG + "prov-agent", PG + "audit-event"], exact="http://www.w3.org/ns/prov#Entity")

governed("nhanes-participant-governed-record", "NHANES Participant Governed Record", "An NHANES participant record.", nh_participant)
governed("nhanes-medication-governed-record", "NHANES Medication Governed Record", "An NHANES medication record.", nh_medication)
governed("brfss-respondent-governed-record", "BRFSS Respondent Governed Record", "A BRFSS respondent record.", br_respondent)
governed("cms-beneficiary-governed-record", "CMS Beneficiary Governed Record", "A CMS beneficiary summary record.", cms_beneficiary)
governed("cms-inpatient-claim-governed-record", "CMS Inpatient Claim Governed Record", "A CMS inpatient claim record.", cms_inpatient)
governed("cms-outpatient-claim-governed-record", "CMS Outpatient Claim Governed Record", "A CMS outpatient claim record.", cms_outpatient)
governed("cms-prescription-drug-event-governed-record", "CMS Prescription Drug Event Governed Record", "A CMS prescription drug event record.", cms_pde)

leaf("fair-system-identifier", "FAIR Pipeline Identifier", "XdString", "The identifier of the pipeline that created the record from a federal source file (PROV agent identifier; the audit's system id).",
     links=[("skos:exactMatch", "http://www.w3.org/ns/prov#SoftwareAgent", "standard")], constraints={"max_length": 120})
C("fair-source-file", "FAIR Source File", "The federal source file a record was generated from, as the ProvGov PROV entity by identifier: its identifier (the download URL), label (the file name), description (the release) and location. The audit's location.",
  [PG + "prov-entity"], exact="http://www.w3.org/ns/prov#Entity")

# ================================================================ retire list and output
COVER_BY_LABEL = {   # old label -> what covers it now (the shared or study component, the slot, or the NIH CDE)
    "Systolic Blood Pressure": F + "systolic-blood-pressure", "Diastolic Blood Pressure": F + "diastolic-blood-pressure", "Pulse Pressure": F + "blood-pressure",
    "60 sec. pulse (30 sec. pulse * 2)": F + "heart-rate", "60 sec HR (30 sec HR * 2)": F + "heart-rate", "Arm selected": nh_arm, "Coded cuff size": nh_cuff, "MIL: maximum inflation levels (mm Hg)": nh_mil,
    "Total Cholesterol (mg/dL)": "nhanes-total-cholesterol", "Total Cholesterol (mmol/L)": "nhanes-total-cholesterol-si", "Dependent Sequence Number": seqn,
    "Generic drug code": nh_drugid, "Generic or investigational drug name of Medication": nh_drug, "Number of days taken medicine": nh_days, "Taken prescription medicine, past month": nh_rxduse,
    "ICD-10-CM code 1": "nhanes-medication-reason-1", "ICD-10-CM code 2": "nhanes-medication-reason-2", "ICD-10-CM code 3": "nhanes-medication-reason-3", "Prescription Date": "nhanes-medication",
    "Beneficiary Code": bene_id, "Date of Birth": BIRTH_DATE, "Date of Death": F + "deceased-date", "Calculated sex variable": SEX, "Race": RACE_ETH, "End-Stage Renal Disease Indicator": cms_esrd,
    "County Code": cms_county, "Hospital Insurance Coverage Months": cms_hi, "Supplementary Medical Insurance Coverage Months": cms_smi, "HMO Coverage Months": cms_hmo, "Part D Plan Coverage Months": cms_partd,
    "Alzheimer's Disease or Related Disorders": COND["alzheimers-disease"], "Congestive Heart Failure": COND["congestive-heart-failure"], "Chronic Kidney Disease": COND["kidney-disease"], "Cancer": COND["cancer"],
    "Chronic Obstructive Pulmonary Disease": COND["copd"], "Depression": COND["depression"], "Ischemic Heart Disease": COND["coronary-heart-disease"], "Osteoporosis": COND["osteoporosis"],
    "Rheumatoid Arthritis / Osteoarthritis": COND["arthritis"], "Stroke / Transient Ischemic Attack": COND["stroke"],
    "Claim ID": claim_id, "Claim Line Segment": segment, "Claims Start Date": F + "encounter-start", "Claims End Date": F + "encounter-end", "Attending Physician NPI": npi["attending"], "Claim Payment Amount": clm_pmt,
    "Blood Deductible Liability Amount": blood_ddctbl, "Claim Admission Date": admsn_dt, "Beneficiary Discharge Date": dschrg_dt, "Diagnosis Related Group Code": drg, "Claim Pass-Through Per Diem Amount": per_diem,
    "Claim Utilization Day Count": util_days, "Admitting Diagnosis Code (ICD-9-CM)": admitting_dx,
    "Prescription Drug Event ID": pde_id, "Service Date": srvc_dt, "Product/Service ID (NDC)": ndc, "Quantity Dispensed": qty, "Days Supply": days_supply, "Patient Payment Amount": ptnt_pay, "Total Prescription Cost": tot_rx,
    "Age": AGE, "BMI": F + "bmi", "Body Weight": F + "body-weight", "Are you male or female?": SEX, "Are You A Veteran": veteran, "(Ever told) you had diabetes": COND["diabetes"], "(Ever told) you had a depressive disorder": COND["depression"],
    "(Ever told) (you had) skin cancer that is not melanoma?": COND["skin-cancer"], "(Ever told) (you had) melanoma or any other types of cancer?": COND["cancer"], "Avg alcoholic drinks per day in past 30": br_avedrnk,
    "Annual Sequence Number": seqno, "Blind or Difficulty seeing": "brfss-blind-or-difficulty-seeing",
}
for n in range(1, 11):
    COVER_BY_LABEL[f"ICD-9-CM Diagnosis Code {n}"] = f"cms-claim-diagnosis-{n}"
    COVER_BY_LABEL[f"HCPCS Code {n}"] = f"cms-claim-hcpcs-{n}"
for n in range(1, 7):
    COVER_BY_LABEL[f"ICD-9-CM Procedure Code {n}"] = f"cms-claim-procedure-{n}"


def retire_rows():
    rows = []
    for ct, r in OLD.items():
        if r["model"] == "DM":
            continue
        if r["label"].endswith("_units"):
            reason, succ = "not rebuilt: a per-column units leaf of the first build; units are library Units records bound by the quantity", ""
        elif r["label"] in COVER_BY_LABEL:
            succ = COVER_BY_LABEL[r["label"]]
            succ = succ if succ.startswith(("http", "ct:")) else succ
            reason = f"covered by {succ}"
        elif "(duplicate label)" in r["label"]:
            reason, succ = "not rebuilt: a duplicate-label leaf of the first build", ""
        elif r["model"] == "Cluster":
            reason, succ = "superseded by the study's data cluster of the second build", ""
        else:
            reason, succ = "not carried into the second build: a column outside the scope of docs/design/FAIR-Demo-2-PRD.md section 3; the first build's model that composes it stays published", ""
        rows.append({"ct_id": ct, "type": r["model"], "label": r["label"], "reason": reason, "successor_key": succ, "decision": "", "note": ""})
    return rows


def main():
    out = ROOT / "records"
    out.mkdir(exist_ok=True)
    for f in out.glob("*.yaml"):
        f.unlink()
    for key, rec in RECORDS.items():
        (out / f"{key}.yaml").write_text(yaml.safe_dump(rec, sort_keys=False, allow_unicode=True, width=140))
    rows = retire_rows()
    (ROOT / "review").mkdir(exist_ok=True)
    with open(ROOT / "review" / "fair-retire.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ct_id", "type", "label", "reason", "successor_key", "decision", "note"]); w.writeheader(); w.writerows(rows)
    (ROOT / "review" / "kept.json").write_text(json.dumps(KEPT, indent=1, ensure_ascii=False) + "\n")
    slots = sorted({m for r in RECORDS.values() for m in r.get("members", []) if m.startswith("http")})
    shared = sorted(k for k, r in RECORDS.items() if sum(k in x.get("members", []) for x in RECORDS.values()) > 1)
    print(json.dumps({"records": len(RECORDS), "clusters": sum(1 for r in RECORDS.values() if r["type"] == "Cluster"), "cdes": len(KEPT), "retire_rows": len(rows),
                      "covered": sum(1 for r in rows if r["successor_key"]), "library_slots": len(slots), "shared_records": shared}, indent=1))
    print("slots:", " ".join(s.replace("https://axius-sdc.com/library/", "") for s in slots))


if __name__ == "__main__":
    main()
