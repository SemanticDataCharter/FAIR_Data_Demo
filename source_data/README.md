# Source Data Download Instructions

This demo uses public data from three NIH-funded studies. Due to licensing and size, source files are not included in the repository. Follow the instructions below to download them.

## NHANES (National Health and Nutrition Examination Survey)

**Source**: CDC National Center for Health Statistics
**URL**: https://wwwn.cdc.gov/nchs/nhanes/Default.aspx

Download the following datasets from the most recent cycle (2017-2018 or later):

| Dataset | File | Description |
|---------|------|-------------|
| Demographics | DEMO_J.XPT | Demographic variables and sample weights |
| Blood Pressure | BPX_J.XPT | Blood pressure measurements |
| Complete Blood Count | CBC_J.XPT | Complete blood count with differential |
| Cholesterol | TCHOL_J.XPT | Total cholesterol |
| Prescription Medications | RXQ_RX_J.XPT | Prescription medication use |
| Medical Conditions | MCQ_J.XPT | Medical conditions questionnaire |
| Smoking | SMQ_J.XPT | Smoking - cigarette use |
| Physical Functioning | PFQ_J.XPT | Physical functioning |

Place downloaded files in `source_data/nhanes/`.

## ADNI (Alzheimer's Disease Neuroimaging Initiative)

**Source**: ADNI Data Sharing Portal (requires free registration)
**URL**: https://adni.loni.usc.edu/data-samples/access-data/

After registration and approval:

1. Navigate to "Download" > "Study Data" > "ALL"
2. Download the following CSV files:

| Dataset | File | Description |
|---------|------|-------------|
| Demographics | PTDEMOG.csv | Participant demographics |
| Vital Signs | VITALS.csv | Vital signs measurements |
| Lab Data | LABDATA.csv | Laboratory test results |
| Biospecimens | BIOMARK.csv | Biospecimen collection |
| Medications | CONMED.csv | Concomitant medications |
| Adverse Events | ADVERSE.csv | Adverse events |
| Cognitive Tests | ADSC_ADASSCORES.csv | ADAS-Cog scores |
| Medical History | MEDHIST.csv | Medical history |

Place downloaded files in `source_data/adni/`.

## SPRINT (Systolic Blood Pressure Intervention Trial)

**Source**: NHLBI BioLINCC (requires free registration and DUA)
**URL**: https://biolincc.nhlbi.nih.gov/studies/sprint/

After data use agreement approval:

1. Download the SPRINT data package
2. Extract the following CSV files:

| Dataset | File | Description |
|---------|------|-------------|
| Baseline | bl_baseline.csv | Baseline demographics and characteristics |
| Blood Pressure | bp.csv | Blood pressure measurements over time |
| Labs | labs.csv | Laboratory results |
| Medications | meds.csv | Medication records |
| Adverse Events | ae.csv | Adverse events |
| Cognitive Function | cog_moca.csv | MoCA cognitive assessment |
| Medical History | medhx.csv | Medical history |

Place downloaded files in `source_data/sprint/`.

## After Downloading

Run the conversion pipeline:

```bash
python datagen/convert_all.py
```

This converts all source data to validated SDC4 XML instances in `app/import_data/`.
