# FAIR Data Demo

**Three NIH studies. One project. Shared semantic infrastructure.**

This repository demonstrates how [SDC](https://semanticdatacharter.com/) (Semantic Data Charter) delivers structural FAIR data compliance across real NIH-funded research studies, without mapping tables, without ETL pipelines, and without reconciliation layers.

## The FAIR Problem

NIH mandates FAIR data sharing. Researchers dutifully publish CSV files. But "available" is not "interoperable."

Consider three NIH-funded studies — NHANES, ADNI, and SPRINT — all collecting demographics, vital signs, lab results, and medications. Each uses NIH Common Data Elements. Each publishes data. None of it is structurally compatible.

The same concept — systolic blood pressure — appears as:
- `BPXSY1` in NHANES (SAS transport, mmHg implied)
- `VSSBP` in ADNI (CSV, units in a separate column)
- `sbp` in SPRINT (CSV, no units metadata)

Three encodings. Three parsers. Three mapping efforts. Multiply by every CDE, every study, every institution. This is the state of FAIR data in 2026.

## The SDC Solution

The NIH CDE catalog publishes data element definitions: names, descriptions, data types, permissible values, and usage contexts. SDC takes all of that published information and maps each CDE to a **content-compliant SDC model component**, preserving every semantic detail from the original definition and then extending it with formal constraints that the CDE catalog does not provide: explicit numeric ranges, required units, ontology predicates, and XSD-enforced validation rules. The result is the best deterministic model possible for each concept, not a lossy approximation.

Each component is identified by a permanent `ct_id` (CUID2) and carries its own compiled schema, units, constraints, and semantic links. Consider systolic blood pressure: many variables affect the measurement, including device type (manual cuff vs. automated oscillometric vs. invasive arterial line), patient position (seated, standing, supine), and anatomical location (upper arm, wrist, thigh). None of these contextual factors are captured in CDEs. At all. Ideally, each measurement context would be modeled as a distinct component with its own constraints, because a reading from an automated arm cuff and a reading from an invasive arterial line are not the same measurement. We understand that assumptions are often made in practice, but SDC4's goal is that domain experts create precisely scoped components and that those components are correctly reused across studies for the best accuracy possible.

In this demo, when NHANES, ADNI, and SPRINT need "systolic blood pressure," they reference the **same component**. Same `ct_id`. Same XSD schema. Same validation rules. Cross-study queries join on `ct_id`. No mapping. No ETL. No reconciliation.

## Why This Matters for Autonomous AI

Current AI and RAG pipelines attempt to solve this interoperability problem *probabilistically* — using LLMs to guess that `BPXSY1` and `VSSBP` mean the same thing. At scale, and at the edges of clinical complexity, this guessing produces hallucinations. The model is confident. The answer is wrong. The patient record is corrupted.

SDC compiles semantic meaning and constraints deterministically into the graph layer via a shared `ct_id`. An AI agent querying this knowledge graph doesn't have to guess what the data means — the structural physics of the data dictate the agent's boundaries. Constraints are enforced by schema validation, not by prompt engineering. The result is a mathematically secure foundation for AI-driven clinical data operations: zero hallucination risk on structure, zero ambiguity on semantics.

## What This Demo Contains

| Study | Type | NIH Institute | CDE Domains |
|-------|------|---------------|-------------|
| **NHANES** | Population Survey | CDC / NCHS | 10 domains |
| **ADNI** | Longitudinal Cohort | NIA | 8 domains |
| **SPRINT** | Randomized Trial | NHLBI | 7 domains |

**12 NIH CDE domains** covered. **5 shared across all 3 studies**:
- Demographics
- Vital Signs
- Laboratory Results
- Medications
- Medical History

Three different study designs. Three different NIH institutes. One shared semantic layer.

### CDE Coverage Matrix

| NIH CDE Domain | NHANES | ADNI | SPRINT |
|----------------|--------|------|--------|
| Demographics | X | X | X |
| Vital Signs | X | X | X |
| Laboratory Results | X | X | X |
| Medications | X | X | X |
| Medical History | X | X | X |
| Biospecimens | X | X | |
| Adverse Events | | X | X |
| Cognitive Assessment | | X | X |
| Substance Use | X | | |
| SDOH | X | | |
| Physical Function | X | | |
| Pain | X | | |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Access to an [SDCStudio](https://sdcstudio.axius-sdc.com/) instance with the NIH-CDE catalog

### 1. Clone and configure

```bash
git clone https://github.com/Axius-SDC/FAIR_Data_Demo.git
cd FAIR_Data_Demo
cp .env.example .env
```

### 2. Create components and assemble clusters via SDC_Agents

Use the [SDC_Agents](https://github.com/Axius-SDC/SDC_Agents) API to create and reuse NIH-CDE components for each study:

- Reuse existing catalog components (same `ct_id`) for shared concepts (demographics, vital signs, etc.)
- Mint new components for study-specific concepts
- Assemble components into clusters within the FAIR Data Demo project

### 3. Approve drafts and build data models in SDCStudio

In [SDCStudio](https://sdcstudio.axius-sdc.com/), review and approve draft components created by the agents, then build study-level data models:

- **NHANES** — 10 CDE domains
- **ADNI** — 8 CDE domains
- **SPRINT** — 7 CDE domains

### 4. Generate all output formats

Generate all 8 output formats for each study model:
- XSD schemas, XML instances, JSON, JSON-LD, HTML, RDF, SHACL, GQL

### 5. Add generated output to this repo

Place the generated files in the appropriate study directories:
- `models/NHANES/`
- `models/ADNI/`
- `models/SPRINT/`

### 6. Run the setup script

```bash
./scripts/setup.sh
```

This starts PostgreSQL, GraphDB, Redis, and the Django web application.

### 7. Explore

- **Demo UI**: http://localhost:8000 — study overview, CDE coverage matrix, SPARQL explorer
- **Django Admin**: http://localhost:8000/admin — credentials: `admin` / `admin`
- **GraphDB Workbench**: http://localhost:7200 — direct SPARQL access and graph visualization

### 8. (Optional) Load study data

Download source data from each study (see [source_data/README.md](source_data/README.md)), then convert and import once the datagen pipeline is built.

## Cross-Study SPARQL Queries

Six pre-built queries demonstrate structural interoperability:

| # | Query | What It Shows |
|---|-------|---------------|
| 1 | Cross-Study Demographics | Same demographic components across all 3 studies |
| 2 | Shared CDE Audit | Which components are reused vs. study-specific |
| 3 | Vital Signs Comparison | Shared units and measurement constraints |
| 4 | Lab Results Interoperability | Compatible result structures and reference ranges |
| 5 | Medication Overlap | Overlapping medication coding across studies |
| 6 | Cross-Study Medical History | Shared history components |

All queries join on `ct_id` — no mapping tables involved. See [sparql/README.md](sparql/README.md) for details.

**Note**: The current SPARQL queries use a placeholder vocabulary. They will be rewritten once real RDF triples are generated from SDCStudio models.

## The Challenge

Submit a payload that violates the NIH CDE constraints.

- The CSV will accept it.
- The SDC schema will reject it.

Try entering a systolic blood pressure of -50 mmHg, or a date of birth in the year 3000, or a medication dosage with no units. The CSV has no opinion. The SDC XSD does.

FAIR means more than findable and accessible. It means the data **means what it claims to mean** and can be **used without translation**.

## How It's Built

Every component in this demo was modeled in [SDCStudio](https://sdcstudio.axius-sdc.com/), the production platform for SDC-compliant data models. [SDC_Agents](https://github.com/Axius-SDC/SDC_Agents) create and reuse NIH-CDE catalog components via the SDCStudio API, and a human approves draft components before building the final data models.

The workflow:
1. Use SDC_Agents API to create/reuse NIH-CDE catalog components (same `ct_id` for shared concepts)
2. Agents assemble components into clusters within the FAIR Data Demo project
3. In SDCStudio, approve draft components and build study-level data models
4. Generate all output formats (XSD, XML, JSON, JSON-LD, HTML, RDF, SHACL, GQL)
5. Load RDF triples into GraphDB
6. Query across studies using SPARQL — joins on shared `ct_id`

No custom integration code. No study-specific adapters. The interoperability is structural.

## Architecture

```
                    ┌─────────────────────────────┐
                    │     Django Web Application   │
                    │  (Landing Page + SPARQL UI)  │
                    └──────────┬──────────────────-┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
     │  PostgreSQL   │  │  GraphDB   │  │    Redis    │
     │  (Django ORM) │  │  (RDF/OWL) │  │   (Cache)   │
     └───────────────┘  └────────────┘  └─────────────┘
```

**Memory target**: 4 GB total (runs on any modern laptop).

## Related Projects

- [SDCStudio](https://sdcstudio.axius-sdc.com/) — Production platform for SDC data models
- [SDC_Agents](https://github.com/Axius-SDC/SDC_Agents) — AI agents for automated SDC model generation
- [CordovaOS](https://github.com/Axius-SDC/CordovaOS) — Sovereign operating system demo (civil registry use case)
- [SDCRM](https://github.com/SemanticDataCharter/SDCRM) — SDC Reference Model specification

## License

Apache 2.0 — see [LICENSE](LICENSE).

Built by [Axius SDC](https://axius-sdc.github.io).
