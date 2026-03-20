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
- Python 3.12+ (for data conversion only)

### 1. Clone and configure

```bash
git clone https://github.com/Axius-SDC/FAIR_Data_Demo.git
cd FAIR_Data_Demo
cp .env.example .env
```

### 2. Run the setup script

```bash
./scripts/setup.sh
```

This starts PostgreSQL, GraphDB, Redis, and the Django web application.

### 3. Explore

- **Demo UI**: http://localhost:8000 — study overview, CDE coverage matrix, SPARQL explorer
- **Django Admin**: http://localhost:8000/admin — credentials: `admin` / `admin`
- **GraphDB Workbench**: http://localhost:7200 — direct SPARQL access and graph visualization

### 4. (Optional) Load study data

Download source data from each study (see [source_data/README.md](source_data/README.md)), then:

```bash
python datagen/convert_all.py
docker compose exec web python manage.py import_data
```

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

## The Challenge

Submit a payload that violates the NIH CDE constraints.

- The CSV will accept it.
- The SDC4 schema will reject it.

Try entering a systolic blood pressure of -50 mmHg, or a date of birth in the year 3000, or a medication dosage with no units. The CSV has no opinion. The SDC4 XSD does.

FAIR means more than findable and accessible. It means the data **means what it claims to mean** and can be **used without translation**.

## How It's Built

Every component in this demo was modeled in [SDCStudio](https://github.com/Axius-SDC/SDCStudio) — the production platform for SDC4-compliant data models. The Django apps, XSD schemas, XML instances, RDF triples, and SPARQL queries were all generated from those models.

The workflow:
1. Model NIH CDEs as SDC4 components in SDCStudio
2. Reuse components across study data models (shared `ct_id`)
3. Generate Django apps via SDCStudio AppGen
4. Convert source data (CSV/XPT) to validated XML instances
5. Extract RDF triples into GraphDB
6. Query across studies using SPARQL

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
