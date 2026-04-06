"""Triangle construction utilities."""

from __future__ import annotations

import chainladder as cl
import pandas as pd


def build_triangle(clean_df: pd.DataFrame, cumulative: bool = True) -> cl.Triangle:
    tri = cl.Triangle(
        clean_df,
        origin="accident_year",
        development="development",
        columns=["value"],
        cumulative=cumulative,
    )
    return tri


def triangle_to_dataframe(triangle: cl.Triangle) -> pd.DataFrame:
    out = triangle.to_frame(origin_as_datetime=False).reset_index()
    return out
