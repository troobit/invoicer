"""Tests for lib/form.py — generate_form."""
import os
from decimal import Decimal

import pytest

from lib.config import Config
from lib.form import generate_form


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
        tax_rate=Decimal("0.00"),
        late_payment_fee=Decimal("150.00"),
        late_payment_margin=Decimal("2.0"),
        rates={
            "hourly":      Decimal("220.00"),
            "overtime":    Decimal("350.00"),
            "white_glove": Decimal("450.00"),
            "on_call":     Decimal("250.00"),
            "on_premise":  Decimal("1500.00"),
            "callout":     Decimal("350.00"),
        },
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerateForm:
    def test_file_is_written(self, tmp_path):
        output = str(tmp_path / "invoice_form.html")
        generate_form(make_config(), output)
        assert os.path.exists(output)

    def test_file_is_non_empty(self, tmp_path):
        output = str(tmp_path / "invoice_form.html")
        generate_form(make_config(), output)
        assert os.path.getsize(output) > 0

    def test_output_is_html(self, tmp_path):
        output = str(tmp_path / "invoice_form.html")
        generate_form(make_config(), output)
        content = open(output).read()
        assert "<!DOCTYPE html>" in content or "<html" in content

    def test_contains_all_six_default_rates(self, tmp_path):
        output = str(tmp_path / "invoice_form.html")
        generate_form(make_config(), output)
        content = open(output).read()
        assert "220" in content   # hourly
        assert "350" in content   # overtime / callout
        assert "450" in content   # white_glove
        assert "250" in content   # on_call
        assert "1500" in content  # on_premise

    def test_contains_payment_terms(self, tmp_path):
        output = str(tmp_path / "invoice_form.html")
        generate_form(make_config(), output)
        content = open(output).read()
        assert "14" in content

    def test_contains_download_location_note(self, tmp_path):
        output = str(tmp_path / "invoice_form.html")
        generate_form(make_config(), output)
        content = open(output).read()
        assert "Downloads" in content

    def test_self_contained_no_external_scripts(self, tmp_path):
        output = str(tmp_path / "invoice_form.html")
        generate_form(make_config(), output)
        content = open(output).read()
        # Should have no <script src="..."> pointing to external CDN
        assert 'script src="http' not in content
        assert "cdn." not in content

    def test_default_output_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_form(make_config())
        assert os.path.exists("invoice_form.html")

    def test_invoice_number_default_js_present(self, tmp_path):
        output = str(tmp_path / "invoice_form.html")
        generate_form(make_config(), output)
        content = open(output).read()
        assert "getElementById('invoice_number').value" in content
        assert "getFullYear()" in content
        assert "getMonth()" in content
        assert "padStart(2, '0')" in content
