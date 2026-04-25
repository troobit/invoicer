"""Tests for lib/pdf_renderer.py — render_pdf."""
import os
from decimal import Decimal

import pytest

from lib.config import Config
from lib.models import InvoiceData, LineItem
from lib.pdf_renderer import render_pdf


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_config():
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
        tax_rate=Decimal("0.10"),
        late_payment_fee=Decimal("150.00"),
        late_payment_margin=Decimal("2.0"),
        rates={"hourly": Decimal("220.00")},
    )


def make_invoice():
    return InvoiceData(
        invoice_number="2024-001",
        issue_date="2024-05-15",
        due_date="2024-05-29",
        client_name=["ACME Pty Ltd"],
        client_address="456 Client Ave, Sydney NSW 2000",
        client_abn="98 765 432 109",
        client_identity=None,
        line_items=[
            LineItem(
                type="hourly",
                description="Technical consulting",
                quantity=Decimal("4"),
                rate=Decimal("220.00"),
                tax_rate=Decimal("0.10"),
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRenderPdf:
    def test_output_file_written(self, tmp_path):
        output = str(tmp_path / "INV-2024-001.pdf")
        render_pdf(make_invoice(), make_config(), output)
        assert os.path.exists(output)

    def test_output_file_non_empty(self, tmp_path):
        output = str(tmp_path / "INV-2024-001.pdf")
        render_pdf(make_invoice(), make_config(), output)
        assert os.path.getsize(output) > 0
