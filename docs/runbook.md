# Operating procedure

Run `python run.py` from the repository root. The default fixture is deterministic.
Keep production exports outside this public repository.

On a failed rate check, repair the effective-date source record and rerun. Do not
remove the check to make the dashboard refresh. On an unknown payment reference,
confirm whether the invoice extract is incomplete before classifying it as an error.

Billing reviews unbilled and amount differences. Receivables reviews overdue balances.
Operations supplies delivery evidence. Commercial confirms the applicable rate.
Record the resolution in the source system; this project never changes an invoice.

The Monday GitHub Actions run uses synthetic data only and retains generated reports
for 14 days. It does not send email or connect to a company account. For larger sources,
replace fixture seeding with transactional upserts and a source batch ledger. The demo
seed routine uses INSERT OR IGNORE and is not a production change-data-capture loader.
