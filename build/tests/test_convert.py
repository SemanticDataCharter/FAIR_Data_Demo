"""The FAIR Data Demo records: every slot resolves in its library, every NIH CDE is a published rebuilt component, every first-build component is retired or covered exactly once."""
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
sys.path.insert(0, str(ROOT / "build"))
import rules  # noqa: E402

LIBS = {"default": Path.home() / "GitHub" / "DefaultLibrary", "provgov": Path.home() / "GitHub" / "ProvGovLibrary", "fhir": Path.home() / "GitHub" / "FHIRLibrary"}


def run(script):
    subprocess.run([PY, str(ROOT / "build" / script)], check=True, capture_output=True)


def records():
    run("author.py")
    run("convert.py")
    return {p.stem: json.loads(p.read_text()) for p in (ROOT / "build" / "records").glob("*.json") if p.name != "_summary.json"}


def export():
    return {r["ct_id"]: r for r in csv.DictReader(open(ROOT / "docs" / "design" / "inventory" / "export-fair-data-demo-2026-09-26.csv", encoding="utf-8"))}


def test_every_record_has_slot_source_publisher():
    for key, r in records().items():
        preds = [l["predicate"] for l in r["links"]]
        assert preds[:3] == ["dcterms:identifier", "dcterms:source", "dcterms:publisher"], key
        assert r["links"][0]["iri"] == rules.IDENTIFIER_BASE + key
        assert "rdfs:isDefinedBy" not in preds and all("wikidata.org/wiki/" not in l["iri"] for l in r["links"]), key


def test_every_library_slot_named_exists_in_its_library():
    r = records()
    slots = {m for v in r.values() for m in v["members"] if m.startswith("http")}
    slots |= {v["constraints"]["units_slot"] for v in r.values() if v["constraints"].get("units_slot")}
    for s in slots:
        lib, key = s.split("/library/")[1].split("/")
        assert (LIBS[lib] / "records" / f"{key}.yaml").exists(), s


def test_every_nih_cde_member_is_a_rebuilt_published_component():
    lookup = json.loads((ROOT / "docs" / "design" / "inventory" / "nih-cde-rebuilt-lookup.json").read_text())
    cts = {v["ct_id"]: v for v in lookup.values()}
    r = records()
    members = {m[3:] for v in r.values() for m in v["members"] if m.startswith("ct:")}
    assert members, "no NIH CDE composed"
    for ct in members:
        assert ct in cts, ct


def test_the_shared_components_are_composed_by_more_than_one_study():
    r = records()
    def composers(key):
        return {k for k, v in r.items() if key in v["members"]}
    assert {"nhanes-smoking", "brfss-tobacco-and-alcohol"} <= composers("smoking-status")
    assert {"nhanes-medical-conditions", "brfss-chronic-conditions", "cms-beneficiary"} <= composers("chronic-condition-indicators")
    assert {"nhanes-demographics", "brfss-demographics"} <= composers("veteran-status")
    for study in ("nhanes-demographics", "brfss-demographics", "cms-beneficiary-demographics"):
        assert rules.DEFAULT_SLOT + "administrative-gender" in r[study]["members"], study


def test_every_governed_record_carries_the_provgov_provenance_and_audit_clusters():
    r = records()
    governed = [v for k, v in r.items() if k.endswith("-governed-record")]
    assert len(governed) == 7
    for g in governed:
        assert {rules.PROVGOV_SLOT + "prov-activity", rules.PROVGOV_SLOT + "prov-agent", rules.PROVGOV_SLOT + "audit-event"} <= set(g["members"]), g["tiny_id"]


def test_every_first_build_component_is_retired_exactly_once_and_models_are_not():
    records()
    old = export()
    rows = list(csv.DictReader(open(ROOT / "review" / "fair-retire.csv", encoding="utf-8")))
    retire = [row["ct_id"] for row in rows]
    assert len(retire) == len(set(retire))
    assert set(retire) == {ct for ct, r in old.items() if r["model"] != "DM"}
    assert all(row["reason"] for row in rows)


def test_bundle_orders_members_before_containers():
    records()
    run("bundle.py")
    bundle = json.loads((ROOT / "build" / "bundle.json").read_text())
    seen = set()
    for r in bundle:
        for m in r["members"]:
            assert m.startswith(("http", "ct:")) or m in seen, (r["tiny_id"], m)
        seen.add(r["tiny_id"])
