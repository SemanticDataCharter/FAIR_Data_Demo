"""
Read a published data-model schema so the generators never carry element ids.

A generated instance names every component by its adapter element (``ms-<adapter>``)
wrapping the component element (``ms-<component>``). Both ids change when a model is
republished (4.3.0 lost a day to that), so the generators resolve them from
``mediafiles/dmlib/dm-<ct_id>.xsd`` by the labels the model fixes, which do not change:

    s = Schema.for_dm("ftluo2nybgxmn7mawttoos20")
    s.cluster("Patient Record")                       -> "ms-ygtbvvmzcw3ukfsg3axqry97"
    s.leaf("Patient Record/National ID (CID)")        -> ("ms-nj7s1gk45tfgyooxpz0qaha3", "ms-znhjge005ihiusslkmbcc4h4")
    s.enums("Visit Record/Outcome")                   -> ["Treated and Released", ...]
    s.units("Visit Record/Body Temperature")          -> "Temperature (SI - Metric)"

A path is the labels from any ancestor cluster down to the leaf, separated by "/"; the
shortest unambiguous suffix is enough, and a bare label works when the model uses it once.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

DMLIB = os.path.join(os.path.dirname(__file__), "..", "app", "sdc4", "mediafiles", "dmlib")
_TYPE = re.compile(r'<xsd:complexType name="mc-([a-z0-9]+)"[^>]*>(.*?)</xsd:complexType>', re.S)
_LABEL = re.compile(r"<rdfs:label>([^<]*)</rdfs:label>")
_BASE = re.compile(r'<xsd:restriction base="sdc4:([A-Za-z]+)"')
_REF = re.compile(r'<xsd:element([^>]*)ref="sdc4:ms-([a-z0-9]+)"')
_MIN = re.compile(r'minOccurs="(\d+)"')
_ELEMENT = re.compile(r'<xsd:element name="ms-([a-z0-9]+)" type="sdc4:mc-([a-z0-9]+)"')
_ENUM = re.compile(r'<xsd:enumeration value="([^"]*)"')
_FIXED_LABEL = re.compile(r'name="label" type="xsd:string" fixed="([^"]*)"')
_UNITS_TYPE = re.compile(r'name="(?:xdquantity|xdcount|xdfloat|xddouble)-units" type="sdc4:mc-([a-z0-9]+)"')


def _unescape(s: str) -> str:
    return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")


class Schema:
    def __init__(self, xsd_text: str):
        self.types: dict[str, str] = {ct: body for ct, body in _TYPE.findall(xsd_text)}
        self.element_type: dict[str, str] = {ms: mc for ms, mc in _ELEMENT.findall(xsd_text)}   # ms-<adapter> -> mc-<adapter>
        self.base = {ct: (m.group(1) if (m := _BASE.search(body)) else "") for ct, body in self.types.items()}
        self.label = {}
        for ct, body in self.types.items():
            m = _LABEL.search(body) or _FIXED_LABEL.search(body)
            if m:
                self.label[ct] = _unescape(m.group(1))
        self.dm = next(ct for ct, b in self.base.items() if b == "DMType")
        self.min_occurs: dict[tuple[str, str], int] = {}   # (parent type, child type) -> minOccurs of the child's reference
        # every (path, component, adapter) reachable from the DM
        self.paths: list[tuple[tuple[str, ...], str, str | None]] = []
        self._walk(self.dm, (), frozenset())

    @classmethod
    @lru_cache(maxsize=None)
    def for_dm(cls, ct_id: str) -> "Schema":
        with open(os.path.join(DMLIB, f"dm-{ct_id}.xsd"), encoding="utf-8") as f:
            return cls(f.read())

    def _children(self, ct: str) -> list[str]:
        out = []
        for attrs, r in _REF.findall(self.types.get(ct, "")):
            child = self.element_type.get(r, r)
            m = _MIN.search(attrs)
            self.min_occurs[(ct, child)] = int(m.group(1)) if m else 1
            out.append(child)
        return out

    def _walk(self, ct: str, path: tuple[str, ...], ancestors: frozenset):
        """Every path from here down. A cluster composed in several places is walked under each (the NIEM location
        sits under an incident, an arrest and an organization); only a cluster inside itself is not followed."""
        for child in self._children(ct):
            base = self.base.get(child, "")
            if base == "XdAdapterType":
                for inner in self._children(child):
                    self.paths.append((path + (self.label.get(inner, ""),), inner, child))
                    if self.base.get(inner) == "ClusterType" and inner not in ancestors:
                        self._walk(inner, path + (self.label.get(inner, ""),), ancestors | {inner})
            else:
                self.paths.append((path + (self.label.get(child, ""),), child, None))
                if base == "ClusterType" and child not in ancestors:
                    self._walk(child, path + (self.label.get(child, ""),), ancestors | {child})

    def _find(self, path: str) -> tuple[str, str | None]:
        want = tuple(path.split("/"))
        hits = {(comp, adapter) for p, comp, adapter in self.paths if p[-len(want):] == want}
        if not hits:
            raise KeyError(f"no element at {path!r} in dm-{self.dm}")
        if len(hits) > 1:
            raise KeyError(f"{path!r} is ambiguous in dm-{self.dm}: {sorted(hits)}; give more of the path")
        return hits.pop()

    def cluster(self, path: str) -> str:
        comp, _ = self._find(path)
        assert self.base.get(comp) == "ClusterType", path
        return f"ms-{comp}"

    def leaf(self, path: str) -> tuple[str, str]:
        comp, adapter = self._find(path)
        assert adapter, f"{path!r} is not adapter-wrapped"
        return f"ms-{comp}", f"ms-{adapter}"

    def component(self, path: str) -> str:
        return f"ms-{self._find(path)[0]}"

    def enums(self, path: str) -> list[str]:
        comp, _ = self._find(path)
        return [_unescape(v) for v in _ENUM.findall(self.types[comp])]

    def units(self, path: str) -> str:
        comp, _ = self._find(path)
        m = _UNITS_TYPE.search(self.types[comp])
        return self.label.get(m.group(1), "") if m else ""

    def units_enums(self, path: str) -> list[str]:
        """The unit codes a quantity's units component enumerates."""
        comp, _ = self._find(path)
        m = _UNITS_TYPE.search(self.types[comp])
        return [_unescape(v) for v in _ENUM.findall(self.types.get(m.group(1), ""))] if m else []

    def base_of(self, path: str) -> str:
        return self.base.get(self._find(path)[0], "")

    def required(self, path: str) -> bool:
        """Whether the element at this path must appear in its parent (minOccurs of the adapter or cluster reference)."""
        comp, adapter = self._find(path)
        child = adapter or comp
        return any(v >= 1 for (parent, c), v in self.min_occurs.items() if c == child)

    def states(self) -> list[str]:
        """The workflow states the model's current-state enumerates (empty when no workflow is bound)."""
        m = re.search(r'name="current-state">(.*?)</xsd:element>', self.types[self.dm], re.S)
        return [_unescape(v) for v in _ENUM.findall(m.group(1))] if m else []

    def temporal_kinds(self, path: str) -> list[str]:
        """The xdtemporal-* elements the schema allows for this temporal component (a model may restrict them to one)."""
        comp, _ = self._find(path)
        return re.findall(r'<xsd:element[^>]*name="(xdtemporal-[a-z-]+)"', self.types[comp])

    def element_enums(self, path: str, element: str) -> list[str]:
        """The enumeration facets declared on one named child element of the component (true-value, false-value, ordinal, symbol)."""
        comp, _ = self._find(path)
        m = re.search(r'<xsd:element[^>]*name="%s"[^>]*>(.*?)</xsd:element>' % re.escape(element), self.types[comp], re.S)
        return [_unescape(v) for v in _ENUM.findall(m.group(1))] if m else []
