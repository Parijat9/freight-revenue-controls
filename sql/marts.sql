-- As-of semantics: an invoice correction arriving after the cutoff must not restate this snapshot.
DROP VIEW IF EXISTS invoice_current;
CREATE TEMP VIEW invoice_current AS
WITH ranked AS (
 SELECT *, ROW_NUMBER() OVER (PARTITION BY invoice_id ORDER BY version DESC) AS rn
 FROM invoice_version WHERE issued_on <= (SELECT as_of FROM settings)
) SELECT invoice_id,shipment_id,amount_cents,issued_on,due_on FROM ranked WHERE rn=1;

-- Aggregate payment grain BEFORE joining invoices. Split payments cannot multiply revenue.
DROP VIEW IF EXISTS invoice_balance;
CREATE TEMP VIEW invoice_balance AS
WITH paid AS (
 SELECT invoice_id,SUM(amount_cents) AS paid_cents FROM payment
 WHERE paid_on <= (SELECT as_of FROM settings) GROUP BY invoice_id
)
SELECT i.*, COALESCE(paid_cents,0) AS paid_cents,
 MAX(0,i.amount_cents-COALESCE(paid_cents,0)) AS outstanding_cents,
 MAX(0,CAST(julianday((SELECT as_of FROM settings))-julianday(due_on) AS INTEGER)) AS days_overdue
FROM invoice_current i LEFT JOIN paid p USING(invoice_id);

DROP VIEW IF EXISTS shipment_finance;
CREATE TEMP VIEW shipment_finance AS
WITH billed AS (
 SELECT shipment_id,COUNT(*) AS invoice_count,SUM(amount_cents) AS billed_cents,
 SUM(outstanding_cents) AS outstanding_cents,
 SUM(CASE WHEN days_overdue>0 THEN outstanding_cents ELSE 0 END) AS overdue_cents
 FROM invoice_balance GROUP BY shipment_id
)
SELECT s.*,r.linehaul_cents+s.accessorial_cents AS expected_cents,
 COALESCE(b.invoice_count,0) AS invoice_count,COALESCE(b.billed_cents,0) AS billed_cents,
 COALESCE(b.outstanding_cents,0) AS outstanding_cents,COALESCE(b.overdue_cents,0) AS overdue_cents,
 COALESCE(b.billed_cents,0)-s.carrier_cost_cents AS billed_margin_cents
FROM shipment s JOIN rate r ON s.lane_id=r.lane_id AND s.delivered_on>=r.valid_from AND s.delivered_on<r.valid_to
LEFT JOIN billed b USING(shipment_id)
WHERE s.delivered_on <= (SELECT as_of FROM settings);

DROP VIEW IF EXISTS audit_queue;
CREATE TEMP VIEW audit_queue AS
SELECT *,CASE WHEN invoice_count=0 THEN 'unbilled'
 WHEN invoice_count>1 THEN 'multiple_invoices'
 WHEN billed_cents < expected_cents-100 THEN 'underbilled'
 WHEN billed_cents > expected_cents+100 THEN 'overbilled'
 ELSE 'matched' END AS finding,
 MAX(0,expected_cents-billed_cents) AS revenue_gap_cents
FROM shipment_finance;
