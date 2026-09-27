from django import template

register = template.Library()


@register.filter
def get_attribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""
    if hasattr(value, str(arg)):
        return getattr(value, str(arg))
    elif hasattr(value, 'get'):
        return value.get(arg)
    return None


@register.filter
def dict_get(dictionary, key):
    """
    Get a value from a dictionary by key.
    Usage: mydict|dict_get:key
    """
    if dictionary is None:
        return None
    return dictionary.get(key, '')


@register.filter
def get_field(form, field_name):
    """
    Get a form field by name.
    Usage: form|get_field:'field_name'
    """
    if form is None:
        return None
    try:
        return form[field_name]
    except KeyError:
        return None


@register.filter
def addclass(field, css_class):
    """
    Add a CSS class to a form field widget.
    Usage: field|addclass:'form-control'
    """
    if field is None:
        return field
    return field.as_widget(attrs={'class': css_class})
