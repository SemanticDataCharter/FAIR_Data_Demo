# FAIR Data Demo

[![CI](https://github.com/SemanticDataCharter/FAIR_Data_Demo/actions/workflows/ci.yml/badge.svg)](https://github.com/SemanticDataCharter/FAIR_Data_Demo/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/SemanticDataCharter/FAIR_Data_Demo)](https://github.com/SemanticDataCharter/FAIR_Data_Demo/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![SDC4](https://img.shields.io/badge/SDC4-Compliant-teal.svg)](https://semanticdatacharter.com)

**Three federal health studies, one component library, and a cross-study question that is a join on the component.**

This is version 4.2.0 ([releases](https://github.com/SemanticDataCharter/FAIR_Data_Demo/releases)), the second build of the FAIR Data Demo and the first in which the studies actually share their components. It takes three real federal releases, the CDC's NHANES 2017-2018 and BRFSS 2022 surveys and the CMS DE-SynPUF Medicare claims sample, and models each as [SDC4](https://semanticdatacharter.com) data models composed from the published component libraries: the person, gender and money from the Default library, race, age, education, marital status and insurance from the NIH CDE library, blood pressure, vital signs, laboratory results, encounters, coverage and medication orders from the FHIR library, provenance and audit from the ProvGov library, each named by its identifier slot. What the studies share and no library holds, smoking status, twenty-one chronic-condition indicators with their SNOMED CT subjects, general health, veteran status, is authored once in this project with LOINC and SNOMED CT links, and every study that measures the concept composes the same one. What one study alone needs stays that study's, coded as it was recorded: ICD-9-CM, HCPCS and NDC for the 2008-2010 claims, the survey identifiers, weights, strata and the agencies' own codes beside every harmonized value.

The seven models and the seven applications SDCStudio generated from them are in the repository exactly as downloaded, under `sdcstudio_downloads/`, so anyone who clones can read the raw models and apps before reading anything we wrote around them. The data is not invented: every record is generated from a row of the federal file by the template engine, validated on the way out against the model's XSD 1.1 schema, and states where it came from. Alongside its data each record carries its **Provenance** (the PROV-O activity that made it, whose used entity is the federal file by URL and release, and the pipeline as agent), an **Audit Event**, and a structural **Audit** naming the system and the source file, bound to the data at the source rather than bolted on afterward. The record's subject is the study's own participant identifier, so a reviewer can trace any value to its row.

## Two guides, depending on why you are here

- **[What to look at, and what to ask](app/sdc4/docs/FOR-DECISION-MAKERS.md)**: a fifteen minute walk-through for the person who signs. No technical background assumed.
- **[For the people who run it](app/sdc4/docs/FOR-IT-STAFF.md)**: what is generated, how one record becomes three projections, how a refused answer is handled, and the operational notes we learned the hard way.

## Run it locally

You need Docker (or Podman) with the compose plugin, about 10GB of free RAM (GraphDB and SirixDB take 4GB each), Python 3.12 on the host (for data generation only), and the three federal source files, which are free to download without registration. Then:

```bash
git clone https://github.com/SemanticDataCharter/FAIR_Data_Demo.git
cd FAIR_Data_Demo
git checkout v4.2.0
# download the source files into source_data/ (see source_data/README.md), then
python3 -m pip install pyreadstat pandas
python3 scripts/convert_xpt_to_csv.py     # NHANES and BRFSS ship as SAS transport files
make demo
```

`git checkout v4.2.0` pins the release this README describes; skip it to run the current `main`. Every release also publishes the web image as `ghcr.io/semanticdatacharter/fair-data-demo:<version>`, and `make pull` fetches it instead of building locally.

`make demo` starts the stack, generates the sampled dataset from the source files, and loads it. There are no accounts to create and nothing to send anywhere. The first run needs the network to pull container images and the host-side Python packages; after that the stack runs disconnected. When it finishes there are two front doors:

| Open | What it is |
|---|---|
| **http://localhost:18100/console/** | The record console. Seven models, one record shown as table, document and graph, and the governance behind every field. Start here. |
| **http://localhost:18100/demo/** | The dashboard, the "Three Studies, One Component" walk-through, and the SPARQL explorer. Every result has a **Graph** tab: the records behind the rows as nodes, every subject identifier two of them share drawn as a node between them, and every component two studies compose drawn as a node the records of both studies meet at, labelled with each record's value. Click a record to open it in the console. |

### Check it worked

The generators are seeded, so every run on every machine produces the same records from the same rows. Only the record timestamps move. The console front page should show:

| | Expected |
|---|---|
| Records loaded | **84,352** |
| Named graphs in GraphDB | **84,352** (one per record, no drift; the loader prints the count per model, and a `COUNT(DISTINCT ?g)` over `GRAPH ?g` in the explorer confirms it) |
| Models | **7** |
| Records stating an absence | **0** |

That last row is different from the CordovaOS demonstration, and deliberately so. Every leaf in these seven models is optional, because a survey row can lack any answer: NHANES codes a refusal as 7 and a don't-know as 9, BRFSS as 7 and 9 or 77 and 99, and CMS leaves the field blank. The generators leave those out of the record and count them, so no 7 is ever averaged as if it were an answer, and the counts are printed when the dataset is generated (`make generate`). Where a model requires a value and the row has none, the record would carry an ISO 21090 null flavor naming the reason and fail validation on purpose; no model here requires one, so no record does.

### Choose your dataset

Generation takes about three minutes; **loading is the cost**: each instance is validated against its XSD 1.1 schema, then written to PostgreSQL and projected into GraphDB as its own named graph.

| Command | Dataset | Records | Load time |
|---|---|---|---|
| `make demo` (default) | every NHANES participant and medication row, a seeded sample of 5,000 BRFSS respondents, a seeded sample of 1,000 CMS beneficiaries with every one of their claims and prescription events | 84,352 | about 107 minutes on a laptop, on the batch path (measured: 106.6 minutes, 0 failed) |
| `make demo-full` | every row of every file | about 7.0 million | days at the measured rate; it is there so a reader can see the generators handle every row, not as a target for a laptop |

| Model | Source rows | Records in `make demo` |
|---|---|---|
| NHANES Participant | DEMO_J joined on SEQN with BPX_J, TCHOL_J, CBC_J, MCQ_J, SMQ_J, PFQ_J | 9,254 |
| NHANES Medication | RXQ_RX_J rows naming a medicine (5,343 rows without one are skipped) | 14,300 |
| BRFSS Respondent | LLCP2022, sampled | 5,000 |
| CMS Beneficiary | 2008 beneficiary summary, sampled | 1,000 |
| CMS Inpatient Claim | 2008-2010 inpatient claims of the sampled beneficiaries | 585 |
| CMS Outpatient Claim | 2008-2010 outpatient claims of the sampled beneficiaries | 6,933 |
| CMS Prescription Drug Event | 2008-2010 Part D events of the sampled beneficiaries | 47,280 |

The CMS sample is 1,000 beneficiaries rather than 5,000 because the claims and events come with them: 5,000 beneficiaries carry about 290,000 records, which loads for hours; 1,000 carry about 57,000. `SAMPLE` in `datagen/shared.py` sets both sample sizes.

## The seven models

All seven applications were generated by [SDCStudio](https://sdcstudio.axius-sdc.com/) from the published models. Nobody wrote seven Django apps. The models compose the libraries by identifier slot, and add only what the study alone defines.

| Model | Composes from the libraries | Shared FAIR components | Study-local |
|---|---|---|---|
| **NHANES Participant** | Default person demographics; NIH CDE race/ethnicity, age, education, marital status, income, pregnancy; FHIR blood pressure and vital signs (first reading, pulse), laboratory results (total cholesterol, WBC, RBC, hemoglobin, hematocrit, platelets) | smoking status, chronic conditions (told by a health professional), general health, physical function | SEQN, cycle, interview and exam weights, PSU, stratum, income-to-poverty ratio, the agency's own codes |
| **NHANES Medication** | FHIR medication order (name), FHIR condition for up to three reasons (ICD-10-CM, as NHANES codes them) | | SEQN, the NHANES drug identifier, days taken, count |
| **BRFSS Respondent** | NIH CDE race/ethnicity, sex, age, education, marital status, income, insurance, employment, pregnancy; FHIR vital signs (self-reported height, weight, BMI) | smoking status, alcohol use, chronic conditions (told by a health professional), general health, physical function and disability, exercise, veteran status | SEQNO, state, interview date, weight, PSU, stratum, the agency's calculated variables |
| **CMS Beneficiary** | Default date of birth and gender; FHIR patient deceased date and insurance coverage; NIH CDE race; Default money for the annual amounts | chronic conditions (found in claims) | DESYNPUF_ID, state and county codes, ESRD indicator |
| **CMS Inpatient Claim** | FHIR encounter and hospitalization; Default money for payment, deductible, coinsurance, per diem | | claim identifier, provider and physician identifiers, utilization days, DRG; ICD-9-CM diagnoses and procedures and HCPCS as coded values |
| **CMS Outpatient Claim** | the same shape without hospitalization | | the same |
| **CMS Prescription Drug Event** | FHIR medication order (quantity, days supply); Default money for patient pay and total cost | | event identifier, service date, NDC as a coded value |

Every model carries the same governance envelope: the ProvGov activity, agent and audit event beside the data, and the FAIR Pipeline Audit in the audit slot. No model binds a workflow: a survey response has no state machine, and the demonstration does not stage one.

### The join is the component

Where two studies mean the same thing, their models compose the *same published component*, not two local conventions that a mapping table later reconciles. Measured on the loaded store by the console's first question, which asks GraphDB directly which components records of more than one model carry:

| Component | Studies carrying it | Records |
|---|---|---|
| Administrative Gender | BRFSS, CMS, NHANES | 15,254 |
| Condition Indicator Basis | BRFSS, CMS, NHANES | 14,897 |
| Race/Ethnicity Self-Identification | BRFSS, CMS, NHANES | 14,438 |
| Condition: Stroke | BRFSS, CMS, NHANES | 11,544 |
| Condition: Cancer | BRFSS, CMS, NHANES | 11,539 |
| Condition: COPD | BRFSS, CMS, NHANES | 11,532 |
| Condition: Arthritis | BRFSS, CMS, NHANES | 11,513 |
| Condition: Coronary Heart Disease | BRFSS, CMS, NHANES | 11,492 |
| Age | BRFSS, NHANES | 14,254 |
| Condition: Asthma | BRFSS, NHANES | 13,863 |
| Observation Status | BRFSS, NHANES | 11,420 |
| Veteran Status | BRFSS, NHANES | 10,925 |
| Condition: Heart Attack | BRFSS, NHANES | 10,516 |
| Marital Status | BRFSS, NHANES | 10,495 |
| Smoking Status | BRFSS, NHANES | 10,457 |
| Condition: Congestive Heart Failure | CMS, NHANES | 6,552 |
| Condition: Diabetes | BRFSS, CMS | 5,988 |
| Condition: Depression | BRFSS, CMS | 5,969 |
| Condition: Kidney Disease | BRFSS, CMS | 5,967 |
| Are you pregnant now? | BRFSS, NHANES | 1,980 |

20 components are carried by more than one study, 8 of them by all three. Another 18 are shared between one study's own models (the CMS claim fields both claim models carry, the beneficiary identifier every CMS record carries, the NHANES participant identifier), which is also true and also visible.

Counted from the records in the triple store, not from a README. The console page prints the query beside the answer. The first visit after a load computes it, which takes about two minutes over 33 million triples; the answer is cached until the next load. The study-local components (the CMS claim codes, the survey weights, NHANES's drug identifier) are carried by one study each, which is also true and also visible.

## Three Studies, One Component

The walk-through at `/demo/narrative/` runs six beats, each answered by one of the saved queries against the shared store:

1. **The audit: what the studies share.** The table above, computed.
2. **Smoking status, two questionnaires, one component.** NHANES and BRFSS ask different questions; both records carry the same LOINC 72166-2 answer set in the same component.
3. **Blood pressure: what was measured and what was asked.** NHANES measured it with a cuff, in FHIR's systolic and diastolic components; BRFSS 2022 did not ask, and the query says so instead of finding a substitute.
4. **Chronic conditions, and the basis each study has for them.** Twenty-one indicators, one component each; the record says whether a health professional said so or a claim was paid for it.
5. **Medications: where the join does not exist, and why.** NHANES names the drug and carries its own identifier; CMS carries an NDC. Neither is RxNorm, so the two do not join, and the page says that rather than staging it.
6. **Demographics side by side.** Gender on the Default component, race and ethnicity on the NIH CDE component, by study.

## SPARQL queries

Six pre-built queries in `sparql/` run against the store the seven applications project, one named graph per record. Each anchors on a published component by its `ct_id` or its label, and the join across studies is the component itself.

| # | Query | Studies |
|---|---|---|
| 1 | Shared component audit | NHANES, BRFSS, CMS |
| 2 | Smoking status by study | NHANES, BRFSS |
| 3 | Blood pressure by study | NHANES, BRFSS |
| 4 | Chronic conditions by study and basis | NHANES, BRFSS, CMS |
| 5 | Medication coding by study | NHANES, CMS |
| 6 | Demographics side by side | NHANES, BRFSS, CMS |

Every query was run against the loaded store before this release; [sparql/README.md](sparql/README.md) has what each returned. The console's cross-study page at `/console/question/` runs the audit and the chronic-condition question with the query printed beside the answer.

## How it was built

The curation is in this repository as code, the way the component libraries themselves are built:

1. `build/author.py` writes the 266 component records (81 tokens, 70 clusters, 49 quantities, 23 strings, 22 counts, 14 units, 4 temporals, 3 links), each with its source, its definition, and its links: 101 `skos:exactMatch` and 41 `skos:closeMatch` to LOINC, SNOMED CT and the agencies' codebooks, 22 `dcterms:subject` SNOMED CT conditions, 152 `rdfs:seeAlso`. Members are composed by identifier slot (`https://axius-sdc.com/library/<library>/<key>`) or by `ct_id` for the NIH CDE library, which has no slot.
2. `review/fair.csv` is the human review of every record; nothing loads without an accept.
3. `load_component_records` on SDCStudio loads the bundles into the production project **FAIR Data Demo** and publishes them; the seven data models are assembled from the published components with the governance envelope; packages and applications are generated and downloaded verbatim into `sdcstudio_downloads/`.
4. `datagen/` generates the records: one generator per model names the facts a row has by their label path in the published model, and `datagen/engine.py` fills the model's own instance template, drops what was not given, and refuses a value of a shape the schema does not allow. No generator carries an element identifier or an XML envelope.
5. The stack is the CordovaOS 4.4.0 skeleton with the seven generated applications merged in and the loader on the batch path.

The project's components from the first build, 976 of them and eight models, stay published and are retired with a reason naming the successor slot or the reason the column was not carried forward. Nothing anyone downloaded stops resolving; `models-4.2.0.json` records every new model's `wasRevisionOf`.

## The first build, as history

The first build (March 2026) ran the SDC_Agents pipeline over the same three studies: introspect the files, discover catalog matches, enrich the sparse federal metadata (about 2,000 lines of codebook parsing in `scripts/enrichment/`, kept as the record of what that took), assemble models by API, and download them. It published 976 components across eight models, and found what this build is built on: the agencies' metadata was too thin for an agent to say that two columns measured the same concept, so each study minted its own components and the studies shared none. The cross-study queries were kept as a specification and the README said so.

That is the finding: the join across studies is a modelling decision a person makes, not a match an agent guesses. This build makes it as reviewed records, once, and every study composes the result. The pipeline scripts and `sdc-agents.yaml` remain in the repository as what the first build did; they are not part of `make demo`.

## What this demonstration does not show

- **Medications do not join across studies.** NHANES carries the drug name and its own identifier; CMS carries an NDC. An RxNorm mapping of both would make the join, and neither source ships one. Beat 5 shows the gap instead of hiding it.
- **Education and income are not harmonized.** The NIH CDE lists (24 education levels by grade and degree; income bands) do not nest with the NHANES and BRFSS bands, so those models carry the agency's own codes only, beside the harmonized values where nesting was clean (gender, race and ethnicity, marital status, pregnancy, smoking, the conditions).
- **BRFSS 2022 has no blood pressure or cholesterol history.** Those modules were not in the 2022 core questionnaire, so beat 3 compares NHANES's measurements with what BRFSS asked, which is nothing.
- **The CMS claims are coded as recorded.** Diagnoses and procedures are ICD-9-CM, procedures on lines are HCPCS; nothing is mapped to ICD-10-CM or CPT. Codes that do not match the code system's pattern in the slot the file put them in are left out and counted (244 procedure slots in the inpatient sample carry diagnosis-shaped codes).
- **There is no person-level join across studies.** The three populations are different people. The join is the component, and the graph draws it as one.
- **The CMS data is synthetic.** DE-SynPUF is CMS's synthetic public use file, built to have the shape of Medicare claims without any beneficiary in it. NHANES and BRFSS are real, de-identified survey releases.
- **BRFSS columns outside the curated set are not carried.** LLCP2022 has 326 columns; the model carries the demographics, health status, conditions, substance use, disability and survey design columns the design names, with the agency's calculated variables.

## If something goes wrong

| Symptom | Cause and fix |
|---|---|
| `make demo` hangs at "Waiting for the web app" | First run migrates the database and initialises the GraphDB repository, which takes 1-2 minutes. If it exceeds five, check `docker compose -f app/sdc4/docker-compose.yml logs web`. |
| `make generate` fails on a missing file | The source files are not in the repository. `source_data/README.md` lists each one with its download page; NHANES and BRFSS need `scripts/convert_xpt_to_csv.py` run once after download. |
| SirixDB exits with "Realm does not exist" | Keycloak did not import the realm SirixDB authenticates against, `app/sdc4/mediafiles/keycloak/import/sirixdb-realm.json`. It is in the repository; if the directory was created root-owned by an earlier container start, fix its ownership and recreate Keycloak. |
| Ports already in use | The stack binds 18100 (web), 17300 (GraphDB), 18081 (Keycloak), 15433 (PostgreSQL), 16380 (Redis), 19444 (SirixDB). Each is overridable by environment variable (`WEB_PORT`, `GRAPHDB_PORT`, `KEYCLOAK_PORT`, `DB_PORT`, `REDIS_PORT`, `SIRIX_PORT`) rather than by editing the compose file. |
| Containers die or the load stalls | GraphDB wants headroom. Give Docker about 10GB of RAM; GraphDB runs with a 4GB heap and is the first to fail without it. |
| Record count is right, named graph count is higher | Orphaned graphs from a previous load. Each load mints new instance identifiers, so `--clear` must clear both stores. Re-run `make demo`, which passes `--clear`. |
| Records show as invalid that should be valid | Schema resolution went to the network and failed. Every data model schema includes `sdc4.xsd` by URL; an OASIS catalog at `app/sdc4/mediafiles/dmlib/catalog.xml` resolves it locally instead. A warning in the load output names it if the catalog was missed. |

**Air-gapped evaluation.** Once the images are pulled and `make demo` has run, the stack needs no outbound network. Unplug and reload: validation falls back to the local schema and every page still renders.

## Repository structure

```
FAIR_Data_Demo/
├── app/sdc4/                    # the stack: settings, compose, loader, console, demo, the seven generated apps
│   ├── mediafiles/dmlib/        # the published model per app (XSD, instance template, RDF, JSON-LD, HTML)
│   └── docs/                    # the two guides
├── build/                       # the curation as code: author.py, convert, bundle, chunk, the one-offs
├── datagen/                     # the template engine and one generator per model; tests
├── records/                     # the 266 component records, as reviewed
├── review/                      # the review sheets (every record accepted, every first-build record retired)
├── sdcstudio_downloads/         # the seven model packages and generated apps, verbatim
├── sparql/                      # the six cross-study queries and what they returned
├── source_data/                 # the federal files (not committed; README says where)
├── scripts/                     # convert_xpt_to_csv.py, and the first build's pipeline as history
└── models-4.2.0.json            # every model's ct_id and what it revises
```

## Related projects

- [SDCStudio](https://sdcstudio.axius-sdc.com/): the platform the models were built and published on
- [CordovaOS](https://github.com/Axius-SDC/CordovaOS): the same stack for a fictional nation's ten government domains
- [SDCRM](https://github.com/SemanticDataCharter/SDCRM): the SDC Reference Model specification
- [SDC_Agents](https://github.com/Axius-SDC/SDC_Agents): the agents the first build ran

## License

Apache 2.0, see [LICENSE](LICENSE).

Built by [Axius SDC, Inc.](https://axius-sdc.com)
