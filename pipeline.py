"""Reproducible freight billing controls. All money is stored in integer USD cents."""

import csv
import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
AS_OF = "2026-09-30"


def connect(path=":memory:"):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript((HERE / "sql/schema.sql").read_text())
    return db


def seed(db, n=4000):
    rng = random.Random(29)
    truth = {}
    with db:
        for c in range(1, 41):
            db.execute(
                "INSERT OR IGNORE INTO customer VALUES(?,?)",
                (f"C{c:03}", ["retail", "industrial", "food"][c % 3]),
            )
        for l in range(1, 9):
            db.execute(
                "INSERT OR IGNORE INTO lane VALUES(?,?)", (f"L{l:02}", 200 + l * 110)
            )
            for start, end, rate in [
                ("2026-01-01", "2026-07-01", 80000 + l * 17000),
                ("2026-07-01", "2027-01-01", 85000 + l * 17000),
            ]:
                db.execute(
                    "INSERT OR IGNORE INTO rate VALUES(?,?,?,?)",
                    (f"L{l:02}", start, end, rate),
                )
        for i in range(1, n + 1):
            sid = f"S{i:06}"
            lid = rng.randint(1, 8)
            delivered = date(2026, 4, 1) + timedelta(days=rng.randrange(168))
            access = rng.choice([0, 0, 0, 7500, 15000])
            expected = (
                (80000 if delivered < date(2026, 7, 1) else 85000)
                + lid * 17000
                + access
            )
            cost = int(expected * rng.uniform(0.72, 0.96))
            db.execute(
                "INSERT OR IGNORE INTO shipment VALUES(?,?,?,?,?,?)",
                (
                    sid,
                    f"C{rng.randint(1,40):03}",
                    f"L{lid:02}",
                    str(delivered),
                    cost,
                    access,
                ),
            )
            kind = "matched"
            amount = expected
            if i % 41 == 0:
                kind = "unbilled"
            elif i % 37 == 0:
                kind = "multiple_invoices"
            elif i % 29 == 0:
                kind = "underbilled"
                amount -= 7500
            elif i % 31 == 0:
                kind = "overbilled"
                amount += 5000
            truth[sid] = kind
            if kind == "unbilled":
                continue
            iid = f"I{i:06}"
            issued = delivered + timedelta(days=2)
            due = issued + timedelta(days=30)
            # Old versions are source history, never additive invoices.
            if i % 7 == 0:
                db.execute(
                    "INSERT OR IGNORE INTO invoice_version VALUES(?,?,?,?,?,?)",
                    (iid, 1, sid, amount - 2500, str(issued), str(due)),
                )
            db.execute(
                "INSERT OR IGNORE INTO invoice_version VALUES(?,?,?,?,?,?)",
                (iid, 2, sid, amount, str(issued), str(due)),
            )
            if kind == "multiple_invoices":
                db.execute(
                    "INSERT OR IGNORE INTO invoice_version VALUES(?,?,?,?,?,?)",
                    (iid + "D", 1, sid, amount, str(issued), str(due)),
                )
            # Partial, full and late receipts, with two transactions for settled invoices.
            if i % 5:
                half = amount // 2
                for p, days, value in [(1, 15, half), (2, 45, amount - half)]:
                    db.execute(
                        "INSERT OR IGNORE INTO payment VALUES(?,?,?,?)",
                        (iid + str(p), iid, str(issued + timedelta(days=days)), value),
                    )
    return truth


def refresh(db, as_of=AS_OF):
    date.fromisoformat(as_of)
    # Contracts must resolve to exactly one rate for each shipment.
    invalid = db.execute(
        "SELECT s.shipment_id FROM shipment s LEFT JOIN rate r ON s.lane_id=r.lane_id AND s.delivered_on>=r.valid_from AND s.delivered_on<r.valid_to GROUP BY s.shipment_id HAVING COUNT(r.lane_id)<>1"
    ).fetchall()
    if invalid:
        raise ValueError("Missing or overlapping effective rates")
    orphan = db.execute(
        "SELECT p.invoice_id FROM payment p LEFT JOIN invoice_version i USING(invoice_id) WHERE i.invoice_id IS NULL LIMIT 1"
    ).fetchone()
    if orphan:
        raise ValueError("Payment references an unknown invoice")
    db.execute("CREATE TEMP TABLE IF NOT EXISTS settings(as_of TEXT)")
    db.execute("DELETE FROM settings")
    db.execute("INSERT INTO settings VALUES(?)", (as_of,))
    db.executescript((HERE / "sql/marts.sql").read_text())
    return [
        dict(r)
        for r in db.execute(
            "SELECT * FROM audit_queue ORDER BY revenue_gap_cents DESC,shipment_id"
        )
    ]


def write_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    db = connect(out / "warehouse.db")
    truth = seed(db)
    rows = refresh(db)
    flags = [r for r in rows if r["finding"] != "matched"]
    tp = sum(r["finding"] == truth[r["shipment_id"]] for r in flags)
    positives = sum(v != "matched" for v in truth.values())
    metrics = {
        "shipments": len(rows),
        "exceptions": len(flags),
        "revenue_gap_usd": round(sum(r["revenue_gap_cents"] for r in rows) / 100, 2),
        "overdue_usd": round(sum(r["overdue_cents"] for r in rows) / 100, 2),
        "precision": tp / len(flags) if flags else None,
        "recall": tp / positives if positives else None,
        "as_of": AS_OF,
        "data": "synthetic",
        "seed": 29,
    }
    write_csv(out / "shipment_finance.csv", rows)
    write_csv(out / "audit_queue.csv", flags)
    lanes = [
        dict(r)
        for r in db.execute(
            "SELECT lane_id,COUNT(*) shipments,SUM(expected_cents)/100.0 expected_usd,SUM(billed_cents)/100.0 billed_usd,SUM(carrier_cost_cents)/100.0 carrier_cost_usd,SUM(billed_margin_cents)/100.0 billed_margin_usd,SUM(overdue_cents)/100.0 overdue_usd FROM shipment_finance GROUP BY lane_id"
        )
    ]
    write_csv(out / "lane_summary.csv", lanes)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    db.close()
    return metrics, flags
