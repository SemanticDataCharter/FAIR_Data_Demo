"""
Wizard Views for cms_beneficiary.

Multi-step wizard for SDC4 data entry with:
- Step 0: Instance Setup (always shown)
- Step 1: Context - Subject/Provider/Participations (conditional)
- Step 2: Data Entry - Cluster tree (always shown)
- Step 3: Review & Attestation (conditional)
"""
from django.views import View
from django.views.generic import TemplateView, FormView
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction
from django.utils import timezone
import logging

from ..models import CmsBeneficiaryInstance
from ..utils.wizard_state import WizardState
from ..utils.wizard_config import WizardStepConfig, DMMetadata
from ..utils.xml_builder import XMLBuilder
from ..utils.sdc_validator import SDCValidator
from ..utils.json_extractor import JSONExtractor
from ..utils.json_instance_generator import JSONInstanceGenerator
from ..utils.rdf_extractor import RDFExtractor
from sdc4_shared.utils.triplestore import get_triplestore_client
from pathlib import Path

logger = logging.getLogger(__name__)


class WizardStartView(View):
    """
    Entry point for the wizard - initializes state and redirects to first step.
    """

    def get(self, request):
        """Start a new wizard session."""
        # Clear any existing wizard state
        wizard = WizardState(request)
        wizard.clear()

        # Generate instance ID upfront
        wizard.generate_instance_id()

        # Redirect to first step
        first_step = WizardStepConfig.get_visible_steps()[0]
        return redirect('cms_beneficiary:wizard-step', step=first_step)


