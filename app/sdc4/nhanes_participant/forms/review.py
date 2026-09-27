
"""
Review Form (Step 3) for nhanes_participant wizard.

Handles review, audit, and attestation:
- Preview of generated XML
- Audit information capture (system, location, committer, timestamp)
- Attestation signature/confirmation (attester, reason, proof)

This step is conditional - only shown if DM has audit or attestation configured.

SDC4 Audit Structure:
- system_id: Identifier of the recording system
- time_committed: When the data was committed
- change_type: Type of change (creation, amendment, etc.)
- description: Optional description of the commit
- committer: Party who committed the data

SDC4 Attestation Structure:
- attested_view: What view was attested (full, partial)
- proof: Proof/signature of attestation
- reason: Reason for attestation
- is_pending: Whether attestation is still pending
- attester: Party who attested
"""
from django import forms
from datetime import datetime

from ..utils.wizard_config import WizardStepConfig


class AuditSubForm(forms.Form):
    """
    Sub-form for Audit entry.

    Maps to SDC4 AuditType with:
    - system_id: Identifier of the system recording this
    - time_committed: When data was committed
    - change_type: Type of change
    - committer: Party information
    """
    audit_system = forms.CharField(
        label='System ID',
        max_length=200,
        required=True,
        help_text='Identifier of the system recording this audit',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'System identifier',
        })
    )

    audit_change_type = forms.ChoiceField(
        label='Change Type',
        choices=[
            ('creation', 'Creation - New record'),
            ('amendment', 'Amendment - Modified existing'),
            ('correction', 'Correction - Fixed errors'),
            ('deletion', 'Deletion - Marked for removal'),
            ('attestation', 'Attestation - Verified/signed'),
            ('synthesis', 'Synthesis - Aggregated from multiple sources'),
        ],
        initial='creation',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    audit_location = forms.CharField(
        label='Location',
        max_length=200,
        required=False,
        help_text='Physical or logical location where data was recorded',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location (optional)',
        })
    )

    audit_time_committed = forms.DateTimeField(
        label='Time Committed',
        required=True,
        help_text='When this data was committed',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
        })
    )

    audit_committer_name = forms.CharField(
        label='Committer Name',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name of person committing',
        })
    )

    audit_description = forms.CharField(
        label='Description',
        max_length=500,
        required=False,
        help_text='Optional description of this audit entry',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Describe the changes made (optional)',
        })
    )


class AttestationSubForm(forms.Form):
    """
    Sub-form for Attestation.

    Maps to SDC4 AttestationType with:
    - attested_view: What was attested
    - proof: Signature or proof
    - reason: Why attestation was made
    - is_pending: Pending status
    - attester: Party who attested
    """
    attestation_view = forms.ChoiceField(
        label='Attested View',
        choices=[
            ('full', 'Full Record - Entire content verified'),
            ('partial', 'Partial Record - Selected portions verified'),
            ('amended', 'Amended Record - Corrections applied'),
        ],
        initial='full',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    attestation_reason = forms.CharField(
        label='Reason',
        max_length=500,
        required=False,
        help_text='Reason for attestation (optional)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for attestation',
        })
    )

    attestation_proof = forms.CharField(
        label='Proof/Signature',
        max_length=500,
        required=False,
        help_text='Digital signature or proof of attestation',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digital signature',
        })
    )

    attester_name = forms.CharField(
        label='Attester Name',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name of attester',
        })
    )

    attestation_time = forms.DateTimeField(
        label='Attestation Time',
        required=True,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
        })
    )

    is_pending = forms.BooleanField(
        label='Attestation Pending',
        required=False,
        help_text='Check if attestation is pending review',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )


