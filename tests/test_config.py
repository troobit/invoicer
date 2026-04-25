"""Tests for lib/config.py — Config dataclass, load_config, validate_abn, ConfigError."""
import os
import tempfile
import textwrap
from decimal import Decimal
from unittest import mock

import pytest

from lib.config import Config, ConfigError, load_config, validate_abn


# ---------------------------------------------------------------------------
# validate_abn
# ---------------------------------------------------------------------------

VALID_ABN = "51 824 753 556"  # checksum: 534 % 89 == 0
VALID_ABN_NODASH = "51824753556"


class TestValidateAbn:
    def test_known_valid_abn_with_spaces(self):
        assert validate_abn(VALID_ABN) is True

    def test_known_valid_abn_no_spaces(self):
        assert validate_abn(VALID_ABN_NODASH) is True

    def test_valid_abn_with_dashes(self):
        assert validate_abn("51-824-753-556") is True

    def test_single_digit_mutation_fails(self):
        # Change last digit 6 → 7 — breaks checksum
        assert validate_abn("51 824 753 557") is False

    def test_all_zeros_fails(self):
        assert validate_abn("00000000000") is False

    def test_too_short_fails(self):
        assert validate_abn("1234567890") is False  # 10 digits

    def test_too_long_fails(self):
        assert validate_abn("123456789012") is False  # 12 digits

    def test_non_digits_after_stripping_fails(self):
        assert validate_abn("5182475355X") is False

    def test_empty_string_fails(self):
        assert validate_abn("") is False

    def test_whitespace_only_fails(self):
        assert validate_abn("   ") is False


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

VALID_YAML = textwrap.dedent("""\
    entity_name: "Test Consulting"
    abn: "51 824 753 556"
    address: "1 Test St, Melbourne VIC 3000"
    email: "test@example.com"
    phone: "+61 400 000 000"
    bank_name: "Test Consulting"
    bsb: "000-000"
    account_number: "123456789"
    payment_terms_days: 14
    output_dir: "./invoices"
    logo_path: "~/repos/cvsite/static/logo.light.svg"
    tax_rate: 0.10
    late_payment_fee: 150.00
    late_payment_margin: 2.0
    rates:
      hourly: 220.00
      overtime: 350.00
      white_glove: 450.00
      on_call: 250.00
      on_premise: 1500.00
      callout: 350.00
""")


def write_temp_yaml(content: str) -> str:
    """Write content to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestLoadConfig:
    def test_loads_valid_yaml(self):
        path = write_temp_yaml(VALID_YAML)
        try:
            cfg = load_config(path)
            assert cfg.entity_name == "Test Consulting"
            assert cfg.abn == "51 824 753 556"
            assert cfg.payment_terms_days == 14
            assert cfg.tax_rate == Decimal("0.10")
            assert cfg.late_payment_fee == Decimal("150.00")
            assert cfg.late_payment_margin == Decimal("2.0")
            assert cfg.rates["hourly"] == Decimal("220.00")
            assert cfg.rates["callout"] == Decimal("350.00")
        finally:
            os.unlink(path)

    def test_logo_path_resolved_with_expanduser(self):
        path = write_temp_yaml(VALID_YAML)
        try:
            cfg = load_config(path)
            assert "~" not in cfg.logo_path
            assert cfg.logo_path.startswith("/")
        finally:
            os.unlink(path)

    def test_missing_file_raises_config_error(self):
        with pytest.raises(ConfigError, match="defaults.yaml"):
            load_config("/nonexistent/path/defaults.yaml")

    def test_invalid_abn_raises_config_error(self):
        bad_abn_yaml = VALID_YAML.replace(
            'abn: "51 824 753 556"', 'abn: "51 824 753 557"'
        )
        path = write_temp_yaml(bad_abn_yaml)
        try:
            with pytest.raises(ConfigError, match="51 824 753 557"):
                load_config(path)
        finally:
            os.unlink(path)

    def test_tax_rate_defaults_to_zero_when_omitted(self):
        yaml_no_tax = VALID_YAML.replace("tax_rate: 0.10\n", "")
        path = write_temp_yaml(yaml_no_tax)
        try:
            cfg = load_config(path)
            assert cfg.tax_rate == Decimal("0.00")
        finally:
            os.unlink(path)

    def test_missing_required_field_raises_config_error(self):
        missing_field = VALID_YAML.replace('entity_name: "Test Consulting"\n', "")
        path = write_temp_yaml(missing_field)
        try:
            with pytest.raises(ConfigError):
                load_config(path)
        finally:
            os.unlink(path)

    def test_rates_loaded_as_decimal(self):
        path = write_temp_yaml(VALID_YAML)
        try:
            cfg = load_config(path)
            for rate in cfg.rates.values():
                assert isinstance(rate, Decimal)
        finally:
            os.unlink(path)
