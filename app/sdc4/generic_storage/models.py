"""Generic storage models for XML instances without dedicated apps."""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex


class GenericInstance(models.Model):
    """
    Store XML instances when no dedicated Django app exists for the data model.

    This model provides generic storage for SDC4 XML instances, with:
    - Full XML content (authoritative)
    - JSON representation for JSONB queries
    - RDF content for semantic integration
    - Validation metadata and error tracking
    """

    # Primary identifier
    instance_id = models.CharField(
        max_length=50,
        primary_key=True,
        help_text="Instance ID - Format: i-{cuid} or i-ev-{cuid}"
    )

    # Data model reference
    dm_ct_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Data Model CT_ID this instance belongs to"
    )
    dm_label = models.CharField(
        max_length=200,
        help_text="Human-readable data model name"
    )

    # Source provenance (Beale-Sovereignty refactor)
    source_instance_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Identifier from the originating source system"
    )
    source_version_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Version identifier from the originating source system"
    )

    # Content storage (XML is authoritative)
    xml_content = models.TextField(
        help_text="Complete validated XML content (authoritative source)"
    )
    json_instance = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON representation for JSONB queries"
    )
    search_text = models.TextField(
        blank=True,
        help_text="Concatenated searchable text from all fields"
    )

    # RDF/Semantic content
    rdf_content = models.TextField(
        blank=True,
        help_text="RDF/Turtle representation of the instance"
    )

    # Validation metadata
    validation_status = models.CharField(
        max_length=20,
        choices=[
            ('valid', 'Valid'),
            ('valid_with_ev', 'Valid with Exceptional Values'),
        ],
        default='valid',
        help_text="Validation status"
    )
    validation_errors = models.JSONField(
        null=True,
        blank=True,
        help_text="Validation errors (if any)"
    )
    auto_corrected_fields = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True,
        help_text="List of field labels that were auto-corrected with EVs"
    )

    # Triplestore sync status
    rdf_sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('synced', 'Synced'),
            ('failed', 'Failed'),
            ('disabled', 'Disabled'),
        ],
        default='pending',
        help_text="RDF triplestore synchronization status"
    )
    graphdb_graph_uri = models.CharField(
        max_length=255,
        blank=True,
        help_text="Named graph URI in GraphDB"
    )
    rdf_uploaded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last successful RDF upload"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Generic Instance'
        verbose_name_plural = 'Generic Instances'
        indexes = [
            models.Index(fields=['dm_ct_id', '-created_at']),
            models.Index(fields=['validation_status']),
            models.Index(fields=['rdf_sync_status']),
            GinIndex(fields=['json_instance']),  # For JSONB queries
        ]

    def __str__(self):
        return f"{self.dm_label} ({self.instance_id})"

    @property
    def has_exceptional_values(self):
        """Check if this instance has exceptional values."""
        return self.validation_status == 'valid_with_ev'

    @property
    def is_rdf_synced(self):
        """Check if RDF is synced to triplestore."""
        return self.rdf_sync_status == 'synced'

    def get_schema_path(self):
        """Get the path to the XSD schema file for this instance."""
        from django.conf import settings
        from django.core.files.storage import default_storage
        return default_storage.path(f'dmlib/dm-{self.dm_ct_id}.xsd')
