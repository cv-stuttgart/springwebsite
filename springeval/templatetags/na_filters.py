from django import template

register = template.Library()

@register.filter
def na_if_missing(value, float_places=3):
    """
    Returns 'n/a' if value is -1, otherwise formats the value to the specified
    number of decimal places.
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    if value == -1:
        return "n/a"
    return f"{value:.{int(float_places)}f}"
