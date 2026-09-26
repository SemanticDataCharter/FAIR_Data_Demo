"""
Custom form fields for SDC components.

These fields handle the complex structure of SDC4 components, including:
- Primary value (the actual data)
- Units (for quantified types)
- Exceptional Values (EVs)

Metadata fields (VTB, VTE, Location, ACT, etc.) are separate named fields
generated alongside each primary field.
"""
from django import forms
from decimal import Decimal


class SDCComponentField(forms.MultiValueField):
    """
    Base multi-value field for SDC components.

    Handles 3 subwidgets:
    - Index 0: Primary value (type-specific)
    - Index 1: Units (for quantified types, hidden otherwise)
    - Index 2: Exceptional Value (EV selector)

    All other metadata (VTB, VTE, Location, ACT, etc.) are separate form fields.
    """

    def __init__(self, base_field, has_units=False, require_all_fields=False, *args, **kwargs):
        """
        Args:
            base_field: The field type for the primary value (e.g., CharField, IntegerField)
            has_units: Whether this field has units (quantified types)
            require_all_fields: Whether all subfields are required
        """
        fields = [
            base_field,  # Primary value
            forms.CharField(required=False),  # Units (or hidden)
            forms.CharField(required=False),  # EV
        ]
        super().__init__(fields=fields, require_all_fields=require_all_fields, *args, **kwargs)
        self.has_units = has_units

    def compress(self, data_list):
        """
        Compress the list of values into a single value.

        Returns only the primary value (index 0) for model field storage.
        Units and EV are handled separately in form.clean().

        Note: Value is returned regardless of EV presence - EVs indicate
        the status of the value, not necessarily that the value is absent.
        """
        if data_list:
            # Return the primary value (EV handling is separate)
            return data_list[0] if data_list[0] not in (None, '') else None
        return None


class SDCStringField(SDCComponentField):
    """SDC field for string values (XdString, XdToken)"""
    def __init__(self, *args, **kwargs):
        super().__init__(forms.CharField(required=False), has_units=False, *args, **kwargs)


class SDCBooleanField(SDCComponentField):
    """SDC field for boolean values (XdBoolean)"""
    def __init__(self, *args, **kwargs):
        # BooleanField doesn't support required=False properly, use NullBooleanField behavior
        super().__init__(
            forms.TypedChoiceField(
                choices=[('', '---'), ('true', 'True'), ('false', 'False')],
                coerce=lambda x: x == 'true' if x else None,
                required=False
            ),
            has_units=False,
            *args,
            **kwargs
        )


class SDCLinkField(SDCComponentField):
    """SDC field for link/URL values (XdLink)"""
    def __init__(self, *args, **kwargs):
        super().__init__(forms.URLField(required=False), has_units=False, *args, **kwargs)


class SDCFileField(SDCComponentField):
    """SDC field for file uploads (XdFile)"""
    def __init__(self, *args, **kwargs):
        super().__init__(forms.FileField(required=False), has_units=False, *args, **kwargs)


# Quantified Fields (require units)

class SDCCountField(SDCComponentField):
    """SDC field for integer count values (XdCount)"""
    def __init__(self, *args, **kwargs):
        super().__init__(forms.IntegerField(required=False), has_units=True, *args, **kwargs)


class SDCQuantityField(SDCComponentField):
    """SDC field for decimal quantity values (XdQuantity)"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            forms.DecimalField(required=False, max_digits=20, decimal_places=10),
            has_units=True,
            *args,
            **kwargs
        )


class SDCFloatField(SDCComponentField):
    """SDC field for float values (XdFloat)"""
    def __init__(self, *args, **kwargs):
        super().__init__(forms.FloatField(required=False), has_units=True, *args, **kwargs)


class SDCOrdinalField(SDCComponentField):
    """SDC field for ordinal values (XdOrdinal)"""
    def __init__(self, *args, **kwargs):
        super().__init__(forms.IntegerField(required=False), has_units=True, *args, **kwargs)


# Temporal Field

class SDCTemporalField(SDCComponentField):
    """
    SDC field for temporal values (XdTemporal).

    Supports multiple formats: datetime, date, time, year, month, day.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(forms.DateTimeField(required=False), has_units=False, *args, **kwargs)
