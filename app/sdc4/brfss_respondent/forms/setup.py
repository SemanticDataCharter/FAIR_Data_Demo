
"""
Setup Form (Step 0) for brfss_respondent wizard.

Handles instance-level setup fields:
- Instance version
- Current state
- Protocol (if configured)
- Workflow (if configured)
"""
from django import forms

from ..utils.wizard_config import WizardStepConfig


class SetupForm(forms.Form):
    """
    Step 0: Instance Setup Form.

    Collects instance metadata that appears at the DM root level.
    """

    instance_version = forms.CharField(
        label='Instance Version',
        initial='1',
        max_length=20,
        help_text='Version number for this instance (e.g., 1, 1.1, 2.0)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
        })
    )

    current_state = forms.ChoiceField(
        label='Current State',
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('amended', 'Amended'),
            ('cancelled', 'Cancelled'),
        ],
        initial='draft',
        help_text='Current lifecycle state of this instance',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    # Conditional fields based on DM configuration
    protocol = forms.CharField(
        label='Protocol',
        required=False,
        max_length=500,
        help_text='Protocol identifier or reference',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter protocol reference',
        })
    )

    workflow_uri = forms.URLField(
        label='Workflow Link',
        required=False,
        help_text='URI reference to associated workflow',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://...',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove fields that aren't configured for this DM
        if not WizardStepConfig.HAS_PROTOCOL:
            del self.fields['protocol']

        if not WizardStepConfig.HAS_WORKFLOW:
            del self.fields['workflow_uri']

    def clean_instance_version(self):
        """Validate version format."""
        version = self.cleaned_data['instance_version']
        # Allow numeric versions like 1, 1.0, 1.0.1
        parts = version.split('.')
        for part in parts:
            if not part.isdigit():
                raise forms.ValidationError(
                    "Version must be numeric (e.g., 1, 1.0, 1.0.1)"
                )
        return version

