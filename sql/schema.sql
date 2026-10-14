PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS customer(customer_id TEXT PRIMARY KEY, segment TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lane(lane_id TEXT PRIMARY KEY, miles INTEGER NOT NULL CHECK(miles>0));
CREATE TABLE IF NOT EXISTS rate(lane_id TEXT REFERENCES lane, valid_from TEXT, valid_to TEXT, linehaul_cents INTEGER, PRIMARY KEY(lane_id,valid_from));
CREATE TABLE IF NOT EXISTS shipment(shipment_id TEXT PRIMARY KEY, customer_id TEXT REFERENCES customer, lane_id TEXT REFERENCES lane, delivered_on TEXT NOT NULL, carrier_cost_cents INTEGER NOT NULL CHECK(carrier_cost_cents>=0), accessorial_cents INTEGER NOT NULL CHECK(accessorial_cents>=0));
CREATE TABLE IF NOT EXISTS invoice_version(invoice_id TEXT, version INTEGER, shipment_id TEXT REFERENCES shipment, amount_cents INTEGER NOT NULL, issued_on TEXT, due_on TEXT, PRIMARY KEY(invoice_id,version));
CREATE TABLE IF NOT EXISTS payment(payment_id TEXT PRIMARY KEY, invoice_id TEXT NOT NULL, paid_on TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(amount_cents>0));
CREATE INDEX IF NOT EXISTS ix_invoice_shipment ON invoice_version(shipment_id);
CREATE INDEX IF NOT EXISTS ix_payment_invoice ON payment(invoice_id,paid_on);