class WizardStepView(View):
    """
    Handles individual wizard steps.

    Each step has its own template and form handling logic.
    """

    def get_template_name(self, step: int) -> str:
        """Get template name for a step."""
        return f'cms_beneficiary/wizard/step_{step}.html'

    def get_form_class(self, step: int):
        """Get form class for a step."""
        from ..forms import (
            SetupForm,
            ContextForm,
            DataEntryForm,
            ReviewForm,
        )
        form_map = {
            0: SetupForm,
            1: ContextForm,
            2: DataEntryForm,
            3: ReviewForm,
        }
        return form_map.get(step)

    def get_context_data(self, request, step: int, form=None) -> dict:
        """Build context data for template."""
        wizard = WizardState(request)
        visible_steps = WizardStepConfig.get_visible_steps()
        step_names = WizardStepConfig.get_step_names()

        context = {
            'step': step,
            'step_name': step_names.get(step, f'Step {step}'),
            'visible_steps': visible_steps,
            'step_names': step_names,
            'is_first_step': WizardStepConfig.is_first_step(step),
            'is_last_step': WizardStepConfig.is_last_step(step),
            'prev_step': WizardStepConfig.get_prev_step(step),
            'next_step': WizardStepConfig.get_next_step(step),
            'total_steps': len(visible_steps),
            'current_step_index': visible_steps.index(step) + 1 if step in visible_steps else 0,
            'dm_metadata': DMMetadata,
            'wizard_config': WizardStepConfig,
            'instance_id': wizard.get_instance_id(),
            'form': form,
        }

        # Add step-specific context
        if step == 0:
            context.update(self._get_setup_context(wizard))
        elif step == 1:
            context.update(self._get_context_context(wizard))
        elif step == 2:
            context.update(self._get_data_entry_context(wizard))
        elif step == 3:
            context.update(self._get_review_context(wizard))

        return context

    def _get_setup_context(self, wizard: WizardState) -> dict:
        """Context for Step 0: Setup."""
        return {
            'has_protocol': WizardStepConfig.HAS_PROTOCOL,
            'has_workflow': WizardStepConfig.HAS_WORKFLOW,
        }

    def _get_context_context(self, wizard: WizardState) -> dict:
        """Context for Step 1: Context (Subject/Provider/Participations)."""
        return {
            'has_subject': WizardStepConfig.HAS_SUBJECT,
            'has_provider': WizardStepConfig.HAS_PROVIDER,
            'has_participations': WizardStepConfig.HAS_PARTICIPATIONS,
        }

    def _get_data_entry_context(self, wizard: WizardState) -> dict:
        """Context for Step 2: Data Entry."""
        from ..utils.wizard_config import COMPONENT_TREE, FIELD_METADATA
        return {
            'component_tree': COMPONENT_TREE,
            'field_metadata': FIELD_METADATA,
        }

    def _get_review_context(self, wizard: WizardState) -> dict:
        """Context for Step 3: Review & Attestation."""
        # Build preview XML
        try:
            preview_xml = wizard.build_xml()
        except Exception as e:
            logger.error(f"Error building preview XML: {e}")
            preview_xml = f"<!-- Error building preview: {e} -->"

        return {
            'has_audit': WizardStepConfig.HAS_AUDIT,
            'has_attestation': WizardStepConfig.HAS_ATTESTATION,
            'preview_xml': preview_xml,
            'all_data': wizard.get_all_data(),
        }

    def get(self, request, step: int):
        """Display wizard step."""
        wizard = WizardState(request)

        # Validate step is visible
        if step not in WizardStepConfig.get_visible_steps():
            messages.error(request, f"Step {step} is not available for this data model.")
            return redirect('cms_beneficiary:wizard-start')

        # Check if user can access this step
        if not wizard.can_proceed_to_step(step):
            messages.warning(request, "Please complete the previous steps first.")
            return redirect('cms_beneficiary:wizard-step',
                          step=WizardStepConfig.get_visible_steps()[0])

        # Get form with any existing data
        form_class = self.get_form_class(step)
        initial_data = wizard.get_step_data(step)
        form = form_class(initial=initial_data) if form_class else None

        context = self.get_context_data(request, step, form)
        return render(request, self.get_template_name(step), context)

    def post(self, request, step: int):
        """Handle form submission for a step."""
        wizard = WizardState(request)

        # Get and validate form
        form_class = self.get_form_class(step)
        form = form_class(request.POST) if form_class else None

        if form and not form.is_valid():
            context = self.get_context_data(request, step, form)
            return render(request, self.get_template_name(step), context)

        # Save step data
        if form:
            step_data = form.cleaned_data.copy()

            # For Step 1 (Context), also capture dynamic participation fields from POST
            if step == 1 and WizardStepConfig.HAS_PARTICIPATIONS:
                step_data.update(self._extract_participation_data(request.POST))

            # For Step 2 (Data Entry), also capture EV and metadata fields from POST
            if step == 2:
                step_data.update(self._extract_component_metadata(request.POST))

            wizard.save_step_data(step, step_data)

        # Check which button was pressed
        if 'prev' in request.POST:
            prev_step = WizardStepConfig.get_prev_step(step)
            if prev_step >= 0:
                return redirect('cms_beneficiary:wizard-step', step=prev_step)

        if 'save_draft' in request.POST:
            messages.info(request, "Draft saved. You can continue later.")
            return redirect('cms_beneficiary:instance-list')

        # Move to next step or complete
        next_step = WizardStepConfig.get_next_step(step)
        if next_step >= 0:
            return redirect('cms_beneficiary:wizard-step', step=next_step)
        else:
            # This was the last step - complete the wizard
            return redirect('cms_beneficiary:wizard-complete')

    def _extract_participation_data(self, post_data) -> dict:
        """
        Extract dynamically added participation fields from POST data.

        Participations are submitted as:
        - participation_0_name, participation_0_function, participation_0_mode, etc.
        """
        participation_data = {}
        idx = 0

        while True:
            name_key = f'participation_{idx}_name'
            if name_key not in post_data:
                break

            # Extract all fields for this participation
            participation_data[name_key] = post_data.get(name_key, '')
            participation_data[f'participation_{idx}_function'] = post_data.get(f'participation_{idx}_function', '')
            participation_data[f'participation_{idx}_mode'] = post_data.get(f'participation_{idx}_mode', 'face-to-face')
            participation_data[f'participation_{idx}_time'] = post_data.get(f'participation_{idx}_time', '')
            participation_data[f'participation_{idx}_id'] = post_data.get(f'participation_{idx}_id', '')

            idx += 1

        return participation_data

    def _extract_component_metadata(self, post_data) -> dict:
        """
        Extract EV and metadata fields from POST data for data entry components.

        These are submitted as:
        - {ct_id}_ev - Exceptional Value selection
        - {ct_id}_vtb - Valid Time Begin
        - {ct_id}_vte - Valid Time End
        - {ct_id}_tr - Time Recorded
        - {ct_id}_latitude - Latitude
        - {ct_id}_longitude - Longitude
        """
        metadata = {}

        for key, value in post_data.items():
            # Skip CSRF and standard form fields
            if key.startswith('csrf') or key in ('prev', 'next', 'save_draft'):
                continue

            # Capture EV fields
            if key.endswith('_ev'):
                metadata[key] = value

            # Capture temporal metadata fields
            if any(key.endswith(suffix) for suffix in ['_vtb', '_vte', '_tr', '_modified']):
                metadata[key] = value

            # Capture location fields
            if key.endswith('_latitude') or key.endswith('_longitude'):
                metadata[key] = value

        return metadata


