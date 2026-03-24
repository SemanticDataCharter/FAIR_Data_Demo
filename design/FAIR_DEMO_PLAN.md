# FAIR Data Demo — Architecture and CDE Coverage

## Purpose

Prove that SDC delivers structural FAIR data interoperability across real federal health studies. Three studies, three agencies, three study designs; one shared semantic infrastructure. All source data is freely downloadable with no registration.

## Studies

| Study | Type | Agency | Format | Access |
|-------|------|--------|--------|--------|
| NHANES 2017-18 | Population Survey | CDC/NCHS | 8 XPT files | Direct download |
| BRFSS 2022 | Telephone Survey | CDC | 1 XPT file (326 vars, ~445K records) | Direct download |
| CMS DE-SynPUF | Medicare Claims (Synthetic) | CMS | CSV, Sample 1 only | Direct download |

## CDE Domain Coverage

8 domains are represented. 3 domains are shared across all three studies.

| Domain | NHANES | BRFSS | CMS | Shared |
|--------|--------|-------|-----|--------|
| Demographics | X | X | X | All 3 |
| Medical History | X | X | X | All 3 |
| Substance Use | X | X | | 2 |
| Vital Signs (BP, BMI) | X | X | | 2 |
| Medications | X | | X | 2 |
| Physical Function | X | X | | 2 |
| Lab Results | X | | | 1 |
| SDOH | X | | | 1 |

## Workflow

### Agent-Based Model Assembly

The demo exercises the real SDCStudio + SDC_Agents pipeline:

1. **SDC_Agents API** creates and reuses NIH-CDE catalog components (same `ct_id` for shared concepts)
2. Agents **assemble components into clusters** within the FAIR Data Demo project
3. Study-specific components are **minted fresh** by the agents during creation
4. In **SDCStudio**, a human reviews and **approves draft components**, then builds study-level data models
5. SDCStudio **generates all 8 output formats** (XSD, XML, JSON, JSON-LD, HTML, RDF, SHACL, GQL)
6. Generated output is placed in `models/{study}/`
7. RDF triples are loaded into GraphDB for cross-study SPARQL queries

### Reusable Component Table

These components from the NIH-CDE catalog are reused across studies:

| Component | Type | ct_id |
|-----------|------|-------|
| Participant ID | XdString | `sdt9aiqjdbjjaafgjzzwygf8` |
| Age in Years | XdCount | `c1nr0ykdr4w99ss7dty1iaug` |
| Birth Date | XdTemporal | `g3k6bj8su3rvkszg2700dhyh` |
| Sex | XdToken | `mw9qdn71urog8egjbp5t3y00` |
| Race | XdToken | `iiwx1rakgy3wfytyskre0v3x` |
| Ethnicity | XdToken | `ltobu9ek54hcnrjxk16jk8qk` |
| Education Level | XdToken | `dbv7fgfi67iztx00lgv1vxni` |
| Marital Status | XdToken | `w3bw02ebbrrs7mzu3ztkb8od` |
| Systolic Blood Pressure | XdQuantity | `v15kv8dnd9th63hmccqetmki` |
| Diastolic Blood Pressure | XdQuantity | `b0qfvgagjyebeuizpe900a93` |
| Heart Rate | XdQuantity | `wmjt38l5le7u3ro7qjmkaaz7` |
| Respiratory Rate | XdQuantity | `zseky2lf0pcuc7rsjtj49dm9` |
| Body Temperature | XdQuantity | `s0yyyjcuu3l4ra93p5lktzig` |
| BMI | XdQuantity | `wpojnsuwae37rfsnj9xpbcun` |
| Person Weight Value | XdQuantity | `scjotdd5kp3yovkvjgsc5a7v` |
| Person Height Value | XdQuantity | `mkelab9gci43xj7akjy8w7h3` |
| Smoking Status | XdToken | `pcqb6t8q1g9e0fagm55fkhf2` |

## Architecture

### Data Flow

