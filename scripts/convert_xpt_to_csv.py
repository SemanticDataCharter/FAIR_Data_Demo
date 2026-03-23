#!/usr/bin/env python3
"""
Convert NHANES XPT (SAS transport) files to CSV with metadata extraction.

NHANES distributes data as .XPT files with embedded SAS metadata: column labels,
value labels, and format information. This script converts XPT to CSV and saves
the metadata as sidecar JSON files for use by the pipeline.

The metadata is critical because NHANES uses coded column names (e.g. BPXSY1)
that are meaningless without the SAS label ("Systolic: Blood pres (1st rdg) mm Hg").
The pipeline uses these labels for better catalog component matching.

Usage:
    python scripts/convert_xpt_to_csv.py

Requires: pip install pyreadstat

Output per XPT file:
    source_data/nhanes/DEMO_J.csv          — tabular data
    source_data/nhanes/DEMO_J.json         — column metadata (4.2.0 sidecar format)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

NHANES_DIR = Path("source_data/nhanes")

# Expected XPT files from NHANES 2017-2018 cycle
XPT_FILES = [
    "DEMO_J.XPT",
    "BPX_J.XPT",
    "CBC_J.XPT",
    "TCHOL_J.XPT",
    "RXQ_RX_J.XPT",
    "MCQ_J.XPT",
    "SMQ_J.XPT",
    "PFQ_J.XPT",
]


def convert_xpt_to_csv(xpt_path: Path) -> tuple[Path, Path]:
    """Convert a single XPT file to CSV + metadata JSON. Returns both paths."""
    import pyreadstat

    csv_path = xpt_path.with_suffix(".csv")
    meta_path = xpt_path.with_suffix(".json")

    df, meta = pyreadstat.read_xport(str(xpt_path))
    df.to_csv(csv_path, index=False)

    # Extract metadata
    metadata = {
        "source_file": xpt_path.name,
        "file_label": meta.file_label or "",
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": {},
    }

    for col in df.columns:
        sas_label = meta.column_names_to_labels.get(col, "")
        col_meta: dict = {
            "label": sas_label,
            "description": sas_label,
            "original_type": meta.readstat_variable_types.get(col, ""),
        }

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


def main() -> None:
    if not NHANES_DIR.exists():
        print(f"NHANES directory not found: {NHANES_DIR}")
        print("Create it and download XPT files per source_data/README.md")
        sys.exit(1)

    converted = 0
    skipped = 0
    missing = 0

    for filename in XPT_FILES:
        xpt_path = NHANES_DIR / filename
        csv_path = xpt_path.with_suffix(".csv")
        meta_path = xpt_path.with_suffix(".json")

        if not xpt_path.exists():
            # Also check lowercase
            xpt_lower = NHANES_DIR / filename.lower()
            if xpt_lower.exists():
                xpt_path = xpt_lower
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
            # Count metadata stats
            with open(meta_out) as f:
                meta_data = json.load(f)
            labels = sum(1 for c in meta_data["columns"].values() if c.get("label"))
            value_maps = sum(1 for c in meta_data["columns"].values() if c.get("value_labels"))
            print(f"  [OK] {xpt_path.name} -> {csv_out.name} + {meta_out.name}")
            print(f"       {meta_data['column_count']} columns, {labels} labels, {value_maps} value maps")
            converted += 1
        except Exception as e:
            print(f"  [!!] Failed: {xpt_path.name}: {e}", file=sys.stderr)

    print()
    print(f"  Converted: {converted}, Skipped: {skipped}, Missing: {missing}")

    if missing:
        print()
        print("  Download missing XPT files from:")
        print("  https://wwwn.cdc.gov/nchs/nhanes/Default.aspx")


if __name__ == "__main__":
    main()
