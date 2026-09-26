"""The schema reader resolves component and adapter ids by label path from the published 4.4.0 models."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from schema import DMLIB, Schema  # noqa: E402


def _by_title(prefix):
    for name in sorted(os.listdir(DMLIB)):
        m = re.match(r"dm-([a-z0-9]{24})\.xsd$", name)
        if m:
            s = Schema.for_dm(m.group(1))
            if s.label.get(s.dm, "").startswith(prefix):
                return s
    raise AssertionError(prefix)


def test_paths_resolve_by_label_and_ambiguity_is_refused():
    s = _by_title("NHANES Participant")
    assert s.cluster("NHANES Blood Pressure").startswith("ms-")
    comp, adapter = s.leaf("NHANES Demographics/Administrative Gender")
    assert comp == "ms-gxzbm758mhdz51xd4bawlfhh" and adapter.startswith("ms-")   # the Default library's component, its adapter minted per model
    assert s.enums("NHANES Smoking/Smoking Status")[0] == "Current every day smoker"
    assert s.units("NHANES Laboratory Results/Hemoglobin") == "Grams per Decilitre"
    assert s.temporal_kinds("Blood Pressure Reading 1/Blood Pressure/Observation Date Time") == ["xdtemporal-datetime"]
    assert s.leaf(("NHANES Demographics", "Race/Ethnicity Self-Identification"))[0] == "ms-u5tietya3u56hbz2kos06ai7"   # the NIH CDE, addressed as a tuple
    assert s.leaf("Systolic Blood Pressure") == s.leaf("Blood Pressure Reading 2/Blood Pressure/Systolic Blood Pressure")   # one component, one adapter, three readings
    try:
        s.leaf("No Such Leaf")
        raise AssertionError("missing path accepted")
    except KeyError as e:
        assert "no element" in str(e)


def test_the_shared_components_are_the_same_ct_id_in_every_study():
    n = _by_title("NHANES Participant"); b = _by_title("BRFSS Respondent"); c = _by_title("CMS Beneficiary")
    for label in ("Smoking Status", "Condition: Diabetes", "Condition Indicator Basis", "Administrative Gender"):
        ids = {s.leaf(label)[0] for s in (n, b, c) if any(p[-1] == label for p, _, _ in s.paths)}
        assert len(ids) == 1, (label, ids)
    assert n.leaf(("NHANES Demographics", "Race/Ethnicity Self-Identification"))[0] == c.leaf(("CMS Beneficiary Demographics", "Race/Ethnicity Self-Identification"))[0]


def test_every_model_has_a_governed_record_and_no_workflow():
    for name in sorted(os.listdir(DMLIB)):
        m = re.match(r"dm-([a-z0-9]{24})\.xsd$", name)
        if not m:
            continue
        s = Schema.for_dm(m.group(1))
        assert s.states() == [], s.label[s.dm]
        data = [p for p, comp, a in s.paths if len(p) == 1 and s.base.get(comp) == "ClusterType"]
        assert data and data[0][0].endswith("Governed Record"), (s.label[s.dm], data)
        assert s.required(data[0][0])
