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
        "Freight revenue controls",
        "Shipment-to-invoice reconciliation and overdue receivables. Reporting cutoff: 30 September 2026.",
        {
            "Delivered shipments": f"{metrics['shipments']:,}",
            "Review exceptions": metrics["exceptions"],
            "Potential billing gap": f"${metrics['revenue_gap_usd']:,.0f}",
            "Overdue receivables": f"${metrics['overdue_usd']:,.0f}",
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
        "Review unbilled and underbilled loads with billing operations. Multiple invoices require investigation, not automatic deletion. Receivables and potential billing gaps are separate measures and must not be added together. The perfect fixture classification measures known injected cases, not production detection quality.",
        chart=chart,
    )
    print(json.dumps(metrics, indent=2))
