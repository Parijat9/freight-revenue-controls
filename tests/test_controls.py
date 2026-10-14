import unittest
from pipeline import connect, seed, refresh


class Controls(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.truth = seed(self.db, 500)

    def tearDown(self):
        self.db.close()

    def test_known_findings(self):
        rows = refresh(self.db)
        self.assertEqual({r["shipment_id"]: r["finding"] for r in rows}, self.truth)

    def test_replay_does_not_change_totals(self):
        first = refresh(self.db)
        seed(self.db, 500)
        self.assertEqual(first, refresh(self.db))

    def test_split_payments_do_not_multiply_invoices(self):
        refresh(self.db)
        expected = self.db.execute(
            "SELECT SUM(amount_cents) FROM invoice_current"
        ).fetchone()[0]
        actual = self.db.execute(
            "SELECT SUM(billed_cents) FROM shipment_finance"
        ).fetchone()[0]
        self.assertEqual(expected, actual)

    def test_future_receipt_excluded(self):
        before = refresh(self.db)
        self.db.execute(
            "INSERT INTO payment VALUES('future','I000001','2027-01-01',50000)"
        )
        self.assertEqual(before, refresh(self.db))

    def test_future_revision_excluded(self):
        before = refresh(self.db)
        self.db.execute(
            "INSERT INTO invoice_version VALUES('I000001',3,'S000001',999999,'2027-01-01','2027-02-01')"
        )
        self.assertEqual(before, refresh(self.db))

    def test_overlapping_rates_fail(self):
        self.db.execute(
            "INSERT INTO rate VALUES('L01','2026-06-01','2026-08-01',90000)"
        )
        with self.assertRaises(ValueError):
            refresh(self.db)

    def test_missing_rates_fail(self):
        self.db.execute("DELETE FROM rate WHERE lane_id='L01'")
        with self.assertRaises(ValueError):
            refresh(self.db)

    def test_unknown_payment_rejected(self):
        self.db.execute(
            "INSERT INTO payment VALUES('orphan','missing','2026-09-01',100)"
        )
        with self.assertRaises(ValueError):
            refresh(self.db)

    def test_one_dollar_tolerance(self):
        self.db.execute(
            "UPDATE invoice_version SET amount_cents=amount_cents-100 WHERE invoice_id='I000001'"
        )
        row = next(r for r in refresh(self.db) if r["shipment_id"] == "S000001")
        self.assertEqual(row["finding"], "matched")

    def test_effective_rate_boundary(self):
        self.db.execute(
            "INSERT INTO shipment VALUES('BOUND','C001','L01','2026-07-01',80000,0)"
        )
        row = next(r for r in refresh(self.db) if r["shipment_id"] == "BOUND")
        self.assertEqual(row["expected_cents"], 102000)


if __name__ == "__main__":
    unittest.main()
