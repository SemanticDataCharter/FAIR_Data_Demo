
"""
Bulk Import Processor for SDC4 XML Instances.

This module processes bulk XML imports from zip files or directories,
running each file through the standard validation pipeline.
"""
import hashlib
import re
import zipfile
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from django.utils import timezone
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from lxml import etree
from cuid2 import cuid_wrapper

logger = logging.getLogger(__name__)

# Initialize CUID2 generator
cuid_generator = cuid_wrapper()


# ISO 21090 null flavors, as carried by SDC4 in the sdc4:ExceptionalValue
# substitution group. The element tag IS the code; there is no xsi:type.
_EV_CODES = frozenset((
    'NI', 'MSK', 'INV', 'DER', 'UNC', 'OTH', 'NINF', 'PINF',
    'ASKR', 'NASK', 'NAV', 'NA', 'TRC', 'ASKU', 'UNK', 'QS',
))


def _xml_has_exceptional_value(xml_content: str) -> bool:
    """
    True when any component in the instance states an absence.

    An authored Exceptional Value is not a defect and not an auto-correction:
    the record is telling the reader why a value is missing, which is exactly
    what it is supposed to do. It does change how the instance should be
    labelled, so the fact survives outside the document.
    """
    try:
        root = etree.fromstring(xml_content.encode('utf-8'))
    except Exception:
        return False
    for elem in root.iter():
        tag = elem.tag
        if isinstance(tag, str):
            local = tag.split('}', 1)[1] if '}' in tag else tag
            if local in _EV_CODES:
                return True
    return False


@dataclass
class ImportResult:
    """Result of importing a single XML file."""
    filename: str
    success: bool
    instance_id: Optional[str] = None
    error_message: Optional[str] = None
    validation_status: Optional[str] = None


