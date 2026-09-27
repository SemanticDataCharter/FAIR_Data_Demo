# Cross-study SPARQL queries

Six queries against the knowledge graph the seven applications project, one named graph per
record (84,352 graphs, 33 million triples in the `make demo` set). Each query anchors on a
published component by its `ct_id`, and the join across studies is the component itself, composed
by every study model that measures the concept.

| # | File | What it shows | Studies |
|---|------|---------------|---------|
| 1 | `01_shared_component_audit.rq` | Every component that records of more than one model carry, with the models and records that carry it | NHANES, BRFSS, CMS |
| 2 | `02_smoking_status_by_study.rq` | Smoking status (one component, LOINC 72166-2 answers) by study | NHANES, BRFSS |
| 3 | `03_blood_pressure_by_study.rq` | The FHIR systolic, diastolic and heart rate components by study, with ranges | NHANES, BRFSS |
| 4 | `04_chronic_conditions_by_study_and_basis.rq` | Twenty-one condition indicators by study and by the basis each study established them on | NHANES, BRFSS, CMS |
| 5 | `05_medication_coding_by_study.rq` | How NHANES and CMS code a medication, and why those two do not join | NHANES, CMS |
| 6 | `06_demographics_side_by_side.rq` | Gender and race/ethnicity, harmonized on the Default and NIH CDE components, by study | NHANES, BRFSS, CMS |

## What each returned (release 4.2.0, the `make demo` set, GraphDB with a 4GB heap, idle)

| # | Rows | Time | What the rows say |
|---|---|---|---|
| 1 | 38 | 78 s | 20 components carried by more than one study, 8 by all three (gender, race/ethnicity, the condition basis, and the stroke, cancer, COPD, arthritis and coronary heart disease indicators); 18 more shared between one study's own models (the CMS claim fields, the beneficiary and participant identifiers) |
| 2 | 9 | 2 s | NHANES 3,497 never / 1,338 former / 805 every-day / 216 some-day smokers; BRFSS 2,805 / 1,227 / 401 / 162, plus 6 "current status unknown"; one answer list, two questionnaires |
| 3 | 3 | 7 s | NHANES only: systolic 6,714 readings, mean 121.8 mmHg (72 to 238); diastolic mean 69.3; heart rate mean 73.7. BRFSS returns no row: the 2022 core did not ask |
| 4 | 35 | 23 s | Every condition, study and basis: for example arthritis is "told by a professional" in 1,695 of 5,552 NHANES and 1,623 of 4,961 BRFSS records and "found in claims" in 138 of 1,000 CMS beneficiaries; diabetes 776 of 4,988 BRFSS, 368 of 1,000 CMS |
| 5 | 5 | 68 s | NHANES: 14,300 generic drug names (666 distinct) and 13,760 ICD-10-CM reasons; CMS: 47,280 NDC codes (40,377 distinct) on the events, ICD-9-CM diagnoses on the claims. Three code systems, no shared product component |
| 6 | 18 | 4 s | Gender and race/ethnicity by study on the same two components: NHANES 4,697 female / 4,557 male; BRFSS 2,642 / 2,358; CMS 549 / 451 |

## The RDF shape, and the one rule for writing a fast query

A field reifier `?r` carries `rdfs:label`, `sdc4:inInstance`, `sdc4:inDataModel`, `sdc4:inCluster` and
`rdf:reifies <<sdc4:mc-<ct_id> ?predicate ?value>>`; the model carries `dc:title`. The reifier's own IRI
is `https://semanticdatacharter.com/ns/dm/v_<component ct_id>_<instance id>`.

**Bind the component.** A triple term with the component unbound (`rdf:reifies <<?mc ?p ?v>>` with
nothing else fixing `?mc`) makes the store scan every reifier; the same query with the component
named (`<<sdc4:mc-n7pn5ctqo81v0v418hez5zv5 ?p ?v>>`, or a `VALUES ?mc` list placed before the
pattern) answers in a fraction of a second. When the component is not known in advance, read it
from the reifier's IRI (`STRBEFORE(STRAFTER(STR(?r), "/dm/v_"), "_")`, as query 1 does) or address
the reifier directly by building that IRI from the component and the record (as query 4 does for
the basis, and as the demo's entity graph does).

Run them from the demo's explorer (`/demo/explorer/`), which draws every result's records and the
shared components between them, or directly:

```bash
curl -s -u admin:admin123 -H "Accept: text/csv" --data-urlencode "query@sparql/01_shared_component_audit.rq" http://localhost:17300/repositories/sdc4_rdf
```
