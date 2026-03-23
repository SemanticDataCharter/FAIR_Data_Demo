#!/usr/bin/env python3
"""
Convert NHANES XPT (SAS transport) files to CSV.

NHANES distributes data as .XPT files. The SDC Agents Introspect toolset
works with CSV, so this script converts XPT to CSV as a preprocessing step.

Usage:
    python scripts/convert_xpt_to_csv.py

Requires: pip install pyreadstat
"""
from __future__ import annotations

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


def convert_xpt_to_csv(xpt_path: Path) -> Path:
    """Convert a single XPT file to CSV. Returns the CSV path."""
    import pyreadstat

    csv_path = xpt_path.with_suffix(".csv")
    df, _ = pyreadstat.read_xport(str(xpt_path))
    df.to_csv(csv_path, index=False)
    return csv_path


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

        if not xpt_path.exists():
            # Also check lowercase
            xpt_lower = NHANES_DIR / filename.lower()
            if xpt_lower.exists():
                xpt_path = xpt_lower
            else:
                print(f"  [--] Missing: {filename}")
                missing += 1
                continue

        if csv_path.exists():
            print(f"  [OK] Already converted: {csv_path.name}")
            skipped += 1
            continue

        try:
            out = convert_xpt_to_csv(xpt_path)
            print(f"  [OK] Converted: {xpt_path.name} -> {out.name}")
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
