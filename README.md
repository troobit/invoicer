# invoicer

CLI tool that generates invoices as Markdown and PDF from YAML input files. Configuration is YAML-based; the business logic is decoupled from I/O for portability.

## Documentation

| File | Scope |
|------|-------|
| [docs/setup.md](setup.md) | Installation via `uv`, `defaults.yaml` configuration |
| [docs/usage.md](usage.md) | HTML form and CLI workflows |
| [docs/invoice-yaml.md](invoice-yaml.md) | Invoice YAML schema and field reference |
| [docs/architecture.md](architecture.md) | Module structure, data flow, design rationale |
| [docs/automation.md](automation.md) | Automating the form-to-PDF workflow with a local server |

## Quick start

```bash
uv sync
cp defaults.yaml.example defaults.yaml
# edit defaults.yaml with real supplier details
uv run invoicer.py generate path/to/invoice.yaml
```

Produces `INV-<number>.md` and `INV-<number>.pdf` in the configured output directory.
