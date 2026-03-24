# Source Data Download Instructions

This demo uses public data from three federal health studies. All source data is freely downloadable with no registration. Due to size, source files are not included in the repository. Follow the instructions below to download them.

## NHANES (National Health and Nutrition Examination Survey)

**Source**: CDC National Center for Health Statistics
**URL**: https://wwwn.cdc.gov/nchs/nhanes/Default.aspx
**Access**: Direct download, no registration

Download the following datasets from the 2017-2018 cycle:

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

## BRFSS (Behavioral Risk Factor Surveillance System)

**Source**: CDC
**URL**: https://www.cdc.gov/brfss/annual_data/annual_2022.html
**Access**: Direct download, no registration

On the 2022 Annual Survey Data page, scroll to the **Data Files** section and download:

> **2022 BRFSS Data (SAS Transport Format)** [ZIP, ~64 MB]

This is the combined landline and cell phone dataset exported as a SAS V9.4 XPT transport file. The ZIP contains a single file named `LLCP2022.XPT` (326 variables, ~445K records).

After downloading:

1. Unzip the file
2. Place `LLCP2022.XPT` in `source_data/brfss/`

| What to download | Filename inside ZIP | Description |
|------------------|---------------------|-------------|
| 2022 BRFSS Data (SAS Transport Format) | LLCP2022.XPT | Combined landline + cell phone, 326 variables |

## CMS DE-SynPUF (Medicare Claims Synthetic Data)

**Source**: CMS (Centers for Medicare & Medicaid Services)
**Access**: Direct download, no registration

The DE-SynPUF is a synthetic (not real patient) dataset modeled on Medicare claims. We use **Sample 1 only** (there are 20 samples; any one is sufficient for the demo).

### How to download

1. Go to the [DE-SynPUF main page](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf)
2. Click **"DE1.0 Sample 1"** to reach the [Sample 1 download page](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1)
3. Download these four ZIP files (each contains one CSV):

| Link text on the page | CSV inside the ZIP | Description |
|-----------------------|-------------------|-------------|
| DE1.0 Sample 1 **2008 Beneficiary Summary** File | `DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv` | Demographics and chronic conditions |
| DE1.0 Sample 1 2008-2010 **Inpatient Claims** | `DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv` | Inpatient hospital claims |
| DE1.0 Sample 1 2008-2010 **Outpatient Claims** | `DE1_0_2008_to_2010_Outpatient_Claims_Sample_1.csv` | Outpatient facility claims |
| DE1.0 Sample 1 2008-2010 **Prescription Drug Events** | `DE1_0_2008_to_2010_Prescription_Drug_Events_Sample_1.csv` | Part D prescription claims |

4. Unzip all four files
5. Place the four CSV files in `source_data/cms/`

**Note**: The page also lists 2009 and 2010 Beneficiary Summary files and a Carrier Claims file. You do not need those for this demo; only the four files above.

## After Downloading

### Step 1: Convert XPT files to CSV

NHANES and BRFSS data is distributed as SAS transport (.XPT) files. Convert to CSV before running the pipeline:

```bash
pip install pyreadstat
python scripts/convert_xpt_to_csv.py
```

This creates `.csv` files alongside the `.XPT` files and `.json` sidecar files containing column descriptions, value labels, and enumerations. The script is idempotent; it skips files that have already been converted.

CMS data is already in CSV format and needs no conversion.

### Step 2: Run the SDC Agents Pipeline

```bash
pip install -r requirements-pipeline.txt
export SDCSTUDIO_URL=http://localhost:8000
export SDC_API_KEY=your-api-key

python scripts/run_pipeline.py --study all
```

This introspects all datasources, discovers reusable catalog components, and assembles data models in SDCStudio. See `scripts/run_pipeline.py --help` for step-by-step options.

### Step 3: Generate XML Instances

After models are approved in SDCStudio:

```bash
python scripts/generate_instances.py --study all --validate
```

This generates validated XML instances in `output/instances/`.
