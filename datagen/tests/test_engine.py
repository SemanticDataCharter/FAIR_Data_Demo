"""The template engine: every 4.4.0 model fills from label paths and validates under its own XSD 1.1 schema."""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine import EV, Quantity, Template  # noqa: E402
from schema import DMLIB, Schema  # noqa: E402

MODELS = {}   # every published model the app carries, by title
for _name in sorted(os.listdir(DMLIB)):
    _m = re.match(r"dm-([a-z0-9]{24})\.xsd$", _name)
    if _m:
        _s = Schema.for_dm(_m.group(1))
        MODELS[_s.label.get(_s.dm, _m.group(1))] = {"ct_id": _m.group(1)}
NHANES = next(v["ct_id"] for k, v in MODELS.items() if k == "NHANES Participant")
CLAIM = next(v["ct_id"] for k, v in MODELS.items() if k == "CMS Inpatient Claim")


def _schema(ct_id):
    from sdcvalidator import build_xsd11_schema
    return build_xsd11_schema(os.path.join(DMLIB, f"dm-{ct_id}.xsd"),
                              uri_mapper={"https://semanticdatacharter.com/ns/sdc4/sdc4.xsd": os.path.abspath(os.path.join(DMLIB, "sdc4.xsd"))}, validation="lax")


def test_the_template_is_completed_from_the_schema_where_the_scaffold_wrote_a_shared_leaf_once():
    # SDCStudio issue #705: the scaffold writes a component composed in several clusters under the first one only
    t = Template.for_dm(CLAIM)
    assert len({id(e) for e in t.paths["Diagnosis Code (ICD-9-CM)"]}) == 11   # the admitting diagnosis and ten claim diagnoses
    n = Template.for_dm(NHANES)
    assert len({id(e) for e in n.paths["Systolic Blood Pressure"]}) == 3   # three readings
    assert ("NHANES Demographics", "Race/Ethnicity Self-Identification") in n.tpaths   # a label with a slash is addressed as a tuple


def test_a_temporal_shape_the_model_does_not_allow_is_refused():
    t = Template.for_dm(NHANES)
    with pytest.raises(AssertionError, match="allows"):
        t.instance({"Blood Pressure Reading 1/Blood Pressure/Observation Date Time": "2025-03-12"}, instance_id="i-x")


def test_no_workflow_is_bound_so_no_state_is_written():
    t = Template.for_dm(NHANES)
    assert t.schema.states() == []
    xml = t.instance({"NHANES Participant/Respondent Sequence Number (SEQN)": "93703"}, instance_id="i-x")
    assert "current-state" not in xml


def _every_leaf(t: Template):
    """A value for every leaf the schema declares, of the shape the schema asks for; one Exceptional Value on the first quantity."""
    s = t.schema
    vals, ev_path = {}, None
    for p, comp, adapter in s.paths:
        base, path = s.base.get(comp, ""), tuple(p)   # a tuple path, since some labels carry a slash
        if base == "ClusterType" or not adapter or path not in t.tpaths:
            continue
        body = s.types[comp]
        if base == "XdTokenType":
            vals[path] = s.enums(path)[0]
        elif base == "XdStringType":
            m = re.search(r'name="xdstring-value"[^>]*>(.*?)</xsd:element>', body, re.S)
            pat = re.search(r'<xsd:pattern value="([^"]*)"', m.group(1)) if m else None
            vals[path] = {r"\S+": "urn:x:1", r"[0-9]{5,6}": "93703", r"[0-9]{10}": "2022000001", r"[0-9]{1,2}": "1", r"[0-9]{1,3}": "1", r"[0-9A-F]{16}": "00013D2EFD8E45D1",
                          r"[0-9]{1,20}": "196661176988405", r"[0-9EV][0-9]{2,4}": "4019", r"[0-9]{2,4}": "3893", r"[0-9A-Z][0-9]{3}[0-9A-Z]": "99213", r"[0-9]{11}": "00093726201", r"[0-9]{3}": "470", r"[0-9]{3,4}": "510",
                          r"COR-(AL|BR|CE)0[1-3]-[0-9]{6}": "COR-AL01-000001", r"BIZ-[0-9]{6}": "BIZ-000001",
                          r"(AL|BR|CE)-0[1-3]-[0-9]{6}": "AL-01-000001", r".+@.+\..+": "a@b.co", r"\+?\d[\d\s\-\(\)]{6,18}": "+99-100-555-0000",
                          r"[0-9]{5,5}": "00001", r"[0-9]{6,18}": "123456", r"[A-Z0-9]{6,6}": "UN1234", r"[A-Z0-9]{3,3}": "COR", r"[A-Z]{2,2}": "CO",
                          r"[0-9]{1,8}": "1234", r"[0-9]{1,3}": "12", r"[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?": "J11.1"}.get(pat.group(1).replace("&quot;", '"') if pat else None, "text")
        elif base == "XdTemporalType":
            vals[path] = {"xdtemporal-datetime": "2025-03-12T09:00:00", "xdtemporal-date": "2025-03-12", "xdtemporal-year": "2025", "xdtemporal-year-month": "2025-03",
                          "xdtemporal-duration": "P3D", "xdtemporal-time": "09:00:00"}[s.temporal_kinds(path)[0]]
        elif base in ("XdQuantityType", "XdCountType", "XdFloatType", "XdDoubleType"):
            if ev_path is None:
                vals[path], ev_path = EV("ASKU"), path
            else:
                lo = re.search(r'<xsd:minInclusive value="([^"]*)"', body); hi = re.search(r'<xsd:maxInclusive value="([^"]*)"', body)
                v = float(lo.group(1)) if lo else 1.0
                if hi and v > float(hi.group(1)):
                    v = float(hi.group(1))
                units = t.schema.units_enums(path)   # the schema enumerates the units since SDCStudio #707; the first is as good as any
                vals[path] = Quantity(str(int(v)) if base == "XdCountType" else f"{v:.1f}", units[0] if units else "unit")
        elif base == "XdBooleanType":
            vals[path] = True
        elif base == "XdFileType":
            vals[path] = b"signature bytes" if "Signature" in path else "https://cordova.example/file.png"
        elif base == "XdOrdinalType":
            vals[path] = (1, "one")
        elif base == "XdLinkType":
            vals[path] = ""
    if ev_path is None:   # a model without a quantity states its absence on a text value instead
        ev_path = next(p for p, v in vals.items() if v == "text" or (isinstance(v, str) and v == "urn:x:1"))
        vals[ev_path] = EV("ASKU")
    return vals, ev_path


