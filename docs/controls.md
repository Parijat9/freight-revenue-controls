# Control definitions

## Grain and ownership

| Object | Grain | Business owner |
|---|---|---|
| Shipment | One delivered load | Operations |
| Rate | Lane and effective start date | Commercial |
| Invoice version | Invoice ID and revision | Billing |
| Payment | Receipt transaction | Receivables |
| Shipment finance | One load at the report cutoff | Finance analytics |

Expected revenue equals the effective lane linehaul rate plus approved accessorials.
Billed margin equals current invoiced revenue less carrier cost. It is not net profit.
Outstanding balance is max(invoice amount minus receipts through cutoff, zero).
An invoice is overdue only after its due date. Future receipts and future revisions
do not change a historical snapshot.

## Rule precedence

1. No current invoice: unbilled.
2. More than one current invoice: multiple invoices, regardless of their combined amount.
3. Billed below expected by more than $1: underbilled.
4. Billed above expected by more than $1: overbilled.
5. Otherwise: matched.

The revenue gap sums positive expected-minus-billed differences. Overbilling cannot
offset another shipment's underbilling. Rates are checked before generating results.
One missing rate blocks publication rather than quietly dropping a shipment.

## Acceptance criteria

- Every eligible shipment appears exactly once.
- Invoice totals reconcile before and after the payment join.
- The same source replay produces identical financial totals.
- A 1 July shipment uses the new rate; 30 June uses the previous rate.
- Known injected findings match the independent generator labels.
- Missing and overlapping rates, unknown invoice receipts and future-dated updates
  have explicit tests.

## Delivery sequence

Agree the grain and definitions with billing; reconcile a closed period; review
exceptions with operations; validate report totals; schedule the refresh; obtain
business sign-off before allowing any downstream financial adjustment.

This repository completes the demonstrator, tests and local report. Live source
onboarding and native BI refresh are deployment acceptance tasks, not claimed results.
