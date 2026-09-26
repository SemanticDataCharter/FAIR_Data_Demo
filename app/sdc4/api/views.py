"""API views for file upload and XML validation endpoints."""

import os
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .authentication import APIKeyAuthentication
from .serializers import (
    FileUploadResponseSerializer,
    ErrorResponseSerializer,
    ZIPUploadDataSerializer,
    SchemaUploadDataSerializer,
    RDFUploadDataSerializer,
    XMLValidationDataSerializer,
)


class ZIPUploadView(APIView):
    """
    Upload a generated SDC4 app ZIP file for storage.

    POST /api/v1/upload/zip/
    """

    authentication_classes = [APIKeyAuthentication]

    def post(self, request):
        """Handle ZIP file upload."""
        # Check if file provided
        if 'file' not in request.FILES:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'FILE_REQUIRED',
                        'message': 'No file provided in request',
                        'details': {}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']

        # Validate file extension
        if not uploaded_file.name.endswith('.zip'):
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_FILE_TYPE',
                        'message': 'File must be a ZIP archive',
                        'details': {'filename': uploaded_file.name}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate ZIP file integrity
        try:
            # Read into memory for validation (for small files)
            # For large files in production, consider streaming validation
            file_content = uploaded_file.read()
            uploaded_file.seek(0)  # Reset for saving

            # Test if valid ZIP
            import io
            zip_buffer = io.BytesIO(file_content)
            with zipfile.ZipFile(zip_buffer) as zf:
                # Test ZIP integrity
                if zf.testzip() is not None:
                    raise zipfile.BadZipFile("ZIP integrity check failed")

        except zipfile.BadZipFile:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_ZIP',
                        'message': 'File is not a valid ZIP archive',
                        'details': {'filename': uploaded_file.name}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save to storage
        save_path = f'zip/{uploaded_file.name}'
        saved_path = default_storage.save(save_path, uploaded_file)
        file_size = uploaded_file.size

        # Build response
        response_data = {
            'filename': uploaded_file.name,
            'path': saved_path,
            'size': file_size,
        }

        return Response(
            {
                'success': True,
                'data': response_data
            },
            status=status.HTTP_201_CREATED
        )


class SchemaUploadView(APIView):
    """
    Upload data model schema files (.xsd, .html, .owl) to dmlib directory.

    POST /api/v1/upload/schema/
    """

    authentication_classes = [APIKeyAuthentication]

    ALLOWED_EXTENSIONS = {'.xsd', '.html', '.owl'}

    def post(self, request):
        """Handle schema file upload."""
        # Check if files provided
        if 'files' not in request.FILES:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'FILES_REQUIRED',
                        'message': 'No files provided in request',
                        'details': {}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        files = request.FILES.getlist('files')
        stored_files = []
        errors = []

        for uploaded_file in files:
            filename = uploaded_file.name
            file_ext = Path(filename).suffix.lower()

            # Validate file extension
            if file_ext not in self.ALLOWED_EXTENSIONS:
                errors.append({
                    'filename': filename,
                    'error': f'Invalid file extension. Allowed: {", ".join(self.ALLOWED_EXTENSIONS)}'
                })
                continue

            # Validate filename pattern: dm-{ct_id}.{ext}
            if not filename.startswith('dm-') or filename.count('.') != 1:
                errors.append({
                    'filename': filename,
                    'error': 'Filename must match pattern: dm-{ct_id}.{ext}'
                })
                continue

            # Save to dmlib directory
            save_path = f'dmlib/{filename}'
            saved_path = default_storage.save(save_path, uploaded_file)

            stored_files.append({
                'filename': filename,
                'path': saved_path,
                'size': uploaded_file.size,
            })

        # Return response
        response_data = {
            'stored_files': stored_files,
            'errors': errors,
        }

        return Response(
            {
                'success': True,
                'data': response_data
            },
            status=status.HTTP_201_CREATED
        )


