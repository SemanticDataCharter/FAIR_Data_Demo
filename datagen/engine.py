"""
Template-driven instance generation (CordovaOS 4.4.0).

Every published model ships its own instance template, ``dm-<ct_id>.xml``, with a
placeholder in every value element (``_PH_`` required, ``_OPT_PH_`` optional) and every
optional branch present once. A generator names the values it has by label path and
the engine does the rest: fills the value elements, drops every optional element it was
not given, keeps every fixed element the schema fixed, and refuses to omit a required
one. Nothing about element ids, adapters or element order lives in the generators, so a
republished model needs no generator change.

    t = Template.for_dm("dcsd8bxr8a6lzcptwwyms44t")
    xml = t.instance(
        values={"Patient Record/National ID (CID)": "COR-AL01-271845",
                "Patient/Person (Demographics)/Given Name (Person)": "Carlos",
                "Vital Signs Panel/Body Temperature": Quantity("37.2", "Cel"),
                "Allergy Intolerance/Allergy Onset Date": "2024-03-01",
                "Medication Order/Dose Quantity": EV("ASKU")},
        instance_id="i-...", current_state="in-progress",
        subject=("Patient", "Carlos Mendoza"), provider=("Healthcare Provider", "Porto Sereno General"),
        audit={"system_id": "urn:cordova:system:healthcare", "user": "Cordova Healthcare System", "city": "Porto Sereno", "province": "Aldara", "timestamp": ...},
        attestation={"reason": "Record created", "committer": "Clerk", "committed": ..., "pending": False})

Values: a string for XdString, XdToken, XdTemporal (the kind is read off the value: date,
datetime, year, year-month, duration) and XdFile (a URI); ``Quantity(magnitude, unit)`` for
XdQuantity and XdCount; a bool, or the literal the model enumerates, for XdBoolean;
``(ordinal, symbol)`` for XdOrdinal; ``bytes`` for an XdFile whose model carries the
content (base64 in ``media-content``), a URI string for one that references it; ``EV(code)`` for an ISO 21090 null flavor in place of
a required value (the instance is then invalid on purpose, as the console explains).
"""
from __future__ import annotations

import base64
import copy
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from lxml import etree

from schema import DMLIB, Schema

SDC4 = "https://semanticdatacharter.com/ns/sdc4/"
NS = {"sdc4": SDC4}
EV_NAMES = {   # the ev-name each null flavor fixes in sdc4.xsd
    "ASKR": "Asked and Refused", "ASKU": "Asked but Unknown", "DER": "Derived", "INV": "Invalid", "MSK": "Masked", "NA": "Not Applicable",
    "NASK": "Not Asked", "NAV": "Not Available", "NI": "No Information", "NINF": "Negative Infinity", "OTH": "Other", "PINF": "Positive Infinity",
    "QS": "Sufficient Quantity", "TRC": "Trace", "UNC": "Unencoded", "UNK": "Unknown",
}
VALUE_ELEMENTS = ("xdstring-value", "xdtoken-value", "xdquantity-value", "xdcount-value", "xdfloat-value", "xddouble-value", "true-value", "false-value",
                  "ordinal", "symbol", "uri", "media-content", "link", "relation", "relation-uri")
ENVELOPE = ("act", "vtb", "vte", "tr", "modified", "latitude", "longitude")
KINDS = (("xdtemporal-datetime", re.compile(r"^\d{4}-\d{2}-\d{2}T")), ("xdtemporal-date", re.compile(r"^\d{4}-\d{2}-\d{2}$")),
         ("xdtemporal-year-month", re.compile(r"^\d{4}-\d{2}$")), ("xdtemporal-year", re.compile(r"^\d{4}$")),
         ("xdtemporal-duration", re.compile(r"^P")), ("xdtemporal-time", re.compile(r"^\d{2}:\d{2}")))


@dataclass(frozen=True)
class Quantity:
    magnitude: str
    unit: str


@dataclass(frozen=True)
class EV:
    code: str


def _unescape_xml(s: str) -> str:
    return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")


def _tag(el) -> str:
    if not isinstance(el.tag, str):
        return ""   # a comment from the scaffold
    return el.tag.split("}")[1] if "}" in el.tag else el.tag


