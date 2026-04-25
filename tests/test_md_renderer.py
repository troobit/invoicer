"""Tests for lib/md_renderer.py — render_markdown."""
import os
import tempfile
from decimal import Decimal

import pytest

from lib.config import Config
from lib.models import InvoiceData, LineItem
from lib.md_renderer import render_markdown


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_config(tax_rate=Decimal("0.10")):
    return Config(
        entity_name="Test Consulting",
        abn="51 824 753 556",
        address="1 Test St, Melbourne VIC 3000",
        email="test@example.com",
        phone="+61 400 000 000",
        bank_name="Test Consulting",
        bsb="000-000",
        account_number="123456789",
        payment_terms_days=14,
        output_dir="./invoices",
        logo_path="/tmp/logo.svg",
        tax_rate=tax_rate,
        late_payment_fee=Decimal("150.00"),
        late_payment_margin=Decimal("2.0"),
        rates={"hourly": Decimal("220.00")},
    )


def make_invoice(with_date=False, client_abn="98 765 432 109"):
    date = "2024-05-15" if with_date else None
    return InvoiceData(
        invoice_number="2024-001",
        issue_date="2024-05-15",
        due_date="2024-05-29",
        client_name=["ACME Pty Ltd"],
        client_address="456 Client Ave, Sydney NSW 2000",
        client_abn=client_abn,
        client_identity=None,
        line_items=[
            LineItem(
                type="hourly",
                description="Technical consulting",
                quantity=Decimal("4"),
                rate=Decimal("220.00"),
                tax_rate=Decimal("0.10"),
                date=date,
            ),
            LineItem(
                type="disbursement",
                description="ASIC search fee",
                quantity=Decimal("1"),
                rate=Decimal("42.00"),
                tax_rate=Decimal("0"),
                date=date,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRenderMarkdown:
    def test_returns_string(self):
        md = render_markdown(make_invoice(), make_config())
        assert isinstance(md, str)

    def test_heading_is_invoice(self):
        md = render_markdown(make_invoice(), make_config())
        assert "INVOICE" in md
        assert "TAX INVOICE" not in md

    def test_supplier_block_present(self):
        md = render_markdown(make_invoice(), make_config())
        assert "Test Consulting" in md
        assert "51 824 753 556" in md
        assert "1 Test St" in md
        assert "test@example.com" in md

    def test_recipient_block_present(self):
        md = render_markdown(make_invoice(), make_config())
        assert "ACME Pty Ltd" in md
        assert "456 Client Ave" in md
        assert "98 765 432 109" in md

    def test_invoice_metadata_present(self):
        md = render_markdown(make_invoice(), make_config())
        assert "2024-001" in md
        assert "2024-05-15" in md
        assert "2024-05-29" in md
        assert "14" in md

    def test_line_items_table_present(self):
        md = render_markdown(make_invoice(), make_config())
        assert "Technical consulting" in md
        assert "ASIC search fee" in md

    def test_date_column_shown_when_date_set(self):
        md = render_markdown(make_invoice(with_date=True), make_config())
        assert "2024-05-15" in md

    def test_date_column_empty_when_no_date(self):
        invoice = make_invoice(with_date=False)
        md = render_markdown(invoice, make_config())
        assert "Technical consulting" in md

    def test_tax_summary_present_when_tax_rate_nonzero(self):
        md = render_markdown(make_invoice(), make_config(tax_rate=Decimal("0.10")))
        assert "Subtotal" in md
        assert "Total Tax" in md
        assert "Total Payable" in md

    def test_tax_summary_absent_when_tax_rate_zero(self):
        md = render_markdown(make_invoice(), make_config(tax_rate=Decimal("0")))
        assert "Total Tax" not in md

    def test_tax_amounts_formatted_as_aud(self):
        md = render_markdown(make_invoice(), make_config())
        # hourly: 4 x $220, tax=88, total=968; disbursement: rate=42, tax=0
        assert "$88.00" in md
        assert "$220.00" in md
        assert "$968.00" in md

    def test_payment_instructions_present(self):
        md = render_markdown(make_invoice(), make_config())
        assert "000-000" in md
        assert "123456789" in md

    def test_late_payment_clause_present(self):
        md = render_markdown(make_invoice(), make_config())
        assert "Late Payment" in md
        assert "$150.00" in md
        assert "2.0" in md

    def test_output_dir_created_if_missing(self, tmp_path):
        invoice = make_invoice()
        invoice.output_path = str(tmp_path / "out")
        config = make_config()
        config.output_dir = str(tmp_path / "out")
        md = render_markdown(invoice, config)
        assert isinstance(md, str)
