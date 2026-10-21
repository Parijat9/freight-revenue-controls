"""Generate a self-contained, filterable review page from verified pipeline outputs."""

import json
from html import escape
from pathlib import Path


def render(path, title, subtitle, metrics, rows, narrative, chart=""):
    fields = list(rows[0]) if rows else []
    payload = json.dumps(rows).replace("<", "\\u003c")
    cards = "".join(
        f"<article><small>{escape(k)}</small><strong>{escape(str(v))}</strong></article>"
        for k, v in metrics.items()
    )
    headers = "".join(f'<th>{escape(k.replace("_", " "))}</th>' for k in fields)
    html = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>TITLE</title><style>STYLES</style>
    <header><small>RECEIVABLES / BILLING REVIEW</small><h1>TITLE</h1><p>SUBTITLE</p></header>
    <main><div class="cards">CARDS</div><div class="overview">CHART<section class="notes"><h2>Reconciliation notes</h2><p>NARRATIVE</p></section></div><section class="results"><h2>Detailed results</h2><label for="filter">Search the results</label><br><br><input id="filter" placeholder="Enter a lane, record ID or status"><p class="count" id="count"></p><div class="scroll"><table><thead><tr>HEADERS</tr></thead><tbody id="rows"></tbody></table></div></section></main><footer>Sample data. Rebuild this report with python run.py.</footer>
    <script>const data=PAYLOAD,fields=FIELDS;const body=document.getElementById('rows');function draw(){const q=document.getElementById('filter').value.toLowerCase();const filtered=data.filter(r=>Object.values(r).some(v=>String(v).toLowerCase().includes(q)));body.replaceChildren();for(const row of filtered.slice(0,500)){const tr=document.createElement('tr');for(const field of fields){const td=document.createElement('td');td.textContent=row[field];tr.appendChild(td)}body.appendChild(tr)}document.getElementById('count').textContent=filtered.length+' matching records'+(filtered.length>500?' (first 500 shown)':'')}document.getElementById('filter').addEventListener('input',draw);draw();</script></html>"""
    for key, value in [
        ("STYLES", Path(__file__).with_name("report.css").read_text(encoding="utf-8")),
        ("SUBTITLE", escape(subtitle)),
        ("TITLE", escape(title)),
        ("CARDS", cards),
        ("CHART", chart),
        ("NARRATIVE", escape(narrative)),
        ("HEADERS", headers),
        ("PAYLOAD", payload),
        ("FIELDS", json.dumps(fields)),
    ]:
        html = html.replace(key, value)
    Path(path).write_text(html, encoding="utf-8")


def comparison_chart(title, labels, series):
    """Small SVG chart. Labels and values come from the same reporting rows."""
    width, left, plot = 900, 90, 650
    height = 85 + len(labels) * (len(series) * 25 + 20)
    maximum = max((value for _, values in series for value in values), default=1) or 1
    colors = ["#997554", "#9f4529"]
    parts = [
        f'<section class="chart-panel"><h2>{escape(title)}</h2><svg role="img" aria-label="{escape(title)}" viewBox="0 0 {width} {height}" style="width:100%;max-width:1100px">'
    ]
    for j, (name, _) in enumerate(series):
        parts.append(
            f'<rect x="{left+j*250}" y="5" width="12" height="12" fill="{colors[j%2]}"/><text x="{left+20+j*250}" y="17" font-size="15">{escape(name)}</text>'
        )
    for i, label in enumerate(labels):
        y = 50 + i * (len(series) * 25 + 20)
        parts.append(
            f'<text x="5" y="{y+15}" font-size="15">{escape(str(label))}</text>'
        )
        for j, (_, values) in enumerate(series):
            value = values[i]
            bar = max(0, value) / maximum * plot
            parts.append(
                f'<rect x="{left}" y="{y+j*25}" width="{bar:.2f}" height="18" fill="{colors[j%2]}"/><text x="{left+bar+9:.2f}" y="{y+j*25+14}" font-size="14">{value:,.1f}</text>'
            )
    return "".join(parts) + "</svg></section>"
