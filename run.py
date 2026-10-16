from pathlib import Path
import json
from pipeline import run
from report import render, comparison_chart

if __name__ == "__main__":
    out = Path("build")
    metrics, rows = run(out)
    lanes = sorted({r["lane_id"] for r in rows})
    gaps = [
        sum(r["revenue_gap_cents"] for r in rows if r["lane_id"] == lane) / 100
        for lane in lanes
    ]
    chart = comparison_chart(
        "Potential billing gap by lane (USD)", lanes, [("Billing gap", gaps)]
    )
    render(
        out / "index.html",
        "Freight billing checks",
        "Compare shipments, agreed rates, invoices and payments. Figures as of 30 September 2026.",
        {
            "Delivered shipments": f"{metrics['shipments']:,}",
            "Items to review": metrics["exceptions"],
            "Potential billing gap": f"${metrics['revenue_gap_usd']:,.0f}",
            "Overdue payments": f"${metrics['overdue_usd']:,.0f}",
        },
        [
            {
                "shipment_id": r["shipment_id"],
                "lane": r["lane_id"],
                "finding": r["finding"],
                "expected_usd": r["expected_cents"] / 100,
                "billed_usd": r["billed_cents"] / 100,
                "gap_usd": r["revenue_gap_cents"] / 100,
            }
            for r in rows
        ],
        "Check missing bills and undercharges with the billing team. If a shipment has several invoices, review them before making changes. Overdue payments and potential billing gaps measure different things; do not add them together. The results come from sample records with known errors.",
        chart=chart,
    )
    print(json.dumps(metrics, indent=2))
