# SPARQL Queries

Pre-built cross-study SPARQL queries demonstrating SDC interoperability.

## Join Mechanism

All queries exploit the fact that SDC components are identified by a permanent `ct_id` (CUID2). When NHANES, ADNI, and SPRINT reuse the same NIH CDE component, their XML instances share the same schema URI (`sdc4:dm-{ct_id}`). The knowledge graph contains RDF triples extracted from each study's schemas — joining on `ct_id` gives cross-study interoperability with zero mapping.

## Queries

| # | File | Description | Domains |
|---|------|-------------|---------|
| 1 | `01_cross_study_demographics.rq` | Subject demographics across all three studies | Demographics |
| 2 | `02_shared_cde_audit.rq` | Audit which CDE components are shared vs. study-specific | All |
| 3 | `03_vital_signs_comparison.rq` | Vital signs distributions across studies | Vital Signs |
| 4 | `04_lab_results_interop.rq` | Lab result components with shared units and ranges | Laboratory Results |
| 5 | `05_medication_overlap.rq` | Medication coding overlap analysis | Medications |
| 6 | `06_cross_study_medical_history.rq` | Medical history components shared across studies | Medical History |

## Running Queries

### Via the Demo UI

Navigate to `http://localhost:8000/` and use the SPARQL Explorer section. Select a pre-built query from the dropdown or paste your own.

### Via GraphDB Workbench

Navigate to `http://localhost:7200/sparql` and paste a query.

### Via curl

```bash
curl -X POST http://localhost:7200/repositories/fair_demo \
  -H "Accept: application/sparql-results+json" \
  -d "query=$(cat sparql/01_cross_study_demographics.rq)"
```
