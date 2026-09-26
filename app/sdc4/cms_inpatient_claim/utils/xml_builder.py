
"""
XML Builder for SDC4 Data Models using Skeleton-Based Approach.

This builder loads a pre-generated XML skeleton template and populates it
with form data at runtime, then prunes unused optional elements.

The skeleton approach ensures:
1. XSD sequence ordering is always correct (elements generated in schema order)
2. Proper handling of complex nested structures
3. Correct element naming based on the actual XSD schema
"""

from lxml import etree
import logging
import json
import os
import re
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from cuid2 import cuid_wrapper
from typing import Dict, Any, Optional, List, Set
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize CUID2 generator once at module level
cuid_generator = cuid_wrapper()


class XMLBuilder:
    """
    Builds SDC XML from form data using skeleton-based approach.

    The skeleton XML is pre-generated at app generation time from the XSD schema.
    At runtime, this class:
    1. Loads the skeleton template
    2. Replaces placeholders with actual form values
    3. Prunes unused optional elements
    4. Generates the final XML instance
    """

    NSMAP = {
        'sdc4': 'https://semanticdatacharter.com/ns/sdc4/',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xs': 'http://www.w3.org/2001/XMLSchema'
    }

    SDC4_NS = 'https://semanticdatacharter.com/ns/sdc4/'
    PLACEHOLDER_PREFIX = '_PH_'
    OPT_PLACEHOLDER_PREFIX = '_OPT_PH_'

    # Exceptional Value codes and their fixed ev-name values
    # These are the substitution group elements from sdc4.xsd
    EV_CODES = {
        'NI': 'No Information',
        'MSK': 'Masked',
        'INV': 'Invalid',
        'DER': 'Derived',
        'UNC': 'Unencoded',
        'OTH': 'Other',
        'NINF': 'Negative Infinity',
        'PINF': 'Positive Infinity',
        'ASKR': 'Asked and Refused',
        'NASK': 'Not Asked',
        'NAV': 'Not Available',
        'NA': 'Not Applicable',
        'TRC': 'Trace',
        'ASKU': 'Asked but Unknown',
        'UNK': 'Unknown',
        'QS': 'Sufficient Quantity',
    }

    # Elements that should be pruned if their placeholder is not replaced
    # (i.e., optional elements with no data)
    OPTIONAL_ELEMENTS = {
        'act', 'vtb', 'vte', 'tr', 'modified', 'latitude', 'longitude',
        'normal-status', 'magnitude-status', 'accuracy_margin', 'precision_digits',
        'xdstring-language'
    }

    # Container elements that should be removed if they're empty or only have comments/placeholders
    # Note: These are only DM-level optional containers, NOT component-level elements like units
    OPTIONAL_CONTAINER_ELEMENTS = {
        'subject', 'provider', 'protocol', 'workflow', 'acs'
    }

    # Units elements that should NOT be pruned even if they have placeholders
    # (they'll be handled by placeholder pruning, not container pruning)
    UNITS_ELEMENTS = {
        'xdcount-units', 'xdquantity-units', 'xdfloat-units', 'xddouble-units', 'xdordinal-units'
    }

    # Elements that are required and should have defaults if placeholder remains
    REQUIRED_ELEMENTS_DEFAULTS = {
        'creation_timestamp': lambda: timezone.now().isoformat(),
        'instance_id': lambda: f'i-{cuid_generator()}',
        'instance_version': lambda: '1.0',
        'source_instance_id': lambda: '',
        'source_version_id': lambda: '',
        'current-state': lambda: '',
    }

    def __init__(self, dm_ct_id: Optional[str] = None, cluster_ct_id: Optional[str] = None,
                 field_metadata: Optional[Dict] = None, dm_label: Optional[str] = None):
        """
        Initialize XMLBuilder.

        Args:
            dm_ct_id: Data Model CT_ID (for root element name)
            cluster_ct_id: Root Cluster CT_ID (for cluster element wrapper)
            field_metadata: Field metadata dictionary with ct_id, adapter_ctid, type, label
            dm_label: Data Model label
        """
        self.dm_ct_id = dm_ct_id
        self.cluster_ct_id = cluster_ct_id
        self.field_metadata = field_metadata or {}
        self.dm_label = dm_label

        # Load skeleton and field mapping at initialization
        self._skeleton_xml = None
        self._field_mapping = None
        self._load_skeleton_files()

    def _load_skeleton_files(self):
        """Load the skeleton XML template and field mapping from files."""
        try:
            # Determine the utils directory path
            current_dir = Path(__file__).parent

            skeleton_path = current_dir / 'xml_skeleton.xml'
            mapping_path = current_dir / 'field_mapping.json'

            if skeleton_path.exists():
                with open(skeleton_path, 'r', encoding='utf-8') as f:
                    self._skeleton_xml = f.read()
                logger.debug(f"Loaded XML skeleton template ({len(self._skeleton_xml)} chars)")
            else:
                logger.warning(f"XML skeleton template not found at {skeleton_path}")

            if mapping_path.exists():
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    self._field_mapping = json.load(f)
                logger.debug(f"Loaded field mapping ({len(self._field_mapping)} fields)")
            else:
                logger.warning(f"Field mapping not found at {mapping_path}")

        except Exception as e:
            logger.error(f"Error loading skeleton files: {e}")

    def build_from_form(self, instance_id: str, form_data: Dict[str, Any],
                        metadata: Optional[Dict[str, Dict]] = None) -> str:
        """
        Build XML from form data using the skeleton template.

        Args:
            instance_id: The instance ID (e.g., i-{cuid2} or i-ev-{cuid2})
            form_data: Dictionary of form field values
            metadata: Optional dict of field_name -> metadata dict
                     (from form.field_metadata after clean())

        Returns:
            str: The generated XML string
        """
        if not self._skeleton_xml:
            # Fallback to programmatic generation if skeleton not available
            logger.warning("Skeleton not available, falling back to programmatic generation")
            return self._build_from_form_fallback(instance_id, form_data, metadata)

        try:
            # Start with the skeleton XML
            xml_content = self._skeleton_xml

            # Replace standard metadata placeholders
            xml_content = self._replace_metadata_placeholders(xml_content, instance_id)

            # Replace field value placeholders
            xml_content = self._replace_field_placeholders(xml_content, form_data, metadata or {})

            # Process Exceptional Values and prune unused optional elements
            # This must be done with lxml to properly handle EV element insertion
            xml_content = self._process_ev_and_prune(xml_content, form_data, metadata or {})

            return xml_content

        except Exception as e:
            logger.error(f"Error building XML from form: {e}")
            raise

    def _replace_metadata_placeholders(self, xml_content: str, instance_id: str) -> str:
        """Replace DM-level metadata placeholders with actual values.

        Uses lxml tree traversal to find elements whose text is _PH_ or _OPT_PH_
        and fills in known metadata values by element tag name.
        """
        try:
            parser = etree.XMLParser(remove_blank_text=False)
            root = etree.fromstring(xml_content.encode('utf-8'), parser)

            # Map tag names to values for DM-level metadata
            meta_values = {
                'creation_timestamp': timezone.now().isoformat(),
                'instance_id': instance_id,
                'instance_version': '1.0',
                'current-state': '',
            }

            for elem in root.iter():
                if callable(elem.tag):
                    continue
                tag = etree.QName(elem.tag).localname if '}' in elem.tag else elem.tag
                if tag in meta_values and elem.text in (self.PLACEHOLDER_PREFIX, self.OPT_PLACEHOLDER_PREFIX):
                    elem.text = meta_values[tag]

            xml_bytes = etree.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)
            return xml_bytes.decode('utf-8')

        except etree.XMLSyntaxError:
            # Fallback: simple string replacement
            return xml_content

    def _replace_field_placeholders(self, xml_content: str, form_data: Dict[str, Any],
                                     metadata_dict: Dict[str, Dict]) -> str:
        """
        Replace field value placeholders with actual form data using lxml tree traversal.

        Published XML uses simple _PH_ and _OPT_PH_ text markers inside elements.
        We use field_mapping.json to locate each component's subtree by ct_id, then
        walk the subtree to find elements with placeholder text and replace them
        based on the element tag name.
        """
        try:
            parser = etree.XMLParser(remove_blank_text=False)
            root = etree.fromstring(xml_content.encode('utf-8'), parser)
        except etree.XMLSyntaxError:
            logger.warning("XML parsing failed in _replace_field_placeholders, returning as-is")
            return xml_content

        nsmap = {'sdc4': self.SDC4_NS}

        for field_name, meta in self.field_metadata.items():
            # field_name IS the ct_id in FIELD_METADATA structure
            ct_id = field_name
            field_type = meta.get('type', '')
            field_label = meta.get('label', field_name)
            field_meta = metadata_dict.get(field_name, {})

            # Find the component's ms-{ct_id} subtree
            comp_elem = root.find(f".//sdc4:ms-{ct_id}", namespaces=nsmap)
            if comp_elem is None:
                continue

            value = form_data.get(field_name)

            # Get the expected value element name for this type
            value_elem_name = self._get_value_element_name(field_type, meta)

            # Walk the subtree and replace _PH_/_OPT_PH_ markers
            for elem in comp_elem.iter():
                if callable(elem.tag):
                    continue
                if elem.text not in (self.PLACEHOLDER_PREFIX, self.OPT_PLACEHOLDER_PREFIX):
                    continue

                tag = etree.QName(elem.tag).localname if '}' in elem.tag else elem.tag

                # Value element — replace with form data
                if tag == value_elem_name and value is not None and value != '':
                    if field_type == 'XdBoolean':
                        elem.text = 'true' if value else 'false'
                    elif field_type == 'XdTemporal':
                        temporal_types = meta.get('temporal_types', ['date'])
                        temporal_type = temporal_types[0] if temporal_types else 'date'
                        elem.text = self._format_temporal_value(value, temporal_type)
                    else:
                        elem.text = str(value)

                # Optional metadata elements
                elif tag == 'act' and field_meta.get('act'):
                    elem.text = str(field_meta['act'])
                elif tag == 'vtb' and field_meta.get('vtb'):
                    elem.text = str(field_meta['vtb'])
                elif tag == 'vte' and field_meta.get('vte'):
                    elem.text = str(field_meta['vte'])
                elif tag == 'tr' and field_meta.get('tr'):
                    elem.text = str(field_meta['tr'])
                elif tag == 'modified' and field_meta.get('mod'):
                    elem.text = str(field_meta['mod'])
                elif tag == 'latitude':
                    location = field_meta.get('location', {})
                    if location.get('lat') is not None:
                        elem.text = str(location['lat'])
                elif tag == 'longitude':
                    location = field_meta.get('location', {})
                    if location.get('lon') is not None:
                        elem.text = str(location['lon'])

            # Handle units placeholder — find the units ms-{units_ct_id} subtree
            units_info = meta.get('units', {})
            if units_info:
                units_ct_id = units_info.get('ct_id', '')
                if units_ct_id:
                    units_elem = root.find(f".//sdc4:ms-{units_ct_id}", namespaces=nsmap)
                    if units_elem is not None:
                        selected_units = field_meta.get('units')
                        for elem in units_elem.iter():
                            if callable(elem.tag):
                                continue
                            if elem.text not in (self.PLACEHOLDER_PREFIX, self.OPT_PLACEHOLDER_PREFIX):
                                continue
                            tag = etree.QName(elem.tag).localname if '}' in elem.tag else elem.tag
                            if tag == 'xdstring-value' and selected_units:
                                elem.text = str(selected_units)
                            elif tag == 'label':
                                elem.text = units_info.get('label', f'{field_label}_units')

        xml_bytes = etree.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)
        return xml_bytes.decode('utf-8')

    def _process_ev_and_prune(self, xml_content: str, form_data: Dict[str, Any],
                               metadata_dict: Dict[str, Dict]) -> str:
        """
        Process Exceptional Values and prune unused elements using lxml.

        This method:
        1. Finds ev-placeholder elements and either replaces them with EV elements or removes them
        2. When EV is present, removes the value element (xdstring-value, xdcount-value, etc.)
        3. Prunes other unused optional elements with placeholders
        """
        try:
            # Parse the XML
            parser = etree.XMLParser(remove_blank_text=False)
            root = etree.fromstring(xml_content.encode('utf-8'), parser)

            # Build a map of ct_id -> ev_code from metadata
            # In FIELD_METADATA, the outer key IS the ct_id
            ev_map = {}  # ct_id -> ev_code
            for field_name, meta in self.field_metadata.items():
                field_meta = metadata_dict.get(field_name, {})
                ev_code = field_meta.get('ev')
                if ev_code and ev_code in self.EV_CODES:
                    ev_map[field_name] = ev_code

            # Process ev-placeholder elements
            self._process_ev_placeholders(root, ev_map)

            # Prune elements with unreplaced placeholders
            elements_to_remove = []
            self._find_placeholder_elements(root, elements_to_remove)
            for elem in elements_to_remove:
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

            # Remove empty optional container elements (subject, provider, protocol, etc.)
            self._prune_empty_containers(root)

            # Remove any remaining XML comments (like <!-- Optional: ... -->)
            self._remove_comments(root)

            # Serialize back to string
            xml_bytes = etree.tostring(
                root,
                pretty_print=True,
                encoding='UTF-8',
                xml_declaration=True
            )
            return xml_bytes.decode('utf-8')

        except etree.XMLSyntaxError as e:
            logger.warning(f"XML parsing failed: {e}")
            # Fallback to simpler pruning
            return self._prune_unused_elements(xml_content)

    def _process_ev_placeholders(self, root, ev_map: Dict[str, str]):
        """
        Process ev-placeholder elements in the XML tree.

        For each ev-placeholder:
        - If ct_id has an EV selected: Replace with proper EV element and remove value element
        - If no EV: Remove the placeholder element
        """
        # Find all ev-placeholder elements
        ev_placeholders = root.findall('.//ev-placeholder')

        for placeholder in ev_placeholders:
            ct_id = placeholder.get('ct_id')
            parent = placeholder.getparent()

            if parent is None:
                continue

            if ct_id and ct_id in ev_map:
                # User selected an EV - replace placeholder with EV element
                ev_code = ev_map[ct_id]
                ev_name = self.EV_CODES.get(ev_code, ev_code)

                # Create the EV element: <sdc4:NASK><ev-name>Not Asked</ev-name></sdc4:NASK>
                ev_element = etree.Element(f"{{{self.SDC4_NS}}}{ev_code}")
                ev_name_child = etree.SubElement(ev_element, 'ev-name')
                ev_name_child.text = ev_name

                # Find the index of the placeholder in parent
                idx = list(parent).index(placeholder)

                # Remove the placeholder
                parent.remove(placeholder)

                # Insert the EV element at the same position
                parent.insert(idx, ev_element)

                # Note: We keep the value element even when EV is present.
                # EVs indicate the status of the value (e.g., DER=Derived, INV=Invalid),
                # not necessarily that the value is absent. We capture all data.

            else:
                # No EV selected - just remove the placeholder
                parent.remove(placeholder)

    def _prune_empty_containers(self, root):
        """
        Remove optional container elements that are empty or only contain comments/whitespace.

        Elements like subject, provider, protocol, workflow, acs should be removed
        if they have no meaningful content.
        """
        for container_name in self.OPTIONAL_CONTAINER_ELEMENTS:
            # Find all elements with this name (could be multiple providers, etc.)
            containers = root.findall(f'.//{container_name}')
            for container in containers:
                if self._is_empty_container(container):
                    parent = container.getparent()
                    if parent is not None:
                        parent.remove(container)
                        logger.debug(f"Removed empty container element: {container_name}")

    def _is_empty_container(self, element) -> bool:
        """
        Check if a container element is effectively empty.

        A container is considered empty if:
        - It has no child elements, OR
        - All child elements only contain comments, placeholders, or whitespace
        """
        # Check if there are any child elements
        children = list(element)
        if not children:
            # No children - check if there's only whitespace/comment text
            text = (element.text or '').strip()
            if not text or text.startswith('<!--'):
                return True
            return False

        # Has children - check if all children are empty or just comments
        for child in children:
            # Skip comments and processing instructions (their .tag is a callable, not a string)
            if callable(child.tag):
                continue
            tag_name = etree.QName(child.tag).localname if '}' in child.tag else child.tag

            # If child has meaningful content, container is not empty
            child_text = (child.text or '').strip()
            if child_text and child_text not in (self.PLACEHOLDER_PREFIX, self.OPT_PLACEHOLDER_PREFIX) and not child_text.startswith('<!--'):
                return False

            # Check if child has non-empty descendants
            if not self._is_empty_container(child):
                return False

        return True

    def _remove_comments(self, root):
        """Remove all XML comments from the tree."""
        # Find and remove all comment nodes
        comments = root.xpath('//comment()')
        for comment in comments:
            parent = comment.getparent()
            if parent is not None:
                parent.remove(comment)

    def _prune_unused_elements(self, xml_content: str) -> str:
        """
        Remove elements that still have unreplaced placeholders.

        This handles optional elements that weren't provided with data.
        """
        try:
            # Parse the XML
            parser = etree.XMLParser(remove_blank_text=False)
            root = etree.fromstring(xml_content.encode('utf-8'), parser)

            # Find all elements with placeholder text
            elements_to_remove = []
            self._find_placeholder_elements(root, elements_to_remove)

            # Remove the elements
            for elem in elements_to_remove:
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

            # Serialize back to string
            xml_bytes = etree.tostring(
                root,
                pretty_print=True,
                encoding='UTF-8',
                xml_declaration=True
            )
            return xml_bytes.decode('utf-8')

        except etree.XMLSyntaxError as e:
            # If parsing fails, do string-based cleanup
            logger.warning(f"XML parsing failed, doing string-based cleanup: {e}")
            return self._string_based_prune(xml_content)

    def _find_placeholder_elements(self, element, to_remove: List):
        """Recursively find elements with unreplaced _PH_/_OPT_PH_ text."""
        # Skip comments and processing instructions (their .tag is callable, not a string)
        if callable(element.tag):
            return

        # Check if this element's text is a placeholder marker
        if element.text in (self.PLACEHOLDER_PREFIX, self.OPT_PLACEHOLDER_PREFIX):
            tag_name = etree.QName(element.tag).localname if '}' in element.tag else element.tag

            if tag_name in self.REQUIRED_ELEMENTS_DEFAULTS:
                # Replace with default value
                element.text = self.REQUIRED_ELEMENTS_DEFAULTS[tag_name]()
            elif tag_name in self.OPTIONAL_ELEMENTS:
                # Mark for removal only if it's explicitly in the optional elements list
                to_remove.append(element)
                return  # Don't recurse into elements we're removing

        # Check children
        for child in element:
            self._find_placeholder_elements(child, to_remove)

    def _string_based_prune(self, xml_content: str) -> str:
        """Fallback string-based pruning of placeholder elements."""
        lines = xml_content.split('\n')
        filtered_lines = []

        for line in lines:
            # Skip lines with unreplaced _PH_/_OPT_PH_ in optional elements
            skip = False
            if self.PLACEHOLDER_PREFIX in line or self.OPT_PLACEHOLDER_PREFIX in line:
                for optional_elem in self.OPTIONAL_ELEMENTS:
                    if f'<{optional_elem}>' in line and f'</{optional_elem}>' in line:
                        skip = True
                        break
            if not skip:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def _get_value_element_name(self, field_type: str, field_meta: Dict = None) -> str:
        """
        Get the value element name for a given field type.

        For XdTemporal, the element name depends on which temporal types are allowed.
        The element name is xdtemporal-{subtype} where subtype is one of:
        date, time, datetime, duration, day, month, year, year-month, month-day

        Args:
            field_type: The SDC4 type (XdString, XdTemporal, etc.)
            field_meta: Optional field metadata dict containing temporal_types for XdTemporal
        """
        type_map = {
            'XdString': 'xdstring-value',
            'XdBoolean': 'xdboolean-value',
            'XdCount': 'xdcount-value',
            'XdQuantity': 'xdquantity-value',
            'XdFloat': 'xdfloat-value',
            'XdDouble': 'xddouble-value',
            'XdLink': 'xdlink-value',
            'XdFile': 'xdfile-value',
            'XdOrdinal': 'xdordinal-value',
            'XdInterval': 'xdinterval-value',
            'XdToken': 'xdtoken-value',
        }

        # Special handling for XdTemporal - element name depends on allowed types
        if field_type == 'XdTemporal':
            if field_meta and field_meta.get('temporal_types'):
                temporal_types = field_meta['temporal_types']
                # Use the first allowed type to determine element name
                # The skeleton generator will have created element with this name
                if temporal_types:
                    # Map internal names to XML element suffixes
                    temporal_element_map = {
                        'date': 'xdtemporal-date',
                        'time': 'xdtemporal-time',
                        'datetime': 'xdtemporal-datetime',
                        'duration': 'xdtemporal-duration',
                        'day': 'xdtemporal-day',
                        'month': 'xdtemporal-month',
                        'year': 'xdtemporal-year',
                        'year_month': 'xdtemporal-year-month',
                        'month_day': 'xdtemporal-month-day',
                    }
                    first_type = temporal_types[0]
                    return temporal_element_map.get(first_type, 'xdtemporal-date')
            # Fallback if no temporal_types specified
            return 'xdtemporal-date'

        return type_map.get(field_type, 'value')

    def _escape_xml(self, value: str) -> str:
        """Escape special XML characters."""
        return (value
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))

    def _format_temporal_value(self, value: Any, temporal_type: str) -> str:
        """
        Format a temporal value according to its XML Schema type.

        Args:
            value: The temporal value (date, time, datetime, timedelta, or string)
            temporal_type: The temporal type (date, time, datetime, duration, etc.)

        Returns:
            Properly formatted string for XML
        """
        if value is None or value == '':
            return ''

        # Handle different Python types
        if isinstance(value, datetime):
            if temporal_type == 'date':
                return value.strftime('%Y-%m-%d')
            elif temporal_type == 'time':
                return value.strftime('%H:%M:%S')
            elif temporal_type == 'datetime':
                return value.isoformat()
            elif temporal_type == 'year':
                return value.strftime('%Y')
            elif temporal_type == 'month':
                return value.strftime('--%m')
            elif temporal_type == 'day':
                return value.strftime('---%d')
            elif temporal_type == 'year_month':
                return value.strftime('%Y-%m')
            elif temporal_type == 'month_day':
                return value.strftime('--%m-%d')
            else:
                return value.isoformat()

        elif isinstance(value, date):
            if temporal_type == 'date':
                return value.strftime('%Y-%m-%d')
            elif temporal_type == 'year':
                return value.strftime('%Y')
            elif temporal_type == 'month':
                return value.strftime('--%m')
            elif temporal_type == 'day':
                return value.strftime('---%d')
            elif temporal_type == 'year_month':
                return value.strftime('%Y-%m')
            elif temporal_type == 'month_day':
                return value.strftime('--%m-%d')
            else:
                return value.strftime('%Y-%m-%d')

        elif isinstance(value, time):
            return value.strftime('%H:%M:%S')

        elif isinstance(value, timedelta):
            # Format as ISO 8601 duration
            total_seconds = int(value.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f'PT{hours}H{minutes}M{seconds}S'

        else:
            # String value - try to parse and reformat if needed
            str_value = str(value)

            # Check if it looks like a datetime string with time component we should strip
            if temporal_type == 'date':
                # Handle "YYYY-MM-DD HH:MM:SS+TZ" format - extract just the date
                if ' ' in str_value:
                    str_value = str_value.split(' ')[0]
                # Handle "YYYY-MM-DDTHH:MM:SS" format
                if 'T' in str_value:
                    str_value = str_value.split('T')[0]
                return str_value

            elif temporal_type == 'time':
                # Handle datetime string - extract just the time
                if 'T' in str_value:
                    str_value = str_value.split('T')[1]
                if '+' in str_value:
                    str_value = str_value.split('+')[0]
                if ' ' in str_value and len(str_value.split(' ')) > 1:
                    # "YYYY-MM-DD HH:MM:SS" format
                    str_value = str_value.split(' ')[1]
                    if '+' in str_value:
                        str_value = str_value.split('+')[0]
                return str_value

            return str_value

    def _build_from_form_fallback(self, instance_id: str, form_data: Dict[str, Any],
                                   metadata: Optional[Dict[str, Dict]] = None) -> str:
        """
        Fallback XML generation when skeleton is not available.

        This implements basic programmatic XML generation.
        """
        if not self.dm_ct_id:
            raise ValueError("dm_ct_id required for build_from_form")
        if not self.cluster_ct_id:
            raise ValueError("cluster_ct_id required for build_from_form")

        # Build XML programmatically
        root = etree.Element(
            f"{{{self.SDC4_NS}}}dm-{self.dm_ct_id}",
            nsmap=self.NSMAP
        )

        root.set(
            f"{{http://www.w3.org/2001/XMLSchema-instance}}schemaLocation",
            f"{self.SDC4_NS} https://semanticdatacharter.com/dmlib/dm-{self.dm_ct_id}.xsd"
        )

        # Add metadata
        self._add_metadata_elements(root, instance_id)

        # Create cluster wrapper
        cluster_elem = etree.SubElement(root, f"{{{self.SDC4_NS}}}ms-{self.cluster_ct_id}")
        cluster_label = etree.SubElement(cluster_elem, "label")
        cluster_label.text = f"{self.dm_label} Data Cluster"

        # Add form fields
        self._add_form_fields_fallback(cluster_elem, form_data, metadata or {})

        xml_bytes = etree.tostring(
            root,
            pretty_print=True,
            encoding='UTF-8',
            xml_declaration=True
        )
        return xml_bytes.decode('utf-8')

    def _add_metadata_elements(self, root, instance_id: str):
        """Add standard DMType metadata elements."""
        etree.SubElement(root, "dm-label").text = self.dm_label or self.dm_ct_id
        etree.SubElement(root, "dm-language").text = "en-US"
        etree.SubElement(root, "dm-encoding").text = "utf-8"
        etree.SubElement(root, "creation_timestamp").text = timezone.now().isoformat()
        etree.SubElement(root, "instance_id").text = instance_id
        etree.SubElement(root, "instance_version").text = "1.0"
        etree.SubElement(root, "current-state").text = ""

    def _add_form_fields_fallback(self, parent_elem, form_data: Dict[str, Any],
                                   metadata_dict: Dict[str, Dict]):
        """Add form fields to XML in fallback mode."""
        for field_name, meta in self.field_metadata.items():
            # In FIELD_METADATA, the outer key IS the ct_id
            ct_id = field_name
            adapter_ctid = meta.get('adapter_ctid', '')
            field_type = meta.get('type', '')
            field_label = meta.get('label', field_name)

            if field_name not in form_data:
                continue

            value = form_data.get(field_name)
            field_meta = metadata_dict.get(field_name, {})

            # Create adapter wrapper
            if adapter_ctid:
                adapter_elem = etree.SubElement(parent_elem, f"{{{self.SDC4_NS}}}ms-{adapter_ctid}")
            else:
                adapter_elem = parent_elem

            # Create component element
            component_elem = etree.SubElement(adapter_elem, f"{{{self.SDC4_NS}}}ms-{ct_id}")

            # Add label
            etree.SubElement(component_elem, "label").text = field_label

            # Add value
            if value is not None and value != '':
                value_elem_name = self._get_value_element_name(field_type, meta)
                value_elem = etree.SubElement(component_elem, value_elem_name)
                if field_type == 'XdBoolean':
                    value_elem.text = 'true' if value else 'false'
                elif field_type == 'XdTemporal':
                    # Get the temporal type from metadata for proper formatting
                    temporal_types = meta.get('temporal_types', ['date'])
                    temporal_type = temporal_types[0] if temporal_types else 'date'
                    value_elem.text = self._format_temporal_value(value, temporal_type)
                else:
                    value_elem.text = str(value)

            # Add units for quantified types
            if field_type in {'XdCount', 'XdQuantity', 'XdFloat', 'XdDouble', 'XdOrdinal'}:
                units_info = meta.get('units', {})
                if units_info:
                    units_elem_name = f'{field_type.lower()}-units'
                    units_elem = etree.SubElement(component_elem, units_elem_name)
                    etree.SubElement(units_elem, "label").text = units_info.get('label', f"{field_label}_units")
                    # Use def_val or first symbol
                    units_value = units_info.get('def_val', '')
                    if not units_value and units_info.get('symbols'):
                        units_value = units_info['symbols'][0]
                    etree.SubElement(units_elem, "xdstring-value").text = str(units_value)

    def build_from_wizard(self, instance_id: str, wizard_data: Dict[str, Any]) -> str:
        """
        Build XML from wizard step data.

        This method consolidates data from all wizard steps and generates
        the final XML instance.

        Args:
            instance_id: The instance ID (e.g., i-{cuid2})
            wizard_data: Dictionary containing data from all wizard steps:
                {
                    'instance_id': str,
                    'setup': dict,      # Step 0 data
                    'context': dict,    # Step 1 data (optional)
                    'data': dict,       # Step 2 data (main data entry)
                    'review': dict,     # Step 3 data (optional)
                }

        Returns:
            str: The generated XML string
        """
        # Extract setup data
        setup_data = wizard_data.get('setup', {})
        context_data = wizard_data.get('context', {})
        data_entry_data = wizard_data.get('data', {})
        review_data = wizard_data.get('review', {})

        # Build form_data dict combining all relevant data
        form_data = {}
        metadata = {}

        # Add data entry fields (Step 2)
        form_data.update(data_entry_data)

        # Add setup fields (Step 0) - these go into metadata/instance elements
        instance_version = setup_data.get('instance_version', '1')
        current_state = setup_data.get('current_state', 'draft')

        # Build the XML using skeleton approach
        if not self._skeleton_xml:
            logger.warning("Skeleton not available, falling back to programmatic generation")
            return self._build_from_wizard_fallback(instance_id, wizard_data)

        try:
            # Start with the skeleton XML
            xml_content = self._skeleton_xml

            # Replace standard metadata placeholders
            xml_content = self._replace_metadata_placeholders(xml_content, instance_id)

            # Replace instance version and current state
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}instance_version',
                str(instance_version)
            )
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}current-state',
                str(current_state)
            )

            # Handle context data (Step 1) - Subject, Provider, Participations
            xml_content = self._replace_context_placeholders(xml_content, context_data)

            # Handle audit/attestation data (Step 3)
            xml_content = self._replace_review_placeholders(xml_content, review_data)

            # Replace field value placeholders from data entry
            xml_content = self._replace_field_placeholders(xml_content, form_data, metadata)

            # Process Exceptional Values and prune unused optional elements
            xml_content = self._process_ev_and_prune(xml_content, form_data, metadata)

            return xml_content

        except Exception as e:
            logger.error(f"Error building XML from wizard: {e}")
            raise

    def _replace_context_placeholders(self, xml_content: str, context_data: Dict[str, Any]) -> str:
        """
        Replace context-related placeholders (subject, provider, participations).

        Context data maps to SDC4 DMType elements:
        - subject -> PartyType element
        - provider -> PartyType element
        - participations -> Participation elements (list)
        """
        # =======================================================================
        # Subject Party
        # =======================================================================
        if context_data.get('subject_name'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}subject_name',
                self._escape_xml(context_data['subject_name'])
            )
        if context_data.get('subject_type'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}subject_type',
                self._escape_xml(context_data['subject_type'])
            )
        if context_data.get('subject_id'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}subject_id',
                self._escape_xml(context_data['subject_id'])
            )
        if context_data.get('subject_id_scheme'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}subject_id_scheme',
                self._escape_xml(context_data['subject_id_scheme'])
            )
        if context_data.get('subject_external_ref'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}subject_external_ref',
                self._escape_xml(context_data['subject_external_ref'])
            )

        # =======================================================================
        # Provider Party
        # =======================================================================
        if context_data.get('provider_name'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}provider_name',
                self._escape_xml(context_data['provider_name'])
            )
        if context_data.get('provider_type'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}provider_type',
                self._escape_xml(context_data['provider_type'])
            )
        if context_data.get('provider_id'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}provider_id',
                self._escape_xml(context_data['provider_id'])
            )
        if context_data.get('provider_id_scheme'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}provider_id_scheme',
                self._escape_xml(context_data['provider_id_scheme'])
            )
        if context_data.get('provider_external_ref'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}provider_external_ref',
                self._escape_xml(context_data['provider_external_ref'])
            )

        # =======================================================================
        # Participations (dynamic list)
        # =======================================================================
        # Participations are handled dynamically since they're a repeating structure
        # The form sends them as participation_0_name, participation_0_function, etc.
        participations = self._extract_participations(context_data)
        if participations:
            xml_content = self._insert_participations(xml_content, participations)

        return xml_content

    def _extract_participations(self, context_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract participation data from form submission.

        Form data comes as:
        - participation_0_name, participation_0_function, participation_0_mode, etc.
        - participation_1_name, participation_1_function, participation_1_mode, etc.
        """
        participations = []
        idx = 0

        while True:
            prefix = f'participation_{idx}_'
            name = context_data.get(f'{prefix}name')

            if not name:
                # Check for alternate naming convention
                alt_prefix = f'participation_{idx}'
                name = context_data.get(f'{alt_prefix}_name')
                if not name:
                    break

            participation = {
                'name': name,
                'function': context_data.get(f'{prefix}function', context_data.get(f'{prefix}role', '')),
                'mode': context_data.get(f'{prefix}mode', 'face-to-face'),
                'time': context_data.get(f'{prefix}time', ''),
                'id': context_data.get(f'{prefix}id', ''),
            }
            participations.append(participation)
            idx += 1

        return participations

    def _insert_participations(self, xml_content: str, participations: List[Dict[str, Any]]) -> str:
        """
        Insert participation elements into the XML.

        Participations in SDC4 follow the structure:
        <Participation>
            <performer>
                <label>Participant Name</label>
            </performer>
            <function>Role/Function</function>
            <mode>Mode of participation</mode>
            <time>Timestamp</time>
        </Participation>
        """
        # Build participation XML elements
        participation_xml_parts = []
        for p in participations:
            parts = [
                '  <Participation>',
                '    <performer>',
                f'      <label>{self._escape_xml(p["name"])}</label>',
            ]

            # Add external ID if present
            if p.get('id'):
                parts.append(f'      <external_ref>')
                parts.append(f'        <xdlink-value>{self._escape_xml(p["id"])}</xdlink-value>')
                parts.append(f'      </external_ref>')

            parts.append('    </performer>')

            if p.get('function'):
                parts.append(f'    <function>{self._escape_xml(p["function"])}</function>')

            if p.get('mode'):
                parts.append(f'    <mode>{self._escape_xml(p["mode"])}</mode>')

            if p.get('time'):
                parts.append(f'    <time>{self._escape_xml(str(p["time"]))}</time>')

            parts.append('  </Participation>')
            participation_xml_parts.append('\n'.join(parts))

        participation_xml = '\n'.join(participation_xml_parts)

        # Find where to insert participations (after provider or subject, before cluster)
        # Look for the placeholder or insert point
        if f'{self.PLACEHOLDER_PREFIX}participations' in xml_content:
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}participations',
                participation_xml
            )
        else:
            # Try to find a good insertion point - before the first cluster element
            # This is a fallback approach
            cluster_pattern = re.compile(r'(<sdc4:ms-[a-z0-9]+>)')
            match = cluster_pattern.search(xml_content)
            if match:
                insert_pos = match.start()
                xml_content = xml_content[:insert_pos] + participation_xml + '\n' + xml_content[insert_pos:]

        return xml_content

    def _replace_review_placeholders(self, xml_content: str, review_data: Dict[str, Any]) -> str:
        """
        Replace review/audit/attestation placeholders.

        SDC4 Audit Structure:
        - system_id: Identifier of the recording system
        - time_committed: When the data was committed
        - change_type: Type of change (creation, amendment, correction, etc.)
        - description: Optional description of the commit
        - committer: Party who committed the data

        SDC4 Attestation Structure:
        - attested_view: What view was attested (full, partial, amended)
        - proof: Digital signature or proof
        - reason: Reason for attestation
        - is_pending: Whether attestation is pending
        - attester: Party who attested
        """
        # =======================================================================
        # Audit fields
        # =======================================================================
        if review_data.get('audit_system'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}audit_system',
                self._escape_xml(review_data['audit_system'])
            )

        if review_data.get('audit_change_type'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}audit_change_type',
                self._escape_xml(review_data['audit_change_type'])
            )

        if review_data.get('audit_location'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}audit_location',
                self._escape_xml(review_data['audit_location'])
            )

        if review_data.get('audit_committer'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}audit_committer',
                self._escape_xml(review_data['audit_committer'])
            )

        if review_data.get('audit_description'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}audit_description',
                self._escape_xml(review_data['audit_description'])
            )

        # Handle time_committed (auto-generated if not provided)
        time_committed = review_data.get('audit_time_committed')
        if time_committed:
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}audit_time_committed',
                self._escape_xml(str(time_committed))
            )
        elif review_data.get('audit_system'):
            # If audit is being recorded, set time_committed to now
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}audit_time_committed',
                timezone.now().isoformat()
            )

        # =======================================================================
        # Attestation fields
        # =======================================================================
        if review_data.get('attestation_view'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}attestation_view',
                self._escape_xml(review_data['attestation_view'])
            )

        if review_data.get('attester_name'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}attester_name',
                self._escape_xml(review_data['attester_name'])
            )

        if review_data.get('attestation_reason'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}attestation_reason',
                self._escape_xml(review_data['attestation_reason'])
            )

        if review_data.get('attestation_proof'):
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}attestation_proof',
                self._escape_xml(review_data['attestation_proof'])
            )

        # Handle is_pending (boolean)
        is_pending = review_data.get('attestation_pending', False)
        xml_content = xml_content.replace(
            f'{self.PLACEHOLDER_PREFIX}attestation_pending',
            'true' if is_pending else 'false'
        )

        # Handle attestation_time (auto-generated if not provided)
        attestation_time = review_data.get('attestation_time')
        if attestation_time:
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}attestation_time',
                self._escape_xml(str(attestation_time))
            )
        elif review_data.get('attester_name'):
            # If attestation is being recorded, set time to now
            xml_content = xml_content.replace(
                f'{self.PLACEHOLDER_PREFIX}attestation_time',
                timezone.now().isoformat()
            )

        return xml_content

    def _build_from_wizard_fallback(self, instance_id: str, wizard_data: Dict[str, Any]) -> str:
        """
        Fallback XML generation from wizard data when skeleton is not available.
        """
        setup_data = wizard_data.get('setup', {})
        data_entry_data = wizard_data.get('data', {})

        # Use the existing fallback mechanism
        return self._build_from_form_fallback(
            instance_id=instance_id,
            form_data=data_entry_data,
            metadata={}
        )

    # Legacy method for compatibility
    def build(self, instance):
        """
        Build XML for the given model instance.

        This is a legacy method for compatibility with model-based workflows.
        """
        try:
            ct_id = getattr(instance, 'DM_CT_ID', getattr(instance, 'CT_ID', 'unknown'))

            root = etree.Element(
                f"{{{self.SDC4_NS}}}dm-{ct_id}",
                nsmap=self.NSMAP
            )

            root.set(
                f"{{http://www.w3.org/2001/XMLSchema-instance}}schemaLocation",
                f"{self.SDC4_NS} https://semanticdatacharter.com/dmlib/dm-{ct_id}.xsd"
            )

            # Add metadata
            instance_id = f"i-{cuid_generator()}"
            self._add_metadata_elements(root, instance_id)

            # Process instance fields
            self._process_instance(instance, root)

            xml_bytes = etree.tostring(
                root,
                pretty_print=True,
                encoding='UTF-8',
                xml_declaration=True
            )
            return xml_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Error building XML: {e}")
            raise

    def _process_instance(self, instance, parent_element):
        """Process fields and nested models of an instance."""
        field_metadata = getattr(instance, 'FIELD_METADATA', {})
        exceptional_values = getattr(instance, 'exceptional_values', {}) or {}

        for field_name, meta in field_metadata.items():
            ct_id = meta.get('ct_id', '')
            adapter_ctid = meta.get('adapter_ctid', '')
            field_type = meta.get('type', '')
            field_label = meta.get('label', field_name)

            # Create adapter wrapper
            if adapter_ctid:
                adapter_elem = etree.SubElement(parent_element, f"{{{self.SDC4_NS}}}ms-{adapter_ctid}")
            else:
                adapter_elem = parent_element

            # Create component element
            component_elem = etree.SubElement(adapter_elem, f"{{{self.SDC4_NS}}}ms-{ct_id}")
            etree.SubElement(component_elem, "label").text = field_label

            # Check for EV
            ev_code = exceptional_values.get(field_name)
            if ev_code and ev_code in self.EV_CODES:
                # Create proper EV element: <sdc4:NASK><ev-name>Not Asked</ev-name></sdc4:NASK>
                ev_elem = etree.SubElement(component_elem, f"{{{self.SDC4_NS}}}{ev_code}")
                ev_name_child = etree.SubElement(ev_elem, 'ev-name')
                ev_name_child.text = self.EV_CODES[ev_code]
            else:
                value = getattr(instance, field_name, None)
                if value is not None:
                    value_elem_name = self._get_value_element_name(field_type, meta)
                    value_elem = etree.SubElement(component_elem, value_elem_name)
                    if field_type == 'XdBoolean':
                        value_elem.text = 'true' if value else 'false'
                    elif field_type == 'XdTemporal':
                        # Get the temporal type from metadata for proper formatting
                        temporal_types = meta.get('temporal_types', ['date'])
                        temporal_type = temporal_types[0] if temporal_types else 'date'
                        value_elem.text = self._format_temporal_value(value, temporal_type)
                    else:
                        value_elem.text = str(value)

        # Process nested models
        nested_models = getattr(instance, 'NESTED_MODELS', [])
        for relation_name in nested_models:
            related_manager = getattr(instance, relation_name, None)
            if related_manager:
                for child in related_manager.all():
                    child_ct_id = getattr(child, 'CT_ID', 'unknown')
                    child_elem = etree.SubElement(parent_element, f"{{{self.SDC4_NS}}}ms-{child_ct_id}")
                    self._process_instance(child, child_elem)

