"""Tests for SDC4 REST API."""

import io
import zipfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from .models import APIKey
from generic_storage.models import GenericInstance


User = get_user_model()


class APIKeyModelTest(TestCase):
    """Test APIKey model functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_api_key(self):
        """Test creating an API key."""
        api_key, plaintext_key = APIKey.create_key(
            organization_name='Test Org',
            contact_email='test@example.com',
            created_by=self.user
        )

        self.assertIsNotNone(api_key)
        self.assertIsNotNone(plaintext_key)
        self.assertTrue(plaintext_key.startswith('sdc4_'))
        self.assertEqual(api_key.organization_name, 'Test Org')
        self.assertTrue(api_key.is_active)

    def test_verify_api_key(self):
        """Test API key verification."""
        api_key, plaintext_key = APIKey.create_key(
            organization_name='Test Org',
            contact_email='test@example.com'
        )

        # Correct key should verify
        self.assertTrue(api_key.verify_key(plaintext_key))

        # Incorrect key should fail
        self.assertFalse(api_key.verify_key('sdc4_wrongkey'))

    def test_hash_key_is_consistent(self):
        """Test that hashing the same key produces same result."""
        test_key = 'sdc4_testkey123'
        hash1 = APIKey.hash_key(test_key)
        hash2 = APIKey.hash_key(test_key)

        self.assertEqual(hash1, hash2)


class APIKeyAuthenticationTest(TestCase):
    """Test API key authentication."""

    def setUp(self):
        self.client = APIClient()
        self.api_key, self.plaintext_key = APIKey.create_key(
            organization_name='Test Org',
            contact_email='test@example.com'
        )

    def test_authenticated_request(self):
        """Test request with valid API key."""
        # Create a test ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        zip_buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            'test.zip',
            zip_buffer.read(),
            content_type='application/zip'
        )

        response = self.client.post(
            '/api/v1/upload/zip/',
            {'file': uploaded_file},
            HTTP_X_API_KEY=self.plaintext_key
        )

        # Should succeed with valid key
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_request(self):
        """Test request without API key."""
        response = self.client.post('/api/v1/upload/zip/')

        # Should fail without API key
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_api_key(self):
        """Test request with invalid API key."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        zip_buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            'test.zip',
            zip_buffer.read(),
            content_type='application/zip'
        )

        response = self.client.post(
            '/api/v1/upload/zip/',
            {'file': uploaded_file},
            HTTP_X_API_KEY='sdc4_invalidkey123'
        )

        # Should fail with invalid key
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deactivated_api_key(self):
        """Test request with deactivated API key."""
        # Deactivate the key
        self.api_key.is_active = False
        self.api_key.save()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        zip_buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            'test.zip',
            zip_buffer.read(),
            content_type='application/zip'
        )

        response = self.client.post(
            '/api/v1/upload/zip/',
            {'file': uploaded_file},
            HTTP_X_API_KEY=self.plaintext_key
        )

        # Should fail with deactivated key
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ZIPUploadViewTest(TestCase):
    """Test ZIP upload endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.api_key, self.plaintext_key = APIKey.create_key(
            organization_name='Test Org',
            contact_email='test@example.com'
        )

    def test_upload_valid_zip(self):
        """Test uploading a valid ZIP file."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        zip_buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            'test.zip',
            zip_buffer.read(),
            content_type='application/zip'
        )

        response = self.client.post(
            '/api/v1/upload/zip/',
            {'file': uploaded_file},
            HTTP_X_API_KEY=self.plaintext_key
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['filename'], 'test.zip')

    def test_upload_without_file(self):
        """Test uploading without a file."""
        response = self.client.post(
            '/api/v1/upload/zip/',
            {},
            HTTP_X_API_KEY=self.plaintext_key
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'FILE_REQUIRED')

    def test_upload_non_zip_file(self):
        """Test uploading a non-ZIP file."""
        uploaded_file = SimpleUploadedFile(
            'test.txt',
            b'test content',
            content_type='text/plain'
        )

        response = self.client.post(
            '/api/v1/upload/zip/',
            {'file': uploaded_file},
            HTTP_X_API_KEY=self.plaintext_key
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'INVALID_FILE_TYPE')


class SchemaUploadViewTest(TestCase):
    """Test schema upload endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.api_key, self.plaintext_key = APIKey.create_key(
            organization_name='Test Org',
            contact_email='test@example.com'
        )

    def test_upload_valid_schema(self):
        """Test uploading valid schema files."""
        xsd_file = SimpleUploadedFile(
            'dm-abc123.xsd',
            b'<xs:schema></xs:schema>',
            content_type='application/xml'
        )

        response = self.client.post(
            '/api/v1/upload/schema/',
            {'files': [xsd_file]},
            HTTP_X_API_KEY=self.plaintext_key
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['stored_files']), 1)

    def test_upload_invalid_filename(self):
        """Test uploading file with invalid filename pattern."""
        invalid_file = SimpleUploadedFile(
            'invalid.xsd',
            b'<xs:schema></xs:schema>',
            content_type='application/xml'
        )

        response = self.client.post(
            '/api/v1/upload/schema/',
            {'files': [invalid_file]},
            HTTP_X_API_KEY=self.plaintext_key
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['data']['errors']), 1)


class GenericInstanceModelTest(TestCase):
    """Test GenericInstance model."""

    def test_create_generic_instance(self):
        """Test creating a generic instance."""
        instance = GenericInstance.objects.create(
            instance_id='i-test123',
            dm_ct_id='abc123',
            dm_label='TestDM',
            xml_content='<test>content</test>',
            validation_status='valid'
        )

        self.assertEqual(instance.instance_id, 'i-test123')
        self.assertEqual(instance.dm_ct_id, 'abc123')
        self.assertFalse(instance.has_exceptional_values)

    def test_instance_with_exceptional_values(self):
        """Test instance with exceptional values."""
        instance = GenericInstance.objects.create(
            instance_id='i-ev-test123',
            dm_ct_id='abc123',
            dm_label='TestDM',
            xml_content='<test>content</test>',
            validation_status='valid_with_ev',
            auto_corrected_fields=['field1', 'field2']
        )

        self.assertTrue(instance.has_exceptional_values)
        self.assertEqual(len(instance.auto_corrected_fields), 2)
