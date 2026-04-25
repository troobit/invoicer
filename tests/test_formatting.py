"""Tests for lib/formatting.py — format_aud currency helper."""
from decimal import Decimal

import pytest

from lib.formatting import format_aud


class TestFormatAud:
    def test_integer_value(self):
        assert format_aud(Decimal("1234")) == "$1,234.00"

    def test_one_decimal_place(self):
        assert format_aud(Decimal("1234.5")) == "$1,234.50"

    def test_two_decimal_places(self):
        assert format_aud(Decimal("1234.56")) == "$1,234.56"

    def test_zero(self):
        assert format_aud(Decimal("0")) == "$0.00"

    def test_zero_with_decimals(self):
        assert format_aud(Decimal("0.00")) == "$0.00"

    def test_small_amount(self):
        assert format_aud(Decimal("0.50")) == "$0.50"

    def test_large_amount_with_thousands_separator(self):
        assert format_aud(Decimal("1000000.00")) == "$1,000,000.00"

    def test_two_comma_groups(self):
        assert format_aud(Decimal("12345.67")) == "$12,345.67"

    def test_exactly_one_thousand(self):
        assert format_aud(Decimal("1000.00")) == "$1,000.00"

    def test_fractional_cent_rounds_correctly(self):
        # 1234.005 should round to $1,234.01 (ROUND_HALF_UP)
        assert format_aud(Decimal("1234.005")) == "$1,234.01"
