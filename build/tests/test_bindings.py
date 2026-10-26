"""The value bindings name codes their terminologies confirm (E-2026-10-03, SOURCE-ERRATA.md)."""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "build"))
import verify_codes  # noqa: E402

BUNDLE = json.loads((ROOT / "build" / "bundle.json").read_text())
VERIFIED = json.loads((ROOT / "build" / "verified-codes.json").read_text())["codes"]


def test_every_concept_code_was_looked_up_in_its_terminology():
    """A code written by hand ships only once build/verify_codes.py has asked its terminology what it is."""
    assert sorted(verify_codes.codes_in(BUNDLE) - set(VERIFIED)) == []


def test_no_two_values_of_one_enumeration_share_a_concept_code():
    """Two values bound to one concept cannot be told apart by any target that reads the code. A codebook page is a
    definition, not a code, and is shared by every value it defines."""
    shared = {}
    for r in BUNDLE:
        codes = collections.Counter(k for e in r.get("enumeration") or [] if (k := verify_codes.key_of(e.get("definition", ""))))
        dup = {k: n for k, n in codes.items() if n > 1}
        if dup:
            shared[r["tiny_id"]] = dup
    assert shared == {}


def test_no_value_is_bound_to_unknown_unless_it_says_so():
    """C17998 is NCI Thesaurus's Unknown: a value bound to it must be an unknown, not a level of a scale."""
    for r in BUNDLE:
        for e in r.get("enumeration") or []:
            if verify_codes.key_of(e.get("definition", "")) == "ncit|C17998":
                assert any(w in e["value"].lower() for w in ("unknown", "cannot ascertain", "don't know")), (r["tiny_id"], e["value"])
