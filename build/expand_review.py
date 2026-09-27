#!/usr/bin/env python3
"""review/fair.csv -> build/review-expanded.csv (one row per loaded record, as the loader reads it)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
decisions = {r["tiny_id"]: r for r in csv.DictReader(open(ROOT / "review" / "fair.csv", encoding="utf-8"))}
rows = []
for p in sorted((ROOT / "build" / "records").glob("*.json")):
    if p.name == "_summary.json":
        continue
    r = json.loads(p.read_text())
    d = decisions.get(r["tiny_id"], {})
    rows.append({"tiny_id": r["tiny_id"], "decision": d.get("decision", ""), "note": d.get("note", "")})
out = ROOT / "build" / "review-expanded.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["tiny_id", "decision", "note"]); w.writeheader(); w.writerows(rows)
print(f"{len(rows)} rows -> {out.relative_to(ROOT)}; accepted: {sum(1 for r in rows if r['decision'].lower() in ('accept', 'exact', 'yes', 'approved', 'ok'))}")
