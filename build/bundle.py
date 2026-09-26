#!/usr/bin/env python3
"""build/records -> build/bundle.json: Units first, then atomic components, then clusters with members before containers."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
records = {r["tiny_id"]: r for r in (json.loads(p.read_text()) for p in sorted((ROOT / "build" / "records").glob("*.json")) if p.name != "_summary.json")}
ordered = [r for r in records.values() if r["sdc_type"] == "Units"] + [r for r in records.values() if r["sdc_type"] not in ("Units", "Cluster")]
placed = {r["tiny_id"] for r in ordered}
clusters = [r for r in records.values() if r["sdc_type"] == "Cluster"]
while clusters:
    ready = [c for c in clusters if all(m in placed or m.startswith(("http", "ct:")) for m in c["members"])]
    assert ready, "cluster membership cycle: " + ", ".join(c["tiny_id"] for c in clusters)
    for c in ready:
        ordered.append(c)
        placed.add(c["tiny_id"])
        clusters.remove(c)
(ROOT / "build" / "bundle.json").write_text(json.dumps(ordered, ensure_ascii=False) + "\n")
print(f"{len(ordered)} records -> build/bundle.json")
