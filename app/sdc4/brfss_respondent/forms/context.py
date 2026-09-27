
"""
Context Form (Step 1) for brfss_respondent wizard.

Handles party and participation fields:
- Subject (Party) - who the data is about
- Provider (Party) - who provided the data
- Participations (list of participants)

This step is conditional - only shown if the DM has any of these configured.

SDC4 Party Structure:
- label: Display name for the party
- details: Optional Cluster with party details
- external_ref: Optional XdLink(s) to external identity systems
"""
from django import forms
from django.forms import formset_factory

from ..utils.wizard_config import WizardStepConfig


class PartySubForm(forms.Form):
    """
    Sub-form for Party entry (used for subject/provider).

    Maps to SDC4 PartyType with:
    - party_name -> label element
    - party_id/party_id_scheme -> external_ref XdLink
    - party_type -> used for categorization
    """
    party_name = forms.CharField(
        label='Name',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Party name',
        })
    )

    party_type = forms.ChoiceField(
        label='Type',
        choices=[
            ('person', 'Person'),
            ('organization', 'Organization'),
            ('device', 'Device'),
            ('software', 'Software Agent'),
            ('other', 'Other'),
        ],
        initial='person',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    party_id = forms.CharField(
        label='Identifier',
        max_length=100,
        required=False,
        help_text='Optional external identifier (e.g., NPI, MRN, SSN)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'External ID (optional)',
        })
    )

    party_id_scheme = forms.CharField(
        label='ID Scheme',
        max_length=100,
        required=False,
        help_text='URI or name of the identification scheme',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., urn:oid:2.16.840.1.113883.4.6 (NPI)',
        })
    )

    external_ref_uri = forms.URLField(
        label='External Reference URI',
        required=False,
        help_text='URI linking to this party in an external system',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.org/parties/12345',
        })
    )


class ParticipationSubForm(forms.Form):
    """
    Sub-form for Participation entry.

    Maps to SDC4 Participation structure with:
    - participant (Party)
    - function (role/responsibility)
    - mode (how they participated)
    - time (when they participated)
    """
    participant_name = forms.CharField(
        label='Participant Name',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Participant name',
        })
    )

    function = forms.CharField(
        label='Function/Role',
        max_length=100,
        required=True,
        help_text='Function or role of this participant',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Witness, Reviewer, Transcriber',
        })
    )

    participation_mode = forms.ChoiceField(
        label='Mode',
        choices=[
            ('face-to-face', 'Face to Face'),
            ('telephone', 'Telephone'),
            ('videoconference', 'Video Conference'),
            ('electronic', 'Electronic/Written'),
            ('delegated', 'Delegated'),
            ('physical-presence', 'Physical Presence'),
        ],
        initial='face-to-face',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    participation_time = forms.DateTimeField(
        label='Participation Time',
        required=False,
        help_text='When this participation occurred',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
        })
    )

    participant_id = forms.CharField(
        label='Participant ID',
        max_length=100,
        required=False,
        help_text='Optional identifier for the participant',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'External ID (optional)',
        })
    )


# Formset for multiple participations
ParticipationFormSet = formset_factory(
    ParticipationSubForm,
    extra=0,  # Start with no extra forms - user adds as needed
    can_delete=True,
    max_num=10,
)


