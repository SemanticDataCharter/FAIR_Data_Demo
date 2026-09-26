"""
JSON Extractor for PostgreSQL JSONB queries.

This module extracts data from SDC4 XML instances into a flattened JSON
structure optimized for PostgreSQL JSONB queries and full-text search.
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class JSONExtractor:
    """
    Extracts queryable JSON from SDC4 XML instances.

    The extracted JSON is optimized for PostgreSQL JSONB with:
    - Flattened structure for easy querying
    - Field labels as keys (human-readable)
    - Values with metadata (value, units, ev, vtb, vte, location)
    - Searchable text concatenation
    """

    # SDC4 namespace
    NS = {'sdc4': 'https://semanticdatacharter.com/ns/sdc4/'}

    # SDC4 Exceptional Value substitution group element names
    EV_TAG_NAMES = frozenset([
        'NI', 'MSK', 'INV', 'DER', 'UNC', 'OTH',
        'NINF', 'PINF', 'ASKR', 'NASK', 'NAV', 'NA',
        'TRC', 'ASKU', 'UNK', 'QS',
    ])

    def __init__(self, field_metadata: Optional[Dict] = None):
        """
        Initialize JSONExtractor.

        Args:
            field_metadata: Optional FIELD_METADATA from model for label mapping
                           Structure: {ct_id: {label, type, ...}, ...}
        """
        self.field_metadata = field_metadata or {}
        # In FIELD_METADATA, ct_id IS the key, so mapping is direct
        # ct_id -> label for human-readable field names
        self.ct_id_to_label = {
            ct_id: meta.get('label', ct_id)
            for ct_id, meta in self.field_metadata.items()
        }

    def extract(self, xml_content: str) -> Dict[str, Any]:
        """
        Extract JSON from SDC4 XML content.

        Args:
            xml_content: SDC4-compliant XML string

        Returns:
            Dict with structure:
            {
                'metadata': {...},
                'fields': {
                    'field_name': {
                        'value': ...,
                        'units': ...,  # if quantified
                        'exceptional_value': ...,  # if present
                        'valid_time_begin': ...,  # if present
                        'valid_time_end': ...,  # if present
                        'location': {'lat': ..., 'lon': ...}  # if present
                    }
                },
                'search_text': 'concatenated searchable text'
            }
        """
        try:
            tree = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            return {'metadata': {}, 'fields': {}, 'search_text': ''}

        result = {
            'metadata': self._extract_metadata(tree),
            'fields': {},
            'search_text': ''
        }

        # Extract all ms-* elements recursively (SDC4 components are nested)
        search_text_parts = []

        # Find all elements with ms-* tags that contain actual data values
        # These are the leaf nodes that have value elements
        self._extract_fields_recursive(tree, result['fields'], search_text_parts)

        result['search_text'] = ' '.join(search_text_parts)

        return result

    def _extract_fields_recursive(self, elem: ET.Element, fields: Dict, search_parts: List):
        """
        Recursively extract field data from all ms-* elements.

        SDC4 XML has nested structure:
        - dm-* (root)
          - ms-* (cluster)
            - ms-* (adapter)
              - ms-* (field with actual value)

        We need to find the innermost ms-* elements that contain value elements.
        """
        tag_name = self._strip_namespace(elem.tag)

        # If this is an ms-* element, check if it has a value
        if tag_name.startswith('ms-'):
            # Extract ct_id from tag name: ms-ju9j0b6yjt84hgwf4sg5mzl6 -> ju9j0b6yjt84hgwf4sg5mzl6
            ct_id = tag_name[3:] if tag_name.startswith('ms-') else None

            # Check if this element has a value (leaf node with data)
            has_value = False
            for value_name in self.VALUE_ELEMENT_NAMES:
                if elem.find(f'.//{value_name}') is not None:
                    has_value = True
                    break

            # Also check for Exceptional Value substitution group elements
            if not has_value:
                for child in elem:
                    if self._strip_namespace(child.tag) in self.EV_TAG_NAMES:
                        has_value = True
                        break

            if has_value and ct_id:
                field_data = self._extract_field(elem)
                if field_data:
                    # Use label from metadata or fall back to ct_id
                    field_name = self.ct_id_to_label.get(ct_id, ct_id)
                    fields[ct_id] = field_data  # Use ct_id as key for consistency

                    # Add to search text
                    if 'value' in field_data:
                        search_parts.append(str(field_data['value']))
                    if 'label' in field_data:
                        search_parts.append(field_data['label'])

        # Recurse into children
        for child in elem:
            self._extract_fields_recursive(child, fields, search_parts)

    def _extract_metadata(self, tree: ET.Element) -> Dict[str, Any]:
        """Extract metadata from root element."""
        metadata = {}

        # Instance ID from attribute
        if 'instance-id' in tree.attrib:
            metadata['instance_id'] = tree.attrib['instance-id']

        # Standard metadata elements
        metadata_fields = [
            'dm-label',
            'dm-language',
            'dm-encoding',
            'creation_timestamp',
            'instance_version',
            'current-state'
        ]

        for field in metadata_fields:
            elem = tree.find(f'.//{field}')
            if elem is not None and elem.text:
                # Convert hyphens to underscores for JSON keys
                key = field.replace('-', '_')
                metadata[key] = elem.text

        return metadata

    # All possible value element names in SDC4 XML
    VALUE_ELEMENT_NAMES = [
        'xdstring-value',
        'xdboolean-value',
        'xdcount-value',
        'xdquantity-value',
        'xdfloat-value',
        'xddouble-value',
        'xdlink-value',
        'xdfile-value',
        'xdordinal-value',
        # XdTemporal variants
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

    def _extract_field(self, elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Extract field data from ms-* element.

        Args:
            elem: ms-* element

        Returns:
            Dict with field data or None if empty
        """
        field_data = {}

        # Label (always present)
        label_elem = elem.find('.//label')
        if label_elem is not None and label_elem.text:
            field_data['label'] = label_elem.text

        # Check for Exceptional Value substitution group elements
        for child in elem:
            child_tag = self._strip_namespace(child.tag)
            if child_tag in self.EV_TAG_NAMES:
                # EV element found — extract the ev-name child text or use the tag
                ev_name_elem = child.find('ev-name')
                field_data['exceptional_value'] = (
                    ev_name_elem.text if ev_name_elem is not None and ev_name_elem.text
                    else child_tag
                )
                return field_data  # EV means no value/metadata

        # Value - try all possible value element names
        value_text = None
        for value_elem_name in self.VALUE_ELEMENT_NAMES:
            value_elem = elem.find(f'.//{value_elem_name}')
            if value_elem is not None and value_elem.text:
                value_text = value_elem.text
                break

        if value_text:
            field_data['value'] = self._parse_value(value_text)

        # Units (for quantified types)
        units_elem = elem.find('.//units')
        if units_elem is not None and units_elem.text:
            field_data['units'] = units_elem.text

        # Valid Time Begin
        vtb_elem = elem.find('.//valid-time-begin')
        if vtb_elem is not None and vtb_elem.text:
            field_data['valid_time_begin'] = vtb_elem.text

        # Valid Time End
        vte_elem = elem.find('.//valid-time-end')
        if vte_elem is not None and vte_elem.text:
            field_data['valid_time_end'] = vte_elem.text

        # Location
        location_elem = elem.find('.//location')
        if location_elem is not None:
            lat_elem = location_elem.find('.//latitude')
            lon_elem = location_elem.find('.//longitude')
            if lat_elem is not None and lon_elem is not None:
                field_data['location'] = {
                    'latitude': float(lat_elem.text),
                    'longitude': float(lon_elem.text)
                }

        return field_data if field_data else None

    def _parse_value(self, value_str: str) -> Any:
        """
        Parse value string to appropriate type.

        Args:
            value_str: String value from XML

        Returns:
            Parsed value (int, float, bool, or str)
        """
        # Try boolean
        if value_str.lower() in ['true', 'false']:
            return value_str.lower() == 'true'

        # Try integer
        try:
            if '.' not in value_str:
                return int(value_str)
        except ValueError:
            pass

        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass

        # Return as string
        return value_str

    def _strip_namespace(self, tag: str) -> str:
        """Remove namespace from tag name."""
        if '}' in tag:
            return tag.split('}')[1]
        return tag
