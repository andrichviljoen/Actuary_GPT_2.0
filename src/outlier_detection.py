"""Link ratio outlier guidance and factor selection."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _origin_key(value) -> str:
    try:
        if hasattr(value, "year"):
            return str(int(value.year))
    except Exception:
        pass
    return str(value)


def compute_link_ratio_table(triangle_df: pd.DataFrame) -> pd.DataFrame:
    dev_cols = [c for c in triangle_df.columns if c != "origin"]
    dev_cols = sorted(dev_cols, key=lambda x: int(x))
    records: list[dict] = []
    for _, row in triangle_df.iterrows():
        origin = row["origin"]
        for d1, d2 in zip(dev_cols[:-1], dev_cols[1:]):
            if pd.notna(row[d1]) and pd.notna(row[d2]) and row[d1] != 0:
                lr = float(row[d2] / row[d1])
                records.append({"origin": origin, "dev_from": int(d1), "dev_to": int(d2), "link_ratio": lr})
    return pd.DataFrame(records)


def flag_outliers(link_ratio_df: pd.DataFrame, z_threshold: float = 2.0) -> pd.DataFrame:
    if link_ratio_df.empty:
        return link_ratio_df.assign(z_score=[], flagged=[])

    flagged_parts = []
    for dev_from, g in link_ratio_df.groupby("dev_from"):
        mean = g["link_ratio"].mean()
        std = g["link_ratio"].std(ddof=0)
        if std == 0 or np.isnan(std):
            z = pd.Series(0.0, index=g.index)
        else:
            z = (g["link_ratio"] - mean) / std
        part = g.copy()
        part["z_score"] = z
        part["flagged"] = z.abs() >= z_threshold
        part["rationale"] = np.where(
            part["flagged"],
            "Large relative deviation from peer link ratios at same development age",
            "Within normal peer range",
        )
        flagged_parts.append(part)
    return pd.concat(flagged_parts).sort_values(["dev_from", "origin"])


def selected_factors(link_ratio_df: pd.DataFrame, exclusions: list[tuple[int, int | str]] | None = None) -> pd.DataFrame:
    work = link_ratio_df.copy()
    work["exclude"] = False
    work["origin_key"] = work["origin"].apply(_origin_key)
    if exclusions:
        ex_set = {(_origin_key(o), int(d)) for o, d in exclusions}
        work["exclude"] = work.apply(lambda r: (r["origin_key"], int(r["dev_from"])) in ex_set, axis=1)
    sel = (
        work.loc[~work["exclude"]]
        .groupby("dev_from", as_index=False)["link_ratio"]
        .mean()
        .rename(columns={"link_ratio": "selected_factor"})
    )
    return sel
