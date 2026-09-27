"""
SDC Validator wrapper with automatic ExceptionalValue recovery.

This module provides validation for SDC4 XML instances using sdcvalidator,
with automatic recovery of invalid components using ISO 21090 ExceptionalValues.

Requires sdcvalidator >= 4.3.0 for ExceptionalValue recovery. Earlier 4.1.x/4.2.x
releases are structural-only; with those installed, structural validation still
works but auto-recovery is disabled.
"""
import logging
import os
import xml.etree.ElementTree as ET
from typing import Tuple, List, Optional
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

# Structural validation is the baseline capability and is imported on its own so
# a missing recovery symbol can never disable basic validation too.
try:
    from sdcvalidator import SDC4Validator
    HAS_SDCVALIDATOR = True
except ImportError:
    HAS_SDCVALIDATOR = False

# ExceptionalValue recovery is additive (sdcvalidator >= 4.3.0). Guarded
# separately so structural validation survives if it is unavailable.
try:
    from sdcvalidator import etree_tostring, SDC4StructuralValidationError
    HAS_EV_RECOVERY = True
except ImportError:
    HAS_EV_RECOVERY = False

# Local schema resolution (sdcvalidator >= 4.4.1). Lets the sdc4.xsd namespace
# include resolve from the reference model bundled beside the data-model schema,
# so validation works offline instead of fetching the namespace URL over the wire.
try:
    from sdcvalidator import build_xsd11_schema
    HAS_LOCAL_RESOLUTION = True
except ImportError:
    HAS_LOCAL_RESOLUTION = False

logger = logging.getLogger(__name__)

SDC4_NS = "https://semanticdatacharter.com/ns/sdc4/"
SDC4_SCHEMA_URL = SDC4_NS + "sdc4.xsd"


def _to_element(xml_source) -> ET.Element:
    """
    Normalize XML content (str/bytes) or a file path into an Element.

    A leading '<' marks XML content; anything else is treated as a file path.
    Content is encoded to bytes so an XML declaration with an encoding is
    accepted (ElementTree rejects encoding declarations on str input).
    """
    if isinstance(xml_source, (bytes, bytearray)):
        return ET.fromstring(xml_source)
    text = xml_source.strip()
    if text.startswith('<'):
        return ET.fromstring(xml_source.encode('utf-8'))
    return ET.parse(xml_source).getroot()


@dataclass
class ValidationResult:
    """Result of XML validation with optional ExceptionalValue recovery."""
    is_valid: bool
    errors: list = field(default_factory=list)
    recovered_xml: Optional[str] = None
    report: Optional[dict] = None
    auto_corrected_fields: List[str] = field(default_factory=list)


def _uri_mapper_from_catalog(xsd_path):
    """
    Build an xmlschema uri_mapper from an OASIS catalog sitting beside the schema.

    xmlschema has no native catalog support, so the catalog is read here and
    turned into the mapping it already expresses. Paths inside it are resolved
    relative to the catalog file, which is the point: one catalog, relative
    entries, portable to any machine, and it covers the reference model include
    and any data-model cross-references in the same file.

    Returns None when there is no catalog, so callers can fall back.
    """
    catalog = os.path.join(os.path.dirname(os.path.abspath(xsd_path)), 'catalog.xml')
    if not os.path.exists(catalog):
        return None

    base = os.path.dirname(catalog)
    mapping = {}
    rewrites = []
    try:
        root = ET.parse(catalog).getroot()
    except Exception as exc:
        logger.warning('Could not read %s: %s', catalog, exc)
        return None

    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        if tag in ('uri', 'system'):
            name = elem.get('name') or elem.get('systemId')
            target = elem.get('uri')
            if name and target:
                mapping[name] = os.path.normpath(os.path.join(base, target))
        elif tag in ('rewriteURI', 'rewriteSystem'):
            start = elem.get('uriStartString') or elem.get('systemIdStartString')
            prefix = elem.get('rewritePrefix')
            if start and prefix is not None:
                rewrites.append((start, os.path.normpath(os.path.join(base, prefix))))

    if not mapping and not rewrites:
        return None

    # Longest prefix first, so a specific rewrite beats a general one.
    rewrites.sort(key=lambda pair: len(pair[0]), reverse=True)

    def resolve(uri):
        if uri in mapping:
            return mapping[uri]
        for start, prefix in rewrites:
            if uri.startswith(start):
                return os.path.join(prefix, uri[len(start):])
        return uri

    return resolve


