"""Integration tests — full generate and form CLI commands end-to-end."""
import os
import subprocess
import sys
import textwrap

import pytest

PYTHON = sys.executable
INVOICER = os.path.join(os.path.dirname(__file__), "..", "invoicer.py")

VALID_DEFAULTS = textwrap.dedent("""\
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
    tax_rate: 0.00
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

VALID_INVOICE_BELOW_1K = textwrap.dedent("""\
    invoice_number: "2024-001"
    issue_date: "2024-05-15"
    due_date: "2024-05-29"
    client_name: "ACME Pty Ltd"
    client_abn: null
    client_identity: null
    client_address: "456 Client Ave, Sydney NSW 2000"
    output_path: null
    line_items:
      - type: hourly
        description: "Technical consulting"
        date: "2024-05-15"
        quantity: 2
        rate: 220.00
""")

VALID_INVOICE_ABOVE_1K = textwrap.dedent("""\
    invoice_number: "2024-002"
    issue_date: "2024-05-15"
    due_date: "2024-05-29"
    client_name: "ACME Pty Ltd"
    client_abn: "51 824 753 556"
    client_identity: null
    client_address: "456 Client Ave, Sydney NSW 2000"
    output_path: null
    line_items:
      - type: hourly
        description: "Technical consulting"
        date: "2024-05-15"
        quantity: 10
        rate: 220.00
""")


def run(args, cwd):
    return subprocess.run(
        [PYTHON, INVOICER] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# generate command
# ---------------------------------------------------------------------------

class TestGenerateCommand:
    def test_valid_invoice_produces_md_and_pdf(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        (tmp_path / "invoice.yaml").write_text(VALID_INVOICE_BELOW_1K)
        result = run(["generate", "invoice.yaml", "--output-dir", str(tmp_path / "out")], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "out" / "INV-2024-001.md").exists()
        assert (tmp_path / "out" / "INV-2024-001.pdf").exists()

    def test_stdout_contains_absolute_output_paths(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        (tmp_path / "invoice.yaml").write_text(VALID_INVOICE_BELOW_1K)
        result = run(["generate", "invoice.yaml", "--output-dir", str(tmp_path / "out")], cwd=tmp_path)
        assert result.returncode == 0
        assert "INV-2024-001.md" in result.stdout
        assert "INV-2024-001.pdf" in result.stdout

    def test_below_1k_no_client_abn_exits_0(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        (tmp_path / "invoice.yaml").write_text(VALID_INVOICE_BELOW_1K)
        result = run(["generate", "invoice.yaml", "--output-dir", str(tmp_path / "out")], cwd=tmp_path)
        assert result.returncode == 0

    def test_above_1k_with_client_abn_exits_0(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        (tmp_path / "invoice.yaml").write_text(VALID_INVOICE_ABOVE_1K)
        result = run(["generate", "invoice.yaml", "--output-dir", str(tmp_path / "out")], cwd=tmp_path)
        assert result.returncode == 0

    def test_overwrite_existing_file_prints_warning(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        (tmp_path / "invoice.yaml").write_text(VALID_INVOICE_BELOW_1K)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        # Pre-create the output file
        (out_dir / "INV-2024-001.md").write_text("old content")
        result = run(["generate", "invoice.yaml", "--output-dir", str(out_dir)], cwd=tmp_path)
        assert result.returncode == 0
        assert "Warning" in result.stderr or "overwriting" in result.stderr.lower()

    def test_missing_defaults_exits_1(self, tmp_path):
        (tmp_path / "invoice.yaml").write_text(VALID_INVOICE_BELOW_1K)
        result = run(["generate", "invoice.yaml"], cwd=tmp_path)
        assert result.returncode == 1
        assert "defaults.yaml" in result.stderr

    def test_line_item_date_appears_in_markdown(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        (tmp_path / "invoice.yaml").write_text(VALID_INVOICE_BELOW_1K)
        result = run(["generate", "invoice.yaml", "--output-dir", str(tmp_path / "out")], cwd=tmp_path)
        assert result.returncode == 0
        md = (tmp_path / "out" / "INV-2024-001.md").read_text()
        assert "2024-05-15" in md


# ---------------------------------------------------------------------------
# form command
# ---------------------------------------------------------------------------

class TestFormCommand:
    def test_form_command_writes_html(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        result = run(["form"], cwd=tmp_path)
        assert result.returncode == 0
        assert (tmp_path / "invoice_form.html").exists()

    def test_form_contains_default_rates(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        run(["form"], cwd=tmp_path)
        content = (tmp_path / "invoice_form.html").read_text()
        assert "220" in content
        assert "1500" in content

    def test_form_custom_output_path(self, tmp_path):
        (tmp_path / "defaults.yaml").write_text(VALID_DEFAULTS)
        out = tmp_path / "custom_form.html"
        result = run(["form", "--output", str(out)], cwd=tmp_path)
        assert result.returncode == 0
        assert out.exists()


# ---------------------------------------------------------------------------
# --version flag
# ---------------------------------------------------------------------------

class TestVersionFlag:
    def test_version_flag_exits_0(self, tmp_path):
        result = run(["--version"], cwd=tmp_path)
        assert result.returncode == 0

    def test_version_flag_prints_version(self, tmp_path):
        result = run(["--version"], cwd=tmp_path)
        # Should print something (version string)
        assert result.stdout.strip() or result.stderr.strip()
