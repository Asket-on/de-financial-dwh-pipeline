from __future__ import annotations

import argparse
import sys
import tempfile
from contextlib import closing
from html import escape
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.local_warehouse import connect_local_warehouse, run_pipeline

DASHBOARD_PATH = PROJECT_ROOT / "docs" / "dashboard.html"
CURRENCY_NAMES = {840: "USD", 978: "EUR"}


def build_dashboard_html() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "financial_dwh.sqlite"
        summary = run_pipeline(database_path)
        with closing(connect_local_warehouse(database_path)) as connection:
            rows = connection.execute(
                """
                select date_update, currency_from, amount_total, amount_usd_total,
                       transaction_count
                from dwh_global_metrics
                order by date_update, currency_from
                """
            ).fetchall()

    total_usd = sum(row["amount_usd_total"] for row in rows)
    transaction_count = sum(row["transaction_count"] for row in rows)
    active_days = len({row["date_update"] for row in rows})
    currencies = len({row["currency_from"] for row in rows})
    max_usd = max(row["amount_usd_total"] for row in rows)

    chart_rows = "\n".join(
        f"""
          <div class="bar-row">
            <div><strong>{escape(row["date_update"])}</strong><span>{CURRENCY_NAMES.get(row["currency_from"], row["currency_from"])}</span></div>
            <div class="bar-track"><div class="bar" style="width: {row["amount_usd_total"] / max_usd * 100:.1f}%"></div></div>
            <strong>${row["amount_usd_total"]:,.2f}</strong>
          </div>"""
        for row in rows
    )
    table_rows = "\n".join(
        f"""
            <tr>
              <td>{escape(row["date_update"])}</td>
              <td>{CURRENCY_NAMES.get(row["currency_from"], row["currency_from"])}</td>
              <td>{row["amount_total"]:,.2f}</td>
              <td>${row["amount_usd_total"]:,.2f}</td>
              <td>{row["transaction_count"]}</td>
            </tr>"""
        for row in rows
    )
    quality_rows = "\n".join(
        f'<li><span>{escape(name.replace("_", " ").title())}</span><strong>{count} failures</strong></li>'
        for name, count in summary["quality_checks"].items()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Financial DWH Metrics Dashboard</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #17202a; background: #f4f7f8; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; }}
    header {{ background: #173b45; color: white; padding: 32px max(24px, calc((100vw - 1120px) / 2)); }}
    header p {{ color: #c5d9dd; margin: 8px 0 0; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
    h1, h2 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: 28px; }}
    h2 {{ font-size: 18px; margin-bottom: 18px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
    .kpi, .panel {{ background: white; border: 1px solid #dce5e7; border-radius: 6px; }}
    .kpi {{ padding: 18px; }}
    .kpi span {{ color: #5e7176; font-size: 13px; }}
    .kpi strong {{ display: block; font-size: 25px; margin-top: 6px; }}
    .grid {{ display: grid; grid-template-columns: 1.7fr 1fr; gap: 16px; }}
    .panel {{ padding: 20px; margin-bottom: 16px; }}
    .bar-row {{ display: grid; grid-template-columns: 125px 1fr 86px; gap: 12px; align-items: center; margin: 15px 0; font-size: 13px; }}
    .bar-row span {{ color: #6e7d81; display: block; margin-top: 3px; }}
    .bar-track {{ height: 14px; background: #e8eef0; border-radius: 3px; overflow: hidden; }}
    .bar {{ height: 100%; background: #e85d4a; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 11px 8px; border-bottom: 1px solid #e5ebed; text-align: right; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
    th {{ color: #5e7176; font-weight: 600; }}
    ul {{ list-style: none; padding: 0; margin: 0; }}
    li {{ display: flex; justify-content: space-between; gap: 16px; padding: 11px 0; border-bottom: 1px solid #e5ebed; font-size: 13px; }}
    li strong {{ color: #16734b; white-space: nowrap; }}
    footer {{ color: #687a7f; font-size: 12px; padding-top: 4px; }}
    @media (max-width: 760px) {{
      .kpis {{ grid-template-columns: repeat(2, 1fr); }}
      .grid {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 95px 1fr 78px; }}
      .panel {{ overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Financial DWH Metrics Dashboard</h1>
    <p>Synthetic daily mart output with verified data-quality gates</p>
  </header>
  <main>
    <section class="kpis" aria-label="Key performance indicators">
      <div class="kpi"><span>Total USD equivalent</span><strong>${total_usd:,.2f}</strong></div>
      <div class="kpi"><span>Transactions</span><strong>{transaction_count}</strong></div>
      <div class="kpi"><span>Active days</span><strong>{active_days}</strong></div>
      <div class="kpi"><span>Currencies</span><strong>{currencies}</strong></div>
    </section>
    <div class="grid">
      <div>
        <section class="panel">
          <h2>USD equivalent by date and currency</h2>
          {chart_rows}
        </section>
        <section class="panel">
          <h2>Mart rows</h2>
          <table>
            <thead><tr><th>Date</th><th>Currency</th><th>Native amount</th><th>USD equivalent</th><th>Transactions</th></tr></thead>
            <tbody>{table_rows}
            </tbody>
          </table>
        </section>
      </div>
      <aside>
        <section class="panel">
          <h2>Data-quality gates</h2>
          <ul>{quality_rows}</ul>
        </section>
        <section class="panel">
          <h2>Refresh contract</h2>
          <ul>
            <li><span>Inclusive window</span><strong>{summary["refresh_start"]} to {summary["refresh_end"]}</strong></li>
            <li><span>Refreshed mart rows</span><strong>{summary["refreshed_rows"]}</strong></li>
            <li><span>Superseded rates</span><strong>{summary["profile"]["currencies.superseded_versions"]}</strong></li>
          </ul>
        </section>
      </aside>
    </div>
    <footer>Generated deterministically from the repository's synthetic sources by <code>python scripts/build_dashboard.py</code>.</footer>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the reproducible mart dashboard")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if docs/dashboard.html does not match the generated dashboard",
    )
    args = parser.parse_args()
    generated = build_dashboard_html()
    if args.check:
        if not DASHBOARD_PATH.exists() or DASHBOARD_PATH.read_text(encoding="utf-8") != generated:
            raise SystemExit("docs/dashboard.html is out of date; run python scripts/build_dashboard.py")
        print("dashboard_artifact=up_to_date")
        return
    DASHBOARD_PATH.write_text(generated, encoding="utf-8")
    print(f"dashboard_artifact={DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