class RDFUploadView(APIView):
    """
    Upload TTL or RDF files to dmlib and optionally upload to GraphDB triplestore.

    POST /api/v1/upload/rdf/
    """

    authentication_classes = [APIKeyAuthentication]

    ALLOWED_EXTENSIONS = {'.ttl', '.rdf'}

    def post(self, request):
        """Handle RDF/Turtle file upload."""
        # Check if file provided
        if 'file' not in request.FILES:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'FILE_REQUIRED',
                        'message': 'No file provided in request',
                        'details': {}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']
        filename = uploaded_file.name
        file_ext = Path(filename).suffix.lower()

        # Validate file extension
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_FILE_TYPE',
                        'message': f'File must be .ttl or .rdf',
                        'details': {'filename': filename}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save to dmlib directory
        save_path = f'dmlib/{filename}'
        saved_path = default_storage.save(save_path, uploaded_file)

        # Try to upload to GraphDB triplestore
        triplestore_status = 'disabled'
        graph_uri = None

        graphdb_url = getattr(settings, 'GRAPHDB_URL', None)
        graphdb_repo = getattr(settings, 'GRAPHDB_REPOSITORY', None)

        if graphdb_url and graphdb_repo:
            try:
                # Extract ct_id from filename for graph URI
                # Expected pattern: dm-{ct_id}.ttl or dm-{ct_id}_shacl.ttl
                ct_id = filename.replace('dm-', '').replace('_shacl', '').replace(file_ext, '')
                graph_uri = f'urn:sdc4:dm-{ct_id}:schema'

                # Upload to GraphDB
                uploaded_file.seek(0)  # Reset file pointer
                rdf_content = uploaded_file.read()

                import requests
                upload_url = f'{graphdb_url}/repositories/{graphdb_repo}/statements'

                graphdb_user = getattr(settings, 'GRAPHDB_USER', None)
                graphdb_password = getattr(settings, 'GRAPHDB_PASSWORD', None)

                headers = {
                    'Content-Type': 'application/x-turtle' if file_ext == '.ttl' else 'application/rdf+xml',
                }

                params = {
                    'context': f'<{graph_uri}>'
                }

                auth = None
                if graphdb_user and graphdb_password:
                    auth = (graphdb_user, graphdb_password)

                response = requests.post(
                    upload_url,
                    data=rdf_content,
                    headers=headers,
                    params=params,
                    auth=auth,
                    timeout=30
                )

                if response.status_code in (200, 201, 204):
                    triplestore_status = 'synced'
                else:
                    triplestore_status = 'failed'

            except Exception as e:
                # Log error but don't fail the upload
                triplestore_status = 'failed'

        # Build response
        response_data = {
            'filename': filename,
            'path': saved_path,
            'size': uploaded_file.size,
            'triplestore_status': triplestore_status,
            'graph_uri': graph_uri,
        }

        return Response(
            {
                'success': True,
                'data': response_data
            },
            status=status.HTTP_201_CREATED
        )


