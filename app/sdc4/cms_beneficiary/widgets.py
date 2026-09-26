"""
Custom widgets for SDC application.
"""
from django import forms
from django.forms.widgets import MultiWidget, Select, TextInput, DateTimeInput

# Standard SDC4 Exceptional Values (from sdc4.xsd substitution group)
# These are the actual EV element names used in XML output
EXCEPTIONAL_VALUE_CHOICES = [
    ('', '---'),  # Empty choice
    ('NI', 'No Information'),
    ('MSK', 'Masked'),
    ('INV', 'Invalid'),
    ('DER', 'Derived'),
    ('UNC', 'Unencoded'),
    ('OTH', 'Other'),
    ('NINF', 'Negative Infinity'),
    ('PINF', 'Positive Infinity'),
    ('ASKR', 'Asked and Refused'),
    ('NASK', 'Not Asked'),
    ('NAV', 'Not Available'),
    ('NA', 'Not Applicable'),
    ('TRC', 'Trace'),
    ('ASKU', 'Asked but Unknown'),
    ('UNK', 'Unknown'),
    ('QS', 'Sufficient Quantity'),
]

class SDCComponentWidget(MultiWidget):
    """
    Enhanced SDC Component Widget with collapsible metadata section.

    Renders:
    1. Primary area:
       - Value input field
       - Units dropdown (if is_quantified - for XdQuantity, XdCount, etc.)
    2. Collapsible metadata section containing:
       - Exceptional Value (EV) selector (if ev_allowed)
       - Valid Time Begin (VTB) (if vtb_allowed or vtb_required)
       - Valid Time End (VTE) (if vte_allowed or vte_required)
       - Latitude (if location_allowed or location_required)
       - Longitude (if location_allowed or location_required)
    """
    template_name = 'cms_beneficiary/widgets/sdc_component_widget.html'

    def __init__(self, primary_widget, metadata_config=None, attrs=None):
        """
        Args:
            primary_widget: The main data input widget
            metadata_config: Dict with keys like:
                - is_quantified: bool (for XdQuantity, XdCount, XdOrdinal)
                - units_choices: list of tuples for dropdown options
                - units_required: bool
                - ev_allowed: bool
                - vtb_allowed: bool
                - vtb_required: bool
                - vte_allowed: bool
                - vte_required: bool
                - location_allowed: bool
                - location_required: bool
        """
        self.metadata_config = metadata_config or {}

        # Build widget list: [primary, units, ev, vtb, vte, lat, lon]
        widgets = [primary_widget]

        # Units widget (for quantified types) - in PRIMARY area
        if self.metadata_config.get('is_quantified'):
            units_choices = self.metadata_config.get('units_choices', [])
            widgets.append(Select(
                choices=units_choices,
                attrs={
                    'class': 'form-select form-select-sm'
                }
            ))
        else:
            widgets.append(forms.HiddenInput())

        # EV widget (always included if ev_allowed)
        if self.metadata_config.get('ev_allowed', True):
            widgets.append(Select(
                choices=EXCEPTIONAL_VALUE_CHOICES,
                attrs={'class': 'form-select form-select-sm'}
            ))
        else:
            widgets.append(forms.HiddenInput())

        # VTB widget
        if self.metadata_config.get('vtb_allowed') or self.metadata_config.get('vtb_required'):
            widgets.append(DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control form-control-sm'
                }
            ))
        else:
            widgets.append(forms.HiddenInput())

        # VTE widget
        if self.metadata_config.get('vte_allowed') or self.metadata_config.get('vte_required'):
            widgets.append(DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control form-control-sm'
                }
            ))
        else:
            widgets.append(forms.HiddenInput())

        # Latitude widget
        if self.metadata_config.get('location_allowed') or self.metadata_config.get('location_required'):
            widgets.append(TextInput(
                attrs={
                    'type': 'number',
                    'step': 'any',
                    'placeholder': 'Latitude',
                    'class': 'form-control form-control-sm'
                }
            ))
        else:
            widgets.append(forms.HiddenInput())

        # Longitude widget
        if self.metadata_config.get('location_allowed') or self.metadata_config.get('location_required'):
            widgets.append(TextInput(
                attrs={
                    'type': 'number',
                    'step': 'any',
                    'placeholder': 'Longitude',
                    'class': 'form-control form-control-sm'
                }
            ))
        else:
            widgets.append(forms.HiddenInput())

        super().__init__(widgets, attrs)

    def decompress(self, value):
        """
        Decompress the value into a list of [data_value, units, ev, vtb, vte, lat, lon].
        """
        if value:
            # If value is a dict (from JSON storage)
            if isinstance(value, dict):
                return [
                    value.get('value'),
                    value.get('units', ''),
                    value.get('ev', ''),
                    value.get('vtb', ''),
                    value.get('vte', ''),
                    value.get('lat', ''),
                    value.get('lon', ''),
                ]
            # Otherwise just the primary value
            return [value, '', '', '', '', '', '']
        return [None, '', '', '', '', '', '']

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Add metadata configuration to context for template
        context['metadata_config'] = self.metadata_config
        context['widget']['name'] = name
        return context


# Backwards compatibility - keep the old widget
class ExceptionalValueWidget(SDCComponentWidget):
    """
    Legacy widget name - maps to new SDCComponentWidget with minimal config.
    """
    def __init__(self, data_widget, attrs=None):
        super().__init__(
            data_widget,
            metadata_config={'ev_allowed': True},
            attrs=attrs
        )