class WizardCompleteView(View):
    """
    Completes the wizard - builds XML, validates, saves, and extracts RDF.
    """

    def get(self, request):
        """
        Complete the wizard and create the instance.
        """
        wizard = WizardState(request)

        try:
            # Build XML from wizard data
            instance_id = wizard.get_instance_id()
            xml_content = wizard.build_xml()

            # Validate XML against XSD
            dm_ct_id = DMMetadata.CT_ID
            xsd_path = Path(__file__).parent.parent / 'mediafiles' / 'dmlib' / f'dm-{dm_ct_id}.xsd'

            validator = SDCValidator(str(xsd_path))
            result = validator.validate(xml_content)

            validation_status = 'valid'
            validation_errors = {}
            auto_corrected_fields = []

            if not result.is_valid:
                # Auto-correct with Exceptional Values
                xml_content, auto_corrected_fields = validator.auto_correct_with_evs(
                    xml_content,
                    result.errors
                )

                # Update instance_id with EV marker
                if instance_id.startswith('i-') and not instance_id.startswith('i-ev-'):
                    base_cuid = instance_id[2:]
                    instance_id = f'i-ev-{base_cuid}'
                    xml_content = xml_content.replace(
                        wizard.get_instance_id(),
                        instance_id
                    )

                validation_status = 'valid_with_ev'
                validation_errors = result.errors

            # Extract JSON for queries
            from ..utils.wizard_config import FIELD_METADATA
            json_extractor = JSONExtractor(field_metadata=FIELD_METADATA)
            extracted = json_extractor.extract(xml_content)
            json_data = extracted.get('fields', {})
            search_text = extracted.get('search_text', '')

            # Generate complete JSON instance
            json_generator = JSONInstanceGenerator(field_metadata=FIELD_METADATA)
            json_instance = json_generator.generate(xml_content)

            # Create database instance
            with transaction.atomic():
                instance = CmsBeneficiaryInstance(
                    instance_id=instance_id,
                    xml_content=xml_content,
                    json_instance=json_instance,
                    search_text=search_text,
                    validation_status=validation_status,
                    validation_errors=validation_errors,
                    auto_corrected_fields=auto_corrected_fields,
                )
                instance.save()

            # Extract and upload RDF (outside transaction)
            try:
                self._upload_rdf(instance, xml_content)
            except Exception as rdf_error:
                logger.error(f"RDF upload failed: {rdf_error}")
                instance.rdf_sync_status = 'failed'
                instance.save(update_fields=['rdf_sync_status'])

            # Clear wizard state
            wizard.clear()

            # Success message
            if validation_status == 'valid_with_ev':
                messages.warning(
                    request,
                    f"Instance created with Exceptional Values applied to: {', '.join(auto_corrected_fields)}"
                )
            else:
                messages.success(request, "Instance created successfully!")

            return redirect('cms_beneficiary:instance-detail', pk=instance_id)

        except Exception as e:
            logger.exception(f"Error completing wizard: {e}")
            messages.error(request, f"Error creating instance: {e}")
            return redirect('cms_beneficiary:wizard-step',
                          step=WizardStepConfig.get_visible_steps()[-1])

    def _upload_rdf(self, instance, xml_content: str):
        """Extract RDF and upload to triplestore."""
        from ..utils.wizard_config import FIELD_METADATA

        triplestore = get_triplestore_client()
        if triplestore is None:
            instance.rdf_sync_status = 'disabled'
            instance.save(update_fields=['rdf_sync_status'])
            return

        rdf_extractor = RDFExtractor(
            dm_ct_id=DMMetadata.CT_ID,
            dm_label=DMMetadata.TITLE,
            field_metadata=FIELD_METADATA,
        )

        rdf_content = rdf_extractor.extract(
            xml_content=xml_content,
            instance_id=instance.instance_id,
            validation_status=instance.validation_status,
            auto_corrected_fields=instance.auto_corrected_fields,
        )

        if rdf_content:
            graph_uri = triplestore.get_graph_uri(
                instance.instance_id,
                DMMetadata.CT_ID
            )

            if triplestore.upload_graph(rdf_content, graph_uri):
                instance.fuseki_graph_uri = graph_uri
                instance.rdf_uploaded_at = timezone.now()
                instance.rdf_sync_status = 'synced'
            else:
                instance.rdf_sync_status = 'failed'

            instance.save(update_fields=[
                'fuseki_graph_uri',
                'rdf_uploaded_at',
                'rdf_sync_status'
            ])
