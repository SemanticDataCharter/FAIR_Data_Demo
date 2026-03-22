# FAIR Data Demo

**Three NIH studies. One project. Shared semantic infrastructure.**

This repository demonstrates how [SDC4](https://github.com/Axius-SDC/SDCStudio) (Semantic Data Charter) delivers structural FAIR data compliance across real NIH-funded research studies — without mapping tables, without ETL pipelines, and without reconciliation layers.

## The FAIR Problem

NIH mandates FAIR data sharing. Researchers dutifully publish CSV files. But "available" is not "interoperable."

Consider three NIH-funded studies — NHANES, ADNI, and SPRINT — all collecting demographics, vital signs, lab results, and medications. Each uses NIH Common Data Elements. Each publishes data. None of it is structurally compatible.

The same concept — systolic blood pressure — appears as:
- `BPXSY1` in NHANES (SAS transport, mmHg implied)
- `VSSBP` in ADNI (CSV, units in a separate column)
- `sbp` in SPRINT (CSV, no units metadata)

Three encodings. Three parsers. Three mapping efforts. Multiply by every CDE, every study, every institution. This is the state of FAIR data in 2026.

## The SDC4 Solution

SDC4 models NIH CDEs as **reusable components** — each identified by a permanent `ct_id`, each carrying its own schema, units, constraints, and semantic links. When NHANES, ADNI, and SPRINT need "systolic blood pressure," they reference the **same component**. Same `ct_id`. Same XSD schema. Same validation rules.

Cross-study queries join on `ct_id`. No mapping. No ETL. No reconciliation.

## Why This Matters for Autonomous AI

Current AI and RAG pipelines attempt to solve this interoperability problem *probabilistically* — using LLMs to guess that `BPXSY1` and `VSSBP` mean the same thing. At scale, and at the edges of clinical complexity, this guessing produces hallucinations. The model is confident. The answer is wrong. The patient record is corrupted.

SDC4 compiles semantic meaning and constraints deterministically into the graph layer via a shared `ct_id`. An AI agent querying this knowledge graph doesn't have to guess what the data means — the structural physics of the data dictate the agent's boundaries. Constraints are enforced by schema validation, not by prompt engineering. The result is a mathematically secure foundation for AI-driven clinical data operations: zero hallucination risk on structure, zero ambiguity on semantics.

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
- Access to an [SDCStudio](https://github.com/Axius-SDC/SDCStudio) instance with the NIH-CDE catalog

### 1. Clone and configure

```bash
git clone https://github.com/Axius-SDC/FAIR_Data_Demo.git
cd FAIR_Data_Demo
cp .env.example .env
```

### 2. Upload templates to SDCStudio

Upload the Markdown templates from `templates/` to the FAIR Data Demo project in SDCStudio:

- `templates/nhanes_study_data.md` — NHANES (10 domains, 17 reused + 15 minted components)
- `templates/adni_study_data.md` — ADNI (8 domains, 21 reused + 14 minted components)
- `templates/sprint_study_data.md` — SPRINT (7 domains, 21 reused + 14 minted components)

SDCStudio assembles the models by directly reusing existing NIH-CDE catalog components (same `ct_id`) and minting fresh components for study-specific concepts.

### 3. Generate models and export

In SDCStudio, generate all 8 output formats for each study model:
- XSD schemas, XML instances, JSON, JSON-LD, HTML, RDF, SHACL, GQL

### 4. Add generated output to this repo

Place the generated files in the appropriate study directories:
- `models/NHANES/`
- `models/ADNI/`
- `models/SPRINT/`

### 5. Run the setup script

```bash
./scripts/setup.sh
```

This starts PostgreSQL, GraphDB, Redis, and the Django web application.

### 6. Explore

- **Demo UI**: http://localhost:8000 — study overview, CDE coverage matrix, SPARQL explorer
- **Django Admin**: http://localhost:8000/admin — credentials: `admin` / `admin`
- **GraphDB Workbench**: http://localhost:7200 — direct SPARQL access and graph visualization

### 7. (Optional) Load study data

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
- The SDC4 schema will reject it.

Try entering a systolic blood pressure of -50 mmHg, or a date of birth in the year 3000, or a medication dosage with no units. The CSV has no opinion. The SDC4 XSD does.

FAIR means more than findable and accessible. It means the data **means what it claims to mean** and can be **used without translation**.

## How It's Built

Every component in this demo was modeled in [SDCStudio](https://github.com/Axius-SDC/SDCStudio) — the production platform for SDC4-compliant data models. The Markdown templates in `templates/` reference existing NIH-CDE catalog components by `ct_id`, and SDCStudio assembles the study models by reusing those components directly.

The workflow:
1. Write Markdown templates referencing existing catalog components via `**Reuse**: ct_id`
2. Upload templates to SDCStudio's FAIR Data Demo project
3. SDCStudio assembles models (reusing shared components, minting study-specific ones)
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

- [SDCStudio](https://github.com/Axius-SDC/SDCStudio) — Production platform for SDC4 data models
- [SDC_Agents](https://github.com/Axius-SDC/SDC_Agents) — AI agents for automated SDC4 model generation
- [CordovaOS](https://github.com/Axius-SDC/CordovaOS) — Sovereign operating system demo (civil registry use case)
- [SDCRM](https://github.com/SemanticDataCharter/SDCRM) — SDC4 Reference Model specification

## License

Apache 2.0 — see [LICENSE](LICENSE).

Built by [Axius SDC](https://axius-sdc.github.io).
