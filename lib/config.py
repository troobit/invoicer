"""Configuration loader for defaults.yaml."""
import os
from dataclasses import dataclass
from decimal import Decimal

import yaml


class ConfigError(Exception):
    """Raised when defaults.yaml is missing, invalid, or fails ABN validation."""


@dataclass
class Config:
    entity_name: str
    abn: str
    address: str
    email: str
    phone: str
    bank_name: str
    bsb: str
    account_number: str
    payment_terms_days: int
    output_dir: str
    logo_path: str
    tax_rate: Decimal
    late_payment_fee: Decimal
    late_payment_margin: Decimal
    rates: dict[str, Decimal]


def validate_abn(abn: str) -> bool:
    """Return True if abn passes the ATO mod-89 weighted checksum."""
    abn = abn.replace(" ", "").replace("-", "")
    if not abn.isdigit() or len(abn) != 11:
        return False
    weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    total = sum(
        (int(d) - (1 if i == 0 else 0)) * w
        for i, (d, w) in enumerate(zip(abn, weights))
    )
    return total % 89 == 0


_REQUIRED_FIELDS = [
    "entity_name", "abn", "address", "email", "phone",
    "bank_name", "bsb", "account_number", "payment_terms_days",
    "late_payment_fee", "late_payment_margin", "rates",
]


def load_config(path: str = "defaults.yaml") -> Config:
    """Load and validate defaults.yaml. Raises ConfigError on failure."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(
            f"defaults.yaml not found at '{path}'. "
            "Copy defaults.yaml.example and fill in your details."
        )

    missing = [field for field in _REQUIRED_FIELDS if field not in data]
    if missing:
        raise ConfigError(
            f"Missing required config fields: {', '.join(missing)}")

    abn = data["abn"]
    if not validate_abn(abn):
        raise ConfigError(
            f"ABN '{abn}' invalid."
        )

    logo_path = os.path.expanduser(
        data.get("logo_path", "~/repos/cvsite/static/logo.light.svg"))

    rates = {k: Decimal(str(v)) for k, v in data["rates"].items()}

    return Config(
        entity_name=data["entity_name"],
        abn=abn,
        address=data["address"],
        email=data["email"],
        phone=data["phone"],
        bank_name=data["bank_name"],
        bsb=data["bsb"],
        account_number=data["account_number"],
        payment_terms_days=int(data["payment_terms_days"]),
        output_dir=data.get("output_dir", "./invoices"),
        logo_path=logo_path,
        tax_rate=Decimal(str(data.get("tax_rate", "0.00"))),
        late_payment_fee=Decimal(str(data["late_payment_fee"])),
        late_payment_margin=Decimal(str(data["late_payment_margin"])),
        rates=rates,
    )
