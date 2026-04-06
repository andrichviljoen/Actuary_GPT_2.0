"""Reserving model wrappers around chainladder."""

from __future__ import annotations

import numpy as np
import pandas as pd
import chainladder as cl


def _normalize_origin(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    if "origin" not in out.columns:
        if "index" in out.columns:
            out = out.rename(columns={"index": "origin"})
        else:
            out = out.rename(columns={out.columns[0]: "origin"})
    return out


def run_chain_ladder(triangle: cl.Triangle) -> dict[str, pd.DataFrame | float | cl.Chainladder]:
    model = cl.Chainladder().fit(triangle)

    latest = _normalize_origin(triangle.latest_diagonal.to_frame(origin_as_datetime=False).reset_index())
    latest.columns = ["origin", "latest"]

    ultimate = _normalize_origin(model.ultimate_.to_frame(origin_as_datetime=False).reset_index())
    ultimate.columns = ["origin", "ultimate"]

    ibnr = _normalize_origin(model.ibnr_.to_frame(origin_as_datetime=False).reset_index())
    ibnr.columns = ["origin", "ibnr"]

    summary = latest.merge(ultimate, on="origin").merge(ibnr, on="origin")
    total_reserve = float(summary["ibnr"].sum())

    ldf = model.ldf_.to_frame(origin_as_datetime=False).T.reset_index(drop=True)
    ldf.columns = [str(c) for c in ldf.columns]

    return {
        "model": model,
        "summary": summary,
        "total_reserve": total_reserve,
        "ldf": ldf,
    }


def run_bootstrap_odp(triangle: cl.Triangle, n_sims: int = 500, random_state: int = 42) -> dict[str, pd.DataFrame | float]:
    boot = cl.BootstrapODPSample(n_sims=n_sims, random_state=random_state).fit(triangle)
    projected = cl.Chainladder().fit(boot.resampled_triangles_)
    ibnr_samples = projected.ibnr_.sum().to_frame(origin_as_datetime=False).iloc[:, 0].astype(float)

    stats = {
        "mean": float(ibnr_samples.mean()),
        "std": float(ibnr_samples.std(ddof=1)),
        "p50": float(np.percentile(ibnr_samples, 50)),
        "p75": float(np.percentile(ibnr_samples, 75)),
        "p90": float(np.percentile(ibnr_samples, 90)),
        "p95": float(np.percentile(ibnr_samples, 95)),
        "p99": float(np.percentile(ibnr_samples, 99)),
    }

    return {
        "samples": pd.DataFrame({"ibnr": ibnr_samples}),
        "summary": pd.DataFrame([stats]),
    }
