"""
Django signals for brfss_respondent.

Automatic triggers for:
- RDF extraction after save
- Data validation
- Cleanup operations
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BrfssRespondentInstance
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BrfssRespondentInstance)
def trigger_rdf_extraction(sender, instance, created, **kwargs):
    """
    Trigger RDF extraction to Fuseki after save.

    Args:
        sender: Model class
        instance: Model instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Import here to avoid circular imports
    from .tasks import extract_and_upload_rdf

    # Only trigger for instances with RDF sync status = 'pending'
    # This prevents infinite loops and unnecessary re-extraction
    if instance.rdf_sync_status == 'pending':
        logger.info(
            f"Triggering RDF extraction for instance {instance.instance_id} "
            f"(created={created})"
        )

        # Queue Celery task (async)
        extract_and_upload_rdf.delay(instance.pk)
