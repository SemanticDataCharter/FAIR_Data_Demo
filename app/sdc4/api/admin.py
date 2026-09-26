"""API admin configuration."""

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin interface for API Keys with secure key generation."""

    list_display = [
        'organization_name',
        'contact_email',
        'key_prefix_display',
        'is_active',
        'request_count',
        'last_used_at',
        'created_at',
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['organization_name', 'contact_email', 'key_prefix']
    readonly_fields = [
        'id',
        'key_prefix',
        'key_hash',
        'created_at',
        'last_used_at',
        'request_count',
        'created_by',
    ]

    # Fields shown when creating a new key
    add_fieldsets = [
        ('Organization Information', {
            'fields': ['organization_name', 'contact_email'],
            'description': 'Enter the organization details. An API key will be generated automatically.'
        }),
    ]

    # Fields shown when editing an existing key
    fieldsets = [
        ('Organization Information', {
            'fields': ['organization_name', 'contact_email']
        }),
        ('Key Details', {
            'fields': ['key_prefix', 'key_hash', 'is_active']
        }),
        ('Usage Statistics', {
            'fields': ['request_count', 'last_used_at', 'created_at', 'created_by']
        }),
    ]

    def key_prefix_display(self, obj):
        """Display key prefix with visual indicator."""
        status = '🟢' if obj.is_active else '🔴'
        return format_html('{} <code>{}</code>...', status, obj.key_prefix)
    key_prefix_display.short_description = 'Key'

    def get_fieldsets(self, request, obj=None):
        """Use different fieldsets for add vs change."""
        if obj is None:  # Adding new key
            return self.add_fieldsets
        return self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly when editing, except is_active."""
        if obj is None:  # Adding new key
            return []
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """
        Override save to generate key on creation.
        Shows the plaintext key ONCE in a success message.
        """
        if not change:  # New key being created
            api_key, plaintext_key = APIKey.create_key(
                organization_name=form.cleaned_data['organization_name'],
                contact_email=form.cleaned_data['contact_email'],
                created_by=request.user,
            )

            # Show the key ONCE - it cannot be retrieved later!
            messages.success(
                request,
                format_html(
                    '<strong>API Key Created Successfully!</strong><br><br>'
                    '<strong>Organization:</strong> {}<br>'
                    '<strong>Email:</strong> {}<br><br>'
                    '<strong style="color: red;">⚠️ COPY THIS KEY NOW - IT CANNOT BE SHOWN AGAIN:</strong><br>'
                    '<code style="background: #f0f0f0; padding: 10px; display: block; '
                    'font-size: 14px; user-select: all;">{}</code><br>'
                    '<small>Store this key securely. Only the hash is saved in the database.</small>',
                    api_key.organization_name,
                    api_key.contact_email,
                    plaintext_key,
                )
            )

            # Don't call super().save_model() - key already created
            return

        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """Allow changing is_active status only."""
        return True

    def response_add(self, request, obj, post_url_continue=None):
        """Redirect to list view after adding (key already shown in message)."""
        return HttpResponseRedirect(reverse('admin:api_apikey_changelist'))
