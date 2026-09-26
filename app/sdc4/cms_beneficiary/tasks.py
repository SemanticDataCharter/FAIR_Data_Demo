"""
Celery tasks for cms_beneficiary.

Automatic background processing for:
- RDF extraction to triplestore (Fuseki/GraphDB)
- Data validation
- Cleanup operations
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def extract_and_upload_rdf(self, instance_id: int):
    """
    Extract RDF from XML instance and upload to triplestore.

    This task is triggered automatically after save via Django signals.

    Args:
        instance_id: Primary key of the DataModel instance

    Returns:
        dict: Result with status and details
    """
    from .models import CmsBeneficiaryInstance
    from .utils.rdf_extractor import RDFExtractor
    from .utils.wizard_config import DMMetadata, FIELD_METADATA
    from sdc4_shared.utils.triplestore import get_triplestore_client

    try:
        # Get instance
        instance = CmsBeneficiaryInstance.objects.get(pk=instance_id)

        logger.info(f"Starting RDF extraction for instance {instance.instance_id}")

        # Extract RDF
        extractor = RDFExtractor(
            dm_ct_id=DMMetadata.CT_ID,
            dm_label=DMMetadata.TITLE,
            field_metadata=FIELD_METADATA
        )

        rdf_content = extractor.extract(
            xml_content=instance.xml_content,
            instance_id=instance.instance_id,
            validation_status=instance.validation_status,
            auto_corrected_fields=instance.auto_corrected_fields
        )

        if not rdf_content:
            logger.error(f"RDF extraction produced empty content for {instance.instance_id}")
            instance.rdf_sync_status = 'failed'
            instance.save(update_fields=['rdf_sync_status'])
            return {'status': 'failed', 'reason': 'empty_rdf'}

        # Upload to triplestore
        triplestore = get_triplestore_client()
        if triplestore is None:
            logger.info(f"Triplestore disabled, skipping RDF upload for {instance.instance_id}")
            instance.rdf_sync_status = 'disabled'
            instance.save(update_fields=['rdf_sync_status'])
            return {'status': 'disabled', 'reason': 'triplestore_disabled'}

        graph_uri = triplestore.get_graph_uri(
            instance_id=instance.instance_id,
            dm_ct_id=DMMetadata.CT_ID
        )

        success = triplestore.upload_graph(
            rdf_content=rdf_content,
            graph_uri=graph_uri,
            content_type='text/turtle'
        )

        if success:
            # Update instance
            instance.fuseki_graph_uri = graph_uri
            instance.rdf_uploaded_at = timezone.now()
            instance.rdf_sync_status = 'synced'
            instance.save(update_fields=[
                'fuseki_graph_uri',
                'rdf_uploaded_at',
                'rdf_sync_status'
            ])

            logger.info(f"Successfully uploaded RDF for {instance.instance_id} to {graph_uri}")

            return {
                'status': 'success',
                'instance_id': instance.instance_id,
                'graph_uri': graph_uri
            }
        else:
            # Mark as failed
            instance.rdf_sync_status = 'failed'
            instance.save(update_fields=['rdf_sync_status'])

            logger.error(f"Failed to upload RDF for {instance.instance_id}")

            return {'status': 'failed', 'reason': 'upload_failed'}

    except CmsBeneficiaryInstance.DoesNotExist:
        logger.error(f"Instance with id {instance_id} does not exist")
        return {'status': 'failed', 'reason': 'instance_not_found'}

    except Exception as e:
        logger.error(f"Error in RDF extraction task: {e}", exc_info=True)

        # Update instance status if possible
        try:
            instance = CmsBeneficiaryInstance.objects.get(pk=instance_id)
            instance.rdf_sync_status = 'failed'
            instance.save(update_fields=['rdf_sync_status'])
        except:
            pass

        # Re-raise to trigger retry
        raise self.retry(exc=e)


@shared_task
def cleanup_failed_rdf_syncs():
    """
    Retry failed RDF syncs.

    This task can be scheduled to run periodically to retry
    instances that failed to sync.
    """
    from .models import CmsBeneficiaryInstance

    failed_instances = CmsBeneficiaryInstance.objects.filter(
        rdf_sync_status='failed'
    )

    count = 0
    for instance in failed_instances:
        extract_and_upload_rdf.delay(instance.pk)
        count += 1

    logger.info(f"Queued {count} failed instances for retry")

    return {'queued': count}
