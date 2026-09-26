"""
RDF 1.2 Triple Term Extractor for SDC4 XML Instances.

This module extracts RDF 1.2 triple terms from SDC4 XML instances for Fuseki.
It uses direct Turtle string generation (rdflib doesn't support RDF 1.2 yet).

RDF 1.2 Design Philosophy (from SDC4 2009/2010 design):
- Each value has a unique XPath within its instance (instance-specific navigation)
- Cross-model queries are possible via shared component CT_IDs (ms-{ct_id})
- RDF 1.2 quoted triples + reifiers enable both patterns simultaneously

Output Format (RDF 1.2 Turtle with quoted triples):
    :v_{ct_id}_{instance_cuid} rdf:reifies
        << sdc4:mc-{ct_id} sdc4:{value_element_name} "actual_value" >> ;
        sdc4:inInstance sdc4:i-{instance_cuid} ;
        sdc4:inDataModel sdc4:dm-{dm_ct_id} ;
        sdc4:inCluster sdc4:mc-{cluster_ct_id} ;
        sdc4:throughAdapter sdc4:mc-{adapter_ct_id} ;
        sdc4:units "people" ;
        sdc4:vtb "2024-01-01T00:00:00"^^xsd:dateTime ;
        sdc4:ev sdc4:NASK .

This enables:
1. Instance-specific queries: "Get all values from instance i-abc123"
2. Cross-model queries: "Get all values for component mc-xyz789 across all instances"
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class RDFExtractor:
    """
    Extracts RDF 1.2 triple terms from SDC4 XML instances.

    Uses direct Turtle string generation for RDF 1.2 features
    (quoted triples, rdf:reifies) since rdflib doesn't support RDF 1.2.

    The output is valid RDF 1.2 Turtle that can be loaded into:
    - Apache Jena 5.4.0+ (with experimental RDF 1.2 support)
    - Future rdflib versions with RDF 1.2 support
    """

    # Namespace prefixes for Turtle output
    PREFIXES = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix sdc4: <https://semanticdatacharter.com/ns/sdc4/> .
@prefix dm: <https://semanticdatacharter.com/ns/dm/> .
@prefix : <https://semanticdatacharter.com/ns/dm/> .

"""

    # SDC4 namespace URI
    SDC4_NS = 'https://semanticdatacharter.com/ns/sdc4/'

    # XSD datatype mappings for SDC4 types
    XSD_DATATYPES = {
        'XdString': 'xsd:string',
        'XdToken': 'xsd:string',
        'XdBoolean': 'xsd:boolean',
        'XdCount': 'xsd:integer',
        'XdOrdinal': 'xsd:integer',
        'XdQuantity': 'xsd:decimal',
        'XdFloat': 'xsd:float',
        'XdDouble': 'xsd:double',
        'XdTemporal': 'xsd:dateTime',
        'XdLink': 'xsd:anyURI',
        'XdFile': 'xsd:base64Binary',
    }

    # Value element names for each type
    VALUE_ELEMENTS = {
        'XdString': 'xdstring-value',
        'XdToken': 'xdtoken-value',
        'XdBoolean': 'xdboolean-value',
        'XdCount': 'xdcount-value',
        'XdOrdinal': 'xdordinal-value',
        'XdQuantity': 'xdquantity-value',
        'XdFloat': 'xdfloat-value',
        'XdDouble': 'xddouble-value',
        'XdLink': 'xdlink-value',
        'XdFile': 'xdfile-value',
        # Note: XdTemporal is handled specially - see TEMPORAL_VALUE_ELEMENTS
    }

    # XdTemporal uses variant element names based on temporal subtype
    TEMPORAL_VALUE_ELEMENTS = [
        'xdtemporal-date',
        'xdtemporal-time',
        'xdtemporal-datetime',
        'xdtemporal-duration',
        'xdtemporal-day',
        'xdtemporal-month',
        'xdtemporal-year',
        'xdtemporal-year-month',
        'xdtemporal-month-day',
    ]

    def __init__(
        self,
        dm_ct_id: str,
        dm_label: str,
        field_metadata: Optional[Dict] = None
    ):
        """
        Initialize RDFExtractor.

        Args:
            dm_ct_id: Data Model CT_ID (e.g., 'its7j6bvrb9n2fxdcxmoemod')
            dm_label: Data Model label (e.g., 'StatePopulation')
            field_metadata: Field metadata dictionary from model's FIELD_METADATA
                           Structure: {ct_id: {label, type, ...}, ...}
        """
        self.dm_ct_id = dm_ct_id
        self.dm_label = dm_label
        self.field_metadata = field_metadata or {}

        # In FIELD_METADATA, ct_id IS the key
        # Build ct_id to label mapping for lookups
        self._ct_id_to_field = {}
        for ct_id, meta in self.field_metadata.items():
            # Use label as the field name, fall back to ct_id
            self._ct_id_to_field[ct_id] = meta.get('label', ct_id)

    def extract(
        self,
        xml_content: str,
        instance_id: str,
        validation_status: str,
        auto_corrected_fields: List[str]
    ) -> str:
        """
        Extract RDF 1.2 triple terms from SDC4 XML content.

        Args:
            xml_content: SDC4-compliant XML string
            instance_id: Instance ID (e.g., 'i-abc123def456')
            validation_status: Validation status ('valid', 'valid_with_ev', 'invalid')
            auto_corrected_fields: List of field labels with auto-applied EVs

        Returns:
            str: RDF 1.2 Turtle string with quoted triples and reifiers
        """
        try:
            tree = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            return ''

        # Start building Turtle output
        turtle_lines = [self.PREFIXES]

        # Extract instance CUID from instance_id (e.g., 'i-abc123' -> 'abc123')
        instance_cuid = instance_id.replace('i-', '').replace('ev-', '')

        # Add instance metadata triples
        turtle_lines.extend(self._generate_instance_metadata(
            tree, instance_id, instance_cuid, validation_status, auto_corrected_fields
        ))

        # Find the root cluster element
        cluster_ct_id = self._find_cluster_ct_id(tree)

        # Extract component values as RDF 1.2 triple terms
        for elem in tree.iter():
            tag_name = self._strip_namespace(elem.tag)

            # Process ms-* component elements that contain values
            if tag_name.startswith('ms-'):
                ct_id = tag_name.replace('ms-', '')

                # Check if this is a data component (has a value element)
                if ct_id in self._ct_id_to_field:
                    triple_terms = self._extract_component_triple_term(
                        elem, ct_id, instance_id, instance_cuid, cluster_ct_id
                    )
                    if triple_terms:
                        turtle_lines.extend(triple_terms)

        # Party references live outside the ms-* tree and are extracted here.
        turtle_lines.extend(self._extract_parties(tree, instance_id, instance_cuid))

        return '\n'.join(turtle_lines)

    def _child_text(self, parent, name: str) -> str:
        """Text of the first direct child with this local name."""
        for child in parent:
            if self._strip_namespace(child.tag) == name and child.text:
                return child.text.strip()
        return ''

    def _extract_parties(
        self,
        tree: ET.Element,
        instance_id: str,
        instance_cuid: str
    ) -> List[str]:
        """
        Emit the party references carried by native PartyType slots.

        Component values live in ms-* elements and are extracted above. A party
        does not: subject, provider and the rest are native RM types, so a
        party-ref never reaches the graph through that path. A party recorded
        only as a name joins nothing, which is the difference between "employed
        by Costa Motors" and a link to the registered organisation.
        """
        lines: List[str] = []
        seen = 0

        for elem in tree.iter():
            ref = None
            for child in elem:
                if self._strip_namespace(child.tag) == 'party-ref':
                    ref = child
                    break
            if ref is None:
                continue

            link = self._child_text(ref, 'link')
            if not link:
                continue

            seen += 1
            node = f'sdc4:party-{instance_cuid}-{seen}'
            slot = self._strip_namespace(elem.tag)
            label = self._child_text(elem, 'label')
            party_name = self._child_text(elem, 'party-name')
            relation = self._child_text(ref, 'relation')
            relation_uri = self._child_text(ref, 'relation-uri')

            lines.append(f'# Party reference: {slot}')
            lines.append(f'{node} a sdc4:PartyReference ;')
            lines.append(f'    sdc4:inInstance sdc4:{instance_id} ;')
            lines.append(f'    sdc4:inDataModel sdc4:dm-{self.dm_ct_id} ;')
            lines.append(f'    sdc4:partySlot "{self._escape_turtle(slot)}" ;')
            if label:
                lines.append(f'    rdfs:label "{self._escape_turtle(label)}" ;')
            if party_name:
                lines.append(f'    sdc4:partyName "{self._escape_turtle(party_name)}" ;')
            lines.append(f'    sdc4:partyRef "{self._escape_turtle(link)}" ;')
            if relation:
                lines.append(f'    sdc4:partyRelation "{self._escape_turtle(relation)}" ;')
            if relation_uri:
                lines.append(f'    sdc4:partyRelationUri <{relation_uri}> ;')
            lines[-1] = lines[-1].rstrip(' ;') + ' .'
            lines.append('')

        return lines

    def _generate_instance_metadata(
        self,
        tree: ET.Element,
        instance_id: str,
        instance_cuid: str,
        validation_status: str,
        auto_corrected_fields: List[str]
    ) -> List[str]:
        """Generate instance-level metadata triples."""
        lines = []
        lines.append(f"# Instance: {instance_id}")
        lines.append(f"sdc4:{instance_id} a sdc4:dm-{self.dm_ct_id} ;")
        lines.append(f'    rdfs:label "{self._escape_turtle(self.dm_label)}" ;')

        # Creation timestamp
        timestamp_elem = tree.find('.//creation_timestamp')
        if timestamp_elem is not None and timestamp_elem.text:
            lines.append(f'    dc:created "{timestamp_elem.text}"^^xsd:dateTime ;')

        # Validation status
        lines.append(f'    sdc4:validationStatus "{validation_status}" ;')

        # Auto-corrected fields
        if auto_corrected_fields:
            for field_label in auto_corrected_fields:
                lines.append(f'    sdc4:autoCorrectedField "{self._escape_turtle(field_label)}" ;')

        # Close the instance description
        lines[-1] = lines[-1].rstrip(' ;') + ' .'
        lines.append('')

        # DM-node metadata so cross-domain queries can resolve the domain title/label
        dm_label_esc = self._escape_turtle(self.dm_label)
        lines.append(f'sdc4:dm-{self.dm_ct_id} dc:title "{dm_label_esc}" ;')
        lines.append(f'    rdfs:label "{dm_label_esc}" .')
        lines.append('')

        return lines

    def _find_cluster_ct_id(self, tree: ET.Element) -> Optional[str]:
        """Find the root cluster CT_ID from the XML tree."""
        for elem in tree:
            tag_name = self._strip_namespace(elem.tag)
            if tag_name.startswith('ms-'):
                return tag_name.replace('ms-', '')
        return None

    def _extract_component_triple_term(
        self,
        elem: ET.Element,
        ct_id: str,
        instance_id: str,
        instance_cuid: str,
        cluster_ct_id: Optional[str]
    ) -> List[str]:
        """
        Extract RDF 1.2 triple term for a component element.

        Generates a quoted triple for the value assertion and a reifier
        node with contextual metadata.

        Args:
            elem: The ms-{ct_id} XML element
            ct_id: Component CT_ID
            instance_id: Full instance ID (e.g., 'i-abc123')
            instance_cuid: Instance CUID only (e.g., 'abc123')
            cluster_ct_id: Parent cluster CT_ID

        Returns:
            List of Turtle lines representing the triple term
        """
        lines = []

        # Get field metadata for this component (FIELD_METADATA is keyed by ct_id)
        field_meta = self.field_metadata.get(ct_id, {})
        if not field_meta:
            return lines

        field_name = self._ct_id_to_field.get(ct_id, ct_id)
        field_type = field_meta.get('type', 'XdString')
        field_label = field_meta.get('label', field_name)
        adapter_ct_id = field_meta.get('adapter_ctid')

        # Find the value element - handle XdTemporal specially
        value_elem = None
        value_elem_name = None
        if field_type == 'XdTemporal':
            # Try each possible temporal element name
            for temporal_elem_name in self.TEMPORAL_VALUE_ELEMENTS:
                value_elem = elem.find(f'.//{temporal_elem_name}')
                if value_elem is not None and value_elem.text:
                    value_elem_name = temporal_elem_name
                    break
        else:
            value_elem_name = self.VALUE_ELEMENTS.get(field_type, 'value')
            value_elem = elem.find(f'.//{value_elem_name}')

        # Check for exceptional value (EV)
        ev_elem = self._find_ev_element(elem)
        ev_code = None
        if ev_elem is not None:
            ev_code = self._strip_namespace(ev_elem.tag)

        # Get the value (may be None if EV-only)
        value = None
        if value_elem is not None and value_elem.text:
            value = value_elem.text

        # If no value and no EV, skip this component
        if value is None and ev_code is None:
            return lines

        # Build the reifier URI
        reifier_uri = f":v_{ct_id}_{instance_cuid}"

        lines.append(f"# {field_label} ({field_type})")

        # Generate the quoted triple if we have a value
        if value is not None:
            xsd_type = self.XSD_DATATYPES.get(field_type, 'xsd:string')
            escaped_value = self._escape_turtle(value)

            # Format the value literal based on type
            if field_type == 'XdBoolean':
                value_literal = value.lower()  # true/false without quotes
            elif field_type in ('XdCount', 'XdOrdinal'):
                value_literal = value  # Integer without quotes
            elif field_type in ('XdQuantity', 'XdFloat', 'XdDouble'):
                value_literal = value  # Decimal without quotes
            else:
                value_literal = f'"{escaped_value}"'

            # RDF 1.2 reifies syntax with quoted triple
            lines.append(f"{reifier_uri} rdf:reifies << sdc4:mc-{ct_id} sdc4:{value_elem_name} {value_literal} >> ;")
        else:
            # EV-only case - create a statement about the EV without a value triple
            lines.append(f"{reifier_uri} a sdc4:ExceptionalValueStatement ;")

        # Add context properties
        lines.append(f"    sdc4:inInstance sdc4:{instance_id} ;")
        lines.append(f"    sdc4:inDataModel sdc4:dm-{self.dm_ct_id} ;")

        if cluster_ct_id:
            lines.append(f"    sdc4:inCluster sdc4:mc-{cluster_ct_id} ;")

        if adapter_ct_id:
            lines.append(f"    sdc4:throughAdapter sdc4:mc-{adapter_ct_id} ;")

        lines.append(f'    rdfs:label "{self._escape_turtle(field_label)}" ;')

        # Add units if present (for quantified types)
        units_elem = self._find_units_element(elem, field_type)
        if units_elem is not None:
            units_value_elem = units_elem.find('.//xdstring-value')
            if units_value_elem is not None and units_value_elem.text:
                lines.append(f'    sdc4:units "{self._escape_turtle(units_value_elem.text)}" ;')

        # Add exceptional value if present
        if ev_code:
            lines.append(f"    sdc4:ev sdc4:{ev_code} ;")

        # Add temporal metadata (VTB, VTE)
        vtb_elem = elem.find('.//vtb')
        if vtb_elem is not None and vtb_elem.text and not vtb_elem.text.startswith('__PLACEHOLDER__'):
            lines.append(f'    sdc4:vtb "{vtb_elem.text}"^^xsd:dateTime ;')

        vte_elem = elem.find('.//vte')
        if vte_elem is not None and vte_elem.text and not vte_elem.text.startswith('__PLACEHOLDER__'):
            lines.append(f'    sdc4:vte "{vte_elem.text}"^^xsd:dateTime ;')

        # Add TR (time recorded)
        tr_elem = elem.find('.//tr')
        if tr_elem is not None and tr_elem.text and not tr_elem.text.startswith('__PLACEHOLDER__'):
            lines.append(f'    sdc4:tr "{tr_elem.text}"^^xsd:dateTime ;')

        # Add modified timestamp
        mod_elem = elem.find('.//modified')
        if mod_elem is not None and mod_elem.text and not mod_elem.text.startswith('__PLACEHOLDER__'):
            lines.append(f'    sdc4:modified "{mod_elem.text}"^^xsd:dateTime ;')

        # Add location (latitude/longitude)
        lat_elem = elem.find('.//latitude')
        lon_elem = elem.find('.//longitude')
        if (lat_elem is not None and lat_elem.text and not lat_elem.text.startswith('__PLACEHOLDER__') and
            lon_elem is not None and lon_elem.text and not lon_elem.text.startswith('__PLACEHOLDER__')):
            lines.append(f'    sdc4:latitude "{lat_elem.text}"^^xsd:decimal ;')
            lines.append(f'    sdc4:longitude "{lon_elem.text}"^^xsd:decimal ;')

        # Add ACT (access control tag)
        act_elem = elem.find('.//act')
        if act_elem is not None and act_elem.text and not act_elem.text.startswith('__PLACEHOLDER__'):
            lines.append(f'    sdc4:act "{self._escape_turtle(act_elem.text)}" ;')

        # Close the reifier description
        lines[-1] = lines[-1].rstrip(' ;') + ' .'
        lines.append('')

        return lines

    def _find_ev_element(self, elem: ET.Element) -> Optional[ET.Element]:
        """
        Find an Exceptional Value element within the component.

        EV elements are from the SDC4 substitution group:
        NI, MSK, INV, DER, UNC, OTH, NINF, PINF, ASKR, NASK, NAV, NA, TRC, ASKU, UNK, QS
        """
        ev_codes = [
            'NI', 'MSK', 'INV', 'DER', 'UNC', 'OTH', 'NINF', 'PINF',
            'ASKR', 'NASK', 'NAV', 'NA', 'TRC', 'ASKU', 'UNK', 'QS'
        ]

        for child in elem:
            tag_name = self._strip_namespace(child.tag)
            if tag_name in ev_codes:
                return child

        return None

    def _find_units_element(self, elem: ET.Element, field_type: str) -> Optional[ET.Element]:
        """Find the units element for quantified types."""
        units_elem_names = {
            'XdCount': 'xdcount-units',
            'XdQuantity': 'xdquantity-units',
            'XdFloat': 'xdfloat-units',
            'XdDouble': 'xddouble-units',
            'XdOrdinal': 'xdordinal-units',
        }

        units_elem_name = units_elem_names.get(field_type)
        if units_elem_name:
            return elem.find(f'.//{units_elem_name}')

        return None

    def _strip_namespace(self, tag: str) -> str:
        """Remove namespace from tag name."""
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    def _escape_turtle(self, value: str) -> str:
        """
        Escape special characters for Turtle string literals.

        Handles backslashes, quotes, newlines, and other special chars.
        """
        if value is None:
            return ''

        # Escape backslashes first
        value = value.replace('\\', '\\\\')
        # Escape double quotes
        value = value.replace('"', '\\"')
        # Escape newlines and other control characters
        value = value.replace('\n', '\\n')
        value = value.replace('\r', '\\r')
        value = value.replace('\t', '\\t')

        return value
