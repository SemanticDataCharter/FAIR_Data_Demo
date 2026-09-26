# Cross-study SPARQL queries

Six queries against the knowledge graph the seven applications project, one named graph per
record. Each query anchors on a published component by its `mc-<ct_id>` (read from
`app/sdc4/mediafiles/dmlib/dm-<ct_id>.xsd`) or on its label; the join across studies is the
component itself, composed by every study model that measures the concept.

| # | File | What it shows | Studies |
|---|------|---------------|---------|
| 1 | `01_shared_component_audit.rq` | Every component that records of more than one model carry, with the models and records that carry it | NHANES, BRFSS, CMS |
| 2 | `02_smoking_status_by_study.rq` | Smoking status (one component, LOINC 72166-2 answers) by study | NHANES, BRFSS |
| 3 | `03_blood_pressure_by_study.rq` | The FHIR systolic, diastolic and heart rate components by study, with ranges | NHANES, BRFSS |
| 4 | `04_chronic_conditions_by_study_and_basis.rq` | Twenty-one condition indicators by study and by the basis each study established them on | NHANES, BRFSS, CMS |
| 5 | `05_medication_coding_by_study.rq` | How NHANES and CMS code a medication, and why those two do not join | NHANES, CMS |
| 6 | `06_demographics_side_by_side.rq` | Gender and race/ethnicity, harmonized on the Default and NIH CDE components, by study | NHANES, BRFSS, CMS |

The RDF shape every query reads: a field reifier `?r` carries `rdfs:label`, `sdc4:inInstance`,
`sdc4:inDataModel` and `rdf:reifies <<sdc4:mc-<ct_id> ?predicate ?value>>`; the model carries
`dc:title`. Run them from the demo's explorer (`/demo/explorer/`), which draws every result's
records and the shared components between them, or directly:

```bash
curl -s -u admin:admin123 -H "Accept: text/csv" --data-urlencode "query@sparql/01_shared_component_audit.rq" http://localhost:17300/repositories/sdc4_rdf
```
