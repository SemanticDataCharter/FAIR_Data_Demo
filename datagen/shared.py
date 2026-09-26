"""
Shared glue for the FAIR Data Demo generators (4.2.0).

A generator reads a federal source file, names the values a row has by label
path in the published model, and calls ``record()``. The engine fills the
model's own instance template; the schema decides everything else. Every record
states which file it came from: the ProvGov activity's used entity, the audit's
location (a PROV entity: the file's URL, name and release) and the record's
subject (the agency's identifier for the person or claim).

Missing values are the agencies' codes: NHANES 7 and 9 (refused, don't know),
BRFSS 7 and 9 or 77 and 99, blank cells everywhere. Where the model requires a
value they become stated absences (ASKR, ASKU, NI); where it does not they are
left out. Nothing is written as a 7 that would average.
"""
from __future__ import annotations

import csv
import os
import random
import re
from datetime import datetime

from engine import EV, Quantity, Template
from schema import DMLIB, Schema

ROOT = os.path.join(os.path.dirname(__file__), "..")
SOURCE = os.path.join(ROOT, "source_data")
IMPORT_ROOT = os.environ.get("FAIR_IMPORT_DIR") or os.path.join(ROOT, "app", "sdc4", "import_data")
DEMO_SCALE = os.environ.get("FAIR_FULL") != "1"   # the seeded samples by default; FAIR_FULL=1 takes every row
SAMPLE = {"brfss": 5000, "cms": 5000}

ASKR = EV("ASKR")   # refused
ASKU = EV("ASKU")   # asked, and the answer is not known
NI = EV("NI")       # absent, no reason recorded
OMIT = None

_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"


def cuid_generator():
    return random.choice(_ID_ALPHABET[:26]) + "".join(random.choices(_ID_ALPHABET, k=23))


def now_iso():
    return datetime.utcnow().isoformat()


# ─── Models ──────────────────────────────────────────────────────────────────
_MODELS: dict[str, str] = {}


def model_ct(title: str) -> str:
    if not _MODELS:
        for name in sorted(os.listdir(DMLIB)):
            m = re.match(r"dm-([a-z0-9]{24})\.xsd$", name)
            if m:
                s = Schema.for_dm(m.group(1))
                _MODELS[s.label.get(s.dm, "")] = m.group(1)
    hits = [ct for t, ct in _MODELS.items() if t == title]
    assert len(hits) == 1, (title, hits)
    return hits[0]


def template(title: str) -> Template:
    return Template.for_dm(model_ct(title))


# ─── Source files ────────────────────────────────────────────────────────────
FILES = {   # key: (relative path, file name, download URL, release)
    "DEMO_J": ("nhanes/DEMO_J.csv", "DEMO_J.XPT", "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DEMO_J.XPT", "NHANES 2017-2018 public release"),
    "BPX_J": ("nhanes/BPX_J.csv", "BPX_J.XPT", "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/BPX_J.XPT", "NHANES 2017-2018 public release"),
    "TCHOL_J": ("nhanes/TCHOL_J.csv", "TCHOL_J.XPT", "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/TCHOL_J.XPT", "NHANES 2017-2018 public release"),
    "CBC_J": ("nhanes/CBC_J.csv", "CBC_J.XPT", "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/CBC_J.XPT", "NHANES 2017-2018 public release"),
    "MCQ_J": ("nhanes/MCQ_J.csv", "MCQ_J.XPT", "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/MCQ_J.XPT", "NHANES 2017-2018 public release"),
    "SMQ_J": ("nhanes/SMQ_J.csv", "SMQ_J.XPT", "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/SMQ_J.XPT", "NHANES 2017-2018 public release"),
    "PFQ_J": ("nhanes/PFQ_J.csv", "PFQ_J.XPT", "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/PFQ_J.XPT", "NHANES 2017-2018 public release"),
    "RXQ_RX_J": ("nhanes/RXQ_RX_J.csv", "RXQ_RX_J.XPT", "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/RXQ_RX_J.XPT", "NHANES 2017-2018 public release"),
    "LLCP2022": ("brfss/LLCP2022.csv", "LLCP2022.XPT", "https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022XPT.zip", "BRFSS 2022 annual survey data"),
    "CMS_BENE": ("cms/DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv", "DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv", "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1", "DE-SynPUF 1.0 sample 1, 2008"),
    "CMS_IP": ("cms/DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv", "DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv", "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1", "DE-SynPUF 1.0 sample 1, 2008-2010"),
    "CMS_OP": ("cms/DE1_0_2008_to_2010_Outpatient_Claims_Sample_1.csv", "DE1_0_2008_to_2010_Outpatient_Claims_Sample_1.csv", "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1", "DE-SynPUF 1.0 sample 1, 2008-2010"),
    "CMS_PDE": ("cms/DE1_0_2008_to_2010_Prescription_Drug_Events_Sample_1.csv", "DE1_0_2008_to_2010_Prescription_Drug_Events_Sample_1.csv", "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1", "DE-SynPUF 1.0 sample 1, 2008-2010"),
}


def source_path(key: str) -> str:
    return os.path.join(SOURCE, FILES[key][0])


