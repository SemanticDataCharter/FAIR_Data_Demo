#!/usr/bin/env python3
"""build/bundle.json -> build/bundle-<n>.json: chunks that each fit one sdcstudio-migrate execution (10-minute task timeout).

Order is kept: Units and the quantities that bind them first, then the other atomic components, then the clusters (members before
containers, as bundle.py ordered them). The loader is idempotent by identifier slot, so chunks load in sequence and a rerun is safe.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 300
bundle = json.loads((ROOT / "build" / "bundle.json").read_text())
units = [r for r in bundle if r["sdc_type"] == "Units"]
bound = [r for r in bundle if r["sdc_type"] in ("XdQuantity", "XdCount") and r["constraints"].get("units_key")]
rest = [r for r in bundle if r not in units and r not in bound and r["sdc_type"] != "Cluster"]
clusters = [r for r in bundle if r["sdc_type"] == "Cluster"]
ordered = units + bound + rest
chunks = [ordered[i:i + SIZE] for i in range(0, len(ordered), SIZE)]
chunks += [clusters[i:i + SIZE] for i in range(0, len(clusters), SIZE)]
for f in (ROOT / "build").glob("bundle-*.json"):
    f.unlink()
SLOT = "https://axius-sdc.com/library/fair/"
for n, c in enumerate(chunks, 1):
    here = {r["tiny_id"] for r in c}
    for r in c:   # a member loaded by an earlier execution is named by its slot; the loader resolves it from the database
        r["members"] = [m if m.startswith(("http", "ct:")) or m in here else SLOT + m for m in r["members"]]
    (ROOT / "build" / f"bundle-{n}.json").write_text(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"bundle-{n}.json: {len(c)} records ({', '.join(f'{t}={sum(1 for r in c if r['sdc_type'] == t)}' for t in sorted({r['sdc_type'] for r in c}))})")
