# Source errata

What the FAIR Data Demo found wrong, or easy to misread, in the libraries and federal files it is built from, and what
it does about each. An error in a source library is corrected in that library, as a revision of the published
component, and the models here compose the correction; a federal file is never edited, and a convention of its own is
carried as the file states it, with what that means written down here.

## From the component libraries

### E-2026-10-01: NIH CDE "Are you pregnant now?" (`LiUWCWluP`), LOINC answer codes one off

**The error.** The NIH CDE Repository's record for Current Pregnancy Indicator binds each answer to the next value's
LOINC code: Yes to LA26683-5 (Not pregnant), No to LA4489-6 (Unknown), Unknown to LA15173-0 (Pregnant). Its own NCI
Thesaurus meanings (C49488 Yes, C49487 No, C17998 Unknown) say otherwise. The NIH CDE library imported the record
faithfully; its `SOURCE-ERRATA.md` (E-2026-10-01) has the evidence.

**How it was found.** 25 October 2026, running HL7's FHIR validator on the FHIR output of `sdc-gdr2fhir` for the NHANES
Participant records: every answer carried a display its LOINC code does not have.

**Effect here.** The NHANES Participant and BRFSS Respondent models compose the component (through NHANES Demographics
and BRFSS Demographics), so every record answering the question bound "Yes" to Not pregnant: 1,980 records in the demo
dataset, and every projection that writes the model's binding (FHIR, OMOP CDM, HL7 v2).

**What we did.**

1. The NIH CDE library published the correction, `zmpqfc6tb0o2hgu8qs6lj8tp`, a revision of `owjt9bcgisxfbco8qnddo2fq`
   (retired), on 25 October 2026.
2. `build/author.py` composes the correction, and the six clusters above it (NHANES Demographics, NHANES Participant,
   NHANES Participant Governed Record, and the three BRFSS clusters) are revisions of their published versions
   (`REVISIONS` in `build/author.py`).
3. `build/oneoff_models_errata.py` revises the NHANES Participant and BRFSS Respondent models onto them.

**Status.** Done on 25 October 2026 and released in 4.2.3: the six cluster revisions and the two models, NHANES
Participant 4.2.3 (`eehpfapwgvxtzdrofgstdcfs`) and BRFSS Respondent 4.2.3 (`w9ozx00idgs5k8tw4359skvn`), are published,
and the records are regenerated on them. Reported to NIH: not yet.

## In the demo's own bindings

### E-2026-10-03: value bindings and concept links that name the wrong concept

**The error.** `build/author.py` binds each enumerated value to a code (`rdfs:isDefinedBy`) and links components to
the concept they measure. Twenty-four records named codes their terminologies do not confirm: some codes name an
unrelated concept, some are shared by values that mean different things, and one scale bound every level to Unknown.
Ours, not a source's: the agencies' files and the NIH CDE library were right.

