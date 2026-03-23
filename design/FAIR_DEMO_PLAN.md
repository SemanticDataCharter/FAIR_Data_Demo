# FAIR Data Demo — Architecture and CDE Coverage

## Purpose

Prove that SDC delivers structural FAIR data interoperability across real NIH-funded studies. Three studies, three NIH institutes, three study designs — one shared semantic infrastructure.

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

These components from the NIH-CDE catalog are reused across all three study templates:

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

Components shared by ADNI and SPRINT (Adverse Events):

| Component | Type | ct_id |
|-----------|------|-------|
| AE Description | XdString | `pp5v32ipc0xbva1hi5l3r91g` |
| AE Term | XdString | `fbfqzhm0es37p5rtrtw2wh0n` |
| AE Start Date | XdTemporal | `w0qi4triqgeeg0oodhy75p8h` |
| AE End Date | XdTemporal | `andj4gpkessj3z0koheyc7gj` |

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

SDC components are identified by a permanent `ct_id` (CUID2). When multiple studies model the same NIH CDE concept, they reuse the identical component — same `ct_id`, same XSD schema, same validation rules.

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
4. **Lab Results**: Compatible result structures and reference ranges
5. **Medications**: Overlapping medication coding
6. **Medical History**: Shared history components

All queries join on `ct_id` — the same mechanism that would work in production with thousands of studies.

**Note**: The current SPARQL queries use a placeholder `sdc4:` vocabulary. They will be rewritten to use the actual `sdc4-meta:` predicates once real RDF triples are generated from SDCStudio models.

## XPT Metadata and the Column Description Gap

### The Problem

NHANES uses coded column names (e.g. `BPXSY1`, `RIDAGEYR`, `DMDEDUC2`) that carry no semantic meaning. The SAS transport (.XPT) format embeds rich metadata alongside the data:

- **Column labels**: `BPXSY1` → "Systolic: Blood pres (1st rdg) mm Hg"
- **Value labels**: `RIAGENDR` 1="Male", 2="Female"
- **Format info**: numeric precision, string lengths

When converted to CSV, this metadata is lost. The SDC Agents `introspect_csv()` sees only the coded name and inferred type, and `discover_components()` matches on `_name_similarity(col_name, comp_label)` via `SequenceMatcher`. Result: `BPXSY1` vs "Systolic Blood Pressure" scores near zero.

### Current Workaround (This Demo)

1. `convert_xpt_to_csv.py` saves metadata as `.meta.json` sidecar files
2. `run_pipeline.py` Step 3 loads SAS labels and matches them against known catalog components before falling back to manual overrides
3. `fair_constants.py` `COLUMN_OVERRIDES` provides a final safety net for columns that don't auto-match

### SDC_Agents Enhancement Needed

For federal health data at scale (NIH, FDA, CDC), the Introspect toolset needs:

1. **Column description/label field** in the introspection cache schema — so that external metadata (SAS labels, data dictionaries, CDISC definitions) can be attached to columns
2. **Discovery matching on description** — `discover_components()` should match on column description in addition to column name, with description matches weighted higher
3. **Metadata ingest hook** — a way to provide external column metadata (JSON sidecar, data dictionary CSV, CDISC Define-XML) that gets merged into introspection results

This is critical for any datasource where column names are coded identifiers rather than human-readable labels: NHANES, FDA CDISC submissions, legacy SAS datasets, SPSS exports, and most government health data.

### Federal Health Data Formats Affected

| Format | Extension | Metadata Type | Agency |
|--------|-----------|---------------|--------|
| SAS Transport | .XPT | Column labels, value labels, formats | CDC, FDA, NIH |
| SAS Dataset | .sas7bdat | Same as XPT + more | All federal |
| SPSS | .sav | Variable labels, value labels, missing codes | NIH surveys |
| Stata | .dta | Variable labels, value labels | NIH, Census |
| CDISC Define-XML | .xml | Full metadata spec for clinical trials | FDA required |
