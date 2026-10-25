# Changelog

All notable changes to the FAIR Data Demo. Version numbers follow the SDC4 release line the models are published on.

## 4.2.3 (2026-10-25)

**The pregnancy answers carry the right codes.** The NIH CDE "Are you pregnant now?" (`LiUWCWluP`) that the NHANES
Participant and BRFSS Respondent models compose bound each answer to the next value's LOINC code (Yes to LA26683-5,
Not pregnant), as NIH's own record does. The NIH CDE library published the correction (`zmpqfc6tb0o2hgu8qs6lj8tp`,
E-2026-10-01), and this release moves the two models onto it: see [SOURCE-ERRATA.md](SOURCE-ERRATA.md).

- Six clusters are revisions of their published versions (NHANES Demographics, NHANES Participant, NHANES Participant
  Governed Record and the three BRFSS clusters), and the two models are revisions of theirs, published as **NHANES
  Participant 4.2.3** (`eehpfapwgvxtzdrofgstdcfs`, revising `xy8upneajsb8vdcmnve01g6g`) and **BRFSS Respondent 4.2.3**
  (`w9ozx00idgs5k8tw4359skvn`, revising `iymux9kjv8ndbkoi36xzx17i`). A model's title is unique in its project, retired
  models included, so a revision carries the release that first ships it. `models-4.2.3.json` records every model.
- The two models' packages, applications and generated records are rebuilt (9,254 and 5,000 records; 1,110 and 870
  answer the question). Nothing else changes: the other five models and their records are as in 4.2.2.
- The 4.2.0 models stay published and resolvable, retired with the reason naming their revision.
- `build/author.py` and `build/make_review.py` keep the review decisions already marked when they regenerate (they had
  blanked them); a record whose content changed is reviewed again.
- [SOURCE-ERRATA.md](SOURCE-ERRATA.md) documents the NIH error and NHANES's reason-code conventions.

## 4.2.2 (2026-10-25)

Rebuilt with pip 26.2.2 pinned by hash in CI and the release job (the eMudhra/emSign CA compromise: pip before 26.2.2 trusts the compromised root through its vendored certifi). This release also carries the models' schemas with their units enumerated (the 2026-09-28 entry below), which had not been released.

## 2026-09-28: the models' schemas now enumerate their units

- SDCStudio issue #707 (fixed in PR #708): Units components were published without their enumeration, so every quantity in the seven models validated any string as a unit. The 14 Units the seven active models compose were republished on production and the seven packages rebuilt; `app/sdc4/mediafiles/dmlib/` carries the rebuilt XSD and template of each. Model identifiers did not change.
- The 84,352 generated records are unaffected: the survey weights and the income ratio carry the unit `1`, which is exactly what the FAIR `units-sample-weight` record enumerates; a 2,100-record sample across the seven apps found no unit outside its enumeration. The engine test now takes its unit from the schema's enumeration instead of a placeholder.
- Every receipt issued for these models before 2026-09-28 names a schema hash the served schema no longer reproduces.

All notable changes to the FAIR Data Demo. Version numbers follow the SDC4 release line the models are published on.

## 4.2.1 (2026-09-27)

- The compose project is named `fair`. Compose names a project after its directory, every generated stack lives in a directory called `sdc4`, and two stacks on one machine reconciled each other's containers away. `.env.example` carries the ports the README states (15433, 17300, 18081, 16380, 19444, 18100).

## 4.2.0 (2026-09-26)

The second build. The three studies now share their components, and the cross-study queries return rows from a loaded store.

### Models

- Seven data models replace the first build's eight, each composed from the published component libraries by identifier slot: Default (person demographics, gender, birth date, money), NIH CDE (race and ethnicity, age, education, marital status, income, insurance, employment, pregnancy), FHIR (blood pressure, vital signs, laboratory result, condition, medication order, encounter, hospitalization, insurance coverage, patient), ProvGov (activity, agent, audit event, system audit). NHANES Participant (`xy8upneajsb8vdcmnve01g6g`), NHANES Medication (`epbdfmvxc3gbh5f66hhb3o2m`), BRFSS Respondent (`iymux9kjv8ndbkoi36xzx17i`), CMS Beneficiary (`fnv3zi2btk3s0sfodjsc25eb`), CMS Inpatient Claim (`ji1eccop92mlmikwq5gwp7cr`), CMS Outpatient Claim (`mllwhe842wtnim4ms48qonio`), CMS Prescription Drug Event (`nvemvhvdkctdlm9alwwgcay7`); each records the first-build model it revises in `models-4.2.0.json`.
- 266 component records authored in this project (`build/author.py`, reviewed in `review/fair.csv`): what the studies share and no library holds (smoking status on LOINC 72166-2, twenty-one chronic-condition indicators each with a SNOMED CT subject, a condition basis component, general health, veteran status), what one study alone needs (survey identifiers, weights, PSU and stratum with the agency's definition, ICD-9-CM, HCPCS and NDC coded values, the agencies' own codes beside every harmonized value), and fourteen Units records.
- The first build's 976 components and eight models remain published and are retired with a reason naming the successor slot, or the reason the column was not carried forward.
- Every record carries the governance envelope of CordovaOS 4.4.0: the ProvGov activity (used entity: the federal file by URL and release), agent, audit event, and the FAIR Pipeline Audit naming the system and the source file. No model binds a workflow.

### Data

- One generator per model in `datagen/`, on the template engine of CordovaOS 4.4.0 (label paths, no element identifiers; tuple paths for labels carrying a slash; labels the scaffold cut at an apostrophe repaired from the schema). NHANES joins its files on SEQN into one participant record; medications are one record per row naming a medicine. Refused and don't-know answers are left out and counted per variable.
- `make demo` = every NHANES row, a seeded 5,000 BRFSS respondents, a seeded 1,000 CMS beneficiaries with all their claims and events: 84,352 records, generated in about three minutes. `make demo-full` = every row (about 7 million).

### Stack

- The CordovaOS 4.4.0 skeleton (settings, compose, batch loader, console, demo pages, entity graph) with the seven generated applications merged in verbatim. Ports 18100 (web), 17300 (GraphDB), 18081 (Keycloak), 15433 (PostgreSQL), 16380 (Redis), 19444 (SirixDB). The Keycloak realm SirixDB needs is tracked.
- Six cross-study SPARQL queries rewritten against the RDF the applications emit and run before release; a six-beat walk-through; the console's cross-study page (the shared-component audit and the chronic-condition question, each with its query printed); the entity graph draws a shared component as a node the records of different studies meet at.

### Findings recorded

- Medications do not join across studies (NHANES name and identifier, CMS NDC, no RxNorm in either source).
- Education and income are not harmonized (the NIH CDE lists do not nest with the agencies' bands).
- BRFSS 2022 did not ask blood pressure or cholesterol history.
- The CMS claims are coded as recorded (ICD-9-CM, HCPCS); 244 inpatient procedure slots in the sample carry diagnosis-shaped codes and are left out.

## 4.0.0 (2026-03)

The first build: the SDC_Agents pipeline over NHANES 2017-2018, BRFSS 2022 and CMS DE-SynPUF (introspect, discover, enrich, assemble by API). 976 components and eight models published; the studies shared none of them, because the agencies' metadata was too thin for the agents to match concepts across studies. The README of 2026-07-25 recorded that and kept the six queries as a specification. The enrichment code stays in `scripts/enrichment/` as the record of what the first pass took.
