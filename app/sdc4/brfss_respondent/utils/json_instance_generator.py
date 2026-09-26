"""
JSON Instance Generator for SDC4 Data Models.

This module generates clean JSON instances from SDC4 XML,
providing a simplified JSON representation of the data values.
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


class SDC4JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for SDC4 data types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class JSONInstanceGenerator:
    """
    Generates clean JSON instances from SDC4 XML.

    The output JSON contains:
    - Instance metadata (instance_id, dm_label, timestamps)
    - Field values in a clean {field_name: value} format
    - Units for quantified types
    - Exceptional values where present

    This is different from JSONExtractor which is optimized for
    PostgreSQL JSONB queries.
    """

    # SDC4 namespace
    SDC4_NS = 'https://semanticdatacharter.com/ns/sdc4/'

    # Placeholder prefix to filter out
    PLACEHOLDER_PREFIX = '__PLACEHOLDER__'

    # XdType value element names
    VALUE_ELEMENTS = {
        'xdstring-value': 'string',
        'xdboolean-value': 'boolean',
        'xdcount-value': 'integer',
        'xdquantity-value': 'decimal',
        'xdfloat-value': 'float',
        'xddouble-value': 'double',
        'xdlink-value': 'uri',
        'xdfile-value': 'base64',
        'xdordinal-value': 'integer',
        # XdTemporal uses variant element names:
        # xdtemporal-date, xdtemporal-time, xdtemporal-datetime,
        # xdtemporal-duration, xdtemporal-day, xdtemporal-month,
        # xdtemporal-year, xdtemporal-year-month, xdtemporal-month-day
    }

    # Exceptional Value codes
    EV_CODES = [
        'NI', 'MSK', 'INV', 'DER', 'UNC', 'OTH', 'NINF', 'PINF',
        'ASKR', 'NASK', 'NAV', 'NA', 'TRC', 'ASKU', 'UNK', 'QS'
    ]

    def __init__(self, field_metadata: Optional[Dict] = None):
        """
        Initialize JSONInstanceGenerator.

        Args:
            field_metadata: FIELD_METADATA from model for field info
                           Structure: {ct_id: {label, type, ...}, ...}
        """
        self.field_metadata = field_metadata or {}
        # In FIELD_METADATA, ct_id IS the key
        # Build ct_id to field info mapping with label as field_name
        self._ct_id_to_meta = {}
        for ct_id, meta in self.field_metadata.items():
            self._ct_id_to_meta[ct_id] = {
                'field_name': meta.get('label', ct_id),
                'ct_id': ct_id,
                **meta
            }

    def generate(self, xml_content: str) -> Dict[str, Any]:
        """
        Generate clean JSON instance from SDC4 XML content.

        Args:
            xml_content: SDC4-compliant XML string

        Returns:
            Dict with clean JSON structure
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            return {}

        # Build the JSON structure
        json_instance = {
            'metadata': self._extract_metadata(root),
            'fields': self._extract_fields(root)
        }

        return json_instance

    def generate_json_string(self, xml_content: str, indent: int = 2) -> str:
        """
        Generate formatted JSON string from XML.

        Args:
            xml_content: SDC4-compliant XML string
            indent: JSON indentation level

        Returns:
            Formatted JSON string
        """
        json_instance = self.generate(xml_content)
        return json.dumps(json_instance, cls=SDC4JSONEncoder, indent=indent)

    def _extract_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Extract instance metadata from root element."""
        metadata = {}

        # Root element - extract DM CT_ID
        tag_name = self._strip_namespace(root.tag)
        if tag_name.startswith('dm-'):
            metadata['dm_ct_id'] = tag_name.replace('dm-', '')

        # Standard metadata elements
        metadata_elements = {
            'dm-label': 'dm_label',
            'creation_timestamp': 'created_at',
            'instance_id': 'instance_id',
        }

        for elem in root:
            tag = self._strip_namespace(elem.tag)
            if tag in metadata_elements and elem.text:
                key = metadata_elements[tag]
                metadata[key] = elem.text

        return metadata

    def _extract_fields(self, root: ET.Element) -> Dict[str, Any]:
        """
        Extract field values from XML.

        Returns a clean dictionary of {field_name: field_data}
        where field_data contains value, units (if applicable), and ev (if applicable).
        """
        fields = {}

        # Find all ms-* elements that correspond to data fields
        for elem in root.iter():
            tag = self._strip_namespace(elem.tag)

            # Only process ms-* elements
            if not tag.startswith('ms-'):
                continue

            ct_id = tag.replace('ms-', '')

            # Check if this is a known data field
            meta = self._ct_id_to_meta.get(ct_id)
            if not meta:
                continue

            field_name = meta['field_name']
            field_type = meta.get('type', 'XdString')

            # Extract the field data
            field_data = self._extract_field_data(elem, field_type)

            if field_data:
                fields[field_name] = field_data

        return fields

    def _extract_field_data(self, elem: ET.Element, field_type: str) -> Optional[Dict[str, Any]]:
        """
        Extract data for a single field.

        Args:
            elem: The ms-* XML element
            field_type: The XdType (XdString, XdCount, etc.)

        Returns:
            Dict with value, units, ev as applicable, or None if empty
        """
        field_data = {}

        # Check for exceptional value first
        ev_data = self._extract_ev(elem)
        if ev_data:
            field_data['ev'] = ev_data

        # Extract value
        value = self._extract_value(elem, field_type)
        if value is not None:
            field_data['value'] = value

        # Extract units for quantified types
        units = self._extract_units_value(elem, field_type)
        if units:
            field_data['units'] = units

        # Only return if we have meaningful data
        if field_data:
            return field_data

        return None

    def _extract_ev(self, elem: ET.Element) -> Optional[str]:
        """Extract exceptional value code from element."""
        for child in elem:
            tag = self._strip_namespace(child.tag)
            if tag in self.EV_CODES:
                return tag
        return None

    def _extract_value(self, elem: ET.Element, field_type: str) -> Any:
        """Extract and parse the value from element."""
        # Map field type to value element name
        type_to_elem = {
            'XdString': 'xdstring-value',
            'XdBoolean': 'xdboolean-value',
            'XdCount': 'xdcount-value',
            'XdQuantity': 'xdquantity-value',
            'XdFloat': 'xdfloat-value',
            'XdDouble': 'xddouble-value',
            'XdLink': 'xdlink-value',
            'XdFile': 'xdfile-value',
            'XdOrdinal': 'xdordinal-value',
        }

        # XdTemporal uses variant element names based on temporal subtype
        if field_type == 'XdTemporal':
            temporal_elem_names = [
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
            # Try each possible temporal element name
            for temporal_elem_name in temporal_elem_names:
                value_elem = elem.find(f'.//{temporal_elem_name}')
                if value_elem is not None and value_elem.text:
                    text = value_elem.text
                    if not text.startswith(self.PLACEHOLDER_PREFIX):
                        return text
            return None

        value_elem_name = type_to_elem.get(field_type, 'value')
        value_elem = elem.find(f'.//{value_elem_name}')

        if value_elem is None or not value_elem.text:
            return None

        text = value_elem.text

        # Skip placeholders
        if text.startswith(self.PLACEHOLDER_PREFIX):
            return None

        # Parse based on type
        return self._parse_value(text, field_type)

    def _extract_units_value(self, elem: ET.Element, field_type: str) -> Optional[str]:
        """Extract units value for quantified types."""
        # Only quantified types have units
        if field_type not in ('XdCount', 'XdQuantity', 'XdFloat', 'XdDouble', 'XdOrdinal'):
            return None

        # Find the units element
        units_elem_names = {
            'XdCount': 'xdcount-units',
            'XdQuantity': 'xdquantity-units',
            'XdFloat': 'xdfloat-units',
            'XdDouble': 'xddouble-units',
            'XdOrdinal': 'xdordinal-units',
        }

        units_elem_name = units_elem_names.get(field_type)
        if not units_elem_name:
            return None

        units_elem = elem.find(f'.//{units_elem_name}')
        if units_elem is None:
            return None

        # Get the xdstring-value inside units
        value_elem = units_elem.find('.//xdstring-value')
        if value_elem is None or not value_elem.text:
            return None

        text = value_elem.text

        # Skip placeholders
        if text.startswith(self.PLACEHOLDER_PREFIX):
            return None

        return text

    def _parse_value(self, value_str: str, field_type: str) -> Any:
        """
        Parse value string to appropriate Python type.

        Args:
            value_str: String value from XML
            field_type: XdType name

        Returns:
            Parsed value (bool, int, float, or str)
        """
        if field_type == 'XdBoolean':
            return value_str.lower() == 'true'

        if field_type in ('XdCount', 'XdOrdinal'):
            try:
                return int(value_str)
            except ValueError:
                return value_str

        if field_type in ('XdQuantity', 'XdFloat', 'XdDouble'):
            try:
                return float(value_str)
            except ValueError:
                return value_str

        # XdString, XdTemporal, XdLink, XdFile - return as string
        return value_str

    def _strip_namespace(self, tag: str) -> str:
        """Remove namespace from tag name."""
        if '}' in tag:
            return tag.split('}')[1]
        return tag