| Record | Value or link | Was | Which is | Now |
|---|---|---|---|---|
| BRFSS BMI category | Underweight | NCIt C17962 | Multimedia | SNOMED CT 248342006 Underweight |
| | Normal Weight | NCIt C17958 | Functional Magnetic Resonance Imaging | SNOMED CT 43664005 Normal weight |
| BRFSS education | Never attended school or only kindergarten; Grades 1 through 8 | NCIt C17953 (both) | Education Level | the BRFSS codebook |
| | Grades 9 through 11 | NCIt C17953 | Education Level | NCIt C198650 Some High School, No Diploma |
| | College 4 years or more | NCIt C39303 | Active Funded Research Project | NCIt C159746 College Completion |
| NHANES education | Less than 9th grade | NCIt C17953 | Education Level | the NHANES codebook (DMDEDUC2) |
| | 9-11th grade | NCIt C17953 | Education Level | NCIt C198650 |
| | College graduate or above | NCIt C39303 | Active Funded Research Project | NCIt C159746 |
| General health status | Excellent, Very good, Good, Fair, Poor | NCIt C25184, C42642, C25185, C42633, C25187 | Lactate Dehydrogenase, Administered Component Concept, Laterality, Classification Scheme Relationship, Low Density Lipoprotein | LOINC LA9206-9, LA13913-1, LA8967-7, LA8968-5, LA8969-3 (LOINC's answer list LL1012-5) |
| Condition indicator basis | Self-report of a professional diagnosis | NCIt C93409 | Healthcare Provider Group Member | NCIt C188309 Self-Reported Information |
| | Claims-based algorithm | NCIt C25404 | Action | NCIt C221359 Healthcare Administrative Claims Data |
| | its concept link | NCIt C25596 | Breast Feeding | NCIt C16493 Data Source |
| NHANES citizenship | Citizen; Not a citizen (both) | NCIt C41130 | Significant | NCIt C90516 Citizen; the NHANES codebook (DMDCITZN) |
| NHANES pregnancy at exam | Yes; Not pregnant (both) | NCIt C25191 | Person Name | NCIt C124295 Pregnant; NCIt C82475 Not Pregnant |
| NHANES race/Hispanic origin | Mexican American | NCIt C67175 | DBVE-PC Regimen | NCIt C67114 Mexican American |
| NHANES difficulty scale (nine items) | No, Some, Much difficulty; Unable to do; Do not do this activity | NCIt C17998 (all five) | Unknown | NCIt C121736, C121739, C121740, C121742; the NHANES codebook (PFQ_J) |
| NHANES Physical Functioning | its concept link | NCIt C20000 (exact) | Zubrod Performance Status 5 | NCIt C150046 Physical Function (close) |
| NHANES and BRFSS Survey Design | its concept link | NCIt C142700 (exact) | Structured Product Labeling | NCIt C71492 Sampling Method (close) |
| Total Cholesterol (SI) | its concept link | LOINC 2093-3 | Cholesterol [Mass/volume] | LOINC 14647-2 Cholesterol [Moles/volume] |
| BRFSS days physical health not good | its concept link | LOINC 63580-5 | Have you ever smoked part or all of a cigarette | LOINC 66577-8 (the HRQOL question) |
| BRFSS days mental health not good | its concept link | LOINC 63579-7 | Have you ever taken a drink to keep from having any of the shakes | LOINC 66578-6 (the HRQOL question) |
| Veteran status | its concept link | NCIt C17742 | Gene Targeting | NCIt C171085 Military Status |

Where no concept says exactly what a value says, the value is defined by the agency's codebook, as the demo's other
survey-specific values are, rather than bound to a concept that is close.

**How it was found.** 25 and 26 October 2026: while checking the E-2026-10-01 codes in the HL7 v2 output, two values of one
list were seen sharing a code; then every code the bundle names was looked up, NCI Thesaurus in NCI's EVS API and
LOINC and SNOMED CT in HL7's terminology server, and its name compared with the value. Every replacement was looked up
the same way before it was written.

**Effect.** A target that writes the model's binding (FHIR, OMOP CDM, HL7 v2) writes these codes: "Underweight" as
Multimedia, every difficulty level as Unknown, both pregnancy answers as one code. The three models whose records
compose them are NHANES Participant, BRFSS Respondent and CMS Beneficiary.

**What we did.** The 24 records and the 14 clusters above them are revisions of their published versions (38;
`REVISIONS` in `build/author.py`), and the three models are revised onto them as NHANES Participant 4.2.4, BRFSS
Respondent 4.2.4 and CMS Beneficiary 4.2.4 (`build/*_e03*.py`). So a code nobody looked up does not ship again:
`build/verify_codes.py` asks each terminology what every code in the bundle is and records the name it gives in
`build/verified-codes.json`, and `build/tests/test_bindings.py` refuses a bundle that names a code not in that file,
binds two values of one list to one concept, or binds a value that is not an unknown to Unknown.

**To review.** Kept, and worth a second look: "Not at all" to *Do you now smoke cigarettes* is bound to LOINC
LA15920-4 Former smoker (true of who is asked, an inference rather than the answer); BRFSS and NHANES "Separated" to
NCIt C51777 Legally Separated; and four clusters claim an exact match to a concept they contain rather than are (BRFSS
Body Measures to BMI, BRFSS Tobacco and Alcohol Use and NHANES Smoking to Tobacco smoking status).

**Status.** Done on 26 October 2026 and released in 4.2.4: the 38 revisions are published and public, and the three
models are NHANES Participant 4.2.4 (`tp5pg0u4dasqarie0b3ujn2u`), BRFSS Respondent 4.2.4 (`j6wmvhr46irxht2ls90nry8k`) and
CMS Beneficiary 4.2.4 (`vj0hr75146j0pbedvc0iaqrz`), with the records regenerated on them.

## From the federal files: conventions to read correctly

### NHANES 2017-2018 prescription medications (`RXQ_RX_J`): prevention codes do not conform to ICD-10-CM

**The standard.** ICD-10-CM, the US clinical modification of the WHO's ICD-10, maintained by CDC's National Center for
Health Statistics. A code is valid only if it is in the code set; the code set has no way to say that a condition is
being prevented rather than diagnosed.

**The departure.** The reasons for use (`RXDRSC1` to `RXDRSC3`) are ICD-10-CM codes, except where the reason was to
prevent a condition. Then NHANES writes the condition's ICD-10-CM code with the letter "P" appended: "When reported
reason was for disease prevention, an appropriate ICD-10-CM code followed by a letter 'P' was used (e.g., A49.9P
Prevent bacterial infection; D75.9P Prevent blood clots)" (the file's Data Processing and Editing notes). The result is
a code ICD-10-CM does not contain, carried in a variable whose other values are ICD-10-CM: 29 such codes, 691 of the
file's 15,565 reason codes, the most used `I21.P` "Prevent heart attack/myocardial infarction" (170) and `D75.9P`
"Prevent blood clots" (148).

**The evidence.** On 26 October 2026 every one of the file's 241 distinct reason codes was looked up in ICD-10-CM on
HL7's terminology server (with D75.9, I21 and I21.9 as controls, which it found). All 209 codes without the suffix
are ICD-10-CM codes; none of the 29 codes with it is. Every one of the 29 is described by NHANES as "Prevent ...". The
other three values, 55555 (a reason that could not be coded, 84), 77777 (refused, 5) and 99999 (don't know, 451), are
not codes of any system.

**Why it matters.** A prevention code read as ICD-10-CM is refused by any system that checks the code set (HL7's
FHIR validator reports `I21.P` as an unknown ICD-10-CM code), and the obvious repair, dropping the "P", is worse: `I21`
is Acute myocardial infarction, so a participant taking aspirin to prevent a heart attack would be recorded as having
had one.

**What the demo does (4.2.5).** The prevention codes are a code system of NHANES's own, and the model carries them as
one: each Medication Reason holds either the ICD-10-CM diagnosis (the FHIR library's coded value) or a **Prevention
Reason (NHANES)** coded value, with the NHANES code as written, NHANES's description, and the code system fixed to the
RXQ_RX_J documentation (`https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/RXQ_RX_J.htm`), never ICD-10-CM. The generator
puts a code in the NHANES coded value only when it both has the NHANES shape and is described as prevention, and stops
if the two disagree (a real ICD-10-CM code can end in P, as a seventh character). 55555, 77777 and 99999 are left out
and counted.

**What a target receives** (once the mappers carry the 4.2.5 model; checked against their output then). The code under NHANES's code system with its description: in FHIR a reason Coding whose
system is the NHANES documentation, not `http://hl7.org/fhir/sid/icd-10-cm`; in OMOP CDM no standard concept (the code
and description as source values); in HL7 v2 a coded element whose coding system is local to NHANES. Each target
states that the code is not ICD-10-CM; none receives a code it would read as a diagnosis.

**Status.** Open: whether 55555, 77777 and 99999 are carried as Exceptional Values (could not be coded, refused,
don't know) rather than left out.

