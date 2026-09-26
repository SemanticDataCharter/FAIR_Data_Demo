"""The FAIR Data Demo model rulebook as code (docs/design/FAIR-Demo-2-PRD.md §2)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISHER_IRI = "https://axius-sdc.com"
IDENTIFIER_BASE = "https://axius-sdc.com/library/fair/"
DEFAULT_SLOT = "https://axius-sdc.com/library/default/"
PROVGOV_SLOT = "https://axius-sdc.com/library/provgov/"
FHIR_SLOT = "https://axius-sdc.com/library/fhir/"
NIEM_SLOT = "https://axius-sdc.com/library/niem/"
SLOT_BASES = (DEFAULT_SLOT, PROVGOV_SLOT, FHIR_SLOT, NIEM_SLOT)
LABEL_MAX = 110
TYPES = {"XdString", "XdToken", "XdOrdinal", "XdBoolean", "XdCount", "XdQuantity", "XdTemporal", "XdLink", "XdFile", "Units", "Cluster"}
SYMBOL_RE = r"^[A-Za-z0-9][A-Za-z0-9_.\- ()/']*$"
#: The studies define their own identifiers, survey design fields and agency codings; everything a standard defines comes from a library by slot or a NIH CDE by ct_id.
STANDARDS = {
    "FAIR Data Demo": "https://github.com/SemanticDataCharter/FAIR_Data_Demo",
    "NHANES 2017-2018": "https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017",
    "BRFSS 2022": "https://www.cdc.gov/brfss/annual_data/annual_2022.html",
    "CMS DE-SynPUF": "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf",
    "LOINC": "https://loinc.org/",
    "SNOMED CT": "http://snomed.info/sct",
    "ICD-9-CM": "http://hl7.org/fhir/sid/icd-9-cm",
    "HCPCS": "http://www.ama-assn.org/go/cpt",
    "NDC": "http://hl7.org/fhir/sid/ndc",
    "QUDT": "http://qudt.org/",
    "UCUM": "https://ucum.org/ucum",
    "schema.org": "https://schema.org/",
    "PROV-O": "https://www.w3.org/TR/prov-o/",
    "FHIR R4": "http://hl7.org/fhir/R4/",
}
CODE_LIST_IRI_PREFIX = "https://docs.oasis-open.org/niemopen/ns/model/"
