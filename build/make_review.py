#!/usr/bin/env python3
"""build/records -> review/fair.csv: one row per record, the source it carries and what it composes."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["tiny_id", "label", "type", "niem", "source", "exact_match", "members", "supersedes_ct_id", "flags", "decision", "note"]
rows = []
for p in sorted((ROOT / "build" / "records").glob("*.json")):
    if p.name == "_summary.json":
        continue
    r = json.loads(p.read_text())
    rows.append({
        "tiny_id": r["tiny_id"], "label": r["label"], "type": r["sdc_type"], "niem": r.get("niem", ""),
        "source": next(l["note"] for l in r["links"] if l["predicate"] == "dcterms:source"),
        "exact_match": next((l["iri"] for l in r["links"] if l["predicate"] == "skos:exactMatch"), ""),
        "members": " | ".join(r["members"]), "supersedes_ct_id": r["supersedes_ct_id"] or "", "flags": "; ".join(r["flags"]), "decision": "", "note": "",
    })
(ROOT / "review").mkdir(exist_ok=True)
with open(ROOT / "review" / "fair.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
print(f"{len(rows)} rows -> review/fair.csv")
