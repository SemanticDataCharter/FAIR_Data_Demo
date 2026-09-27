"""API serializers for request/response formatting."""

from rest_framework import serializers


class FileUploadResponseSerializer(serializers.Serializer):
    """Serializer for file upload responses."""

    success = serializers.BooleanField()
    data = serializers.DictField()


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""

    success = serializers.BooleanField(default=False)
    error = serializers.DictField()


class ZIPUploadDataSerializer(serializers.Serializer):
    """Serializer for ZIP upload response data."""

    filename = serializers.CharField()
    path = serializers.CharField()
    size = serializers.IntegerField()


class SchemaFileSerializer(serializers.Serializer):
    """Serializer for individual schema file information."""

    filename = serializers.CharField()
    path = serializers.CharField()
    size = serializers.IntegerField()


class SchemaUploadDataSerializer(serializers.Serializer):
    """Serializer for schema upload response data."""

    stored_files = serializers.ListField(
        child=SchemaFileSerializer()
    )
    errors = serializers.ListField()


class RDFUploadDataSerializer(serializers.Serializer):
    """Serializer for RDF/Turtle upload response data."""

    filename = serializers.CharField()
    path = serializers.CharField()
    size = serializers.IntegerField()
    triplestore_status = serializers.ChoiceField(
        choices=['synced', 'failed', 'disabled']
    )
    graph_uri = serializers.CharField(allow_null=True)


class XMLValidationDataSerializer(serializers.Serializer):
    """Serializer for XML validation response data."""

    instance_id = serializers.CharField()
    dm_ct_id = serializers.CharField()
    dm_label = serializers.CharField()
    validation_status = serializers.ChoiceField(
        choices=['valid', 'valid_with_ev']
    )
    storage_type = serializers.ChoiceField(
        choices=['app_specific', 'generic']
    )
    auto_corrected_fields = serializers.ListField()
    validation_errors = serializers.DictField(allow_null=True)
    rdf_sync_status = serializers.ChoiceField(
        choices=['pending', 'synced', 'failed', 'disabled']
    )