class ReviewForm(forms.Form):
    """
    Step 3: Review & Attestation Form.

    Allows user to:
    - Review the generated XML preview
    - Add audit information (if configured)
    - Provide attestation (if configured)
    - Confirm submission

    Maps to SDC4 elements:
    - audit -> Audit elements (M2M on DM)
    - attestation -> Attestation element
    """

    # Confirmation checkbox (always shown)
    confirm_submission = forms.BooleanField(
        label='I confirm this data is accurate and ready for submission',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    # ==========================================================================
    # Audit fields (conditional - shown if HAS_AUDIT)
    # ==========================================================================
    audit_system = forms.CharField(
        label='System ID',
        max_length=200,
        required=False,
        help_text='Identifier of the recording system',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'System identifier',
        })
    )

    audit_change_type = forms.ChoiceField(
        label='Change Type',
        choices=[
            ('creation', 'Creation'),
            ('amendment', 'Amendment'),
            ('correction', 'Correction'),
            ('synthesis', 'Synthesis'),
        ],
        initial='creation',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    audit_location = forms.CharField(
        label='Location',
        max_length=200,
        required=False,
        help_text='Physical or logical location',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location',
        })
    )

    audit_committer = forms.CharField(
        label='Committer',
        max_length=200,
        required=False,
        help_text='Name of person committing this data',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Committer name',
        })
    )

    audit_description = forms.CharField(
        label='Description',
        max_length=500,
        required=False,
        help_text='Optional description of changes',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Describe the changes (optional)',
        })
    )

    # ==========================================================================
    # Attestation fields (conditional - shown if HAS_ATTESTATION)
    # ==========================================================================
    attestation_view = forms.ChoiceField(
        label='Attested View',
        choices=[
            ('full', 'Full Record'),
            ('partial', 'Partial Record'),
            ('amended', 'Amended Record'),
        ],
        initial='full',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    attester_name = forms.CharField(
        label='Attester Name',
        max_length=200,
        required=False,
        help_text='Name of person attesting to this data',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Attester name',
        })
    )

    attestation_reason = forms.CharField(
        label='Reason',
        max_length=500,
        required=False,
        help_text='Reason for attestation',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for attestation (optional)',
        })
    )

    attestation_proof = forms.CharField(
        label='Digital Signature',
        max_length=500,
        required=False,
        help_text='Digital signature or proof of attestation',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digital signature or proof',
        })
    )

    attestation_pending = forms.BooleanField(
        label='Attestation Pending',
        required=False,
        help_text='Check if attestation is still pending review',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove audit fields if not configured
        if not WizardStepConfig.HAS_AUDIT:
            audit_fields = [
                'audit_system', 'audit_change_type', 'audit_location',
                'audit_committer', 'audit_description'
            ]
            for field in audit_fields:
                if field in self.fields:
                    del self.fields[field]

        # Remove attestation fields if not configured
        if not WizardStepConfig.HAS_ATTESTATION:
            attestation_fields = [
                'attestation_view', 'attester_name', 'attestation_reason',
                'attestation_proof', 'attestation_pending'
            ]
            for field in attestation_fields:
                if field in self.fields:
                    del self.fields[field]

    def clean(self):
        """Validate review form."""
        cleaned_data = super().clean()

        # Require audit fields if audit is enabled
        if WizardStepConfig.HAS_AUDIT:
            if not cleaned_data.get('audit_system'):
                self.add_error('audit_system', 'System ID is required for audit')
            if not cleaned_data.get('audit_committer'):
                self.add_error('audit_committer', 'Committer name is required for audit')

        # Require attestation fields if attestation is enabled
        if WizardStepConfig.HAS_ATTESTATION:
            if not cleaned_data.get('attester_name'):
                self.add_error('attester_name', 'Attester name is required')

        return cleaned_data

    def get_audit_data(self) -> dict:
        """Extract audit data from cleaned form data."""
        if not WizardStepConfig.HAS_AUDIT:
            return {}

        return {
            'system': self.cleaned_data.get('audit_system', ''),
            'change_type': self.cleaned_data.get('audit_change_type', 'creation'),
            'location': self.cleaned_data.get('audit_location', ''),
            'committer': self.cleaned_data.get('audit_committer', ''),
            'description': self.cleaned_data.get('audit_description', ''),
        }

    def get_attestation_data(self) -> dict:
        """Extract attestation data from cleaned form data."""
        if not WizardStepConfig.HAS_ATTESTATION:
            return {}

        return {
            'view': self.cleaned_data.get('attestation_view', 'full'),
            'attester': self.cleaned_data.get('attester_name', ''),
            'reason': self.cleaned_data.get('attestation_reason', ''),
            'proof': self.cleaned_data.get('attestation_proof', ''),
            'is_pending': self.cleaned_data.get('attestation_pending', False),
        }

