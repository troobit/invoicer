# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- `lib/pdf_renderer.py`: Replaced WeasyPrint with Playwright/Chromium for PDF rendering. `render_pdf` now writes rendered HTML to a temp file, navigates headless Chromium to a `file://` URI, and calls `page.pdf(format="A4", print_background=True)`. Added type hints (`data: InvoiceData, config: Config`) and inline comments explaining the temp-file and print-background decisions. Module docstring updated.
- `pyproject.toml`: Replaced `weasyprint>=61.0` with `playwright>=1.40`; added `pytest>=8.0` and `hypothesis>=6.0` as dev dependencies under `[dependency-groups]` so tests run correctly via `uv run pytest`.
- `defaults.yaml.example`: Updated `logo_path` default from `~/repos/cvsite/static/logo.light.svg` to `logo.png`.
- `docs/agent-notes/architecture.md`: Replaced `weasyprint system dependency` section with Playwright prerequisite (`playwright install chromium`); updated Portability section to note the native C library blocker (Pango/Cairo/GLib) is removed.

---

### Added

- `lib/config.py`: `tax_rate: Decimal` field on `Config`; loaded from `defaults.yaml` with a default of `0.00` when absent.
- `tests/test_config.py`: `test_tax_rate_defaults_to_zero_when_omitted` — asserts `tax_rate` defaults to `Decimal("0.00")` when the key is missing from YAML.

### Changed

- `lib/config.py`: Removed `gst_registered: bool` field and its stderr warning; replaced with `tax_rate: Decimal`.
- `lib/models.py`: Removed `GST_RATE` and `GST_EXEMPT` constants; renamed `gst_rate` → `tax_rate`, `gst` → `tax`, `total_gst` → `total_tax` on `LineItem` and `InvoiceData`.
- `lib/validator.py`: Renamed `assign_gst_rates(items)` → `assign_tax_rates(items, rate)`; removed per-type GST exemption logic — all items receive the same configured rate.
- `invoicer.py`: Updated call to `assign_tax_rates(data.line_items, config.tax_rate)`; renamed `gst_rate=` → `tax_rate=` in `load_invoice_yaml`.
- `templates/invoice.html.j2`: Tax column and summary rows now conditional on `config.tax_rate > 0`; labels renamed from GST to Tax.
- `templates/invoice.md.j2`: Same conditional tax changes as HTML template; heading always "INVOICE".
- `templates/form.html.j2`: Removed GST summary row, JS GST calculation, and `GST_EXEMPT_TYPES` constant; renamed summary labels to "Subtotal" / "Total"; removed front-end `required` attributes, error spans, and JS validation block; fixed broken `{ { } }` Jinja2 syntax in `DEFAULT_RATES`; updated header hint to reference Downloads folder.
- `defaults.yaml.example`: Replaced `gst_registered: false` with `tax_rate: 0.00`.
- `tests/`: Updated all helpers and assertions — `gst_registered=` → `tax_rate=`, `gst_rate=` → `tax_rate=`, `GST_RATE` import → `Decimal` literal; removed GST-specific test cases; renamed test classes (`TestLineItemGst` → `TestLineItemTax`, `TestAssignGstRates` → `TestAssignTaxRates`).

---

### Added (prior)

- `templates/form.html.j2`: invoice number field is now pre-filled on page load with `yyyy-MM-001` (current year and zero-padded month) via an extension of the existing date-defaults IIFE. Inline comments document how to add a client-specific prefix string or replace the field with a `<select>` dropdown.
- `tests/test_form.py`: `test_invoice_number_default_js_present` — asserts the rendered HTML contains the JS expressions that build and set the invoice number default.

- `lib/config.py`: `Config` dataclass, `load_config`, `validate_abn`, `ConfigError`. Loads and validates `defaults.yaml`, applies ATO mod-89 ABN checksum, warns to stderr when `gst_registered` is false, expands `logo_path` via `expanduser`.
- `lib/models.py`: `LineItem` and `InvoiceData` dataclasses with `Decimal` arithmetic (`ROUND_HALF_UP`). `LineItem` supports an optional `date` field (MVP for dateable invoices). `InvoiceData` exposes `subtotal`, `total_gst`, and `total_payable` as properties.
- `lib/validator.py`: `ValidationError`, `validate_invoice`, `assign_gst_rates`. Collects all validation failures before raising. Enforces the ATO $1,000 recipient-identity rule. `assign_gst_rates` sets `gst_rate` per line item based on type, keeping business logic out of the model.
- `lib/formatting.py`: `format_aud(Decimal) -> str` currency helper for Jinja2 templates.
- `defaults.yaml.example`: fully documented reference configuration with all supported fields.
- `requirements.txt`, `requirements-dev.txt`: pip dependency manifests.
- `tests/`: unit and property-based tests for all four library modules (69 tests via pytest + Hypothesis).
