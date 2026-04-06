"""Triangle construction utilities."""

from __future__ import annotations

import chainladder as cl
import pandas as pd


def build_triangle(clean_df: pd.DataFrame, cumulative: bool = True) -> cl.Triangle:
    """Build a chainladder triangle from AY + development age data."""
    work = clean_df.copy()
    work["origin_date"] = pd.to_datetime(work["accident_year"].astype(str) + "-01-01")
    work["valuation_year"] = work["accident_year"] + (work["development"] // 12) - 1
    work["valuation_date"] = pd.to_datetime(work["valuation_year"].astype(int).astype(str) + "-12-31")

    tri = cl.Triangle(
        work,
        origin="origin_date",
        development="valuation_date",
        columns=["value"],
        cumulative=cumulative,
    )
    return tri


def triangle_to_dataframe(triangle: cl.Triangle) -> pd.DataFrame:
    out = triangle.to_frame(origin_as_datetime=False).reset_index()
    out.columns = [str(c) for c in out.columns]
    if "origin" not in out.columns:
        if "index" in out.columns:
            out = out.rename(columns={"index": "origin"})
        else:
            out = out.rename(columns={out.columns[0]: "origin"})
    return out