```
Source Data (CSV/XPT)
    │
    ▼
SDC Agents Pipeline (scripts/run_pipeline.py)
    ├── Introspect datasources
    ├── Discover/reuse catalog components
    ├── Propose cluster hierarchies
    └── Assemble data models
    │
    ▼
SDCStudio (approve drafts → build data models → generate app)
    │
    ▼
Generated Output (models/{study}/)
    ├── XSD schemas
    ├── XML instances
    ├── JSON / JSON-LD
    ├── HTML documentation
    ├── RDF triples
    ├── SHACL constraints
    └── GQL CREATE statements

XML Instance Generation (scripts/generate_instances.py)
    │
    ▼
Validated XML Instances (output/instances/)
```

### Interoperability Mechanism

SDC components are identified by a permanent `ct_id` (CUID2). When multiple studies model the same NIH CDE concept, they reuse the identical component; same `ct_id`, same XSD schema, same validation rules.

Cross-study queries join on `ct_id`. No mapping tables. No ETL. No reconciliation.

## What Gets Generated in SDCStudio

For each study, SDCStudio generates:

1. **XSD schemas** for each data model
2. **XML instance documents** (complete data examples)
3. **JSON instance data** (mirrors XML structure)
4. **JSON-LD schema** (semantic descriptions for linked data)
5. **HTML documentation**
6. **RDF triples** extracted from schemas
7. **SHACL constraints** for validation
8. **GQL CREATE statements** for property graphs
9. **Django application** via AppGen for study-specific views and data management

## SPARQL Query Strategy

Six pre-built queries demonstrate different interoperability patterns:

1. **Demographics**: Direct component reuse across studies
2. **CDE Audit**: Which components are shared vs. study-specific
3. **Vital Signs**: Shared units and measurement constraints
4. **Chronic Conditions**: Medical history components shared across studies
5. **Medications**: Overlapping medication coding
6. **Medical History**: Shared history components

All queries join on `ct_id`, the same mechanism that would work in production with thousands of studies.

**Note**: The SPARQL queries use a placeholder `sdc4:` vocabulary. They will be rewritten to use the actual `sdc4-meta:` predicates once real RDF triples are generated from SDCStudio models.

## XPT Metadata Handling

### The Problem

NHANES and BRFSS use coded column names (e.g. `BPXSY1`, `_AGE80`, `_SMOKER3`) that carry no semantic meaning. The SAS transport (.XPT) format embeds rich metadata alongside the data:

- **Column labels**: `BPXSY1` → "Systolic: Blood pres (1st rdg) mm Hg"
- **Value labels**: `RIAGENDR` 1="Male", 2="Female"
- **Format info**: numeric precision, string lengths

When converted to CSV, this metadata is lost.

### Solution: Sidecar Metadata with SDC_Agents 4.2.0

SDC_Agents 4.2.0 supports JSON sidecar metadata files that are merged into introspection results automatically. The pipeline leverages this as follows:

1. `convert_xpt_to_csv.py` converts XPT to CSV and saves metadata as `.json` sidecar files, including `description` and `enumeration` fields per column
2. `sdc-agents.yaml` datasource entries include `metadata_path` pointing to the sidecar files
3. `introspect_csv` merges sidecar metadata into its 13-field column schema; `discover_components` matches on the `description` field, allowing coded names like `BPXSY1` to match catalog components via the SAS label
4. `fair_constants.py` `COLUMN_OVERRIDES` provides a manual safety net for columns that do not auto-match

### Future: Native Statistical Format Introspection

SDC_Agents does not yet have native XPT/SAS/SPSS introspection. These formats require pre-conversion to CSV + JSON sidecar (via `convert_xpt_to_csv.py`). A native `introspect_xpt` tool would eliminate this preprocessing step for federal health data workflows.

| Format | Extension | Metadata Type | Agency |
|--------|-----------|---------------|--------|
| SAS Transport | .XPT | Column labels, value labels, formats | CDC, FDA, NIH |
| SAS Dataset | .sas7bdat | Same as XPT + more | All federal |
| SPSS | .sav | Variable labels, value labels, missing codes | NIH surveys |
| Stata | .dta | Variable labels, value labels | NIH, Census |
| CDISC Define-XML | .xml | Full metadata spec for clinical trials | FDA required |
