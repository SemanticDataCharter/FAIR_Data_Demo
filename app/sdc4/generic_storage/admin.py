"""Generic storage admin configuration."""

from django.contrib import admin
from django.utils.html import format_html

from .models import GenericInstance


@admin.register(GenericInstance)
class GenericInstanceAdmin(admin.ModelAdmin):
    """Admin interface for generic XML instances."""

    list_display = [
        'instance_id',
        'dm_label',
        'dm_ct_id',
        'validation_status_display',
        'rdf_sync_display',
        'created_at',
    ]
    list_filter = [
        'validation_status',
        'rdf_sync_status',
        'dm_ct_id',
        'created_at',
    ]
    search_fields = [
        'instance_id',
        'dm_label',
        'dm_ct_id',
        'search_text',
    ]
    readonly_fields = [
        'instance_id',
        'dm_ct_id',
        'dm_label',
        'validation_status',
        'auto_corrected_fields',
        'validation_errors',
        'rdf_sync_status',
        'graphdb_graph_uri',
        'rdf_uploaded_at',
        'created_at',
        'updated_at',
        'xml_preview',
        'json_preview',
    ]

    fieldsets = [
        ('Instance Information', {
            'fields': [
                'instance_id',
                'dm_ct_id',
                'dm_label',
                'created_at',
                'updated_at',
            ]
        }),
        ('Validation', {
            'fields': [
                'validation_status',
                'auto_corrected_fields',
                'validation_errors',
            ]
        }),
        ('Content', {
            'fields': [
                'xml_preview',
                'json_preview',
                'search_text',
            ],
            'classes': ['collapse'],
        }),
        ('RDF Synchronization', {
            'fields': [
                'rdf_sync_status',
                'graphdb_graph_uri',
                'rdf_uploaded_at',
            ]
        }),
    ]

    def validation_status_display(self, obj):
        """Display validation status with icon."""
        if obj.validation_status == 'valid':
            icon = '✓'
            color = 'green'
        else:
            icon = '⚠'
            color = 'orange'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.get_validation_status_display()
        )
    validation_status_display.short_description = 'Validation'

    def rdf_sync_display(self, obj):
        """Display RDF sync status with icon."""
        icons = {
            'synced': ('✓', 'green'),
            'pending': ('⏱', 'orange'),
            'failed': ('✗', 'red'),
            'disabled': ('⊘', 'gray'),
        }
        icon, color = icons.get(obj.rdf_sync_status, ('?', 'black'))
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.get_rdf_sync_status_display()
        )
    rdf_sync_display.short_description = 'RDF Sync'

    def xml_preview(self, obj):
        """Show preview of XML content."""
        if not obj.xml_content:
            return '-'
        preview = obj.xml_content[:500]
        if len(obj.xml_content) > 500:
            preview += '...'
        return format_html('<pre>{}</pre>', preview)
    xml_preview.short_description = 'XML Content Preview'

    def json_preview(self, obj):
        """Show preview of JSON content."""
        if not obj.json_instance:
            return '-'
        import json
        preview = json.dumps(obj.json_instance, indent=2)[:500]
        if len(preview) > 500:
            preview += '...'
        return format_html('<pre>{}</pre>', preview)
    json_preview.short_description = 'JSON Content Preview'

    def has_add_permission(self, request):
        """Disable manual creation - instances created via API."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make read-only - instances managed via API."""
        return False