def read_csv(key: str):
    """Rows of a source file as dicts of strings; a blank cell is ''. NHANES floats like '1.0' are normalized to '1'."""
    with open(source_path(key), encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            yield {k.strip('"'): _norm(v) for k, v in row.items()}


def _norm(v):
    v = (v or "").strip()
    if v.endswith(".0") and v[:-2].lstrip("-").isdigit():
        return v[:-2]
    return v


def code(v: str, table: dict, refused=("7", "77", "777"), dont_know=("9", "99", "999")):
    """A coded survey answer: the table's value, or the absence the code states, or None for blank or out-of-table.

    NHANES and BRFSS use 7 / 77 / 777 for refused and 9 / 99 / 999 for don't know across most items; a
    variable whose codes differ passes its own tuples.
    """
    if v == "":
        return None
    if v in table:
        return table[v]
    if v in refused:
        return ASKR
    if v in dont_know:
        return ASKU
    return None


def number(v: str, missing=()):
    """A numeric answer as text, or None when blank or a missing-value code."""
    if v == "" or v in missing:
        return None
    return v


def qty(v: str, unit: str, missing=(), scale: float | None = None, digits: int | None = None):
    """A Quantity from a numeric cell, or None."""
    n = number(v, missing)
    if n is None:
        return None
    if scale is not None:
        n = f"{float(n) * scale:.{digits or 2}f}"
    return Quantity(n, unit)


def cms_date(v: str):
    """CMS dates are YYYYMMDD integers."""
    v = (v or "").strip()
    return f"{v[:4]}-{v[4:6]}-{v[6:8]}" if len(v) == 8 and v.isdigit() else None


def seeded_sample(keys, n: int, seed: str):
    """A fixed sample of n keys, the same on every run."""
    keys = sorted(keys)
    rng = random.Random(seed)
    return set(rng.sample(keys, min(n, len(keys))))


# ─── Governance ──────────────────────────────────────────────────────────────
SOFTWARE_VERSION = open(os.path.join(ROOT, "app", "sdc4", "VERSION"), encoding="utf-8").read().strip()
PIPELINE = "FAIR Data Demo pipeline"
PIPELINE_ID = "urn:fair-data-demo:pipeline:4.2.0"
_counter = 0


def record(title: str, values: dict, *, study: str, agency: str, source_key: str, subject: tuple[str, str], row_ref: str, when: str = "2026-09-26T00:00:00",
           instance_id: str | None = None) -> str:
    """One instance of the model titled ``title`` from one source row.

    ``values`` maps label paths to values (a string, a Quantity, a bool, an EV, or None to leave the fact out).
    ``study`` names the agency's study; ``agency`` the provider party; ``source_key`` the file in FILES; ``subject``
    the party the record is about (label, the agency's identifier); ``row_ref`` names the row for the audit event.
    """
    global _counter
    _counter += 1
    t = template(title)
    vals = {k: v for k, v in values.items() if v is not None}
    rel, fname, url, release = FILES[source_key]
    vals.update({
        "PROV Activity/Activity Identifier": f"urn:fair-data-demo:activity:{source_key.lower()}:{_counter:08d}",
        "PROV Activity/Activity Label": f"Generate a {title} record from {fname}",
        "PROV Activity/Activity Type": "RecordGeneration",
        "PROV Activity/Activity Description": f"One row of {fname} ({release}) generated as a {title} record by the {PIPELINE}.",
        "PROV Activity/Activity Status": "ActivityCompleted",
        "PROV Activity/Started At": when,
        "PROV Activity/Ended At": when,
        "PROV Activity/Used Entity Reference": url,
        "PROV Activity/Was Associated With Reference": PIPELINE_ID,
        "PROV Agent/Agent Identifier": PIPELINE_ID,
        "PROV Agent/Agent Name": PIPELINE,
        "PROV Agent/PROV Agent Type": "SoftwareAgent",
        "PROV Agent/Software Name": "FAIR Data Demo",
        "PROV Agent/Software Version": SOFTWARE_VERSION,
        "PROV Agent/Agent Organization Name": "Semantic Data Charter",
        "Audit Event/Audit Event Identifier": f"urn:fair-data-demo:audit:{source_key.lower()}:{_counter:08d}",
        "Audit Event/Audit Event Action": "C",
        "Audit Event/Audit Event Outcome": "0",
        "Audit Event/Audit Recorded At": when,
        "Audit Event/Audit Agent Reference": PIPELINE_ID,
        "Audit Event/Audit Entity Reference": f"{url}#{row_ref}",
        "Audit Event/Data Subject Reference": f"urn:{study.lower()}:{subject[1]}",
        "Audit Event/Purpose of Use": "HRESCH",
        "Audit Event/Confidentiality": "N",
        "Audit Event/Provenance Agent Type": "author",
        "Audit Event/System Identifier": PIPELINE_ID,
        "Audit Event/System Location Name": "FAIR Data Demo, local",
    })
    return t.instance(vals, instance_id=instance_id or cuid_generator(), current_state=None, timestamp=now_iso(),
                      subject=subject, provider=(f"{study} ({agency})", agency),
                      audit={"system_id": PIPELINE_ID, "user": PIPELINE, "timestamp": when,
                             "values": {"FAIR Pipeline Audit/PROV Entity/Entity Identifier": url, "FAIR Pipeline Audit/PROV Entity/Entity Label": fname,
                                        "FAIR Pipeline Audit/PROV Entity/Entity Description": release}},
                      attestation={"reason": f"Generated from {fname} without alteration of the values; absences stated where the row had none", "committer": PIPELINE, "committed": when, "pending": False})


def import_dir(app: str) -> str:
    return os.path.join(IMPORT_ROOT, app)


def write_record(directory: str, prefix: str, xml: str) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{prefix}-{cuid_generator()}.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml)
    return path
