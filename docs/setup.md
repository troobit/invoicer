# Setup

## Prerequisites

- Python 3.10+ (pinned in `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- macOS: `brew install pango` (system dependency for weasyprint's PDF rendering)

## Install

```bash
uv sync
```

This resolves `pyproject.toml` and installs pyyaml, jinja2, and weasyprint into a managed virtualenv.

## Configure

```bash
cp defaults.yaml.example defaults.yaml
```

Edit `defaults.yaml` with real supplier, banking, and rate details. The example file is fully annotated — every field is documented inline. Key points:

- **`abn`** is validated against the ATO mod-89 weighted checksum at load time. An invalid ABN will fail immediately.
- **`tax_rate`** controls whether tax columns appear on invoices. Set to `0.10` for 10% GST; `0.00` to exclude tax entirely.
- **`rates`** are the per-type defaults baked into the HTML form and used as fallbacks when a line item omits its own rate.
- **`logo_path`** accepts `~` expansion. SVG only. Embedded in the PDF header via `file://` URI.

`defaults.yaml` is gitignored. It contains banking details and should never be committed.

## Verify

```bash
uv run invoicer.py --version
# invoicer 0.1.0
```
