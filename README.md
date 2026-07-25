# FAIR Data Demo

**Three federal health studies. One project. Shared semantic infrastructure.**

All source data is freely downloadable with no registration.

This repository demonstrates how [SDC](https://semanticdatacharter.com/) (Semantic Data Charter) delivers structural FAIR data compliance across real federal health studies, without mapping tables, without ETL pipelines, and without reconciliation layers.

## The FAIR Problem

NIH mandates FAIR data sharing. Researchers dutifully publish CSV files. But "available" is not "interoperable."

Consider three federal health studies — NHANES, BRFSS, and CMS DE-SynPUF — all collecting demographics, vital signs, medical history, and medications. Each uses NIH Common Data Elements. Each publishes data. None of it is structurally compatible.

The same concept — a diabetes indicator — appears as:
- `DIQ010` in NHANES (SAS transport, coded 1/2/3)
- `DIABETE4` in BRFSS (SAS transport, coded 1/2/3/4)
- `SP_DIABETES` in CMS (CSV, coded 1/2)

Three encodings. Three parsers. Three mapping efforts. Multiply by every CDE, every study, every institution. This is the state of FAIR data in 2026.

## The SDC Solution

The NIH CDE catalog publishes data element definitions: names, descriptions, data types, permissible values, and usage contexts. SDC takes all of that published information and maps each CDE to a **content-compliant SDC model component**, preserving every semantic detail from the original definition and then extending it with formal constraints that the CDE catalog does not provide: explicit numeric ranges, required units, ontology predicates, and XSD-enforced validation rules. The result is the best deterministic model possible for each concept, not a lossy approximation.

Each component is identified by a permanent `ct_id` (CUID2) and carries its own compiled schema, units, constraints, and semantic links. Consider systolic blood pressure: many variables affect the measurement, including device type (manual cuff vs. automated oscillometric vs. invasive arterial line), patient position (seated, standing, supine), and anatomical location (upper arm, wrist, thigh). None of these contextual factors are captured in CDEs. At all. Ideally, each measurement context would be modeled as a distinct component with its own constraints, because a reading from an automated arm cuff and a reading from an invasive arterial line are not the same measurement. We understand that assumptions are often made in practice, but SDC4's goal is that domain experts create precisely scoped components and that those components are correctly reused across studies for the best accuracy possible.

In this demo, when NHANES, BRFSS, and CMS need "systolic blood pressure," they reference the **same component**. Same `ct_id`. Same XSD schema. Same validation rules. Cross-study queries join on `ct_id`. No mapping. No ETL. No reconciliation.

## Why This Matters for Autonomous AI

Current AI and RAG pipelines attempt to solve this interoperability problem *probabilistically* — using LLMs to guess that `BPXSY1` and `BPHIGH6` mean the same thing. At scale, and at the edges of clinical complexity, this guessing produces hallucinations. The model is confident. The answer is wrong. The patient record is corrupted.

SDC compiles semantic meaning and constraints deterministically into the graph layer via a shared `ct_id`. An AI agent querying this knowledge graph doesn't have to guess what the data means — the structural physics of the data dictate the agent's boundaries. Constraints are enforced by schema validation, not by prompt engineering. The result is a mathematically secure foundation for AI-driven clinical data operations: zero hallucination risk on structure, zero ambiguity on semantics.

## What This Demo Contains

| Study | Type | Agency | Format | Access |
|-------|------|--------|--------|--------|
| **NHANES** | Population Survey | CDC / NCHS | 8 XPT files | Direct download |
| **BRFSS** | Telephone Survey | CDC | 1 XPT file | Direct download |
| **CMS DE-SynPUF** | Medicare Claims (Synthetic) | CMS | CSV (Sample 1) | Direct download |

**8 CDE domains** covered. **3 shared across all 3 studies**:
- Demographics
- Medical History
- Medications (NHANES + CMS)

Three different study designs. Three different federal agencies. One shared semantic layer.

### CDE Coverage Matrix

| Domain | NHANES | BRFSS | CMS |
|--------|--------|-------|-----|
| Demographics | X | X | X |
| Medical History | X | X | X |
| Substance Use | X | X | |
| Vital Signs (BP, BMI) | X | X | |
| Medications | X | | X |
| Physical Function | X | X | |
| Lab Results | X | | |
| SDOH | X | | |

## What's Included vs. What You Download

**Included in this repository:**
- `models/` -- 8 SDC4 model packages (XSD schemas, XML instances, JSON, JSON-LD, HTML, RDF, SHACL, GQL) exported from SDCStudio
- `apps/` -- 8 generated application packages (self-contained Django projects, lightweight FOSS stack, with full SDC4 integration)
- `scripts/` -- Pipeline scripts, enrichment code, and conversion tools
- `sparql/` -- Pre-built cross-study SPARQL queries

**Not included (download separately):**
- `source_data/` -- Raw federal health data files (NHANES XPT, BRFSS XPT, CMS CSV). These are freely available from CDC and CMS with no registration. See [source_data/README.md](source_data/README.md) for download instructions.

The model and app packages let you inspect the complete SDC4 output without running the pipeline or downloading source data. If you want to reproduce the pipeline end-to-end, follow the Quick Start below.

## Quick Start

### Prerequisites

- Python 3.11+
- Access to an [SDCStudio](https://sdcstudio.axius-sdc.com/) instance with the NIH-CDE catalog
- SDCStudio API key

### 1. Clone and configure

```bash
git clone https://github.com/Axius-SDC/FAIR_Data_Demo.git
cd FAIR_Data_Demo

# Create and activate a Python virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

cp .env.example .env
# Edit .env with your SDCStudio URL and API key
pip install -r requirements-pipeline.txt
```

**Important**: In SDCStudio, go to **Settings > Preferences** and set your **Default Project** to the project where new components should be created. The assembly API creates all new components and data models in the Modeler's default project. If no default project is set, assembly will fail.

### 2. Download source data

Follow the instructions in [source_data/README.md](source_data/README.md) to download the freely available federal health data. NHANES and BRFSS XPT files need conversion to CSV with metadata sidecars:

```bash
python scripts/convert_xpt_to_csv.py
```

This produces `.csv` data files and `.json` sidecar files containing column descriptions, value labels, and enumerations. The sidecar metadata is referenced via `metadata_path` in `sdc-agents.yaml` and merged into introspection results by SDC_Agents 4.2.0, enabling automatic component matching on SAS labels instead of coded column names.

CMS data is already CSV and needs no conversion.

### 3. Run the SDC Agents pipeline

```bash
python scripts/run_pipeline.py --study all
```

The pipeline runs 7 steps with human approval gates:

| Step | Action | Human Review |
|------|--------|--------------|
| 1 | Introspect all datasources | No |
| 2 | Verify catalog components exist | No |
| 3 | Discover component matches + manual overrides | Yes |
| 4 | Propose cluster hierarchy per study | Yes |
| 5 | Check wallet balance and estimate cost | Yes |
| 6 | Assemble data models (reuse + mint) | No |
| 7 | Download schemas and artifacts | No |

Each step caches results in `.sdc-cache/` so the pipeline can resume from any point:

```bash
python scripts/run_pipeline.py --study nhanes --step 6
```

### 4. Review and approve in SDCStudio

The assembly pipeline uses an LLM to infer component types, constraints, descriptions, and semantic links from the introspected data. This is a **probabilistic process**: the LLM makes its best determination based on column names, sample values, and sidecar metadata, but it cannot guarantee correctness. A blood pressure column might be typed as XdString instead of XdQuantity. A unit might be omitted. An enumeration might include spurious values. A semantic link might point to the wrong ontology concept.

This is why the pipeline produces **draft components**, not published ones. A human domain expert must review each draft in [SDCStudio](https://sdcstudio.axius-sdc.com/) before it becomes part of the permanent catalog:

- **Verify component types** — confirm each component uses the correct SDC4 type (XdQuantity vs. XdCount vs. XdString, etc.)
- **Check constraints** — validate numeric ranges, string patterns, enumeration values, and required units against the study codebook
- **Assign semantic links** — connect components to the correct ontology concepts (LOINC, SNOMED CT, UMLS, etc.) where the LLM's suggestions are incomplete or incorrect
- **Edit descriptions** — refine LLM-generated descriptions to accurately reflect the study variable's meaning
- **Publish** — once a component is correct, publish it to make it available for reuse across studies

After all components are reviewed and published, generate all 8 output formats:
- XSD schemas, XML instances, JSON, JSON-LD, HTML, RDF, SHACL, GQL

SDCStudio generates the complete application from the approved data models.

### 5. Generate XML instances from source data

After models are approved:

```bash
python scripts/generate_instances.py --study all --validate
```

This generates validated XML instances in `output/instances/`.

## Cross-Study SPARQL Queries

Six pre-built queries demonstrate structural interoperability:

| # | Query | What It Shows |
|---|-------|---------------|
| 1 | Cross-Study Demographics | Same demographic components across all 3 studies |
| 2 | Shared CDE Audit | Which components are reused vs. study-specific |
| 3 | Vital Signs Comparison | Shared units and measurement constraints |
| 4 | Chronic Conditions Interoperability | Shared medical history components across studies |
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

Every component in this demo was modeled in [SDCStudio](https://sdcstudio.axius-sdc.com/), the production platform for SDC-compliant data models. [SDC_Agents](https://github.com/Axius-SDC/SDC_Agents) create and reuse NIH-CDE catalog components via the SDCStudio API, and a human approves draft components before building the final data models. SDCStudio then generates the complete application from the approved models.

The workflow:
1. Use SDC_Agents API to create/reuse NIH-CDE catalog components (same `ct_id` for shared concepts)
2. Agents assemble components into clusters within the FAIR Data Demo project
3. In SDCStudio, approve draft components and build study-level data models
4. Generate all output formats (XSD, XML, JSON, JSON-LD, HTML, RDF, SHACL, GQL)
5. SDCStudio generates the application from the data models
6. Query across studies using SPARQL — joins on shared `ct_id`

No custom integration code. No study-specific adapters. The interoperability is structural.

## The Enrichment Story

The 567 components in this demo did not arrive self-describing. Getting them there required significant one-time effort, and that effort is the whole point.

### What we found

Three federal datasets, three different metadata formats, none structurally compatible:

| Study | Metadata Format | How You Access It |
|-------|----------------|-------------------|
| **NHANES** | SAS transport labels + HTML codebook | Parse `.xpt` variable labels, scrape CDC HTML pages with BeautifulSoup |
| **BRFSS** | HTML codebook (400+ pages) | Parse HTML tables, cross-reference variable-specific coding |
| **CMS DE-SynPUF** | PDF codebook + no machine-readable metadata | Hardcode 121 variable definitions by hand from the PDF |

None of these formats share a schema. None publish constraints (numeric ranges, required units, valid enumerations) in a machine-readable form. The "FAIR" data is findable and accessible, but it is not interoperable and not reusable without significant manual effort.

### What it took

~1,974 lines of Python in `scripts/enrichment/`:

- **`metadata_nhanes.py`**: Parses SAS transport labels and augments with descriptions, constraints, and units per NHANES codebook
- **`metadata_brfss.py`**: Scrapes BRFSS HTML codebook, extracts variable descriptions, value labels, and coding schemes
- **`metadata_cms.py`**: 121 hardcoded CMS variable definitions (descriptions, data types, enumerations) transcribed from the PDF codebook
- **`semantic_mappings.py`**: 85 curated LOINC and SNOMED CT mappings linking components to standard ontology concepts
- **`component_mapper.py`**: Maps enriched metadata to SDC4 component types with appropriate constraints
- **`api_client.py`**: Batch updates components in SDCStudio via the API (800+ API calls)

This is the work that "FAIR" compliance actually requires when your source data lacks self-describing metadata.

### The punchline

All of this was a **one-time effort**. Now that the 567 components exist in the SDC catalog, every subsequent user who needs NHANES demographics, BRFSS vital signs, or CMS claims data gets **100% catalog reuse at $0.00**. The metadata, constraints, semantic links, and validation rules travel inside each component permanently, identified by its `ct_id`.

When you run this pipeline, the discovery step finds all 567 components already in the catalog. Zero new components to mint. Zero enrichment scripts to run. Zero codebooks to parse. The ~2,000 lines of enrichment code in this repository exist solely to document what it took the first time, so you understand what you are no longer paying for.

### The contrast

Without SDC, every new researcher working with these datasets repeats some version of this work from scratch: parsing codebooks, hardcoding definitions, mapping variables across studies, reconciling units and enumerations. The NIH CDE catalog publishes definitions but not constraints. The data files publish values but not semantics. The gap between "available" and "interoperable" is filled by graduate students, one study at a time, and their work is never reusable by the next team.

## Repository Structure

```
FAIR_Data_Demo/
├── scripts/                     # Pipeline scripts
│   ├── run_pipeline.py          # 7-step SDC Agents orchestration
│   ├── generate_instances.py    # Post-assembly XML generation
│   ├── convert_xpt_to_csv.py    # NHANES + BRFSS XPT preprocessing
│   ├── fair_constants.py        # Shared ct_ids and study metadata
│   └── enrichment/              # One-time metadata enrichment (~1,974 lines)
│       ├── metadata_nhanes.py   # NHANES SAS labels + codebook parsing
│       ├── metadata_brfss.py    # BRFSS HTML codebook scraping
│       ├── metadata_cms.py      # CMS hardcoded definitions (121 variables)
│       ├── semantic_mappings.py  # 85 LOINC/SNOMED CT mappings
│       ├── component_mapper.py  # Metadata → SDC4 component type mapping
│       └── api_client.py        # Batch SDCStudio API updates
├── source_data/                 # Raw study data (NOT included -- user downloads separately)
│   ├── nhanes/
│   ├── brfss/
│   └── cms/
├── models/                      # SDC4 model packages (INCLUDED -- 8 zip files)
│   ├── NHANES/                  #   Blood-Pressure, Cholesterol, Medications
│   ├── BRFSS/                   #   Brfss
│   └── CMS/                     #   Beneficiary, Inpatient, Outpatient, Prescriptions
├── sparql/                      # Pre-built SPARQL queries
├── apps/                        # Generated app packages, FOSS stack (INCLUDED -- 8 zip files)
├── sdc-agents.yaml              # SDC Agents configuration (13 datasources)
└── requirements-pipeline.txt    # Pipeline dependencies
```

## The Public Good Guarantee

The US taxpayers already paid for this data. Why is the industry charging researchers thousands of dollars to map it over and over again? Once a publicly published, standards-based, content-compliant component is built, it should be free for reuse. Axius SDC paid the initial $82.40 to compile the exact semantic boundaries of these federal datasets into permanent CUIDs, plus the engineering cost of ~2,000 lines of enrichment code to extract metadata that the source datasets should have included but did not. Now that the physics are built, they belong to the public. When you run this pipeline, your cost is $0.00. FOR REAL.

## Related Projects

- [SDCStudio](https://sdcstudio.axius-sdc.com/) — Production platform for SDC data models
- [SDC_Agents](https://github.com/Axius-SDC/SDC_Agents) — AI agents for automated SDC model generation
- [CordovaOS](https://github.com/Axius-SDC/CordovaOS) — Sovereign operating system demo (civil registry use case)
- [SDCRM](https://github.com/SemanticDataCharter/SDCRM) — SDC Reference Model specification

## License

Apache 2.0 — see [LICENSE](LICENSE).

Built by [Axius SDC](https://axius-sdc.github.io).
