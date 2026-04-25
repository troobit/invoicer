"""Markdown invoice renderer — Jinja2 template → Markdown string."""
import os

from jinja2 import FileSystemLoader, Environment

from lib.formatting import format_aud

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def render_markdown(data, config) -> str:
    """Return rendered Markdown string from invoice data and config."""
    env = Environment(
        loader=FileSystemLoader(os.path.abspath(_TEMPLATES_DIR)),
        autoescape=False,
        keep_trailing_newline=True,
    )
    env.filters["aud"] = format_aud

    template = env.get_template("invoice.md.j2")
    return template.render(data=data, config=config)