class SDCValidator:
    """
    Wrapper around sdcvalidator.SDC4Validator with convenience methods.

    Validates XML instances against XSD schema and can automatically
    apply ExceptionalValues to invalid components using the SDC4
    quarantine-and-tag pattern.

    ExceptionalValue types use ISO 21090 NULL Flavor codes:
        INV  - Invalid (type violations, pattern mismatches)
        OTH  - Other (value not in coding system)
        NI   - No Information (missing/omitted value)
        NA   - Not Applicable (unexpected content)
        UNC  - Unencoded (encoding/format errors)
        UNK  - Unknown
        ASKU - Asked but Unknown
        ASKR - Asked and Refused
        NASK - Not Asked
        NAV  - Not Available
        MSK  - Masked (privacy/security)
        DER  - Derived
        PINF - Positive Infinity
        NINF - Negative Infinity
        TRC  - Trace
    """

    def __init__(self, xsd_path: str):
        """
        Initialize validator with XSD schema path.

        Args:
            xsd_path: Path to the XSD schema file
        """
        self.xsd_path = xsd_path
        if HAS_SDCVALIDATOR:
            # 'lax' schema-build mode: generated SDC4 data-model schemas use
            # restriction derivations that xmlschema's 'strict' build rejects;
            # lax tolerates them so instance validation/recovery can run.
            if HAS_LOCAL_RESOLUTION:
                # Resolve the sdc4.xsd namespace include from the reference model
                # bundled beside the data-model schema (dmlib/sdc4.xsd), so
                # validation works offline and does not depend on network access
                # to the namespace URL. Over-the-wire resolution can be slow or
                # unavailable, and must be local for air-gapped deployments.
                # An OASIS catalog beside the schema is preferred: one file,
                # relative entries, covering the reference model and any
                # data-model cross-references. Falls back to a sibling copy of
                # the reference model, then to network resolution.
                uri_mapper = _uri_mapper_from_catalog(xsd_path)
                if uri_mapper is None:
                    local_rm = os.path.join(
                        os.path.dirname(os.path.abspath(xsd_path)), 'sdc4.xsd')
                    uri_mapper = (
                        {SDC4_SCHEMA_URL: local_rm} if os.path.exists(local_rm) else None)
                if uri_mapper is None:
                    logger.warning(
                        'No local resolution for %s: validation will try the '
                        'network and its verdicts become non-deterministic.',
                        SDC4_SCHEMA_URL)
                schema = build_xsd11_schema(
                    xsd_path, validation='lax', uri_mapper=uri_mapper)
                self.validator = SDC4Validator(schema)
            else:
                self.validator = SDC4Validator(xsd_path, validation='lax')
        else:
            self.validator = None
            logger.warning(
                "sdcvalidator not installed. Validation will be skipped. "
                "Install with: pip install 'sdcvalidator>=4.3.0'"
            )

    def validate(self, xml_content: str) -> ValidationResult:
        """
        Validate XML content against XSD schema.

        Args:
            xml_content: XML string (or file path) to validate

        Returns:
            ValidationResult with validation status and errors
        """
        if self.validator is None:
            return ValidationResult(is_valid=True)

        try:
            report = self.validator.validate_and_report(_to_element(xml_content))
            return ValidationResult(
                is_valid=report['valid'],
                errors=report.get('errors', []),
                report=report,
            )
        except Exception as e:
            logger.error("Validation failed: %s", e)
            return ValidationResult(
                is_valid=False,
                errors=[{'reason': str(e), 'xpath': '/', 'exceptional_value_type': 'INV'}],
            )

    def auto_correct_with_evs(
        self,
        xml_content: str,
        errors: list,
    ) -> Tuple[str, List[str]]:
        """
        Validate and recover XML with ExceptionalValue injection.

        Uses sdcvalidator's validate_with_recovery to automatically
        insert ExceptionalValue elements for semantic validation errors.
        Structural (Tier 1) errors cannot be recovered; the original XML is
        returned unchanged in that case.

        Args:
            xml_content: Original XML content with validation errors
            errors: List of error dicts from validate() (used for field labeling)

        Returns:
            Tuple of (recovered_xml_string, list_of_corrected_field_xpaths)
        """
        if self.validator is None or not HAS_EV_RECOVERY:
            if self.validator is not None and not HAS_EV_RECOVERY:
                logger.warning(
                    "Installed sdcvalidator lacks ExceptionalValue recovery; "
                    "upgrade to 'sdcvalidator>=4.3.0'. Returning original XML."
                )
            return xml_content, []

        try:
            recovered_tree = self.validator.validate_with_recovery(
                _to_element(xml_content), save=False
            )
            recovered_xml = etree_tostring(
                recovered_tree.getroot(), namespaces={'sdc4': SDC4_NS}
            )

            corrected_fields = [
                error.get('xpath', 'unknown')
                for error in errors
            ]

            return recovered_xml, corrected_fields
        except SDC4StructuralValidationError as e:
            logger.warning("Structural (Tier 1) errors cannot be auto-recovered: %s", e)
            return xml_content, []
        except Exception as e:
            logger.error("ExceptionalValue recovery failed: %s", e)
            return xml_content, []

    def validate_and_recover(self, xml_content: str) -> ValidationResult:
        """
        Validate XML and automatically recover with ExceptionalValues.

        Combines validate() and auto_correct_with_evs() in a single call.

        Args:
            xml_content: XML string to validate

        Returns:
            ValidationResult with recovered XML if errors were found
        """
        result = self.validate(xml_content)

        if not result.is_valid and result.errors:
            recovered_xml, corrected_fields = self.auto_correct_with_evs(
                xml_content, result.errors
            )
            result.recovered_xml = recovered_xml
            result.auto_corrected_fields = corrected_fields

        return result
