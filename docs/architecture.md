# Architecture

## Module map

```
invoicer.py              CLI entry point. All filesystem I/O lives here.
lib/
  models.py              Dataclasses: Config, InvoiceData, LineItem
  config.py              YAML loader → Config; ABN checksum validation
  md_renderer.py         InvoiceData + Config → Markdown string (Jinja2)
  pdf_renderer.py        InvoiceData + Config → PDF file (Jinja2 + weasyprint)
  form.py                Config → standalone invoice_form.html (Jinja2)
  formatting.py          format_aud(): Decimal → "$1,234.50"
templates/
  invoice.md.j2          Markdown invoice template
  invoice.html.j2        HTML invoice template (rendered to PDF)
  form.html.j2           HTML form template (rates baked into JS at generation)
```

## Data flow

```
defaults.yaml                          invoice.yaml
     │                                      │
     ▼                                      ▼
 load_config()                     load_invoice_yaml()
     │                                      │
     ▼                                      ▼
  Config ──────────┐                  InvoiceData
                   │                      │
                   │          assign_tax_rates(items, config.tax_rate)
                   │                      │
                   │              validate_invoice(data)
                   │                      │
                   ▼                      ▼
              render_markdown(data, config) ──► .md file
              render_pdf(data, config, path) ──► .pdf file
```

Two inputs, one pipeline. `Config` is the supplier/rate context. `InvoiceData` is the per-invoice payload. Both are required by the renderers.

## Dataclasses

The three core types — `Config`, `InvoiceData`, `LineItem` — are `@dataclass` objects. These are Python's built-in way to define a struct with named, typed fields:

```python
@dataclass
class LineItem:
    type: str
    description: str
    quantity: Decimal
    rate: Decimal
    tax_rate: Decimal
    date: str | None = None
```

This replaces what would otherwise be a plain `dict`. The difference that matters: attribute access (`item.rate`) instead of string keys (`item["rate"]`), with IDE autocompletion and type checking on every field. If a field is misspelled or missing, it fails at construction — not silently at render time.

### Computed properties

`LineItem` defines three `@property` methods that compute values on access rather than storing them:

```python
item.net    # quantity * rate, rounded to cents
item.tax    # net * tax_rate, rounded to cents
item.total  # net + tax
```

`InvoiceData` aggregates these across all line items:

```python
data.subtotal       # sum of item.net
data.total_tax      # sum of item.tax
data.total_payable  # subtotal + total_tax
```

These are read-only derived values. Changing `item.rate` or `item.tax_rate` immediately changes `item.net`, `item.tax`, and everything above it. There is no cached state to invalidate.

## Design rationale

### Pure lib/ modules

Every function in `lib/` takes dataclass arguments and returns a value or raises an exception. None perform file I/O or access global state. `invoicer.py` is the sole I/O boundary.

This separation is the foundation for two things:
1. **Testability** — `tests/` construct `InvoiceData` and `Config` objects directly, without touching the filesystem.
2. **Portability** — the same `lib/` modules run inside any HTTP wrapper with zero changes. See [automation.md](automation.md).

### Tax rate assignment before validation

`tax_rate` lives in `Config`, not in the invoice YAML. The validator checks the ATO $1,000 threshold using `item.total`, which depends on `tax_rate` being set. The call order is a hard precondition:

```python
assign_tax_rates(data.line_items, config.tax_rate)  # must precede validation
validate_invoice(data)
```

This is a deliberate split, not an artefact. Tax policy is a supplier-level concern (config), not an invoice-level one.

### Decimal arithmetic

All monetary values use `Decimal`, not `float`. Rounding (`ROUND_HALF_UP` to 2 decimal places) is applied at the point of computation in `LineItem.net` and `LineItem.tax` — not deferred to display. The `|aud` Jinja2 filter handles formatting only.

## Templates

Both renderers load Jinja2 templates from `templates/` and register a custom `|aud` filter (implemented in `lib/formatting.py`).

- **Markdown renderer**: `autoescape=False`. Outputs a Markdown string returned to the caller.
- **PDF renderer**: `autoescape=True`. Renders `invoice.html.j2` to an HTML string, then passes it to `weasyprint.HTML(string=...).write_pdf(path)`. The logo is resolved to a `file://` URI; if the file doesn't exist at render time, the logo block is skipped.

Both templates conditionally render tax columns: when `config.tax_rate == 0`, the Tax column and subtotal/tax breakdown are omitted entirely.

## The form command

`invoicer.py form` renders `form.html.j2` with config values (rates, payment terms) injected into the template's `<script>` block as JavaScript constants. The resulting `invoice_form.html` is fully self-contained — it runs without a server and has no runtime dependency on Python. It serialises form input to YAML and triggers a browser file download. See [automation.md](automation.md) for how this changes when a local server is present.