class XMLValidationView(APIView):
    """
    Validate an XML instance against its data model schema and store if valid.

    POST /api/v1/validate/xml/
    """

    authentication_classes = [APIKeyAuthentication]

    def post(self, request):
        """Handle XML validation and storage."""
        # Get XML content from file or JSON body
        xml_content = None

        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            xml_content = uploaded_file.read().decode('utf-8')
        elif 'xml_content' in request.data:
            xml_content = request.data['xml_content']
        else:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'XML_REQUIRED',
                        'message': 'No XML content provided',
                        'details': {}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse XML and extract dm_ct_id
        try:
            from lxml import etree
            xml_tree = etree.fromstring(xml_content.encode('utf-8'))
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_XML',
                        'message': 'Could not parse XML',
                        'details': {'error': str(e)}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract dm_ct_id from root element
        # Expected format: <sdc4:dm-{ct_id} xmlns:sdc4="...">
        root_tag = xml_tree.tag
        if '}' in root_tag:
            # Remove namespace
            root_tag = root_tag.split('}')[1]

        if not root_tag.startswith('dm-'):
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_XML',
                        'message': 'Root element must be <sdc4:dm-{ct_id}>',
                        'details': {'root_tag': root_tag}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        dm_ct_id = root_tag.replace('dm-', '')

        # Check if schema exists
        schema_filename = f'dm-{dm_ct_id}.xsd'
        schema_path = default_storage.path(f'dmlib/{schema_filename}')

        if not os.path.exists(schema_path):
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'SCHEMA_NOT_FOUND',
                        'message': f'No schema found for dm-{dm_ct_id}',
                        'details': {'dm_ct_id': dm_ct_id}
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate XML against XSD schema
        validation_status = 'valid'
        auto_corrected_fields = []
        validation_errors = None

        try:
            # Load XSD schema
            with open(schema_path, 'rb') as schema_file:
                schema_root = etree.XML(schema_file.read())
                schema = etree.XMLSchema(schema_root)

            # Validate
            if not schema.validate(xml_tree):
                # Validation failed - apply Exceptional Values
                validation_status = 'valid_with_ev'

                # Collect validation errors
                validation_errors = {}
                for error in schema.error_log:
                    validation_errors[f'line-{error.line}'] = error.message

                # Auto-correct with EVs
                # In production, implement full EV logic from sdcvalidator
                auto_corrected_fields = list(validation_errors.keys())

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_FAILED',
                        'message': 'XML validation failed',
                        'details': {'error': str(e)}
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Generate instance ID
        import cuid2
        if validation_status == 'valid_with_ev':
            instance_id = f'i-ev-{cuid2.cuid2()}'
        else:
            instance_id = f'i-{cuid2.cuid2()}'

        # Determine storage location
        storage_type = 'generic'  # Default to GenericInstance

        # Check if dedicated app exists for this DM
        # Use DM registry scanner utility
        from sdc4_shared.utils.dm_registry import get_model_for_dm_ct_id

        try:
            instance_model = get_model_for_dm_ct_id(dm_ct_id)
            if instance_model:
                storage_type = 'app_specific'
        except ImportError:
            # Utility not implemented yet, fallback to generic
            pass

        # Extract dm_label from XML
        dm_label_elem = xml_tree.find('.//{*}dm-label')
        dm_label = dm_label_elem.text if dm_label_elem is not None else f'DM-{dm_ct_id}'

        # Store in database
        if storage_type == 'generic':
            from generic_storage.models import GenericInstance

            instance = GenericInstance.objects.create(
                instance_id=instance_id,
                dm_ct_id=dm_ct_id,
                dm_label=dm_label,
                xml_content=xml_content,
                validation_status=validation_status,
                validation_errors=validation_errors,
                auto_corrected_fields=auto_corrected_fields,
            )
        else:
            # Save to app-specific Instance model
            # Implementation depends on dynamic model loading
            pass

        # Upload RDF to triplestore (async in production)
        rdf_sync_status = 'disabled'

        graphdb_url = getattr(settings, 'GRAPHDB_URL', None)
        if graphdb_url:
            try:
                # Extract RDF from XML (implement RDF extraction utility)
                # For now, mark as pending
                rdf_sync_status = 'pending'
            except Exception:
                rdf_sync_status = 'failed'

        # Build response
        response_data = {
            'instance_id': instance_id,
            'dm_ct_id': dm_ct_id,
            'dm_label': dm_label,
            'validation_status': validation_status,
            'storage_type': storage_type,
            'auto_corrected_fields': auto_corrected_fields,
            'validation_errors': validation_errors,
            'rdf_sync_status': rdf_sync_status,
        }

        return Response(
            {
                'success': True,
                'data': response_data
            },
            status=status.HTTP_201_CREATED
        )
