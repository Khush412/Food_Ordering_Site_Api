from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument, robustly handling types."""
    try:
        # Convert both to Decimal safely
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        if not isinstance(arg, Decimal):
            arg = Decimal(str(arg))
        return value * arg
    except (ValueError, TypeError, InvalidOperation):
        return 0 