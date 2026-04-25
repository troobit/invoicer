"""Data models for invoices — LineItem and InvoiceData."""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


@dataclass
class LineItem:
    type: str
    description: str
    quantity: Decimal
    rate: Decimal
    tax_rate: Decimal
    date: str | None = None

    @property
    def net(self) -> Decimal:
        return (self.quantity * self.rate).quantize(CENTS, rounding=ROUND_HALF_UP)

    @property
    def tax(self) -> Decimal:
        return (self.net * self.tax_rate).quantize(CENTS, rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        return self.net + self.tax


@dataclass
class InvoiceData:
    invoice_number: str
    issue_date: str
    due_date: str
    client_name: list[str]
    client_address: str
    client_abn: str | None
    client_identity: str | None
    line_items: list
    output_path: str | None = None

    @property
    def subtotal(self) -> Decimal:
        return sum((item.net for item in self.line_items), Decimal("0"))

    @property
    def total_tax(self) -> Decimal:
        return sum((item.tax for item in self.line_items), Decimal("0"))

    @property
    def total_payable(self) -> Decimal:
        return self.subtotal + self.total_tax
