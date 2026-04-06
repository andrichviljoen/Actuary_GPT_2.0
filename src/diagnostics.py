"""Diagnostic chart generators."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px


def triangle_heatmap(triangle_df: pd.DataFrame, title: str):
    mat = triangle_df.set_index("origin")
    fig = px.imshow(mat, aspect="auto", color_continuous_scale="Blues", title=title)
    fig.update_layout(xaxis_title="Development Age", yaxis_title="Accident Year")
    return fig


def trend_by_origin(triangle_df: pd.DataFrame):
    long = triangle_df.melt(id_vars=["origin"], var_name="development", value_name="value").dropna()
    fig = px.line(long, x="development", y="value", color="origin", title="Origin (AY) Development Trend")
    return fig


def calendar_effect_series(triangle_df: pd.DataFrame) -> pd.DataFrame:
    long = triangle_df.melt(id_vars=["origin"], var_name="development", value_name="value").dropna()
    long["development"] = long["development"].astype(int)
    long["calendar_year"] = long["origin"].astype(int) + long["development"] - 1
    cal = long.groupby("calendar_year", as_index=False)["value"].mean().rename(columns={"value": "avg_value"})
    cal["z_score"] = (cal["avg_value"] - cal["avg_value"].mean()) / cal["avg_value"].std(ddof=0)
    cal["flagged"] = cal["z_score"].abs() > 1.5
    return cal


def bootstrap_histogram(samples_df: pd.DataFrame):
    return px.histogram(samples_df, x="ibnr", nbins=40, title="Bootstrap IBNR Distribution")
