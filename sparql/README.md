# SPARQL Queries

Pre-built SPARQL queries expressing the intended SDC cross-study join pattern.

## Join Mechanism

All queries exploit the fact that SDC components are identified by a permanent `ct_id` (CUID2). When studies reuse the *same* NIH CDE component, the knowledge graph (RDF triples extracted from each study's schemas) shares that `ct_id`, and joining on it gives cross-study interoperability with zero mapping.

**This depends on the shared concepts having been canonicalized to a single component.** In the current demo models, each study uses its own components — the reuse gap documented in [Current Limitations and Future Work](../README.md#current-limitations-and-future-work) — so the three studies share no `ct_id`s. These queries therefore express the *target* pattern and return results only once the expert-reviewed canonicalization is done. They are kept as the specification of what that state enables.

## Queries

| # | File | Description | Domains |
|---|------|-------------|---------|
| 1 | `01_cross_study_demographics.rq` | Subject demographics across all three studies | Demographics |
| 2 | `02_shared_cde_audit.rq` | Audit which CDE components are shared vs. study-specific | All |
| 3 | `03_vital_signs_comparison.rq` | Vital signs distributions across studies | Vital Signs |
| 4 | `04_chronic_conditions_interop.rq` | Chronic condition components shared across studies | Medical History |
| 5 | `05_medication_overlap.rq` | Medication coding overlap analysis | Medications |
| 6 | `06_cross_study_medical_history.rq` | Medical history components shared across studies | Medical History |

## Running Queries

After RDF triples are generated from the approved SDCStudio models, load them into a SPARQL-capable triplestore (Fuseki, GraphDB, etc.) and run these queries against it.

### Via Fuseki

```bash
curl -X POST http://localhost:3030/fair_demo/query \
  -H "Accept: application/sparql-results+json" \
  -d "query=$(cat sparql/01_cross_study_demographics.rq)"
```

### Via GraphDB

```bash
curl -X POST http://localhost:7200/repositories/fair_demo \
  -H "Accept: application/sparql-results+json" \
  -d "query=$(cat sparql/01_cross_study_demographics.rq)"
```