class Template:
    def __init__(self, ct_id: str, xml_text: str):
        self.ct_id = ct_id
        self.schema = Schema.for_dm(ct_id)
        parser = etree.XMLParser(remove_blank_text=True)
        self.root = etree.fromstring(xml_text.encode(), parser)
        self.paths: dict[str, list[etree._Element]] = {}   # label path -> component elements in the template
        self._complete()
        self._index(self.root, ())

    @classmethod
    @lru_cache(maxsize=None)
    def for_dm(cls, ct_id: str) -> "Template":
        with open(os.path.join(DMLIB, f"dm-{ct_id}.xml"), encoding="utf-8") as f:
            return cls(ct_id, f.read())

    # ---------------------------------------------------------------- completion
    def _complete(self):
        """Give every cluster every member the schema declares under it.

        The scaffold (SDCStudio issue #705) writes a component composed in several clusters only under the first
        one, and writes an Audit's location cluster with its label alone, so missing members are cloned from their
        first occurrence in the template (the adapter is the same element in every cluster of a model) or, when
        the template has none, built from the schema with placeholders.
        """
        first: dict[str, etree._Element] = {}
        for el in self.root.iter():
            tag = _tag(el)
            if tag.startswith("ms-") and self.schema.base.get(tag[3:]) in ("XdAdapterType", "ClusterType"):
                first.setdefault(tag[3:], el)
        grew = True
        while grew:   # a clone may itself be a cluster missing members
            grew = False
            for cl in list(self.root.iter()):
                ct = self._cluster_type(cl)
                if ct is None:
                    continue
                present = {_tag(c)[3:] for c in cl if isinstance(c.tag, str)}
                for child in self.schema._children(ct):
                    if child in present or self.schema.base.get(child) not in ("XdAdapterType", "ClusterType"):
                        continue
                    src = first.get(child)
                    cl.append(copy.deepcopy(src) if src is not None else self._synthesize(child))
                    grew = True

    def _cluster_type(self, el) -> str | None:
        """The cluster type an element carries: an ms- cluster, or an Audit's location / a Party's details by the parent's type."""
        tag = _tag(el)
        if tag.startswith("ms-"):
            return tag[3:] if self.schema.base.get(tag[3:]) == "ClusterType" else None
        if tag in ("location", "party-details"):
            parent = el.getparent()
            ptag = _tag(parent) if parent is not None else ""
            body = self.schema.types.get(ptag[3:], "") if ptag.startswith("ms-") else ""
            m = re.search(r'name="%s" type="sdc4:mc-([a-z0-9]+)"' % tag, body)
            return m.group(1) if m else None
        return None

    _VALUE_OF = {"XdStringType": ("xdstring-value",), "XdTokenType": ("xdtoken-value",), "XdBooleanType": ("true-value",),
                 "XdOrdinalType": ("ordinal", "symbol"), "XdFileType": ("uri",),
                 "XdQuantityType": ("xdquantity-value", "xdquantity-units"), "XdCountType": ("xdcount-value", "xdcount-units"),
                 "XdFloatType": ("xdfloat-value", "xdfloat-units"), "XdDoubleType": ("xddouble-value", "xddouble-units")}

    def _synthesize(self, ct: str):
        """An element for this adapter or cluster, from the schema alone: label, placeholders, members."""
        el = etree.Element(f"{{{SDC4}}}ms-{ct}")
        base = self.schema.base.get(ct, "")
        if base == "XdAdapterType":
            for inner in self.schema._children(ct):
                el.append(self._synthesize(inner))
            return el
        etree.SubElement(el, "label").text = self.schema.label.get(ct, "")
        if base == "ClusterType":
            for child in self.schema._children(ct):
                el.append(self._synthesize(child))
            return el
        if base == "XdTemporalType":
            kinds = re.findall(r'name="(xdtemporal-[a-z-]+)"', self.schema.types[ct])
            etree.SubElement(el, kinds[0] if kinds else "xdtemporal-date").text = "_PH_"
            return el
        if base == "XdLinkType":
            for name in ("link", "relation", "relation-uri"):
                m = re.search(r'name="%s"[^>]*fixed="([^"]*)"' % name, self.schema.types[ct])
                if m:
                    etree.SubElement(el, name).text = _unescape_xml(m.group(1))
            return el
        names = self._VALUE_OF.get(base)
        assert names, f"cannot build a {base} ({self.schema.label.get(ct)}) from the schema"
        for name in names:
            if name.endswith("-units"):
                m = re.search(r'name="%s" type="sdc4:mc-([a-z0-9]+)"' % name, self.schema.types[ct])
                units = etree.SubElement(el, name)
                etree.SubElement(units, "label").text = self.schema.label.get(m.group(1), "") if m else ""
                etree.SubElement(units, "xdstring-value").text = "_PH_"
            else:
                etree.SubElement(el, name).text = "_PH_"
        return el

    # ---------------------------------------------------------------- indexing
    def _index(self, el, path: tuple[str, ...]):
        for child in el:
            tag = _tag(child)
            if tag.startswith("ms-"):
                label_el = child.find("label")
                if label_el is not None and self.schema.base.get(tag[3:], "") not in ("XdAdapterType",):
                    p = path + (label_el.text or "",)
                    for n in range(1, len(p) + 1):
                        self.paths.setdefault("/".join(p[-n:]), []).append(child)
                    self._index(child, p)
                    continue
            self._index(child, path)

    def _component(self, path: str):
        hits = self.paths.get(path)
        if not hits:
            raise KeyError(f"no component at {path!r} in the template of dm-{self.ct_id}")
        distinct = {id(h) for h in hits}
        if len(distinct) > 1:
            raise KeyError(f"{path!r} is ambiguous in dm-{self.ct_id}; give more of the path")
        return hits[0]

    # ---------------------------------------------------------------- filling
    def instance(self, values: dict[str, Any], instance_id: str, current_state: str | None = None, timestamp: str = "2026-01-01T00:00:00",
                 subject: tuple[str, str] | None = None, provider: tuple[str, str] | None = None, audit: dict | None = None, attestation: dict | None = None,
                 keep: tuple[str, ...] = ()) -> str:
        root = copy.deepcopy(self.root)
        # re-index the copy
        t = Template.__new__(Template)
        t.ct_id, t.schema, t.root, t.paths = self.ct_id, self.schema, root, {}
        t._index(root, ())
        filled: set = set()
        t._filled = filled
        for path, value in values.items():
            comp = t._component(path)
            t._fill(comp, path, value)
            filled.add(comp)
            for anc in comp.iterancestors():
                filled.add(anc)
        for path in keep:
            comp = t._component(path)
            filled.add(comp)
            for anc in comp.iterancestors():
                filled.add(anc)
        # header
        for name, text in (("creation_timestamp", timestamp), ("instance_id", instance_id), ("instance_version", "1")):
            el = root.find(name)
            if el is not None:
                el.text = text
        cs = root.find("current-state")
        if cs is not None:
            if current_state:
                states = self.schema.states()
                assert not states or current_state in states, f"current-state {current_state!r} is not a state of the bound workflow {states}"
                cs.text = current_state
            else:
                root.remove(cs)
        t._parties(root, subject, provider)
        t._audit(root, audit, timestamp)
        t._attestation(root, attestation, timestamp)
        for el in list(root):
            if _tag(el).startswith("ms-") and self.schema.base.get(_tag(el)[3:]) == "ParticipationType":
                root.remove(el)   # 4.4.0 models carry no participations; a generator that wants one fills it explicitly
        t._prune(root, filled)
        t._reorder(root)
        return etree.tostring(root, pretty_print=True, encoding="unicode", xml_declaration=False)

    DM_ORDER = ("dm-label", "dm-language", "dm-encoding", "creation_timestamp", "instance_id", "instance_version", "source_instance_id", "source_version_id",
                "current-state", "@data", "subject", "provider", "@ParticipationType", "protocol", "workflow", "acs", "@AuditType", "attestation", "@XdLinkType")

    def _rank(self, el, order):
        tag = _tag(el)
        if tag.startswith("ms-"):
            base = self.schema.base.get(tag[3:], "")
            key = "@data" if base == "ClusterType" else "@" + base
        else:
            key = tag
        return order.index(key) if key in order else len(order)

    def _reorder(self, root):
        """Children in the order the schema declares them: the DM's fixed sequence, and for each cluster the nested clusters and adapters as declared."""
        root[:] = sorted(list(root), key=lambda e: self._rank(e, self.DM_ORDER))
        for el in root.iter():
            tag = _tag(el)
            if tag.startswith("ms-") and self.schema.base.get(tag[3:]) == "ClusterType":
                declared = self.schema._children(tag[3:])
                def rank(c):
                    ct = _tag(c)
                    if ct == "label":
                        return -1
                    if ct.startswith("ms-") and ct[3:] in declared:
                        return declared.index(ct[3:])
                    return len(declared)
                el[:] = sorted(list(el), key=rank)

    def _fill(self, comp, path: str, value):
        base = self.schema.base.get(_tag(comp)[3:], "")
        if isinstance(value, EV):
            self._exceptional(comp, value.code)
            for kind in ("xdquantity", "xdcount", "xdfloat", "xddouble"):
                units = comp.find(f"{kind}-units")
                if units is not None:   # the schema still requires the units beside a stated absence
                    enums = self.schema.units_enums(path)
                    self._set(units, "xdstring-value", enums[0] if enums else "1")
            return
        if base == "XdStringType":
            self._set(comp, "xdstring-value", value)
        elif base == "XdTokenType":
            self._set(comp, "xdtoken-value", value)
        elif base == "XdTemporalType":
            self._temporal(comp, path, value)
        elif base in ("XdQuantityType", "XdCountType", "XdFloatType", "XdDoubleType"):
            assert isinstance(value, Quantity), f"{path}: a Quantity(magnitude, unit) is needed"
            kind = {"XdQuantityType": "xdquantity", "XdCountType": "xdcount", "XdFloatType": "xdfloat", "XdDoubleType": "xddouble"}[base]
            self._set(comp, f"{kind}-value", value.magnitude)
            units = comp.find(f"{kind}-units")
            if units is not None:
                self._set(units, "xdstring-value", value.unit)
        elif base == "XdBooleanType":
            self._boolean(comp, path, value)
        elif base == "XdOrdinalType":
            ordinal, symbol = value
            self._set(comp, "ordinal", str(ordinal))
            self._set(comp, "symbol", symbol)
        elif base == "XdFileType":
            if comp.find("media-content") is not None:   # the model fixed content mode: bytes, carried base64
                assert isinstance(value, bytes), f"{path}: the model carries the file content; give bytes"
                self._set(comp, "media-content", base64.b64encode(value).decode())
            else:
                self._set(comp, "uri", value)
        elif base == "XdLinkType":
            pass   # fixed in the schema
        elif base == "ClusterType":
            pass   # a cluster is kept by naming it; its members carry the values
        else:
            raise KeyError(f"{path}: cannot fill a {base}")

    def _set(self, parent, name: str, text):
        el = parent.find(name)
        assert el is not None, f"{name} not in the template under {_tag(parent)}"
        el.text = str(text)

    def _temporal(self, comp, path: str, value: str):
        name = next((n for n, rx in KINDS if rx.search(value)), None)
        assert name, f"temporal value {value!r} matches no kind"
        allowed = self.schema.temporal_kinds(path)
        assert name in allowed, f"{path}: the model allows {allowed}, not a {name[11:]} ({value!r})"
        present = [c for c in comp if _tag(c).startswith("xdtemporal-")]
        assert present, f"{_tag(comp)}: no temporal element in the template"
        target = next((c for c in present if _tag(c) == name), None)
        if target is None:   # the template shows one branch; the value asks for another the schema allows
            target = present[0]
            target.tag = name
        for c in present:
            if c is not target:
                comp.remove(c)
        target.text = value

    def _boolean(self, comp, path: str, value):
        trues = self.schema.element_enums(path, "true-value") or ["true"]
        falses = self.schema.element_enums(path, "false-value") or ["false"]
        el = comp.find("true-value")
        if el is None:
            el = comp.find("false-value")
        assert el is not None, f"{_tag(comp)}: no boolean value element"
        if value is True or str(value) in trues:
            el.tag, el.text = "true-value", (value if isinstance(value, str) else trues[0])
        else:
            el.tag, el.text = "false-value", (value if isinstance(value, str) else falses[0])

    def _exceptional(self, comp, code: str):
        assert code in EV_NAMES, code
        for c in list(comp):
            tag = _tag(c)
            if tag in VALUE_ELEMENTS or tag.startswith("xdtemporal-"):
                comp.remove(c)   # the value goes; what the schema still requires beside it (a quantity's units) stays
        ev = etree.SubElement(comp, f"{{{SDC4}}}{code}")
        name = etree.SubElement(ev, "ev-name")
        name.text = EV_NAMES[code]
        act = comp.find("act")
        comp.remove(ev)
        comp.insert(list(comp).index(act) + 1 if act is not None else 1, ev)

    # ---------------------------------------------------------------- governance slots
    @staticmethod
    def _party_name(party, name: str):
        """PartyType is label?, party-name?, party-ref?, party-details?: the name goes right after the label."""
        pn = party.find("party-name")
        if pn is None:
            return   # a modeled party may restrict party-name away (the June System Audit's system user does)
        pn.text = name

    def _parties(self, root, subject, provider):
        for name, party in (("subject", subject), ("provider", provider)):
            el = root.find(name)
            if party is None:
                if el is not None:
                    root.remove(el)
                continue
            if el is None:
                el = etree.SubElement(root, name)   # the scaffold leaves optional parties out; _reorder places it
            label, party_name = party
            for c in list(el):
                el.remove(c)
            etree.SubElement(el, "label").text = label
            etree.SubElement(el, "party-name").text = party_name

    def _audit(self, root, audit, timestamp):
        audits = [c for c in root if _tag(c).startswith("ms-") and self.schema.base.get(_tag(c)[3:]) == "AuditType"]
        for el in audits:
            if audit is None:
                root.remove(el)
                continue
            sid = el.find("system-id")
            if sid is not None:
                self._set(sid, "xdstring-value", audit["system_id"])
            user = el.find("system-user")
            if user is not None:
                self._party_name(user, audit["user"])
            ts = el.find("timestamp")
            if ts is not None:
                ts.text = audit.get("timestamp", timestamp)
            for path, value in audit.get("values", {}).items():   # members of the audit's location cluster, by path
                comp = self._component(path)
                self._fill(comp, path, value)
                self._filled.add(comp)
                for anc in comp.iterancestors():
                    self._filled.add(anc)

    ATTESTATION_ORDER = ("label", "view", "proof", "reason", "committer", "committed", "pending")

    def _attestation(self, root, attestation, timestamp):
        el = root.find("attestation")
        if el is None:
            return
        if attestation is None:
            root.remove(el)
            return
        reason = el.find("reason")
        if reason is None:
            reason = etree.SubElement(el, "reason")
            etree.SubElement(reason, "label").text = "Attestation Reason"
            etree.SubElement(reason, "xdstring-value")
        self._set(reason, "xdstring-value", attestation.get("reason", "Recorded"))
        committer = el.find("committer")
        if committer is None:
            committer = etree.SubElement(el, "committer")
            etree.SubElement(committer, "label").text = "Committer"
            etree.SubElement(committer, "party-name")
        self._party_name(committer, attestation.get("committer", "Registrar"))
        committed = el.find("committed")
        if committed is None:
            committed = etree.SubElement(el, "committed")
        committed.text = attestation.get("committed", timestamp)
        pending = el.find("pending")
        if pending is None:
            pending = etree.SubElement(el, "pending")
        pending.text = str(bool(attestation.get("pending", False))).lower()
        el[:] = sorted(list(el), key=lambda c: self.ATTESTATION_ORDER.index(_tag(c)) if _tag(c) in self.ATTESTATION_ORDER else 99)

    # ---------------------------------------------------------------- pruning
    def _prune(self, root, filled: set):
        # 1. every optional placeholder goes; a required placeholder left over is a generator bug
        for el in list(root.iter()):
            if el.text == "_OPT_PH_":
                el.getparent().remove(el)
        # 2. components the generator did not fill: drop the adapter (or the bare element) unless the schema requires it
        for el in list(root.iter()):
            tag = _tag(el) if isinstance(el.tag, str) else ""
            if not tag.startswith("ms-") or el.getparent() is None:
                continue
            base = self.schema.base.get(tag[3:], "")
            if base == "XdAdapterType":
                inner = [c for c in el if isinstance(c.tag, str)]
                if inner and inner[0] not in filled and el.getparent() is not None:
                    parent_type = _tag(el.getparent())[3:]
                    if self.schema.min_occurs.get((parent_type, tag[3:]), 0) < 1:
                        el.getparent().remove(el)
            elif base == "ClusterType" and el not in filled and _tag(el.getparent()).startswith("ms-") is False:
                pass
        # 3. clusters left with only a label, innermost first, until none is left
        dropped = True
        while dropped:
            dropped = False
            for el in list(root.iter()):
                tag = _tag(el) if isinstance(el.tag, str) else ""
                if tag.startswith("ms-") and self.schema.base.get(tag[3:]) == "ClusterType" and el not in filled:
                    members = [c for c in el if isinstance(c.tag, str) and _tag(c) != "label"]
                    if not members and el.getparent() is not None:
                        parent = el.getparent()
                        ptag = _tag(parent)
                        if ptag.startswith("ms-") and self.schema.base.get(ptag[3:]) == "XdAdapterType":
                            gp = parent.getparent(); gtag = _tag(gp)[3:] if gp is not None else ""
                            if self.schema.min_occurs.get((gtag, ptag[3:]), 0) < 1:
                                gp.remove(parent); dropped = True
                        elif self.schema.min_occurs.get((ptag[3:] if ptag.startswith("ms-") else self.schema.dm, tag[3:]), 0) < 1:
                            parent.remove(el); dropped = True
        # 4. no placeholder may remain
        left = [(_tag(el.getparent()), _tag(el)) for el in root.iter() if el.text == "_PH_"]
        assert not left, f"required values not supplied: {left[:8]}"
        for el in list(root.iter()):
            if not isinstance(el.tag, str):
                el.getparent().remove(el)   # the scaffold's comments
