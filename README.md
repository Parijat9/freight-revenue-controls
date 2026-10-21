# Freight billing checks

Checks whether completed shipments have been billed correctly and which invoices still need payment.

For each shipment, the report compares the agreed rate, the invoice and the payments received. It puts differences in a list that a billing team can review.

## Billing review desk

A ledger-style view of shipment charges and receivables, with lane-level exceptions and a searchable review list.

![Billing report showing amounts to check](docs/preview.png)

[Open the sample report](https://parijat9.github.io/reports/revenue.html)

## What it does

- Finds shipments with no invoice, more than one invoice, or a different amount than expected.
- Uses the rate that applied on the shipment date.
- Uses the latest invoice available on the chosen reporting date.
- Adds separate payments together before checking the balance.
- Keeps billing mistakes separate from overdue payments.

## Try it

Install Python 3.10 or newer, then run these commands from this folder. No extra packages or accounts are needed.

```bash
python -m unittest discover -s tests -v
python run.py
```

Open `build/index.html` in your browser. Use its search box to find a shipment, route or issue. The run also saves CSV files for spreadsheets and a local SQLite database.

## Sample results

The included example uses 4,000 made-up shipments. It finds 453 items to review and $169,170 in possible missing or incorrect billing. This is an amount to investigate, not money recovered. The overdue balance is a separate total.

## How it works

1. Load the sample shipments, rates, invoices and payments.
2. Match each shipment to the right rate and invoice.
3. Compare the amounts and calculate what is still owed.
4. Save a review list and a browser report.

Python runs the steps. SQL checks the records. GitHub Actions reruns the tests and report after changes and each Monday.

## Files worth opening

- [SQL checks](sql/marts.sql)
- [Billing rules](docs/controls.md)
- [Power BI and Tableau setup](bi/README.md)
- [How to run and check the results](docs/runbook.md)

## What still needs work

The example assumes one customer invoice per shipment. Taxes, credit notes, currency changes and split billing need additional rules. Power BI and Tableau files contain queries and calculations to build from, not finished desktop reports.
