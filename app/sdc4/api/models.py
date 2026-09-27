"""API models."""

import hashlib
import secrets
import uuid

from django.db import models
from django.conf import settings


class APIKey(models.Model):
    """
    API Key for authenticating external clients.

    Keys are generated automatically and shown ONCE at creation time.
    Only the SHA-256 hash is stored in the database.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Organization metadata
    organization_name = models.CharField(
        max_length=100,
        help_text="Name of the organization this key belongs to"
    )
    contact_email = models.EmailField(
        help_text="Contact email for this API key holder"
    )

    # Key storage (hash only - plaintext never stored)
    key_prefix = models.CharField(
        max_length=12,
        help_text="First 12 chars of key for identification (e.g., 'sdc4_xK9m...')"
    )
    key_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="SHA-256 hash of the API key"
    )

    # Status and audit
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_api_keys'
    )

    # Optional: usage limits
    request_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'

    def __str__(self):
        return f"{self.organization_name} ({self.key_prefix}...)"

    @classmethod
    def generate_key(cls):
        """Generate a new API key with sdc4_ prefix."""
        random_part = secrets.token_urlsafe(32)
        return f"sdc4_{random_part}"

    @classmethod
    def hash_key(cls, plaintext_key: str) -> str:
        """Hash a plaintext key using SHA-256."""
        return hashlib.sha256(plaintext_key.encode()).hexdigest()

    @classmethod
    def create_key(cls, organization_name: str, contact_email: str, created_by=None):
        """
        Create a new API key.

        Returns:
            tuple: (APIKey instance, plaintext_key)

        Note: The plaintext_key is only available at creation time!
        """
        plaintext_key = cls.generate_key()
        key_hash = cls.hash_key(plaintext_key)
        key_prefix = plaintext_key[:12]  # "sdc4_" + first 7 chars

        instance = cls.objects.create(
            organization_name=organization_name,
            contact_email=contact_email,
            key_prefix=key_prefix,
            key_hash=key_hash,
            created_by=created_by,
        )

        return instance, plaintext_key

    def verify_key(self, plaintext_key: str) -> bool:
        """Verify a plaintext key against this stored hash."""
        return secrets.compare_digest(
            self.key_hash,
            self.hash_key(plaintext_key)
        )

    def record_usage(self):
        """Record that this key was used."""
        from django.utils import timezone
        self.last_used_at = timezone.now()
        self.request_count += 1
        self.save(update_fields=['last_used_at', 'request_count'])
