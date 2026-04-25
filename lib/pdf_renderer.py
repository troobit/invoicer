"""PDF invoice renderer — Jinja2 template → HTML → Playwright/Chromium → PDF file."""
import os
import sys
import tempfile
from pathlib import Path

from jinja2 import FileSystemLoader, Environment

from lib.formatting import format_aud
from lib.models import InvoiceData
from lib.config import Config

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def render_pdf(data: InvoiceData, config: Config, output_path: str) -> None:
    """Render invoice as PDF and write to output_path."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Error: playwright is not installed.\n"
            "Install it with: pip install playwright\n"
            "Then install Chromium with: playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    logo_path = config.logo_path
    logo_uri = Path(logo_path).resolve().as_uri() if logo_path and os.path.exists(logo_path) else None

    env = Environment(
        loader=FileSystemLoader(os.path.abspath(_TEMPLATES_DIR)),
        autoescape=True,
        keep_trailing_newline=True,
    )
    env.filters["aud"] = format_aud

    template = env.get_template("invoice.html.j2")
    html_string = template.render(data=data, config=config, logo_uri=logo_uri)

    # Write HTML to a temp file so Chromium loads it via a file:// URI.
    # This is required because the logo src is a file:// URI — Chromium only
    # allows cross-origin file:// requests when the page itself is also file://.
    tmp_html = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
            f.write(html_string)
            tmp_html = f.name

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(Path(tmp_html).as_uri())
            # print_background=True preserves the dark header band, which is
            # rendered via CSS background-color and would be stripped without it.
            page.pdf(path=output_path, format="A4", print_background=True)
            browser.close()
    finally:
        if tmp_html and os.path.exists(tmp_html):
            os.unlink(tmp_html)
