"""Load and validate reserving input data."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import BinaryIO

import chainladder as cl
import pandas as pd


LOGGER = logging.getLogger(__name__)
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@dataclass
class MappingConfig:
    accident_year_col: str
    development_col: str
    value_col: str
    measure_col: str | None = None


class DataIngestionError(ValueError):
    """User-friendly ingestion error."""


def load_uploaded_file(file_obj: BinaryIO, filename: str) -> pd.DataFrame:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise DataIngestionError(f"Unsupported file extension '{ext}'. Please upload CSV or Excel.")
    if ext == ".csv":
        df = pd.read_csv(file_obj)
    else:
        df = pd.read_excel(file_obj)
    return df


def ensure_origin_column(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure an `origin` column exists before long-format melting."""
    if df is None or df.empty:
        raise DataIngestionError("Input dataset is empty; cannot infer origin column.")

    work = df.copy()
    work.columns = [str(c) for c in work.columns]

    if "origin" in work.columns:
        return work

    # Attempt recovery from index if origin is not currently a column.
    work = work.reset_index()
    work.columns = [str(c) for c in work.columns]

    if "origin" in work.columns:
        # De-duplicate origin columns defensively.
        if work.columns.tolist().count("origin") > 1:
            work = work.loc[:, ~work.columns.duplicated()]
        return work

    # If reset_index introduced a synthetic row counter, drop it before fallback inference.
    if len(work.columns) > 1 and str(work.columns[0]) == "index":
        idx_vals = pd.to_numeric(work.iloc[:, 0], errors="coerce")
        if idx_vals.notna().all() and (idx_vals.astype(int).to_numpy() == range(len(work))).all():
            work = work.iloc[:, 1:].copy()

    # Fallback: rename the first column to origin if still absent.
    first_col = str(work.columns[0])
    if first_col != "origin":
        work = work.rename(columns={first_col: "origin"})

    if "origin" not in work.columns:
        LOGGER.error("Unable to infer origin column. Available columns: %s", list(work.columns))
        raise DataIngestionError(
            f"Could not infer an origin column from dataset. Available columns: {list(work.columns)}"
        )

    if work.columns.tolist().count("origin") > 1:
        work = work.loc[:, ~work.columns.duplicated()]

    LOGGER.info("Origin inferred for dataset. Columns now: %s", list(work.columns))
    return work


def load_demo_dataset() -> pd.DataFrame:
    """Load a chainladder demo dataset transformed to long Accident Year format."""
    tri = cl.load_sample("genins")
    df = tri.to_frame(origin_as_datetime=False)
    df = ensure_origin_column(df)

    long_df = df.melt(id_vars=["origin"], var_name="development", value_name="value")
    long_df.rename(columns={"origin": "accident_year"}, inplace=True)
    long_df["development"] = pd.to_numeric(long_df["development"], errors="coerce")
    # chainladder may provide origin as a PeriodIndex-backed dtype, so normalize to year strings first.
    long_df["accident_year"] = pd.to_numeric(long_df["accident_year"].astype(str), errors="coerce").astype("Int64")
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df.dropna(subset=["accident_year", "development", "value"], inplace=True)
    return long_df.sort_values(["accident_year", "development"]).reset_index(drop=True)
