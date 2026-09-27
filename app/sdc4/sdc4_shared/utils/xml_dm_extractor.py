"""
XML DM Extractor - Extract dm_ct_id from SDC4 XML instances.

This utility parses XML content and extracts the data model CT_ID
from the root element, which follows the pattern: <sdc4:dm-{ct_id}>
"""

from typing import Optional, Tuple
from lxml import etree


def extract_dm_ct_id_from_xml(xml_content: str) -> Optional[str]:
    """
    Extract dm_ct_id from XML root element.

    Args:
        xml_content: XML content as string

    Returns:
        dm_ct_id if found, None otherwise

    Raises:
        ValueError: If XML cannot be parsed or root element is invalid

    Example:
        >>> xml = '''<?xml version="1.0"?>
        ... <sdc4:dm-rb46xg2fk464oqmlmyejpn2j xmlns:sdc4="...">
        ...     ...
        ... </sdc4:dm-rb46xg2fk464oqmlmyejpn2j>'''
        >>> extract_dm_ct_id_from_xml(xml)
        'rb46xg2fk464oqmlmyejpn2j'
    """
    try:
        # Parse XML
        xml_tree = etree.fromstring(xml_content.encode('utf-8'))
    except Exception as e:
        raise ValueError(f"Could not parse XML: {e}")

    # Get root tag
    root_tag = xml_tree.tag

    # Remove namespace if present
    if '}' in root_tag:
        # Format: {http://namespace.url}dm-abc123
        root_tag = root_tag.split('}')[1]

    # Validate format
    if not root_tag.startswith('dm-'):
        raise ValueError(
            f"Root element must be <sdc4:dm-{'{ct_id}'}>, got: {root_tag}"
        )

    # Extract ct_id
    dm_ct_id = root_tag.replace('dm-', '')

    if not dm_ct_id:
        raise ValueError("dm_ct_id is empty")

    return dm_ct_id


def extract_dm_info_from_xml(xml_content: str) -> Tuple[str, Optional[str]]:
    """
    Extract dm_ct_id and dm_label from XML.

    Args:
        xml_content: XML content as string

    Returns:
        Tuple of (dm_ct_id, dm_label)

    Raises:
        ValueError: If XML cannot be parsed or root element is invalid

    Example:
        >>> xml = '''<?xml version="1.0"?>
        ... <sdc4:dm-rb46xg2fk464oqmlmyejpn2j>
        ...     <dm-label>TestData3</dm-label>
        ...     ...
        ... </sdc4:dm-rb46xg2fk464oqmlmyejpn2j>'''
        >>> extract_dm_info_from_xml(xml)
        ('rb46xg2fk464oqmlmyejpn2j', 'TestData3')
    """
    try:
        # Parse XML
        xml_tree = etree.fromstring(xml_content.encode('utf-8'))
    except Exception as e:
        raise ValueError(f"Could not parse XML: {e}")

    # Extract dm_ct_id from root tag
    root_tag = xml_tree.tag
    if '}' in root_tag:
        root_tag = root_tag.split('}')[1]

    if not root_tag.startswith('dm-'):
        raise ValueError(
            f"Root element must be <sdc4:dm-{'{ct_id}'}>, got: {root_tag}"
        )

    dm_ct_id = root_tag.replace('dm-', '')

    # Extract dm_label from content
    dm_label = None
    dm_label_elem = xml_tree.find('.//{*}dm-label')

    if dm_label_elem is not None:
        dm_label = dm_label_elem.text

    # Fallback to DM-{ct_id} if no label found
    if not dm_label:
        dm_label = f'DM-{dm_ct_id}'

    return dm_ct_id, dm_label


def validate_xml_root_element(xml_content: str, expected_dm_ct_id: Optional[str] = None) -> bool:
    """
    Validate that XML has correct SDC4 root element format.

    Args:
        xml_content: XML content as string
        expected_dm_ct_id: Optional expected dm_ct_id to validate against

    Returns:
        True if valid, False otherwise

    Example:
        >>> xml = '<sdc4:dm-abc123>...</sdc4:dm-abc123>'
        >>> validate_xml_root_element(xml)
        True
        >>> validate_xml_root_element(xml, expected_dm_ct_id='abc123')
        True
        >>> validate_xml_root_element(xml, expected_dm_ct_id='xyz789')
        False
    """
    try:
        dm_ct_id = extract_dm_ct_id_from_xml(xml_content)

        if expected_dm_ct_id:
            return dm_ct_id == expected_dm_ct_id

        return True

    except ValueError:
        return False
