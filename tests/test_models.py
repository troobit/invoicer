"""Tests for lib/models.py — LineItem, InvoiceData, Decimal arithmetic."""
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lib.models import InvoiceData, LineItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_line_item(
    item_type="hourly",
    description="Test work",
    quantity="4",
    rate="220.00",
    tax_rate=None,
    date=None,
):
    if tax_rate is None:
        tax_rate = Decimal("0.10")
    return LineItem(
        type=item_type,
        description=description,
        quantity=Decimal(quantity),
        rate=Decimal(rate),
        tax_rate=tax_rate,
        date=date,
    )


def make_invoice(line_items=None):
    if line_items is None:
        line_items = [make_line_item()]
    return InvoiceData(
        invoice_number="2024-001",
        issue_date="2024-05-15",
        due_date="2024-05-29",
        client_name=["ACME Pty Ltd"],
        client_address="456 Client Ave, Sydney NSW 2000",
        client_abn="98 765 432 109",
        client_identity=None,
        line_items=line_items,
    )


# ---------------------------------------------------------------------------
# LineItem
# ---------------------------------------------------------------------------

class TestLineItemNet:
    def test_net_equals_quantity_times_rate(self):
        item = make_line_item(quantity="4", rate="220.00")
        assert item.net == Decimal("880.00")

    def test_net_two_decimal_places(self):
        item = make_line_item(quantity="1.5", rate="220.00")
        assert item.net == Decimal("330.00")

    def test_net_rounds_half_up(self):
        # 3 * 0.335 = 1.005 → rounds to 1.01
        item = make_line_item(quantity="3", rate="0.335")
        assert item.net == Decimal("1.01")


class TestLineItemTax:
    def test_tax_applied_at_10_percent_for_taxable(self):
        item = make_line_item(tax_rate=Decimal("0.10"), quantity="1", rate="100.00")
        assert item.tax == Decimal("10.00")

    def test_tax_zero_for_exempt(self):
        item = make_line_item(tax_rate=Decimal("0"), quantity="1", rate="42.00")
        assert item.tax == Decimal("0.00")

    def test_tax_two_decimal_places(self):
        item = make_line_item(tax_rate=Decimal("0.10"), quantity="1", rate="333.00")
        assert item.tax == Decimal("33.30")


class TestLineItemTotal:
    def test_total_equals_net_plus_tax(self):
        item = make_line_item(tax_rate=Decimal("0.10"), quantity="4", rate="220.00")
        assert item.total == item.net + item.tax

    def test_total_for_zero_tax_item(self):
        item = make_line_item(tax_rate=Decimal("0"), quantity="1", rate="42.00")
        assert item.total == Decimal("42.00")


class TestLineItemDate:
    def test_date_defaults_to_none(self):
        item = make_line_item()
        assert item.date is None

    def test_date_can_be_set(self):
        item = make_line_item(date="2024-05-15")
        assert item.date == "2024-05-15"

    def test_date_can_be_time_range(self):
        item = make_line_item(date="09:00-17:00")
        assert item.date == "09:00-17:00"


# ---------------------------------------------------------------------------
# InvoiceData aggregates
# ---------------------------------------------------------------------------

class TestInvoiceDataAggregates:
    def test_subtotal_sum_of_nets(self):
        items = [
            make_line_item(quantity="4", rate="220.00"),   # net = 880.00
            make_line_item(quantity="1", rate="42.00", tax_rate=Decimal("0")),  # net = 42.00
        ]
        invoice = make_invoice(items)
        assert invoice.subtotal == Decimal("922.00")

    def test_total_tax_sum_of_tax(self):
        items = [
            make_line_item(tax_rate=Decimal("0.10"), quantity="1", rate="100.00"),  # tax = 10.00
            make_line_item(tax_rate=Decimal("0"), quantity="1", rate="50.00"),  # tax = 0
        ]
        invoice = make_invoice(items)
        assert invoice.total_tax == Decimal("10.00")

    def test_total_payable_equals_subtotal_plus_total_tax(self):
        items = [
            make_line_item(tax_rate=Decimal("0.10"), quantity="4", rate="220.00"),
        ]
        invoice = make_invoice(items)
        assert invoice.total_payable == invoice.subtotal + invoice.total_tax

    def test_mixed_items_aggregate(self):
        items = [
            make_line_item(tax_rate=Decimal("0.10"), quantity="1", rate="500.00"),   # net=500, tax=50
            make_line_item(tax_rate=Decimal("0"), quantity="1", rate="100.00"),  # net=100, tax=0
            make_line_item(tax_rate=Decimal("0.10"), quantity="2", rate="250.00"),   # net=500, tax=50
        ]
        invoice = make_invoice(items)
        assert invoice.subtotal == Decimal("1100.00")
        assert invoice.total_tax == Decimal("100.00")
        assert invoice.total_payable == Decimal("1200.00")


class TestInvoiceDataOptionalFields:
    def test_output_path_defaults_to_none(self):
        invoice = make_invoice()
        assert invoice.output_path is None

    def test_output_path_can_be_set(self):
        invoice = make_invoice()
        invoice.output_path = "./custom"
        assert invoice.output_path == "./custom"

    def test_client_abn_can_be_none(self):
        invoice = make_invoice()
        invoice.client_abn = None
        assert invoice.client_abn is None

    def test_client_identity_can_be_set(self):
        invoice = make_invoice()
        invoice.client_identity = "ACME International Ltd"
        assert invoice.client_identity == "ACME International Ltd"


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------

# Use 4dp values to exercise ROUND_HALF_UP in quantize paths
positive_decimal = st.decimals(
    min_value=Decimal("0.0001"),
    max_value=Decimal("100000"),
    places=4,
    allow_nan=False,
    allow_infinity=False,
)

zero_or_ten_pct = st.sampled_from([Decimal("0"), Decimal("0.10")])


@given(quantity=positive_decimal, rate=positive_decimal, tax_rate=zero_or_ten_pct)
@settings(max_examples=200)
def test_total_equals_net_plus_tax(quantity, rate, tax_rate):
    item = LineItem(
        type="hourly",
        description="pbt",
        quantity=quantity,
        rate=rate,
        tax_rate=tax_rate,
    )
    assert item.total == item.net + item.tax


@given(quantity=positive_decimal, rate=positive_decimal, tax_rate=zero_or_ten_pct)
@settings(max_examples=200)
def test_monetary_values_have_at_most_two_decimal_places(quantity, rate, tax_rate):
    item = LineItem(
        type="hourly",
        description="pbt",
        quantity=quantity,
        rate=rate,
        tax_rate=tax_rate,
    )
    for value in (item.net, item.tax, item.total):
        # exponent of a 2dp Decimal is -2 or higher (e.g. "10.00" has exp -2)
        assert value == value.quantize(Decimal("0.01"))


@given(
    items=st.lists(
        st.builds(
            lambda q, r, g: LineItem(
                type="hourly", description="pbt", quantity=q, rate=r, tax_rate=g
            ),
            q=positive_decimal,
            r=positive_decimal,
            g=zero_or_ten_pct,
        ),
        min_size=1,
        max_size=10,
    )
)
@settings(max_examples=100)
def test_invoice_total_payable_equals_subtotal_plus_total_tax(items):
    invoice = make_invoice(items)
    assert invoice.total_payable == invoice.subtotal + invoice.total_tax
