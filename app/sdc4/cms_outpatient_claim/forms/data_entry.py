
"""
Data Entry Form (Step 2) for cms_outpatient_claim wizard.

This is the main data entry step that handles the Cluster tree structure.
The form is dynamically generated based on the DM's component tree.

Each data type (XdString, XdBoolean, XdCount, etc.) has specific fields
and validation rules. Labels and constraints are read-only (from schema).
"""
from django import forms
from datetime import datetime, date, time
from decimal import Decimal, InvalidOperation
import json

from ..utils.wizard_config import FIELD_METADATA, COMPONENT_TREE


class DataEntryForm(forms.Form):
    """
    Step 2: Data Entry Form.

    Dynamically builds form fields from the DM's component tree.
    Each field corresponds to a data component (XdString, XdQuantity, etc.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._build_fields_from_tree()

    def _build_fields_from_tree(self):
        """
        Build form fields from the component tree.

        FIELD_METADATA contains information about each field:
        {
            'ct_id': {
                'label': str,
                'field_type': str,  # XdString, XdBoolean, etc.
                'required': bool,
                'constraints': {...},
                'help_text': str,
            }
        }
        """
        for ct_id, meta in FIELD_METADATA.items():
            # Support both 'type' and 'field_type' keys for backward compatibility
            field_type = meta.get('type') or meta.get('field_type', 'XdString')
            label = meta.get('label', ct_id)
            required = meta.get('required', False)
            help_text = meta.get('help_text', '')
            constraints = meta.get('constraints', {})

            # Create appropriate field based on type
            field = self._create_field_for_type(
                field_type=field_type,
                label=label,
                required=required,
                help_text=help_text,
                constraints=constraints,
                ct_id=ct_id,
            )

            if field:
                self.fields[ct_id] = field

    def _create_field_for_type(self, field_type, label, required, help_text, constraints, ct_id):
        """
        Create a Django form field for a given SDC4 type.

        Args:
            field_type: SDC4 type name (XdString, XdBoolean, etc.)
            label: Display label for the field
            required: Whether field is required
            help_text: Help text to display
            constraints: Type-specific constraints
            ct_id: Component type ID for the field name

        Returns:
            Django form field instance
        """
        common_attrs = {
            'label': label,
            'required': required,
            'help_text': help_text,
        }

        widget_class = 'form-control'

        if field_type == 'XdString':
            max_length = constraints.get('max_length', 500)
            min_length = constraints.get('min_length', 0)
            pattern = constraints.get('pattern')
            enumerations = constraints.get('enumerations', [])

            # If enumerations exist, render as Select widget
            if enumerations:
                choice_list = [(e, e) for e in enumerations]
                field = forms.ChoiceField(
                    **common_attrs,
                    choices=[('', '-- Select --')] + choice_list,
                    widget=forms.Select(attrs={
                        'class': 'form-select',
                        'data-ct-id': ct_id,
                    })
                )
            else:
                # Build widget attrs - only include pattern if it's a real value
                widget_attrs = {
                    'class': widget_class,
                    'data-ct-id': ct_id,
                }
                if pattern:
                    widget_attrs['pattern'] = pattern

                field = forms.CharField(
                    **common_attrs,
                    max_length=max_length,
                    min_length=min_length,
                    widget=forms.TextInput(attrs=widget_attrs)
                )

        elif field_type == 'XdBoolean':
            field = forms.BooleanField(
                **common_attrs,
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                    'data-ct-id': ct_id,
                })
            )

        elif field_type == 'XdCount':
            min_val = constraints.get('min_inclusive')
            max_val = constraints.get('max_inclusive')

            field = forms.IntegerField(
                **common_attrs,
                min_value=min_val,
                max_value=max_val,
                widget=forms.NumberInput(attrs={
                    'class': widget_class,
                    'data-ct-id': ct_id,
                })
            )

        elif field_type == 'XdQuantity':
            min_val = constraints.get('min_inclusive')
            max_val = constraints.get('max_inclusive')
            decimal_places = constraints.get('decimal_places', 4)

            field = forms.DecimalField(
                **common_attrs,
                min_value=Decimal(str(min_val)) if min_val is not None else None,
                max_value=Decimal(str(max_val)) if max_val is not None else None,
                decimal_places=decimal_places,
                widget=forms.NumberInput(attrs={
                    'class': widget_class,
                    'step': 'any',
                    'data-ct-id': ct_id,
                })
            )

        elif field_type == 'XdFloat':
            min_val = constraints.get('min_inclusive')
            max_val = constraints.get('max_inclusive')

            field = forms.FloatField(
                **common_attrs,
                min_value=min_val,
                max_value=max_val,
                widget=forms.NumberInput(attrs={
                    'class': widget_class,
                    'step': 'any',
                    'data-ct-id': ct_id,
                })
            )

        elif field_type == 'XdDouble':
            min_val = constraints.get('min_inclusive')
            max_val = constraints.get('max_inclusive')

            field = forms.FloatField(
                **common_attrs,
                min_value=min_val,
                max_value=max_val,
                widget=forms.NumberInput(attrs={
                    'class': widget_class,
                    'step': 'any',
                    'data-ct-id': ct_id,
                })
            )

        elif field_type == 'XdToken':
            enumerations = constraints.get('enumerations', [])
            if enumerations:
                choice_list = [(e, e) for e in enumerations]
                field = forms.ChoiceField(
                    **common_attrs,
                    choices=[('', '-- Select --')] + choice_list,
                    widget=forms.Select(attrs={
                        'class': 'form-select',
                        'data-ct-id': ct_id,
                    })
                )
            else:
                field = forms.CharField(
                    **common_attrs,
                    widget=forms.TextInput(attrs={
                        'class': widget_class,
                        'data-ct-id': ct_id,
                    })
                )

        elif field_type == 'XdTemporal':
            # Determine temporal subtype from constraints
            temporal_type = constraints.get('temporal_type', 'date')

            if temporal_type == 'date':
                field = forms.DateField(
                    **common_attrs,
                    widget=forms.DateInput(attrs={
                        'class': widget_class,
                        'type': 'date',
                        'data-ct-id': ct_id,
                    })
                )
            elif temporal_type == 'time':
                field = forms.TimeField(
                    **common_attrs,
                    widget=forms.TimeInput(attrs={
                        'class': widget_class,
                        'type': 'time',
                        'data-ct-id': ct_id,
                    })
                )
            elif temporal_type == 'datetime':
                field = forms.DateTimeField(
                    **common_attrs,
                    widget=forms.DateTimeInput(attrs={
                        'class': widget_class,
                        'type': 'datetime-local',
                        'data-ct-id': ct_id,
                    })
                )
            else:
                # Default to date
                field = forms.DateField(
                    **common_attrs,
                    widget=forms.DateInput(attrs={
                        'class': widget_class,
                        'type': 'date',
                        'data-ct-id': ct_id,
                    })
                )

        elif field_type == 'XdOrdinal':
            # Ordinal has predefined choices
            choices = constraints.get('choices', [])
            choice_list = [(str(i), c) for i, c in enumerate(choices)]

            field = forms.ChoiceField(
                **common_attrs,
                choices=[('', '-- Select --')] + choice_list,
                widget=forms.Select(attrs={
                    'class': 'form-select',
                    'data-ct-id': ct_id,
                })
            )

        elif field_type == 'XdLink':
            field = forms.URLField(
                **common_attrs,
                widget=forms.URLInput(attrs={
                    'class': widget_class,
                    'placeholder': 'https://...',
                    'data-ct-id': ct_id,
                })
            )

        elif field_type == 'XdFile':
            # File handling - store as base64 or file reference
            field = forms.FileField(
                **common_attrs,
                widget=forms.FileInput(attrs={
                    'class': widget_class,
                    'data-ct-id': ct_id,
                })
            )

        elif field_type == 'XdInterval':
            # Interval needs two values - handled as JSON string for now
            field = forms.CharField(
                **common_attrs,
                help_text=help_text or 'Enter as JSON: {"lower": value, "upper": value}',
                widget=forms.Textarea(attrs={
                    'class': widget_class,
                    'rows': 2,
                    'data-ct-id': ct_id,
                })
            )

        else:
            # Default to text field for unknown types
            field = forms.CharField(
                **common_attrs,
                widget=forms.TextInput(attrs={
                    'class': widget_class,
                    'data-ct-id': ct_id,
                })
            )

        return field

    def clean(self):
        """
        Validate all fields and apply cross-field validation.
        """
        cleaned_data = super().clean()

        # Convert values to appropriate types for XML generation
        for ct_id, value in list(cleaned_data.items()):
            meta = FIELD_METADATA.get(ct_id, {})
            field_type = meta.get('type') or meta.get('field_type', 'XdString')

            # Convert datetime objects to ISO strings
            if isinstance(value, datetime):
                cleaned_data[ct_id] = value.isoformat()
            elif isinstance(value, date):
                cleaned_data[ct_id] = value.isoformat()
            elif isinstance(value, time):
                cleaned_data[ct_id] = value.isoformat()
            elif isinstance(value, Decimal):
                cleaned_data[ct_id] = str(value)

        return cleaned_data