@dataclass
class BulkImportResult:
    """Result of a bulk import operation."""
    total_files: int
    successful: int
    failed: int
    skipped: int = 0
    results: List[ImportResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate duration of import."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100

    def get_failures(self) -> List[ImportResult]:
        """Get list of failed imports."""
        return [r for r in self.results if not r.success]


class BulkImportProcessor:
    """
    Processes bulk XML imports for SDC4 data models.

    Supports importing from:
    - Directory path containing XML files
    - Zip file containing XML files

    Each XML file is processed through the same pipeline as form submissions:
    1. Parse XML and assign new instance_id
    2. Validate with sdcvalidator
    3. Extract JSON data
    4. Extract RDF and upload to Fuseki
    5. Save to database (invalid files saved with 'invalid' status and inv_ filename prefix)
    """

    SDC4_NS = 'https://semanticdatacharter.com/ns/sdc4/'

    def __init__(
        self,
        model_class,
        xsd_path: Union[str, Path],
        dm_ct_id: str,
        dm_label: str,
        field_metadata: Dict[str, Any]
    ):
        """
        Initialize BulkImportProcessor.

        Args:
            model_class: Django model class for the data model
            xsd_path: Path to the XSD schema file
            dm_ct_id: Data Model CT_ID
            dm_label: Data Model label
            field_metadata: FIELD_METADATA from the model
        """
        self.model_class = model_class
        self.xsd_path = Path(xsd_path)
        self.dm_ct_id = dm_ct_id
        self.dm_label = dm_label
        self.field_metadata = field_metadata

    def process_directory(self, directory_path: Union[str, Path]) -> BulkImportResult:
        """
        Process all XML files in a directory.

        Args:
            directory_path: Path to directory containing XML files

        Returns:
            BulkImportResult with success/failure counts and details
        """
        directory = Path(directory_path)
        if not directory.exists():
            return BulkImportResult(
                total_files=0,
                successful=0,
                failed=1,
                results=[ImportResult(
                    filename=str(directory_path),
                    success=False,
                    error_message=f"Directory not found: {directory_path}"
                )]
            )

        # Find all XML files
        xml_files = list(directory.glob('*.xml'))
        return self._process_files(xml_files)

    def process_zipfile(self, zip_path: Union[str, Path]) -> BulkImportResult:
        """
        Process all XML files in a zip archive.

        Args:
            zip_path: Path to zip file containing XML files

        Returns:
            BulkImportResult with success/failure counts and details
        """
        zip_path = Path(zip_path)
        if not zip_path.exists():
            return BulkImportResult(
                total_files=0,
                successful=0,
                failed=1,
                results=[ImportResult(
                    filename=str(zip_path),
                    success=False,
                    error_message=f"Zip file not found: {zip_path}"
                )]
            )

        # Extract to temp directory and process
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    # Extract only XML files
                    xml_names = [n for n in zf.namelist() if n.lower().endswith('.xml')]
                    zf.extractall(temp_dir, members=xml_names)

                # Find extracted XML files
                xml_files = list(Path(temp_dir).rglob('*.xml'))
                return self._process_files(xml_files)

            except zipfile.BadZipFile:
                return BulkImportResult(
                    total_files=0,
                    successful=0,
                    failed=1,
                    results=[ImportResult(
                        filename=str(zip_path),
                        success=False,
                        error_message=f"Invalid zip file: {zip_path}"
                    )]
                )

    @staticmethod
    def _content_fingerprint(xml_content: str) -> str:
        """Compute a SHA-256 fingerprint of XML content, ignoring instance_id and creation_timestamp.

        Uses lxml to parse and re-serialize so that both raw source files and
        already-imported (lxml-serialized) content produce identical output.
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            # Blank out the two fields that change on every import
            for tag in ('instance_id', 'creation_timestamp'):
                elem = root.find(f'.//{tag}')
                if elem is not None:
                    elem.text = ''
            normalized = etree.tostring(root, method='c14n2')
        except etree.XMLSyntaxError:
            # Fallback: regex strip + whitespace normalization
            normalized = re.sub(r'<instance_id>[^<]*</instance_id>', '<instance_id></instance_id>', xml_content)
            normalized = re.sub(r'<creation_timestamp>[^<]*</creation_timestamp>', '<creation_timestamp></creation_timestamp>', normalized)
            normalized = re.sub(r'>\s+<', '><', normalized).encode('utf-8')
        return hashlib.sha256(normalized).hexdigest()

    def _build_existing_fingerprints(self) -> Set[str]:
        """Build a set of content fingerprints from all existing instances in the database."""
        fingerprints = set()
        for xml_content in self.model_class.objects.values_list('xml_content', flat=True).iterator():
            fingerprints.add(self._content_fingerprint(xml_content))
        return fingerprints

    def _process_files(self, xml_files: List[Path]) -> BulkImportResult:
        """Process a list of XML files, skipping duplicates."""
        result = BulkImportResult(
            total_files=len(xml_files),
            successful=0,
            failed=0,
            skipped=0,
            started_at=timezone.now()
        )

        # Build fingerprint set from existing DB instances
        existing_fingerprints = self._build_existing_fingerprints()

        for xml_file in xml_files:
            # Check for duplicate before full processing
            try:
                raw_content = xml_file.read_text(encoding='utf-8')
                fingerprint = self._content_fingerprint(raw_content)
                if fingerprint in existing_fingerprints:
                    result.skipped += 1
                    result.results.append(ImportResult(
                        filename=xml_file.name,
                        success=True,
                        validation_status='skipped',
                    ))
                    continue
            except Exception:
                pass  # Fall through to normal processing if fingerprint check fails

            file_result = self._process_single_file(xml_file)
            result.results.append(file_result)

            if file_result.success:
                result.successful += 1
                # Add the new instance's fingerprint to prevent intra-batch duplicates
                try:
                    raw_content = xml_file.read_text(encoding='utf-8')
                    existing_fingerprints.add(self._content_fingerprint(raw_content))
                except Exception:
                    pass
            else:
                result.failed += 1

        result.completed_at = timezone.now()
        return result

    def _process_single_file(self, xml_file: Path) -> ImportResult:
        """
        Process a single XML file through the import pipeline.

        Args:
            xml_file: Path to XML file

        Returns:
            ImportResult for this file
        """
        filename = xml_file.name

        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            # Parse and assign new instance_id
            has_ev = _xml_has_exceptional_value(xml_content)
            xml_content, instance_id = self._assign_new_instance_id(xml_content, has_ev)

            # Update creation_timestamp
            xml_content = self._update_creation_timestamp(xml_content)

            # Import the utilities we need
            from .sdc_validator import SDCValidator
            from .json_extractor import JSONExtractor
            from .json_instance_generator import JSONInstanceGenerator
            from .rdf_extractor import RDFExtractor
            from sdc4_shared.utils.triplestore import get_triplestore_client

            # Validate with sdcvalidator
            validator = SDCValidator(str(self.xsd_path))
            validation_result = validator.validate(xml_content)

            # An authored Exceptional Value is valid data that states an absence.
            # It is recorded as valid_with_ev, distinct from the invalid case
            # below and distinct from auto-correction, which is a VaaS concern.
            validation_status = 'valid_with_ev' if has_ev else 'valid'
            validation_errors = {}

            if not validation_result.is_valid:
                # Save as invalid — EV injection is reserved for VaaS
                validation_status = 'invalid'
                validation_errors = validation_result.errors
                # Prefix filename for easy sorting of valid vs invalid files
                filename = f"inv_{filename}"

            # Extract JSON for JSONB queries
            json_extractor = JSONExtractor(field_metadata=self.field_metadata)
            extracted = json_extractor.extract(xml_content)
            json_data = extracted['fields']
            search_text = extracted['search_text']

            # Generate complete JSON instance
            json_instance_generator = JSONInstanceGenerator(field_metadata=self.field_metadata)
            json_instance = json_instance_generator.generate(xml_content)

            # Create the model instance
            from django.db import transaction

            with transaction.atomic():
                instance = self.model_class(
                    instance_id=instance_id,
                    xml_content=xml_content,
                    json_instance=json_instance,
                    search_text=search_text,
                    validation_status=validation_status,
                    validation_errors=validation_errors,
                )
                instance.save()

            # Project to the triple store, outside the transaction.
            #
            # Every instance is projected, including an invalid one. An
            # Exceptional Value is a stated absence, and a stated absence is
            # information: "this person's blood pressure was not asked for" is
            # an answer, and it is one an auditor may be looking for. Whether
            # invalid instances belong in a given analysis is the consumer's
            # decision, and the RDF carries sdc4:validationStatus so they can
            # make it in a FILTER. Withholding the triples would make that
            # decision for them by leaving no trace to filter on, which is
            # indistinguishable from the record never existing.
            try:
                triplestore = get_triplestore_client()
                if triplestore is None:
                    instance.rdf_sync_status = 'disabled'
                    instance.save(update_fields=['rdf_sync_status'])
                else:
                    rdf_extractor = RDFExtractor(
                        dm_ct_id=self.dm_ct_id,
                        dm_label=self.dm_label,
                        field_metadata=self.field_metadata
                    )
                    rdf_content = rdf_extractor.extract(
                        xml_content=xml_content,
                        instance_id=instance_id,
                        validation_status=validation_status,
                        auto_corrected_fields=[],
                    )

                    if rdf_content:
                        graph_uri = triplestore.get_graph_uri(instance_id, self.dm_ct_id)

                        if triplestore.upload_graph(rdf_content, graph_uri):
                            instance.fuseki_graph_uri = graph_uri
                            instance.rdf_uploaded_at = timezone.now()
                            instance.rdf_sync_status = 'synced'
                        else:
                            instance.rdf_sync_status = 'failed'

                        instance.save(update_fields=['fuseki_graph_uri', 'rdf_uploaded_at', 'rdf_sync_status'])
                    else:
                        # Extraction produced nothing. Report it rather than
                        # leaving the row on its default status, which reads
                        # as "not attempted yet".
                        logger.warning(f"RDF extraction produced no content for {filename}")
                        instance.rdf_sync_status = 'failed'
                        instance.save(update_fields=['rdf_sync_status'])

            except Exception as rdf_error:
                logger.warning(f"RDF upload failed for {filename}: {rdf_error}")
                instance.rdf_sync_status = 'failed'
                instance.save(update_fields=['rdf_sync_status'])

            return ImportResult(
                filename=filename,
                success=True,
                instance_id=instance_id,
                validation_status=validation_status,
            )

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            return ImportResult(
                filename=filename,
                success=False,
                error_message=str(e)
            )

    def _assign_new_instance_id(self, xml_content: str, has_ev: bool = False) -> Tuple[str, str]:
        """
        Assign a new instance_id to the XML content.

        Args:
            xml_content: XML string

        Returns:
            Tuple of (updated_xml_content, new_instance_id)
        """
        # Generate new instance_id. An instance carrying an Exceptional Value
        # takes the i-ev- prefix so a stated absence is visible in the
        # identifier itself, not only in a status column.
        prefix = 'i-ev-' if has_ev else 'i-'
        new_instance_id = f"{prefix}{cuid_generator()}"

        try:
            # Parse XML
            root = etree.fromstring(xml_content.encode('utf-8'))

            # Find instance_id element
            instance_id_elem = root.find('.//instance_id')
            if instance_id_elem is not None:
                instance_id_elem.text = new_instance_id
            else:
                # If not found, try to add it
                logger.warning("instance_id element not found in XML")

            # Serialize back
            xml_content = etree.tostring(
                root,
                pretty_print=True,
                encoding='UTF-8',
                xml_declaration=True
            ).decode('utf-8')

        except etree.XMLSyntaxError as e:
            logger.warning(f"XML parsing error during instance_id assignment: {e}")
            # Try string replacement as fallback
            import re
            pattern = r'<instance_id>[^<]*</instance_id>'
            xml_content = re.sub(pattern, f'<instance_id>{new_instance_id}</instance_id>', xml_content)

        return xml_content, new_instance_id

    def _update_creation_timestamp(self, xml_content: str) -> str:
        """Update the creation_timestamp to now."""
        timestamp = timezone.now().isoformat()

        try:
            root = etree.fromstring(xml_content.encode('utf-8'))

            # Find creation_timestamp element
            ts_elem = root.find('.//creation_timestamp')
            if ts_elem is not None:
                ts_elem.text = timestamp

            xml_content = etree.tostring(
                root,
                pretty_print=True,
                encoding='UTF-8',
                xml_declaration=True
            ).decode('utf-8')

        except etree.XMLSyntaxError as e:
            logger.warning(f"XML parsing error during timestamp update: {e}")
            import re
            pattern = r'<creation_timestamp>[^<]*</creation_timestamp>'
            xml_content = re.sub(pattern, f'<creation_timestamp>{timestamp}</creation_timestamp>', xml_content)

        return xml_content

    def _extract_field_values(self, xml_content: str) -> Dict[str, Any]:
        """
        Extract field values from XML for Django model fields.

        Args:
            xml_content: XML string

        Returns:
            Dict of field_name -> value
        """
        field_values = {}

        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            nsmap = {'sdc4': self.SDC4_NS}

            for field_name, meta in self.field_metadata.items():
                # In FIELD_METADATA, the outer key IS the ct_id
                ct_id = field_name
                field_type = meta.get('type', 'XdString')

                # Find the component element
                comp_elem = root.find(f".//sdc4:ms-{ct_id}", namespaces=nsmap)
                if comp_elem is None:
                    continue

                # Get value element name
                value_elem_name = self._get_value_element_name(field_type)

                # Handle XdTemporal specially - try all variant element names
                if value_elem_name is None and field_type == 'XdTemporal':
                    raw_value = None
                    for temporal_elem_name in self.TEMPORAL_ELEMENT_NAMES:
                        value_elem = comp_elem.find(f".//{temporal_elem_name}")
                        if value_elem is not None and value_elem.text:
                            raw_value = value_elem.text.strip()
                            break
                    if raw_value is None:
                        continue
                else:
                    # Find value element
                    value_elem = comp_elem.find(f".//{value_elem_name}")
                    if value_elem is None or not value_elem.text:
                        continue

                    # Parse value based on type
                    raw_value = value_elem.text.strip()

                # Skip placeholder values
                if raw_value in ('_PH_', '_OPT_PH_') or raw_value.startswith('<!-- '):
                    continue

                field_values[field_name] = self._parse_value(raw_value, field_type)

        except etree.XMLSyntaxError as e:
            logger.warning(f"XML parsing error during field extraction: {e}")

        return field_values

    # XdTemporal variant element names
    TEMPORAL_ELEMENT_NAMES = [
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

    def _get_value_element_name(self, field_type: str) -> str:
        """Get the value element name for a given field type."""
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
        }
        # XdTemporal returns None - caller must handle specially
        if field_type == 'XdTemporal':
            return None
        return type_map.get(field_type, 'value')

    def _parse_value(self, value_str: str, field_type: str) -> Any:
        """Parse a string value to the appropriate Python type."""
        if field_type == 'XdBoolean':
            return value_str.lower() == 'true'

        if field_type in ('XdCount', 'XdOrdinal'):
            try:
                return int(value_str)
            except ValueError:
                return None

        if field_type in ('XdQuantity', 'XdFloat', 'XdDouble'):
            try:
                from decimal import Decimal
                return Decimal(value_str)
            except Exception:
                return None

        # XdString, XdTemporal, XdLink, XdFile - return as string
        return value_str

