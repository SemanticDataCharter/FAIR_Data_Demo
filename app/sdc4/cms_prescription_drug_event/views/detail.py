
"""
Detail View for cms_prescription_drug_event instances.

Provides:
- XML content display with syntax highlighting
- JSON instance display
- Validation status and errors
- RDF sync status
- Download options (XML, JSON)
"""
from django.views.generic import DetailView
from django.http import HttpResponse, JsonResponse
from django.views import View
import json

from ..models import CmsPrescriptionDrugEventInstance
from ..utils.wizard_config import DMMetadata


class InstanceDetailView(DetailView):
    """
    Detail view for a single CmsPrescriptionDrugEvent instance.
    """
    model = CmsPrescriptionDrugEventInstance
    template_name = 'cms_prescription_drug_event/instance_detail.html'
    context_object_name = 'instance'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        """Add metadata and formatted content to context."""
        context = super().get_context_data(**kwargs)
        instance = self.object

        context['dm_metadata'] = DMMetadata

        # Format XML for display (with indentation preserved)
        context['xml_display'] = instance.xml_content

        # Format JSON for display
        try:
            context['json_display'] = json.dumps(
                instance.json_instance,
                indent=2,
                ensure_ascii=False
            )
        except (TypeError, ValueError):
            context['json_display'] = str(instance.json_instance)

        # Validation info
        context['validation_errors_display'] = json.dumps(
            instance.validation_errors,
            indent=2
        ) if instance.validation_errors else None

        context['auto_corrected_display'] = instance.auto_corrected_fields

        return context


class InstanceDownloadXMLView(View):
    """
    Download instance XML content.
    """

    def get(self, request, pk):
        """Return XML content as downloadable file."""
        try:
            instance = CmsPrescriptionDrugEventInstance.objects.get(pk=pk)
        except CmsPrescriptionDrugEventInstance.DoesNotExist:
            return HttpResponse("Instance not found", status=404)

        response = HttpResponse(
            instance.xml_content,
            content_type='application/xml'
        )
        response['Content-Disposition'] = f'attachment; filename="{pk}.xml"'
        return response


class InstanceDownloadJSONView(View):
    """
    Download instance JSON content.
    """

    def get(self, request, pk):
        """Return JSON content as downloadable file."""
        try:
            instance = CmsPrescriptionDrugEventInstance.objects.get(pk=pk)
        except CmsPrescriptionDrugEventInstance.DoesNotExist:
            return JsonResponse({"error": "Instance not found"}, status=404)

        response = HttpResponse(
            json.dumps(instance.json_instance, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{pk}.json"'
        return response


class InstanceDeleteView(View):
    """
    Delete an instance (with RDF cleanup).
    """

    def post(self, request, pk):
        """Delete instance and its RDF graph."""
        from django.shortcuts import redirect
        from django.contrib import messages
        from sdc4_shared.utils.triplestore import get_triplestore_client

        try:
            instance = CmsPrescriptionDrugEventInstance.objects.get(pk=pk)
        except CmsPrescriptionDrugEventInstance.DoesNotExist:
            messages.error(request, "Instance not found")
            return redirect('cms_prescription_drug_event:instance-list')

        # Delete RDF graph if exists
        if instance.fuseki_graph_uri:
            try:
                triplestore = get_triplestore_client()
                if triplestore:
                    triplestore.delete_graph(instance.fuseki_graph_uri)
            except Exception as e:
                messages.warning(request, f"Could not delete RDF graph: {e}")

        # Delete instance
        instance_id = instance.instance_id
        instance.delete()

        messages.success(request, f"Instance {instance_id} deleted successfully")
        return redirect('cms_prescription_drug_event:instance-list')

