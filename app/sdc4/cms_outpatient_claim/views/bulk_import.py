"""
Bulk Import and Template Download views for cms_outpatient_claim.
"""
import tempfile
import logging
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, Http404
from django.views import View
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from ..forms.bulk_import import BulkImportForm
from ..models import CmsOutpatientClaimInstance
from ..utils.bulk_import import BulkImportProcessor
from ..utils.wizard_config import DMMetadata, FIELD_METADATA

logger = logging.getLogger(__name__)


class BulkImportView(FormView):
    """Import XML instances from a ZIP archive or server directory."""

    template_name = 'cms_outpatient_claim/bulk_import.html'
    form_class = BulkImportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dm_metadata'] = DMMetadata
        return context

    def form_valid(self, form):
        source = form.cleaned_data['import_source']

        # Locate the XSD schema
        xsd_path = self._find_xsd_path()
        if not xsd_path:
            form.add_error(None, 'XSD schema file not found. Cannot validate imports.')
            return self.form_invalid(form)

        processor = BulkImportProcessor(
            model_class=CmsOutpatientClaimInstance,
            xsd_path=xsd_path,
            dm_ct_id=CmsOutpatientClaimInstance.DM_CT_ID,
            dm_label=CmsOutpatientClaimInstance.DM_LABEL,
            field_metadata=FIELD_METADATA,
        )

        if source == 'zip':
            zip_file = form.cleaned_data['zip_file']
            # Save uploaded file to temp location
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                for chunk in zip_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            result = processor.process_zipfile(tmp_path)
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
        else:
            directory_path = form.cleaned_data['directory_path']
            result = processor.process_directory(directory_path)

        # Render results
        context = self.get_context_data(form=form)
        context['import_result'] = result
        return self.render_to_response(context)

    def _find_xsd_path(self):
        """Find the XSD schema file in dmlib."""
        dmlib_dir = Path(settings.MEDIA_ROOT) / 'dmlib'
        ct_id = CmsOutpatientClaimInstance.DM_CT_ID
        xsd_pattern = f"dm-{ct_id}.xsd"
        candidates = list(dmlib_dir.glob(xsd_pattern))
        if candidates:
            return candidates[0]
        # Fallback: any XSD in dmlib matching the ct_id
        for xsd_file in dmlib_dir.glob('*.xsd'):
            if ct_id in xsd_file.name:
                return xsd_file
        return None


class TemplateDownloadView(View):
    """Download the dm-*.xml template from dmlib."""

    def get(self, request, *args, **kwargs):
        dmlib_dir = Path(settings.MEDIA_ROOT) / 'dmlib'
        ct_id = CmsOutpatientClaimInstance.DM_CT_ID
        xml_pattern = f"dm-{ct_id}.xml"
        candidates = list(dmlib_dir.glob(xml_pattern))
        if not candidates:
            raise Http404('XML template not found in dmlib.')

        template_path = candidates[0]
        content = template_path.read_text(encoding='utf-8')
        response = HttpResponse(content, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{template_path.name}"'
        return response
