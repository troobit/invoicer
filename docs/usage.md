# Usage

## Workflow 1: HTML form (recommended)

**Generate the form** (re-run whenever `defaults.yaml` changes):

```bash
uv run invoicer.py form
```

Writes `invoice_form.html` — a standalone HTML file with default rates and payment terms embedded in the JavaScript. Open it in a browser, complete the fields, and click **Download Invoice YAML**. This saves a `.yaml` file locally.

**Generate the invoice:**

```bash
uv run invoicer.py generate ~/Downloads/invoice-2024-05-001.yaml
```

Output:

```
/abs/path/to/invoices/INV-2024-05-001.md
/abs/path/to/invoices/INV-2024-05-001.pdf
```

## Workflow 2: Write YAML directly

Author the YAML by hand (see [invoice-yaml.md](invoice-yaml.md) for the schema) and run the same `generate` command.

---

## CLI reference

```
uv run invoicer.py generate <invoice.yaml> [--output-dir <path>]
uv run invoicer.py form [--output <path>]
```

### Output directory resolution

Evaluated in order; first non-null value wins:

1. `--output-dir` CLI flag
2. `output_path` in the invoice YAML (per-invoice override)
3. `output_dir` in `defaults.yaml`
4. `./invoices` (hardcoded fallback)

### Generate pipeline

1. Load `defaults.yaml` into a `Config` object
2. Parse the invoice YAML into an `InvoiceData` object
3. Stamp `config.tax_rate` onto every line item
4. Validate all fields and business rules (see below)
5. Render `INV-<number>.md` and `INV-<number>.pdf`
6. Warn on stderr if either output file already exists (overwrites regardless)

### Validation rules

All errors are collected and raised together — not fail-fast.

| Rule | Detail |
|------|--------|
| Required fields | `invoice_number`, `issue_date`, `due_date`, `client_name`, `client_address` |
| Line items | At least one required |
| Billing type | Each `type` must be in the allowed set (see [invoice-yaml.md](invoice-yaml.md#billing-types)) |
| ATO $1,000 threshold | If total payable >= $1,000: `client_abn` or `client_identity` must be present |
