# FAIR Data Demo, second build: the three studies on the component libraries

**Status:** APPROVED 2026-09-26 (Tim's answers in §6: public repo; seven models; shared FAIR components; ProvGov audit; no workflow; ICD-9-CM stays; the samples; **a complete stack like CordovaOS**, table, document and graph views, the engine copied in; version 4.2.0).  
**Method:** the same as the five library rebuilds and CordovaOS 4.4.0. Inventory from the production export, never from a job log. Supersede and retire, never delete. Curation as code in a repository, loaded by `load_component_records`, models by one-off, apps by `generate_app`, instances by the template engine, everything measured on the release commit.

## 0. Why

The demo's headline claim was that three federal studies reference the same component for the same concept, so a cross-study question is a join on `ct_id` with no mapping table. The first build did not realize it: the agents could not match concepts across the studies' sparse metadata, each study minted its own components, and the README was reframed on 2026-07-25 to say so. The six SPARQL queries were kept as a specification and never ran, because they use a vocabulary (`sdc4:Component`, `sdc4:domain`, `sdc4:study`) that no generated RDF carries.

What was missing in March is what September built: five component libraries, each composing the others by identifier slot. The FHIR library carries the vital signs panel, the condition, the medication order, the laboratory result, the encounter and the insurance coverage. The NIH CDE library carries the endorsed demographics: race, ethnicity, sex at birth, age, educational attainment, marital status, household income, health insurance, standing height, measured weight, date of birth. The Default library carries person demographics, money, addresses. The ProvGov library carries the provenance every record should state, including which federal file a row came from. A study model that composes those by slot shares the component with every other study that composes it, and the join the demo exists to show becomes a fact of the models rather than a hope about an agent.

## 1. Facts (inventory 2026-09-26, `docs/design/inventory/`)

Production project **FAIR Data Demo**: 976 published components, all published, none retired: 368 `Units`, 312 `XdQuantity`, 218 `XdString`, 56 `XdCount`, 12 `Cluster`, 8 `DM`, 2 `XdBoolean`.

| Model (DM `ct_id`) | Components | What it is |
|---|---|---|
| BRFSS — Brfss (`ffq1c2tkbzexmxqnrxg48oqj`) | 521 | every one of the 326 LLCP2022 columns as its own leaf, 186 of them quantities with a `<VAR>_units` component each |
| CMS — Beneficiary (`q9xk7y13y2115tr4sn2c7m39`) | 58 | the 2008 beneficiary summary |
| CMS — Inpatient (`ra4tn4wzsu2rlbk5dineab5g`) | 103 | claims header, 10 ICD-9-CM diagnosis slots, 45 HCPCS slots |
| CMS — Outpatient (`k6f8kugg359vc6ew75ulojg9`) | 104 | the same shape; 19 components carry "(duplicate label)" |
| CMS — Prescriptions (`dg6lyhgvz9wd9cuqxqdc5g4p`) | 17 | part D events |
| NHANES — Blood Pressure (`r3gyip9ebl7ockdpj4kwabjo`) | 20 | BPX_J |
| NHANES — Cholesterol (`s70cbgpe2gqfmpund4vvwyi5`) | 7 | TCHOL_J |
| NHANES — Medications (`g72xhdxvd7q53qnxx6dsczg5`) | 15 | RXQ_RX_J |

Shared across studies: **0 components**. Ontology links: 85 curated LOINC and SNOMED CT mappings, none of which made two studies share a component. Structure: every model is one flat cluster of leaves; 368 of the 976 components are per-column `_units` XdStrings; nine model titles carry an em dash. No NHANES demographics, CBC, conditions, smoking or physical-function model was published (the assembly calls for those files returned 400). Instances: none in the repository; `generate_instances.py` produced at most 100 rows per source through SDC_Agents and wrote them outside the repo.

Source data on disk (`source_data/`, downloaded, not committed): NHANES 2017–2018 DEMO_J (9,254 participants, 46 columns), BPX_J, CBC_J, TCHOL_J, RXQ_RX_J (19,643 medication rows), MCQ_J, SMQ_J, PFQ_J; BRFSS LLCP2022 (445,132 respondents, 328 columns); CMS DE-SynPUF sample 1: beneficiary summary (116,352), inpatient claims (66,773), outpatient claims (790,790), prescription drug events (5,552,421).

What the libraries now hold for these studies (active, by identifier slot):

| Concept | Library component (slot) |
|---|---|
| Person: birth date, administrative gender, language, country | Default `person-demographics` (in FHIR `patient`) |
| Race, Ethnicity, Race/Ethnicity Self-Identification | NIH CDE `Fakc6Jy2x`, `PtRlg7yLP_`, `LakF0YkywC` |
| Sex at Birth | NIH CDE `rGEh0ckdmr` |
| Age (years or months) | NIH CDE `PDjBiGXjO` |
| Current Educational Attainment, Marital Status, Annual Household Income Range | NIH CDE `Co2d1RyYS3`, `C6SezX_mKG`, `_N_myh18QM` |
| Health Insurance, Category of Health Insurance, Employment Status, pregnancy | NIH CDE `e4Dng_5sU66`, `cPiK4Amjn5`, `RME88_Wg_hV`, `LiUWCWluP` |
| Standing Height, Measured Weight | NIH CDE `e_4BbhlpUx`, `fKMleOU9K2` |
| Blood pressure (systolic, diastolic, site, status, time), vital signs panel (BMI, heart rate, height, weight) | FHIR `blood-pressure`, `vital-signs-panel` |
| Laboratory result (LOINC result code, value, units, status, time) | FHIR `laboratory-result` |
| Condition (ICD-10-CM and SNOMED CT coded, status, onset) | FHIR `condition` |
| Medication order (RxNorm coded, status, dose, date) | FHIR `medication-order` |
| Encounter, hospitalization (admit source, discharge disposition) | FHIR `encounter`, `hospitalization` |
| Insurance coverage, cost sharing | FHIR `insurance-coverage`, `cost-sharing` |
| Procedure (CPT coded) | FHIR `procedure`, `procedure-cpt` |
| Money | Default `money` (USD is ISO 4217, so amounts are real currency here) |
| Provenance activity and agent, audit event, workflows | ProvGov |

What no library holds and the three studies all measure: smoking status; the self-reported "ever told you had" chronic-condition indicators (asthma, arthritis, COPD, kidney disease, depression, diabetes, cancer, stroke, heart disease); alcohol use; the physical-function and disability items; general health status. And what one study alone needs: ICD-9-CM diagnosis codes and HCPCS procedure codes (CMS 2008–2010), NDC product codes (CMS part D), NHANES's own drug identifier, DRG codes, survey design fields (SEQN, SEQNO, DESYNPUF_ID, weights, PSU, strata).

## 2. Rules

**Supersede, never unpublish.** The eight models and 976 components stay published; each is retired with a reason naming its successor or the slot that replaced it. Nothing anyone downloaded stops resolving.

**Compose by slot; the join is the component.** Where a library component measures the concept, the study model composes it by identifier slot and adds nothing. Three studies composing FHIR's `blood-pressure` carry the same `systolic-blood-pressure` component, and query 3 is a join. The libraries decide the vocabulary: NIH CDE's race list, FHIR's ICD-10-CM diagnosis, RxNorm medication.

**What the studies share and no library holds becomes a shared FAIR component, once.** Smoking status, the chronic-condition indicators, alcohol use, general health, the physical-function items are authored once in this project as FAIR components with `skos:exactMatch` to LOINC or SNOMED CT (smoking status LOINC 72166-2; "ever told you had diabetes" LOINC 45912-6 and its kin), and every study that measures the concept composes the same one. That is the canonicalization the July README said had to be done by people: here it is done as records a person reviewed, not as an agent's guess.

**What one study alone needs stays study-local, coded honestly.** ICD-9-CM, HCPCS, NDC and DRG are Coded Value clusters (code, display text, code-system link) owned by this project, because the FHIR library carries ICD-10-CM and CPT and neither is what CMS 2008–2010 recorded; a claim's diagnosis is not silently promoted to a code system it was not coded in. NHANES's drug identifier stays NHANES's, beside the drug name.

**Survey design is data, not junk.** Participant and respondent identifiers, sample weights, PSU and stratum are components with the agency's definition, because a reader who wants a weighted estimate needs them and the first build threw them in with everything else.

**A fact a row lacks is left out.** NHANES codes "refused" and "don't know" as 7 and 9; BRFSS as 7 and 9 or 77 and 99; CMS leaves fields blank. Those become stated absences (`ASKR`, `ASKU`, `NI`) where the schema requires a value and omissions where it does not; never a 7 that averages.

**One person is one record.** NHANES joins its files on SEQN: one participant record carries demographics, blood pressure, cholesterol, CBC, conditions, smoking and physical function; medications are one record per medication row. BRFSS is one respondent record. CMS is one beneficiary record and one record per claim and per prescription event, joined on the beneficiary identifier, which is a component.

**Every record states where it came from.** The ProvGov activity's used entity is the federal file (its URL and release), the agent is this pipeline, and the record's subject is the participant identifier, so a reviewer can trace any value to its row.

## 3. Scope: seven models on the libraries

| Model | Composes | Study-local |
|---|---|---|
| **NHANES Participant** | D `person-demographics` (gender, birth country); N `Race/Ethnicity Self-Identification`, `Age`, `Current Educational Attainment`, `Marital Status`, `Annual Household Income Range`, pregnancy; F `blood-pressure` (first reading; pulse as `heart-rate` in the `vital-signs-panel`); F `laboratory-result` × total cholesterol (2093-3), WBC, RBC, hemoglobin, hematocrit, platelets; FAIR smoking status, chronic-condition indicators (asthma, arthritis, CHF, CHD, angina, heart attack, stroke, emphysema, COPD, liver condition, cancer), physical-function items, general health | SEQN, survey cycle, interview and exam weights, PSU, stratum, income-to-poverty ratio, blood pressure cuff and arm (NIH CDE has `Blood Pressure Cuff Size` retired; check) |
| **NHANES Medication** | F `medication-order` (name; RxNorm where NHANES's Lexicon maps, else text), F `condition` × up to 3 reasons (ICD-10-CM, which NHANES codes) | SEQN, NHANES drug identifier, days taken, count |
| **BRFSS Respondent** | N `Race/Ethnicity`, `Sex at Birth` (as BRFSS records sex), `Age`, `Current Educational Attainment`, `Marital Status`, `Annual Household Income Range`, `Health Insurance`, `Employment Status`, pregnancy; F `vital-signs-panel` (self-reported height, weight, BMI); FAIR smoking status, alcohol use, chronic-condition indicators, general health, physical-function and disability items, exercise | SEQNO, state, interview date, weights (_LLCPWT), PSU, stratum, the calculated variables the agency publishes (_BMI5CAT, _SMOKER3, _RFHYPE6) as tokens with the agency's definitions |
| **CMS Beneficiary** | D `person-demographics` (birth date, gender, deceased date via F `patient`), N `Race`; F `insurance-coverage` (parts A, B, HMO, D coverage months as coverage periods or counts); D `money` × annual reimbursement and responsibility amounts; FAIR chronic-condition indicators × 11 (SP_ALZHDMTA … SP_STRKETIA, the same components NHANES and BRFSS compose for the self-reported ones, with the CMS definition "claims-based") | DESYNPUF_ID, state and county codes, ESRD indicator |
| **CMS Inpatient Claim** | F `encounter` + `hospitalization` (admission, discharge, DRG as study-local), D `money` × payment, deductible, coinsurance, per diem; FAIR ICD-9-CM diagnosis (admitting + up to 10) and procedure (up to 6), HCPCS (up to 45) as Coded Value clusters | DESYNPUF_ID, claim id, segment, provider number, physician NPIs, utilization days |
| **CMS Outpatient Claim** | the same shape without hospitalization | the same |
| **CMS Prescription Event** | F `medication-order` (dispense request: quantity, days supply), D `money` × patient pay and total cost; FAIR NDC Coded Value | DESYNPUF_ID, event id, service date |

Every model: the governed-record pattern of CordovaOS 4.4.0, the data cluster beside ProvGov `prov-activity`, `prov-agent` and `audit-event`, the ProvGov `System Audit` in the audit slot (decision 4), no workflow bound (decision 5).

Cross-study shared components after the rebuild, by construction: race/ethnicity, sex, age, education, marital status, income, insurance, height, weight, BMI, blood pressure, smoking, alcohol, general health, every chronic-condition indicator, ICD-10-CM diagnosis (NHANES medications and, if decision 6 says so, CMS mapped), medication order, money, the provenance set. The `02_shared_cde_audit` query then has an answer in the store instead of in the README.

### 3.1 Retire

All 976 components and the 8 models: successors named where the concept is composed from a library or a FAIR component (`superseded by <slot>`), "not rebuilt: <reason>" for the 368 `_units` leaves and the columns the second build does not carry (BRFSS's 326 columns are not all worth a component; §3 says which are).

### 3.2 The dataset is a deliverable

Instances generated from the real rows by the template engine (`datagen/engine.py` of CordovaOS 4.4.0, copied into this repository or published as a package, decision 8), validated on the way out against each model's XSD 1.1 schema: a fixed sample per study large enough for the queries to say something (decision 7), the full files as an option. Instances, RDF projections and a load script are in the repository; the counts and the time to generate and load are measured on the release commit and written in the README.

### 3.3 The queries

The six queries are rewritten against the RDF the generated apps actually emit (reifiers with `rdfs:label`, `sdc4:inDataModel`, `rdf:reifies <<mc ?p ?v>>`, as CordovaOS's are), anchored on the shared components' `ct_id`s, and run against a loaded store before the release: which components every study carries (the audit), the distribution of systolic blood pressure by study, smoking status by study, chronic conditions by study and by source (self-report vs claims), medication coding overlap, demographics side by side. Each returns rows or the README says why not.

### 3.4 The stack (decisions 3, 8, 9)

This is the flagship demonstration for federal buyers, so it runs the way CordovaOS does: the seven generated applications in one clone-and-run stack (`make demo`), the console showing any record as table, document and graph with the governance behind each field, the demo pages with the saved cross-study queries and a graph tab drawing the shared components as the joins they are, the loader on the batch path. The CordovaOS 4.4.0 skeleton (settings, compose, loader, console, demo, docs, three-way merge method) is reused; the narrative, the query catalog, the entity graph's join keys and title labels are this demo's. The engine and schema reader come from CordovaOS `datagen/`.

### 3.5 Not in this build

The SDC_Agents pipeline story (discovery, enrichment, assembly by API): kept in the README as what the first build did and what it found, not rerun. The BRFSS columns outside §3. Person-level joins across studies (different populations; the join is the component, and the README says so).

## 4. Process

1. Repository for the curation (decision 1): `build/author.py` (the records as code, the `K()`/slot pattern of CordovaOSModels), `convert.py`, `bundle.py`, `chunk.py`, `review/`, `tests/`.
2. Load into production project FAIR Data Demo with `load_component_records --publish`; verify from the export.
3. Retire the 976 and the 8 by one-off; verify from the export.
4. Seven DMs by one-off (data cluster, ProvGov envelope, audit, attestation); publish; packages; `generate_app --standalone`; the downloads into the repo verbatim as before (`models/`, `apps/`).
5. Generators: one per model, reading the source files, naming values by label path; NHANES joins on SEQN; stated absences from the agencies' missing-value codes; every record validated on the way out; tests.
6. The stack: CordovaOS skeleton + the seven domain packages by the three-way merge; loader; console; demo pages with the FAIR narrative and the rewritten queries; run, load, count.
7. README rewritten: the claim, now true, with the audit query's answer on the page; the March story kept as history; limitations that remain.
8. Release: VERSION 4.2.0, tag `v4.2.0`, CHANGELOG naming the March build's findings and this build's numbers.

## 5. Facts checked 2026-09-26

- `load_component_records` accepts members by tiny_id, slot IRI and `ct:<ct_id>` (PR #704); chunks of 300 fit the 600 s job.
- The instance template (`dm-<ct>.xml`) writes a component composed in several clusters once (SDCStudio #705); the engine completes it.
- The NIH CDE library has no blood pressure, heart rate, BMI, smoking or chronic-condition CDEs among its 346 endorsed; FHIR has the first three, none has the last two.
- NHANES codes medication reasons in ICD-10-CM; CMS DE-SynPUF codes diagnoses in ICD-9-CM and procedures in HCPCS.
- The Cordoba lesson does not apply: every amount here is USD.

## 6. Decisions for Tim

1. **Where the curation lives.** In this public repository (`SemanticDataCharter/FAIR_Data_Demo/build/`), since the records are the demo's content and the point is that a reader can see them. Recommended. Alternative: a private `Axius-SDC/FAIRDemoModels` like CordovaOSModels.
Tim: in the public repo.  
2. **Seven models** as in §3 (NHANES participant + medication, BRFSS respondent, CMS beneficiary + inpatient + outpatient + prescription). Recommended. Alternative: keep the eight-per-file shape.
Tim: confirmed  
3. **Shared FAIR components** for smoking, alcohol, general health, chronic-condition indicators and physical function, authored once in this project with exactMatch links, composed by every study that measures them. Recommended; it is the canonicalization the July README asked for. Alternative: propose them to the NIH CDE library first (the endorsed set does not carry them; that library's rule is endorsed-only, so this would wait).
Tim: This is going to be our flagship demo for federal buyers so I'm thinking a complete stack like the CordovaOS demo so they can see that this is a demo with their real data.    
4. **Audit slot:** the ProvGov `System Audit` as the libraries ship it. Recommended (nothing here needs a Cordova-style owned audit).  
Tim: confirmed  
5. **No workflow bound.** These are observations of a survey or a claim, not documents with a lifecycle. Recommended. Alternative: bind ProvGov `document-publishing` so records settle like CordovaOS's.  
Tim: confirmed  
6. **CMS diagnosis codes stay ICD-9-CM**, in a study-local Coded Value cluster, not mapped to ICD-10-CM. Recommended: the data was coded in ICD-9-CM and a general equivalence mapping is a modeling decision the demo should show, not hide. The cross-study condition join then runs on the chronic-condition indicators, which all three carry.  
Tim: confirmed  
7. **Sample size:** NHANES all 9,254 participants (the files are small) and all 19,643 medication rows; BRFSS a fixed seeded sample of 5,000 respondents; CMS a fixed seeded sample of 5,000 beneficiaries with all their claims and events in the sample. Full files as `make full`. Recommended.  
Tim: confirmed  
8. **The engine:** copy `engine.py` and `schema.py` from CordovaOS into `datagen/` here now; extract a shared package (`sdcinstance`) when a third consumer appears. Recommended.
9. **The store:** a `docker-compose.yml` with GraphDB only, a load script that projects RDF with the generated apps' extractor and uploads named graphs in TriG batches, the queries run by `make queries`. No Django stack, no console. Recommended. Alternative: a CordovaOS-style stack with the seven apps running.
Tim: we can discuss 8 & 9 but I'm leaning towards the full stack demo with tables view and graph views.  
10. **Version:** the demo's next tag (its last is whatever the repo carries; check) with a CHANGELOG entry that names the March build's findings and this build's numbers.  
Tim: Maybe we should version this like the other SDC version tracking. Maybe 4.2.0?
