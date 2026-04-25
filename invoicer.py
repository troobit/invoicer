#!/usr/bin/env python3
"""invoicer — local CLI for generating invoices."""
import argparse
import os
import sys
from decimal import Decimal

__version__ = "0.1.0"


def resolve_output_dir(data, config, cli_override: str | None) -> str:
    """Priority: CLI flag > invoice YAML output_path > defaults.yaml output_dir > ./invoices"""
    if cli_override:
        return cli_override
    if data.output_path:
        return data.output_path
    if config.output_dir:
        return config.output_dir
    return "./invoices"


def load_invoice_yaml(path: str):
    """Parse an invoice YAML file into an InvoiceData object."""
    import yaml
    from lib.models import InvoiceData, LineItem

    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: invoice file not found: '{path}'", file=sys.stderr)
        sys.exit(1)

    # Parse line items — rates default to 0 if omitted (overridden from config at render time)
    items = []
    for li in raw.get("line_items", []):
        items.append(LineItem(
            type=li.get("type", ""),
            description=li.get("description", ""),
            quantity=Decimal(str(li.get("quantity", 1))),
            rate=Decimal(str(li.get("rate", 0))),
            # assigned at render time from config.tax_rate
            tax_rate=Decimal("0"),
            date=li.get("date"),
        ))

    client_name = raw.get("client_name", "")
    if isinstance(client_name, list):
        client_name = [str(n) for n in client_name]
    else:
        client_name = [str(client_name)] if client_name else []

    return InvoiceData(
        invoice_number=raw.get("invoice_number", ""),
        issue_date=raw.get("issue_date", ""),
        due_date=raw.get("due_date", ""),
        client_name=client_name,
        client_address=raw.get("client_address", ""),
        client_abn=raw.get("client_abn") or None,
        client_identity=raw.get("client_identity") or None,
        line_items=items,
        output_path=raw.get("output_path") or None,
    )


def cmd_generate(args):
    from lib.config import ConfigError, load_config
    from lib.md_renderer import render_markdown
    from lib.pdf_renderer import render_pdf

    try:
        config = load_config("defaults.yaml")
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    data = load_invoice_yaml(args.invoice)

    # Assign tax rate from config to each line item for tax calculations
    for item in data.line_items:
        item.tax_rate = config.tax_rate

    out_dir = resolve_output_dir(data, config, args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    md_path = os.path.abspath(os.path.join(
        out_dir, f"INV-{data.invoice_number}.md"))
    pdf_path = os.path.abspath(os.path.join(
        out_dir, f"INV-{data.invoice_number}.pdf"))

    for path in (md_path, pdf_path):
        if os.path.exists(path):
            print(
                f"Warning: overwriting existing file {path}", file=sys.stderr)

    md_content = render_markdown(data, config)
    with open(md_path, "w") as f:
        f.write(md_content)

    render_pdf(data, config, pdf_path)

    print(md_path)
    print(pdf_path)


def cmd_form(args):
    from lib.config import ConfigError, load_config
    from lib.form import generate_form

    try:
        config = load_config("defaults.yaml")
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    output = args.output if args.output else "invoice_form.html"
    generate_form(config, output)
    print(f"Form written to: {os.path.abspath(output)}")


def main():
    parser = argparse.ArgumentParser(
        prog="invoicer",
        description="Generate invoices.",
    )
    parser.add_argument("--version", action="version",
                        version=f"invoicer {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    # generate
    gen_parser = subparsers.add_parser(
        "generate", help="Generate MD and PDF invoice from YAML.")
    gen_parser.add_argument("invoice", help="Path to YAML file.")
    gen_parser.add_argument("--output-dir", default=None,
                            help="Override the output directory.")

    # form
    form_parser = subparsers.add_parser(
        "form", help="Generate the static HTML invoice form (helps build YAML).")
    form_parser.add_argument("--output", default=None,
                             help="Path for invoice_form.html output")

    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "form":
        cmd_form(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