class ContextForm(forms.Form):
    """
    Step 1: Context Form.

    Collects information about parties involved:
    - Subject: who/what the data is about
    - Provider: who provided/recorded the data
    - Participations: other parties involved

    Maps to SDC4 DMType elements:
    - subject -> PartyType (who the data is about)
    - provider -> PartyType (who provided/recorded the data)
    - Participation (via formset) -> Participation elements
    """

    # ==========================================================================
    # Subject Party Fields (conditional - shown if HAS_SUBJECT)
    # ==========================================================================
    subject_name = forms.CharField(
        label='Subject Name',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Who or what this data is about',
        })
    )

    subject_type = forms.ChoiceField(
        label='Subject Type',
        choices=[
            ('person', 'Person'),
            ('organization', 'Organization'),
            ('device', 'Device'),
            ('specimen', 'Specimen'),
            ('location', 'Location'),
            ('other', 'Other'),
        ],
        initial='person',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    subject_id = forms.CharField(
        label='Subject ID',
        max_length=100,
        required=False,
        help_text='External identifier for the subject (e.g., MRN, SSN)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject identifier',
        })
    )

    subject_id_scheme = forms.CharField(
        label='Subject ID Scheme',
        max_length=100,
        required=False,
        help_text='Scheme or namespace for the identifier',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., urn:oid:2.16.840.1.113883.4.1',
        })
    )

    subject_external_ref = forms.URLField(
        label='Subject External Reference',
        required=False,
        help_text='URI to subject record in external system',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://...',
        })
    )

    # ==========================================================================
    # Provider Party Fields (conditional - shown if HAS_PROVIDER)
    # ==========================================================================
    provider_name = forms.CharField(
        label='Provider Name',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Who provided or recorded this data',
        })
    )

    provider_type = forms.ChoiceField(
        label='Provider Type',
        choices=[
            ('person', 'Person'),
            ('organization', 'Organization'),
            ('device', 'Device'),
            ('software', 'Software Agent'),
            ('other', 'Other'),
        ],
        initial='person',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    provider_id = forms.CharField(
        label='Provider ID',
        max_length=100,
        required=False,
        help_text='External identifier for the provider (e.g., NPI)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Provider identifier',
        })
    )

    provider_id_scheme = forms.CharField(
        label='Provider ID Scheme',
        max_length=100,
        required=False,
        help_text='Scheme or namespace for the identifier',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., urn:oid:2.16.840.1.113883.4.6 (NPI)',
        })
    )

    provider_external_ref = forms.URLField(
        label='Provider External Reference',
        required=False,
        help_text='URI to provider record in external system',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://...',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove subject fields if not configured
        if not WizardStepConfig.HAS_SUBJECT:
            subject_fields = [
                'subject_name', 'subject_type', 'subject_id',
                'subject_id_scheme', 'subject_external_ref'
            ]
            for field in subject_fields:
                if field in self.fields:
                    del self.fields[field]

        # Remove provider fields if not configured
        if not WizardStepConfig.HAS_PROVIDER:
            provider_fields = [
                'provider_name', 'provider_type', 'provider_id',
                'provider_id_scheme', 'provider_external_ref'
            ]
            for field in provider_fields:
                if field in self.fields:
                    del self.fields[field]

    def clean(self):
        """Validate that required party info is provided."""
        cleaned_data = super().clean()

        # If subject is configured and shown, name is required
        if WizardStepConfig.HAS_SUBJECT:
            if not cleaned_data.get('subject_name'):
                self.add_error('subject_name', 'Subject name is required')

        # If provider is configured and shown, name is required
        if WizardStepConfig.HAS_PROVIDER:
            if not cleaned_data.get('provider_name'):
                self.add_error('provider_name', 'Provider name is required')

        return cleaned_data

    def get_subject_data(self) -> dict:
        """Extract subject party data from cleaned form data."""
        if not WizardStepConfig.HAS_SUBJECT:
            return {}

        return {
            'name': self.cleaned_data.get('subject_name', ''),
            'type': self.cleaned_data.get('subject_type', 'person'),
            'id': self.cleaned_data.get('subject_id', ''),
            'id_scheme': self.cleaned_data.get('subject_id_scheme', ''),
            'external_ref': self.cleaned_data.get('subject_external_ref', ''),
        }

    def get_provider_data(self) -> dict:
        """Extract provider party data from cleaned form data."""
        if not WizardStepConfig.HAS_PROVIDER:
            return {}

        return {
            'name': self.cleaned_data.get('provider_name', ''),
            'type': self.cleaned_data.get('provider_type', 'person'),
            'id': self.cleaned_data.get('provider_id', ''),
            'id_scheme': self.cleaned_data.get('provider_id_scheme', ''),
            'external_ref': self.cleaned_data.get('provider_external_ref', ''),
        }

