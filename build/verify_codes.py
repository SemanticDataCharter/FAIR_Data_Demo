#!/usr/bin/env python3
"""Every concept code the bundle names, looked up in its terminology -> build/verified-codes.json.

A code is written in build/author.py by hand; this asks the terminology what each one is (NCI Thesaurus from NCI's EVS
API, LOINC and SNOMED CT from HL7's terminology server) and records the name it gives. build/tests/test_bindings.py
refuses a bundle that names a code not in the file, so a code nobody looked up does not ship (E-2026-10-03,
SOURCE-ERRATA.md). Run it after changing a code, read the names it prints, and commit the file.
"""
from __future__ import annotations

import datetime
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "verified-codes.json"
CODE = re.compile(r"NCIT_(C\d+)|loinc\.org/((?:LA|LP|LG)?\d+-\d)|snomed\.info/id/(\d+)")


def codes_in(bundle) -> set[str]:
    found = set()
    for r in bundle:
        if r.get("excluded"):
            continue
        iris = [e.get("definition", "") for e in r.get("enumeration") or []] + [l["iri"] for l in r.get("links") or []]
        for iri in iris:
            m = CODE.search(iri)
            if m:
                found.add("ncit|" + m.group(1) if m.group(1) else "loinc|" + m.group(2) if m.group(2) else "sct|" + m.group(3))
    return found


def key_of(iri: str) -> str | None:
    m = CODE.search(iri)
    return None if not m else "ncit|" + m.group(1) if m.group(1) else "loinc|" + m.group(2) if m.group(2) else "sct|" + m.group(3)


def lookup(keys: list[str]) -> dict[str, str]:
    names = {}
    ncit = [k.split("|")[1] for k in keys if k.startswith("ncit|")]
    for i in range(0, len(ncit), 40):
        url = "https://api-evsrest.nci.nih.gov/api/v1/concept/ncit?include=minimal&list=" + ",".join(ncit[i:i + 40])
        for c in json.load(urllib.request.urlopen(url, timeout=60)):
            names["ncit|" + c["code"]] = c["name"]
    for k in keys:
        if k.startswith("ncit|"):
            continue
        system, code = k.split("|")
        url = "https://tx.fhir.org/r4/CodeSystem/$lookup?" + urllib.parse.urlencode(
            {"system": "http://loinc.org" if system == "loinc" else "http://snomed.info/sct", "code": code})
        p = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/fhir+json"}), timeout=60))
        names[k] = next(x["valueString"] for x in p["parameter"] if x["name"] == "display")
    missing = sorted(set(keys) - set(names))
    if missing:
        raise SystemExit(f"not in their terminology: {missing}")
    return names


def main():
    bundle = json.loads((ROOT / "build" / "bundle.json").read_text())
    names = lookup(sorted(codes_in(bundle)))
    OUT.write_text(json.dumps({"_about": __doc__.strip().splitlines()[0], "looked_up": datetime.date.today().isoformat(),
                               "codes": dict(sorted(names.items()))}, indent=1, ensure_ascii=False) + "\n")
    for k, n in sorted(names.items()):
        print(f"{k:18} {n}")


if __name__ == "__main__":
    main()
