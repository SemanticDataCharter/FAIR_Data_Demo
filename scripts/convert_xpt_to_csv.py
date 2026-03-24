#!/usr/bin/env python3
"""
Convert NHANES and BRFSS XPT (SAS transport) files to CSV with metadata extraction.

NHANES and BRFSS distribute data as .XPT files with embedded SAS metadata: column
labels, value labels, and format information. This script converts XPT to CSV and
saves the metadata as sidecar JSON files for use by the pipeline.

The metadata is critical because both surveys use coded column names (e.g. BPXSY1,
_AGE80) that are meaningless without the SAS labels. The pipeline uses these labels
for better catalog component matching.

Usage:
    python scripts/convert_xpt_to_csv.py

Requires: pip install pyreadstat

Output per XPT file:
    source_data/nhanes/DEMO_J.csv          — tabular data
    source_data/nhanes/DEMO_J.json         — column metadata (4.2.0 sidecar format)
    source_data/brfss/LLCP2022.csv         — tabular data
    source_data/brfss/LLCP2022.json        — column metadata (4.2.0 sidecar format)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

NHANES_DIR = Path("source_data/nhanes")
BRFSS_DIR = Path("source_data/brfss")

# Expected XPT files from NHANES 2017-2018 cycle
NHANES_XPT_FILES = [
    "DEMO_J.XPT",
    "BPX_J.XPT",
    "CBC_J.XPT",
    "TCHOL_J.XPT",
    "RXQ_RX_J.XPT",
    "MCQ_J.XPT",
    "SMQ_J.XPT",
    "PFQ_J.XPT",
]

BRFSS_XPT_FILE = "LLCP2022.XPT"


def _read_xpt(xpt_path: Path):
    """Read an XPT file, handling character set issues across CDC datasets.

    pyreadstat.read_xport can fail on files with non-standard character set
    markers (common in BRFSS). Falls back to pandas.read_sas which is more
    lenient but returns no SAS metadata.
    """
    import pyreadstat

    try:
        return pyreadstat.read_xport(str(xpt_path))
    except Exception:
        pass

    # Fallback: pandas.read_sas handles XPT without character set restrictions
    import pandas as pd

    df = pd.read_sas(str(xpt_path), format="xport", encoding="latin-1")
    return df, None


def convert_xpt_to_csv(xpt_path: Path) -> tuple[Path, Path]:
    """Convert a single XPT file to CSV + metadata JSON. Returns both paths."""
    csv_path = xpt_path.with_suffix(".csv")
    meta_path = xpt_path.with_suffix(".json")

    df, meta = _read_xpt(xpt_path)
    df.to_csv(csv_path, index=False)

    # Extract metadata
    metadata = {
        "source_file": xpt_path.name,
        "file_label": (meta.file_label or "") if meta else "",
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": {},
    }

    for col in df.columns:
        if meta:
            sas_label = meta.column_names_to_labels.get(col, "")
        else:
            sas_label = ""

        col_meta: dict = {
            "label": sas_label,
            "description": sas_label,
        }

        if meta:
            col_meta["original_type"] = meta.readstat_variable_types.get(col, "")

            # Value labels (coded values -> human-readable)
            # e.g. RIAGENDR: {1.0: "Male", 2.0: "Female"}
            value_label_name = meta.variable_to_label.get(col, "")
            if value_label_name and value_label_name in meta.value_labels:
                raw_labels = meta.value_labels[value_label_name]
                # Convert numeric keys to strings for JSON serialization
                col_meta["value_labels"] = {
                    str(k): v for k, v in raw_labels.items()
                }
                # 4.2.0 sidecar: enumeration as list of display values
                col_meta["enumeration"] = list(raw_labels.values())

            # Variable format (e.g. "F8.0" for numeric, "$CHAR50" for string)
            if hasattr(meta, "original_variable_types"):
                fmt = meta.original_variable_types.get(col, "")
                if fmt:
                    col_meta["sas_format"] = fmt

        metadata["columns"][col] = col_meta

    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    return csv_path, meta_path


def _convert_directory(directory: Path, xpt_files: list[str], label: str) -> tuple[int, int, int]:
    """Convert XPT files in a directory. Returns (converted, skipped, missing)."""
    if not directory.exists():
        print(f"  {label} directory not found: {directory}")
        print(f"  Create it and download XPT files per source_data/README.md")
        return 0, 0, len(xpt_files)

    converted = 0
    skipped = 0
    missing = 0

    for filename in xpt_files:
        xpt_path = directory / filename
        csv_path = xpt_path.with_suffix(".csv")
        meta_path = xpt_path.with_suffix(".json")

        if not xpt_path.exists():
            # Fuzzy fallback: case-insensitive, strip whitespace from filenames
            # (some ZIP tools leave trailing spaces in extracted filenames)
            match = next(
                (f for f in directory.iterdir()
                 if f.name.strip().lower() == filename.lower()),
                None,
            )
            if match:
                # Rename to the canonical name so downstream tools aren't affected
                clean_path = directory / filename
                if match.name != filename:
                    match.rename(clean_path)
                    print(f"  [..] Renamed: {match.name!r} -> {filename}")
                xpt_path = clean_path
            else:
                print(f"  [--] Missing: {filename}")
                missing += 1
                continue

        if csv_path.exists() and meta_path.exists():
            print(f"  [OK] Already converted: {csv_path.name} + {meta_path.name}")
            skipped += 1
            continue

        try:
            csv_out, meta_out = convert_xpt_to_csv(xpt_path)
            with open(meta_out) as f:
                meta_data = json.load(f)
            labels = sum(1 for c in meta_data["columns"].values() if c.get("label"))
            value_maps = sum(1 for c in meta_data["columns"].values() if c.get("value_labels"))
            print(f"  [OK] {xpt_path.name} -> {csv_out.name} + {meta_out.name}")
            print(f"       {meta_data['column_count']} columns, {labels} labels, {value_maps} value maps")
            converted += 1
        except Exception as e:
            print(f"  [!!] Failed: {xpt_path.name}: {e}", file=sys.stderr)

    return converted, skipped, missing


def main() -> None:
    # --- NHANES ---
    print("NHANES XPT Conversion")
    print("-" * 40)
    nh_conv, nh_skip, nh_miss = _convert_directory(NHANES_DIR, NHANES_XPT_FILES, "NHANES")
    print(f"\n  Converted: {nh_conv}, Skipped: {nh_skip}, Missing: {nh_miss}")

    if nh_miss:
        print()
        print("  Download missing NHANES XPT files from:")
        print("  https://wwwn.cdc.gov/nchs/nhanes/Default.aspx")

    # --- BRFSS ---
    print()
    print("BRFSS XPT Conversion")
    print("-" * 40)
    br_conv, br_skip, br_miss = _convert_directory(BRFSS_DIR, [BRFSS_XPT_FILE], "BRFSS")
    print(f"\n  Converted: {br_conv}, Skipped: {br_skip}, Missing: {br_miss}")

    if br_miss:
        print()
        print("  Download the BRFSS 2022 LLCP XPT file from:")
        print("  https://www.cdc.gov/brfss/annual_data/annual_2022.html")


if __name__ == "__main__":
    main()
