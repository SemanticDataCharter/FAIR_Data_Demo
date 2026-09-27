
"""
List View for cms_prescription_drug_event instances.

Provides:
- Paginated list of all instances
- Search by text fields
- Filter by validation status
- Sort by date, ID, status
"""
from django.views.generic import ListView
from django.db.models import Q

from ..models import CmsPrescriptionDrugEventInstance
from ..utils.wizard_config import DMMetadata


class InstanceListView(ListView):
    """
    List view for CmsPrescriptionDrugEvent instances.
    """
    model = CmsPrescriptionDrugEventInstance
    template_name = 'cms_prescription_drug_event/instance_list.html'
    context_object_name = 'instances'
    paginate_by = 25
    ordering = ['-created_at']

    def get_queryset(self):
        """Apply search and filters."""
        queryset = super().get_queryset()

        # Text search
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(instance_id__icontains=search) |
                Q(search_text__icontains=search)
            )

        # Validation status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(validation_status=status)

        # RDF sync status filter
        rdf_status = self.request.GET.get('rdf_status')
        if rdf_status:
            queryset = queryset.filter(rdf_sync_status=rdf_status)

        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['created_at', '-created_at', 'instance_id', '-instance_id',
                    'validation_status', '-validation_status']:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        """Add filter options to context."""
        context = super().get_context_data(**kwargs)
        context['dm_metadata'] = DMMetadata
        context['search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_rdf_status'] = self.request.GET.get('rdf_status', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        context['validation_choices'] = CmsPrescriptionDrugEventInstance.VALIDATION_STATUS_CHOICES
        context['rdf_status_choices'] = CmsPrescriptionDrugEventInstance.RDF_SYNC_STATUS_CHOICES
        return context