@pytest.mark.parametrize("title", sorted(MODELS))
def test_every_model_fills_every_leaf_and_validates_except_the_one_stated_absence(title):
    ct = MODELS[title]["ct_id"]
    t = Template.for_dm(ct)
    vals, ev_path = _every_leaf(t)
    assert len(vals) > 40, title
    xml = t.instance(vals, instance_id="i-test000000000000000001",
                     subject=("Subject", "Name"), provider=("Provider", "Agency"),
                     audit={"system_id": "urn:cordova:system:x", "user": "Cordova System"}, attestation={"reason": "Test", "committer": "Registrar", "pending": False})
    assert "_PH_" not in xml
    errors = [str(e) for e in _schema(ct).iter_errors(xml)]
    assert len(errors) == 1, (title, errors[:3])   # exactly the Exceptional Value in place of a required value: invalid on purpose
    assert "-value" in errors[0], errors[0]
    assert "<ev-name>Asked but Unknown</ev-name>" in xml
    # without the absence, valid
    if t.schema.base_of(ev_path) in ("XdQuantityType", "XdCountType", "XdFloatType", "XdDoubleType"):
        body = t.schema.types[t.schema._find(ev_path)[0]]
        lo = re.search(r'<xsd:minInclusive value="([^"]*)"', body)
        v = float(lo.group(1)) if lo else 1.0
        units = t.schema.units_enums(ev_path)
        vals[ev_path] = Quantity(str(int(v)) if t.schema.base_of(ev_path) == "XdCountType" else f"{v:.1f}", units[0] if units else "unit")
    else:
        vals[ev_path] = "text"
    xml = t.instance(vals, instance_id="i-test000000000000000002", subject=("Subject", "Name"), provider=("Provider", "Agency"),
                     audit={"system_id": "urn:cordova:system:x", "user": "Cordova System"}, attestation={"reason": "Test", "committer": "Registrar", "pending": False})
    assert not list(_schema(ct).iter_errors(xml)), title


def test_omitted_optional_members_are_dropped_and_the_instance_stays_valid():
    t = Template.for_dm(NHANES)
    xml = t.instance({"NHANES Participant/Respondent Sequence Number (SEQN)": "93703", "NHANES Laboratory Results/Hemoglobin": Quantity("14.2", "g/dL")},
                     instance_id="i-test000000000000000003", subject=("NHANES Participant", "93703"), provider=("NHANES", "NCHS"),
                     audit={"system_id": "urn:x:pipeline", "user": "pipeline", "values": {"FAIR Pipeline Audit/PROV Entity/Entity Label": "DEMO_J.XPT"}},
                     attestation={"reason": "Generated", "committer": "pipeline", "pending": False})
    assert "NHANES Smoking" not in xml and "NHANES Laboratory Results" in xml and "<label>Hemoglobin</label>" in xml
    assert "DEMO_J.XPT" in xml
    assert not list(_schema(NHANES).iter_errors(xml))
