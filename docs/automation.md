# Automation

## Current state

The workflow is manual: fill in the HTML form, download a YAML file, run the CLI. The `lib/` modules are already decoupled from I/O (see [architecture.md](architecture.md)), so removing the manual step is a matter of writing a thin HTTP wrapper — not restructuring the codebase.

## Why not serverless

WeasyPrint depends on native C libraries (Pango, Cairo, GLib). These are not available in standard function runtimes (Lambda, Azure Functions, Firebase Cloud Functions). Container-based deployment is possible but adds significant complexity for a single-user invoicing tool. Serverless is out of scope.

## Local development server

The practical next step is a local HTTP server that the form POSTs to. This eliminates the YAML download and manual CLI invocation while keeping the same machine (and its system dependencies) as the runtime.

### Skeleton

```python
#!/usr/bin/env python3
"""Minimal HTTP wrapper around lib/ — accepts JSON, returns PDF."""
import json
import os
import tempfile
from decimal import Decimal
from http.server import HTTPServer, BaseHTTPRequestHandler

from lib.config import load_config
from lib.models import InvoiceData, LineItem
from lib.pdf_renderer import render_pdf

CONFIG = load_config("defaults.yaml")  # loaded once at startup


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))

        items = [
            LineItem(
                type=li["type"],
                description=li["description"],
                quantity=Decimal(str(li["quantity"])),
                rate=Decimal(str(li["rate"])),
                tax_rate=Decimal("0"),
                date=li.get("date"),
            )
            for li in body["line_items"]
        ]
        data = InvoiceData(
            invoice_number=body["invoice_number"],
            issue_date=body["issue_date"],
            due_date=body["due_date"],
            client_name=body["client_name"],
            client_address=body["client_address"],
            client_abn=body.get("client_abn"),
            client_identity=body.get("client_identity"),
            line_items=items,
        )

        assign_tax_rates(data.line_items, CONFIG.tax_rate)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name

        render_pdf(data, CONFIG, pdf_path)

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        os.unlink(pdf_path)

        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="INV-{data.invoice_number}.pdf"',
        )
        self.send_header("Content-Length", str(len(pdf_bytes)))
        self.end_headers()
        self.wfile.write(pdf_bytes)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8787), Handler)
    print("listening on http://127.0.0.1:8787")
    server.serve_forever()
```

Run with:

```bash
uv run python server.py
```

No additional dependencies — `http.server` is stdlib. The server loads `defaults.yaml` once at startup and reuses the same `Config` for every request.

### Form-side change

Replace the YAML download block in the form's submit handler with a `fetch` call:

```javascript
const payload = {
  invoice_number: document.getElementById('invoice_number').value.trim(),
  issue_date: document.getElementById('issue_date').value,
  due_date: document.getElementById('due_date').value,
  client_name: document.getElementById('client_name').value.trim(),
  client_abn: document.getElementById('client_abn').value.trim() || null,
  client_identity: null,
  client_address: document.getElementById('client_address').value.trim(),
  line_items: [...document.querySelectorAll('#items-body tr')].map(tr => ({
    type: tr.querySelector('.item-type')?.value,
    description: tr.querySelector('.item-desc')?.value,
    date: tr.querySelector('.item-date')?.value || null,
    quantity: parseFloat(tr.querySelector('.item-qty')?.value) || 1,
    rate: parseFloat(tr.querySelector('.item-rate')?.value) || 0,
  })),
};

const res = await fetch('http://127.0.0.1:8787', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
});

if (!res.ok) {
  const err = await res.json();
  alert(err.error);
  return;
}

const blob = await res.blob();
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = `INV-${payload.invoice_number}.pdf`;
a.click();
URL.revokeObjectURL(url);
```

The JSON payload mirrors the YAML schema exactly — the same fields, same names.

## Remote access

If the server needs to be reachable beyond localhost (e.g. from a different machine on the same network), bind to `0.0.0.0` instead of `127.0.0.1`. For access over the internet, run it on a VM behind a reverse proxy with TLS. The server itself is stateless — `defaults.yaml` and system dependencies (Pango/Cairo) are the only local requirements.

## What the lib/ split enables

The pure-function design in `lib/` means the business logic is not tied to any specific entry point. The CLI (`invoicer.py`), the dev server above, and any future wrapper all call the same `assign_tax_rates → validate_invoice → render_pdf` pipeline with the same dataclass arguments. Adding a new entry point does not require changes to `lib/` or `templates/`.
