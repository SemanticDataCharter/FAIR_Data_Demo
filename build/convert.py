#!/usr/bin/env python3
"""
records/*.yaml -> build/records/*.json in the loader's shape; _summary.json alongside.

CordovaOS 4.4.0 model records: clusters composing library components by slot, published
Cordova components by ``ct:<ct_id>``, and the new Cordova-local leaves as records (PRD §2, §4).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rules  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "records"
LINK_PREDICATES = ("skos:exactMatch", "skos:closeMatch", "skos:broadMatch", "rdfs:seeAlso", "dcterms:subject")


def validate(r: dict, path: Path):
    for k in ("key", "label", "type", "description"):
        assert r.get(k), f"{path}: missing {k}"
    assert r["type"] in rules.TYPES, f"{path}: unknown type {r['type']}"
    assert len(r["label"]) <= rules.LABEL_MAX, f"{path}: label over {rules.LABEL_MAX}"
    assert r.get("source") and r["source"].get("name") in rules.STANDARDS, f"{path}: source must name a standard in rules.STANDARDS"
    for l in r.get("links") or []:
        assert l["predicate"] in LINK_PREDICATES, f"{path}: predicate {l['predicate']}"
        assert l["iri"].startswith("http") and "wikidata.org/wiki/" not in l["iri"], f"{path}: bad IRI {l['iri']}"
        assert l.get("basis") in ("standard", "concept"), f"{path}: link basis"
    if r["type"] in ("XdToken", "XdOrdinal", "Units"):
        assert r.get("enumeration"), f"{path}: {r['type']} needs an enumeration"
        assert all(x.get("definition", "").startswith("http") for x in r["enumeration"]), f"{path}: a definition IRI per value"
    if r["type"] == "XdLink":
        assert all((r.get("constraints") or {}).get(k) for k in ("link", "relation", "relation_uri")), f"{path}: XdLink needs link, relation, relation_uri (the link is fixed in the schema)"
    if r["type"] in ("XdCount", "XdQuantity"):
        assert (r.get("constraints") or {}).get("units"), f"{path}: {r['type']} needs constraints.units (a Units record key)"
    if r["type"] == "XdBoolean":
        assert (r.get("constraints") or {}).get("trues") and r["constraints"].get("falses"), f"{path}: XdBoolean needs trues and falses"
    if r["type"] == "XdTemporal":
        assert (r.get("constraints") or {}).get("allow"), f"{path}: XdTemporal needs constraints.allow"
    if r["type"] == "Cluster":
        assert r.get("members"), f"{path}: cluster needs members"


def base_links(key: str, source_name: str, note: str = "") -> list[dict]:
    return [
        {"predicate": "dcterms:identifier", "iri": rules.IDENTIFIER_BASE + key, "basis": "mechanical", "note": "library slot; stable across revisions"},
        {"predicate": "dcterms:source", "iri": rules.STANDARDS[source_name], "basis": "mechanical", "note": source_name},
        {"predicate": "dcterms:publisher", "iri": rules.PUBLISHER_IRI, "basis": "mechanical", "note": "Axius SDC, Inc."},
    ]


def own_links(r: dict) -> list[dict]:
    return [{"predicate": l["predicate"], "iri": l["iri"], "basis": "mechanical" if l["basis"] == "standard" else "concept", "note": l.get("note", "")}
            for l in r.get("links") or []]


def identity(links: list[dict]) -> str:
    preds = {l["predicate"] for l in links}
    return "exact" if "skos:exactMatch" in preds else ("close" if "skos:closeMatch" in preds else "none")


def record(key, label, description, sdc_type, links, constraints=None, enumeration=None, members=None, supersedes=None, flags=None, extra=None):
    rec = {
        "tiny_id": key, "label": label[:rules.LABEL_MAX], "description": " ".join(description.split()), "sdc_type": sdc_type, "excluded": False,
        "constraints": constraints or {}, "enumeration": enumeration or [], "links": links, "identity_status": identity(links),
        "supersedes_ct_id": supersedes or None, "members": members or [], "flags": flags or [],
        "selection_reason": "FAIR Data Demo 4.2.0 models 2026-09",
    }
    rec.update(extra or {})
    return rec


def enumeration_of(r: dict) -> list[dict]:
    return r.get("enumeration") or []


def build_plain(r: dict, by_key: dict) -> dict:
    links = base_links(r["key"], r["source"]["name"]) + own_links(r)
    c = dict(r.get("constraints") or {})
    enum = enumeration_of(r)
    if r["type"] in ("XdCount", "XdQuantity"):
        if c["units"].startswith("http"):
            c["units_slot"] = c.pop("units")   # another library's Units, by slot
        else:
            u = by_key[c["units"]]
            uenum = enumeration_of(u)
            c["units_key"] = u["key"]
            c["units_spec"] = {"label": u["label"], "enums": [x["value"] for x in uenum], "definitions": [x["definition"] for x in uenum]}
            c["units"] = u["label"]
    if r["type"] in ("XdToken", "Units") and enum:
        c.update(enums=[x["value"] for x in enum], enum_descr=[x.get("name", x["value"]) for x in enum], definitions=[x["definition"] for x in enum])
    if r["type"] == "XdOrdinal" and enum:
        c.update(ordinals=[x["value"] for x in enum], symbols=[x.get("name", x["value"]) for x in enum], annotations=[x["definition"] for x in enum])
    return record(r["key"], r["label"], r["description"], r["type"], links, constraints=c, enumeration=enum,
                  members=r.get("members"), supersedes=r.get("supersedes"), flags=r.get("flags"))


def main():
    raw = {}
    for p in sorted((ROOT / "records").glob("*.yaml")):
        r = yaml.safe_load(p.read_text())
        validate(r, p)
        assert r["key"] not in raw, f"duplicate key {r['key']}"
        raw[r["key"]] = r
    records = []
    for r in raw.values():
        records.append(build_plain(r, raw))
    keys = {x["tiny_id"] for x in records}
    assert len(keys) == len(records), "duplicate expanded keys"
    for x in records:
        for m in x["members"]:
            assert m in keys or m.startswith(rules.SLOT_BASES) or m.startswith("ct:"), f"{x['tiny_id']}: member {m} is not a record, a library slot or a NIH CDE ct_id"
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.json"):
        f.unlink()
    summary = {"records": len(records), "by_type": {}, "identity": {}, "supersedes": 0}
    for x in records:
        (OUT / f"{x['tiny_id']}.json").write_text(json.dumps(x, indent=2, ensure_ascii=False) + "\n")
        summary["by_type"][x["sdc_type"]] = summary["by_type"].get(x["sdc_type"], 0) + 1
        summary["identity"][x["identity_status"]] = summary["identity"].get(x["identity_status"], 0) + 1
        summary["supersedes"] += bool(x["supersedes_ct_id"])
    (OUT / "_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
