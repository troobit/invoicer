# Invoice YAML schema

## Example

```yaml
invoice_number: '2024-05-001'
issue_date: '2024-05-01'
due_date: '2024-05-15'
client_name: 'ACME Pty Ltd'
client_abn: '98 765 432 109'
client_identity: null
client_address: '58 Manson Road, D4'
output_path: null

line_items:
  - type: hourly
    description: 'Backend consulting — auth service'
    date: '2024-04-29'
    quantity: 4
    rate: 220.00

  - type: callout
    description: 'Emergency after-hours support'
    date: '2024-04-30'
    quantity: 1
    rate: 450.00

  - type: reimbursement
    description: 'Cloud compute costs'
    date: '2024-04-30'
    quantity: 1
    rate: 87.50
```

## Invoice-level fields

| Field | Required | Notes |
|-------|----------|-------|
| `invoice_number` | Yes | Used in output filename: `INV-<number>.md/.pdf` |
| `issue_date` | Yes | `YYYY-MM-DD` |
| `due_date` | Yes | `YYYY-MM-DD` |
| `client_name` | Yes | |
| `client_address` | Yes | |
| `client_abn` | Conditional | Required when total >= $1,000 (unless `client_identity` is set) |
| `client_identity` | Conditional | Alternative to ABN for unregistered clients |
| `output_path` | No | Per-invoice output directory override |

## Line item fields

| Field | Required | Notes |
|-------|----------|-------|
| `type` | Yes | Must match a billing type below |
| `description` | Yes | Free text |
| `quantity` | Yes | Decimal: hours, days, units |
| `rate` | Yes | AUD per unit. Falls back to the matching rate in `defaults.yaml` when 0 or omitted |
| `date` | No | `YYYY-MM-DD`. Rendered in the line items table |

## Billing types

| Type | Unit |
|------|------|
| `hourly` | Per hour |
| `overtime` | Per hour (after-hours) |
| `white_glove` | Per hour (premium) |
| `on_call` | Per 24h period |
| `on_premise` | Per day |
| `callout` | Per callout |
| `reimbursement` | Pass-through (no default rate) |
| `disbursement` | Pass-through (no default rate) |

## Tax

`tax_rate` is not part of this schema. It is sourced from `defaults.yaml` and applied uniformly to every line item during the generate pipeline. When `tax_rate` is `0.00`, tax columns are omitted from both Markdown and PDF output.
