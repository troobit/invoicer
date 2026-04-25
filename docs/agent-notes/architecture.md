# Architecture notes

## Module responsibilities

- `lib/models.py` — dataclasses only. `LineItem.net/tax/total` and `InvoiceData.subtotal/total_tax/total_payable` are `@property` computed on access, not stored.
- `lib/config.py` — loads `defaults.yaml`, validates ABN via ATO mod-89 checksum. `rates` is `dict[str, Decimal]` keyed by billing type.
- `lib/form.py` — bakes config rates into JS `DEFAULT_RATES` at generation time. Output HTML is standalone.
- `invoicer.py` — sole I/O boundary. Everything in `lib/` is pure.

## Non-obvious behaviour

- `tax_rate` never appears in invoice YAML — always sourced from config via `assign_tax_rates()`.
- Tax columns conditionally rendered: `{% if config.tax_rate > 0 %}`. Zero tax = no tax column.
- PDF logo resolved to `file://` URI at render time. Missing file → `logo_uri = None` → template skips the block.
- `Decimal` used throughout (not `float`). `ROUND_HALF_UP` applied at computation (`LineItem.net`, `LineItem.tax`), not at display.
- Output filename: `INV-<invoice_number>.md/.pdf`. Existing files are overwritten with a stderr warning.

## Portability

The `lib/` split is intentional — any entry point (CLI, HTTP server, future wrapper) calls the same pipeline. See `docs/automation.md` for the local dev server approach. Serverless remains descoped (Playwright/Chromium binary is large and not suited to ephemeral functions), but the native C library blocker (Pango/Cairo/GLib) is removed by the switch to Playwright.

## Playwright prerequisite

After `uv sync`, Chromium must be installed once before `generate` or tests will work:

```
playwright install chromium
```

No system libraries are required — Playwright bundles its own Chromium build.
