"""Currency formatting helpers for Jinja2 templates."""
from decimal import ROUND_HALF_UP, Decimal

from lib.models import CENTS


def format_aud(amount: Decimal) -> str:
    """Format a Decimal as an AUD currency string, e.g. '$1,234.50'."""
    rounded = amount.quantize(CENTS, rounding=ROUND_HALF_UP)
    return f"${rounded:,.2f}"
