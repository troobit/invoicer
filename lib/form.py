"""Static HTML form generator — reads defaults.yaml config and bakes in default rates."""
import os

from jinja2 import FileSystemLoader, Environment

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def generate_form(config, output_path: str = "invoice_form.html") -> None:
    """Render form.html.j2 with defaults baked in and write to output_path."""
    env = Environment(
        loader=FileSystemLoader(os.path.abspath(_TEMPLATES_DIR)),
        autoescape=False,
        keep_trailing_newline=True,
    )

    template = env.get_template("form.html.j2")
    html = template.render(
        rates=config.rates,
        payment_terms_days=config.payment_terms_days,
    )

    with open(output_path, "w") as f:
        f.write(html)
