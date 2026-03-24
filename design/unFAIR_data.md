# unFAIR Data: What We Actually Found

## The Goal

Build a FAIR Data Demo that anyone can reproduce in 10 minutes. No registration. No application forms. No committee approval. Clone the repo, download three public datasets, run one command, get validated SDC4 components with full provenance.

That was the goal. Here is what actually happened.

## The Access Problem: ADNI and SPRINT

The original demo design called for three datasets spanning different federal agencies and health domains. Two of them never made it past the download step.

**ADNI (Alzheimer's Disease Neuroimaging Initiative)** requires committee approval through the LONI Image and Data Archive. The application demands institutional affiliation and a proposed-use statement. The Data Sharing and Publications Committee "generally reviews data use applications within two weeks of submission." Incomplete applications or those "without a clear focus will not receive approval." At the time of writing, the repository page displayed: "This repository is under review for potential modification in compliance with Administration directives."

**SPRINT (Systolic Blood Pressure Intervention Trial)** requires an NHLBI BioLINCC Data Use Agreement. Another bureaucratic process. Another form. Another wait.

Neither dataset can be linked in a README and downloaded in 10 minutes. Both are unreliable under the current administration. We replaced them with freely downloadable federal data: BRFSS from the CDC and CMS DE-SynPUF from Medicare.

## The Download Problem: Finding the Right Files

Even "freely available" does not mean "easy to find."

**BRFSS (Behavioral Risk Factor Surveillance System)**: The [2022 Annual Survey Data page](https://www.cdc.gov/brfss/annual_data/annual_2022.html) lists multiple file formats with unclear descriptions. The correct file is "2022 BRFSS Data (SAS Transport Format) [ZIP - 64.3 MB]." It contains a single file, `LLCP2022.XPT`. This is not obvious without reading the full page. The page also notes that "some of the variable labels get truncated in the process of converting to the XPT format," which turns out to be an understatement: there are no labels at all.

**CMS DE-SynPUF (Medicare Claims Synthetic Public Use Files)**: Two levels of navigation. The [main page](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf) lists 20 samples. You must click through to the "DE1.0 Sample 1" sub-page to find download links. There you find four separate ZIP files, each containing one CSV. The page also lists files you do not need (2009/2010 beneficiary files, carrier claims) with no guidance on which subset is sufficient for any purpose.

**NHANES**: The least problematic of the three. Freely available from the CDC without application. Still uses cryptic column codes. Still requires a separate codebook to interpret.

## The Filename Problem: Invisible Corruption

After downloading, the files did not have the names we expected.

**NHANES XPT files** downloaded with lowercase `.xpt` extensions (`DEMO_J.xpt`) instead of the expected `.XPT`. Exact path matching failed. The script's initial fallback tried fully-lowercased names like `demo_j.xpt`, which did not match the actual on-disk name `DEMO_J.xpt` (uppercase stem, lowercase extension).

**BRFSS XPT ZIP** extracted `LLCP2022.XPT ` with a trailing space in the filename. Invisible to the user. Fails silently on path lookup. The user sees:

```
[--] Missing: LLCP2022.XPT
```

...and assumes their download was wrong. It was not wrong. The filename had an invisible trailing space baked into the ZIP archive by the CDC.

**BRFSS ASC ZIP** has the same bug. The CDC also publishes BRFSS as a fixed-width ASCII flat file. The ZIP extracts `LLCP2022.ASC ` — another trailing space. The file itself is 914 MB, 445,132 records, each exactly 2,053 characters wide. No delimiters. No headers. No column names. A wall of digits:

```
01              0102032022     11002022000001 ...
```

To parse it, you need the [HTML variable layout page](https://www.cdc.gov/brfss/annual_data/2022/llcp_varlayout_22_onecolumn.html) to know that columns 1-2 are `_STATE` and columns 3-4 are `FMONTH`. That page provides column positions and field widths, nothing else. The ASC file contains strictly less information than the XPT (which at least embeds column names), weighs 914 MB vs 1.1 GB, and exists as an additional download option on the same page with no guidance on which format to choose or why. It adds to the confusion without adding to the data.

We built case-insensitive file detection with whitespace stripping and auto-rename into the conversion script:

```
[..] Renamed: 'LLCP2022.XPT ' -> LLCP2022.XPT
[..] Renamed: 'DEMO_J.xpt' -> DEMO_J.XPT
[..] Renamed: 'BPX_J.xpt' -> BPX_J.XPT
[..] Renamed: 'CBC_J.xpt' -> CBC_J.XPT
[..] Renamed: 'TCHOL_J.xpt' -> TCHOL_J.XPT
[..] Renamed: 'RXQ_RX_J.xpt' -> RXQ_RX_J.XPT
[..] Renamed: 'MCQ_J.xpt' -> MCQ_J.XPT
[..] Renamed: 'SMQ_J.xpt' -> SMQ_J.XPT
[..] Renamed: 'PFQ_J.xpt' -> PFQ_J.XPT
```

A casual user would not have built that workaround. A casual user would have given up.

## The Encoding Problem: Character Sets in SAS Transport Files

pyreadstat is the standard Python library for reading SAS transport (XPT) files. It worked fine on NHANES. It failed on BRFSS.

**First attempt** (default UTF-8):

```
[!!] Failed: LLCP2022.XPT: 'utf-8' codec can't decode byte 0xb4 in position 5: invalid start byte
```

Byte `0xb4` is an acute accent in latin-1, embedded in CDC SAS metadata.

**Second attempt** (explicit `encoding="latin-1"`):

```
[!!] Failed: LLCP2022.XPT: File has an unsupported character set
```

pyreadstat rejects the file's internal character set marker entirely. The encoding parameter does not help because pyreadstat validates the SAS file's own character set declaration before it even attempts to decode.

**Workaround**: Fall back to `pandas.read_sas()`, which is more lenient about character sets. The tradeoff: `pandas.read_sas()` returns zero SAS metadata. No column labels. No value maps. No format information. Just raw data with cryptic column headers.

## The Metadata Problem: 328 Columns, Zero Labels

The BRFSS fallback worked. We got data. We got nothing else.

```
[OK] LLCP2022.XPT -> LLCP2022.csv + LLCP2022.json
     328 columns, 0 labels, 0 value maps
```

A 1.1 GB file. 328 columns. Column names like `_AGE80`, `DIABETE4`, `_SMOKER3`, `_BMI5`, `HTM4`, `WTK3`. Not one embedded description of what any column means.

The CDC publishes three separate documentation artifacts for this data, none of which are embedded in or linked from the data file:

1. **An [HTML variable layout page](https://www.cdc.gov/brfss/annual_data/2022/llcp_varlayout_22_onecolumn.html)** listing ~370 variable names with starting column position and field length. No descriptions. No value labels. No question text. No valid ranges. It is a fixed-width file parsing reference for the ASC format, not a codebook.

2. **A SAS-generated HTML codebook** (`USCODE22_LLCP_102523.HTML`, 1.8 MB, 30,547 lines, 974 HTML tables). This is the real documentation. For each variable it provides a label, section name, question number, column position, data type, SAS variable name, original survey question text, and value labels. It is genuinely useful. It is also a separate ZIP download, encoded in `windows-1252`, rendered in HTML 4.01 Transitional with inline CSS generated by SAS 9.4. It documents 324 of the 328 variables in the XPT. Four variables present in the actual data (`CPDEMO1C`, `DIABAGE4`, `NUMPHON4`, `USEMRJN4`) are not in the codebook at all.

3. **A separate codebook PDF** with the same content in a non-machine-readable format.

So the metadata exists, scattered across three formats, in three separate downloads, none linked from the data file, none embedded in the XPT, and none complete. A user who downloads only the XPT — the obvious action — gets 328 cryptic column codes and no way to know that a 1.8 MB HTML file in a differently-named ZIP on the same page would explain them. Mostly.

NHANES was marginally better. pyreadstat succeeded and extracted SAS labels:

```
DEMO_J.XPT:   46 columns, 46 labels, 0 value maps
BPX_J.XPT:    21 columns, 21 labels, 0 value maps
CBC_J.XPT:    22 columns, 22 labels, 0 value maps
TCHOL_J.XPT:   3 columns,  3 labels, 0 value maps
RXQ_RX_J.XPT: 13 columns, 13 labels, 0 value maps
MCQ_J.XPT:    76 columns, 76 labels, 0 value maps
SMQ_J.XPT:    37 columns, 37 labels, 0 value maps
PFQ_J.XPT:    36 columns, 36 labels, 0 value maps
```

Labels present, but the labels themselves are terse abbreviations. `BPXSY1` means "Systolic: Blood pres (1st rdg) mm Hg." `RIDAGEYR` means "Age in years at screening." Better than nothing. Still requires the codebook for real understanding.

CMS CSV headers follow the same pattern: `DESYNPUF_ID`, `BENE_SEX_IDENT_CD`, `BENE_RACE_CD`, `BENE_BIRTH_DT`. Code suffixes everywhere, no inline documentation.

## What SDC Does Differently

In the SDC pipeline, every column maps to a permanent component identified by a `ct_id` (a CUID2 that never changes). That component carries:

- A human-readable label and description
- Formal data type constraints (range, pattern, enumeration)
- Units of measure where applicable
- Ontology links to standard vocabularies
- Provenance back to the source dataset

The codebook knowledge moves from a separate PDF into the schema itself. Any study reusing the same concept (age, sex, BMI, systolic blood pressure) gets the same `ct_id`. Cross-study analysis becomes a join on permanent identifiers instead of a manual mapping exercise between incompatible column codes.

The conversion pipeline handles file chaos automatically. Case mismatches, trailing whitespace, encoding failures, missing metadata: the script resolves all of it. The user runs one command.

## Summary: Every Issue Encountered

| Issue | Dataset | What Happened | Our Fix | Casual User Outcome |
|-------|---------|--------------|---------|-------------------|
| Committee approval required | ADNI | LONI portal application, weeks of waiting | Replaced dataset | No data |
| Data Use Agreement required | SPRINT | NHLBI BioLINCC DUA process | Replaced dataset | No data |
| Confusing download page | BRFSS | Multiple formats, unclear descriptions | Step-by-step instructions in README | Wrong file or gives up |
| Two-level navigation | CMS DE-SynPUF | 20 samples, must click through to sub-page | Step-by-step instructions in README | Confused, downloads wrong files |
| Lowercase file extension | NHANES | `.xpt` instead of `.XPT`, path matching fails | Case-insensitive file detection with auto-rename | "File not found" error |
| Trailing space in XPT filename | BRFSS | ZIP extracts `LLCP2022.XPT ` (invisible space) | Whitespace-stripping file detection with auto-rename | "Missing: LLCP2022.XPT" and no idea why |
| Trailing space in ASC filename | BRFSS | ZIP extracts `LLCP2022.ASC ` (same bug, different format) | Same whitespace-stripping fix | Same silent failure |
| Useless alternate format | BRFSS | 914 MB fixed-width ASCII file, no headers, no column names, requires external layout doc to parse | Ignored it, used XPT instead | Downloads wrong format or tries both, confused by which to use |
| UTF-8 encoding failure | BRFSS | `0xb4` byte in SAS metadata breaks pyreadstat | Fallback to `pandas.read_sas()` | Script crash, no output |
| Unsupported character set | BRFSS | pyreadstat rejects internal charset marker even with latin-1 | Fallback to `pandas.read_sas()` | Script crash, no output |
| No embedded labels | BRFSS | 328 columns, 0 labels, 0 value maps in 1.1 GB XPT file | Manual COLUMN_OVERRIDES mapping to SDC components | 328 meaningless column codes |
| Codebook incomplete | BRFSS | SAS-generated HTML codebook documents 324 of 328 variables; 4 undocumented | Cross-referenced manually | 4 variables with no explanation anywhere |
| Codebook not linked from data | BRFSS | Three separate documentation artifacts (layout HTML, codebook HTML, codebook PDF) in separate ZIPs, none referenced by the data file | Found by browsing download page | Downloads data, has no idea codebook exists |
| Cryptic column codes | All three | `_AGE80`, `BPXSY1`, `BENE_SEX_IDENT_CD` | SDC components with permanent ct_id and descriptions | Requires separate codebook |
| No machine-readable codebook | BRFSS, CMS | Codebook is SAS-generated HTML (windows-1252) or PDF, not JSON/CSV | SDC schema carries all metadata inline | Manual cross-reference |

Every row in this table is a violation of at least one FAIR principle. These are not edge cases. These are the flagship public health datasets of the United States federal government.
