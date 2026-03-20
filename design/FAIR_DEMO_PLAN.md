# FAIR Data Demo — Architecture and CDE Coverage

## Purpose

Prove that SDC4 delivers structural FAIR data interoperability across real NIH-funded studies. Three studies, three NIH institutes, three study designs — one shared semantic infrastructure.

## Studies

| Study | Type | Funder | Source |
|-------|------|--------|--------|
| NHANES | Population Survey | CDC/NCHS | https://wwwn.cdc.gov/nchs/nhanes/ |
| ADNI | Longitudinal Cohort | NIA | https://adni.loni.usc.edu/ |
| SPRINT | Randomized Trial | NHLBI | https://biolincc.nhlbi.nih.gov/studies/sprint/ |

## NIH CDE Domain Coverage

All 12 NIH Common Data Element domains are represented. 5 domains are shared across all three studies.

| Domain | NHANES | ADNI | SPRINT | Shared |
|--------|--------|------|--------|--------|
| Demographics | X | X | X | All 3 |
| Vital Signs | X | X | X | All 3 |
| Lab Results | X | X | X | All 3 |
| Medications | X | X | X | All 3 |
| Medical History | X | X | X | All 3 |
| Biospecimens | X | X | | 2 |
| Adverse Events | | X | X | 2 |
| Cognitive Assessment | | X | X | 2 |
| Substance Use | X | | | 1 |
| SDOH | X | | | 1 |
| Physical Function | X | | | 1 |
| Pain | X | | | 1 |

## Architecture

### Services

- **PostgreSQL 16**: Django ORM storage (study app models, user accounts)
- **GraphDB 10.8**: RDF triplestore with OWL 2 RL reasoning (knowledge graph, SPARQL endpoint)
- **Redis 7**: Django cache backend
- **Django 5.1**: Web application (landing page, SPARQL explorer, admin)

### Data Flow

```
Source Data (CSV/XPT)
    │
    ▼
datagen/ converters
    │
    ▼
Validated XML Instances (app/import_data/)
    │
    ├──▶ Django bulk import (PostgreSQL)
    │
    └──▶ RDF triple extraction (GraphDB)
            │
            ▼
        SPARQL queries (cross-study joins on shared ct_id)
```

### Interoperability Mechanism

SDC4 components are identified by a permanent `ct_id` (CUID2). When multiple studies model the same NIH CDE concept, they reuse the identical component — same `ct_id`, same XSD schema, same validation rules.

Cross-study queries join on `ct_id`. No mapping tables. No ETL. No reconciliation.

## Memory Target

4 GB total:
- PostgreSQL: ~512 MB
- GraphDB: 1 GB heap + ~512 MB overhead
- Redis: ~128 MB
- Django: ~256 MB per gunicorn worker (3 workers)

## What Gets Generated in SDCStudio

For each study, SDCStudio will generate:

1. **Django app** (models, views, admin, templates) via AppGen
2. **XSD schemas** for each data model
3. **RDF triples** extracted from schemas
4. **SHACL constraints** for validation
5. **JSON-LD** semantic descriptions

The generated apps get placed in `app/{study_name}/` and registered in Django settings.

## SPARQL Query Strategy

Six pre-built queries demonstrate different interoperability patterns:

1. **Demographics**: Direct component reuse across studies
2. **CDE Audit**: Which components are shared vs. study-specific
3. **Vital Signs**: Shared units and measurement constraints
4. **Lab Results**: Compatible result structures and reference ranges
5. **Medications**: Overlapping medication coding
6. **Medical History**: Shared history components

All queries join on `ct_id` — the same mechanism that would work in production with thousands of studies.
