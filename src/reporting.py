"""Report generation utilities."""

from __future__ import annotations

from datetime import datetime, timezone


def generate_markdown_report(context: dict) -> str:
    cl = context.get("chain_ladder", {})
    bootstrap = context.get("bootstrap", {})
    diag = context.get("diagnostics", {})

    return f"""# IBNR Reserving Report

Generated at: {datetime.now(timezone.utc).isoformat()}

## Scope and Method
- Reserving basis: **Accident Year only**
- Core method: **Chain Ladder**
- Uncertainty method: **ODP Bootstrap** (if run)
- Advisory note: outputs require actuarial judgment.

## Key Results
- Total IBNR (Chain Ladder): **{cl.get('total_reserve', 'N/A')}**
- Bootstrap Summary: **{bootstrap.get('summary', 'Not run')}**

## Diagnostics Commentary
- Calendar effect indicators: {diag.get('calendar_summary', 'Not available')}
- Outlier guidance: {diag.get('outlier_summary', 'Not available')}

## Assumptions and Caveats
1. Cumulative development data quality materially influences all outputs.
2. Outlier exclusions are user-selected and should be governance-approved.
3. AI commentary is advisory only.
"""
