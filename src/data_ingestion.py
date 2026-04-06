"""Load and validate reserving input data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import chainladder as cl
import pandas as pd


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


def load_demo_dataset() -> pd.DataFrame:
    """Load a chainladder demo dataset transformed to long Accident Year format."""
    tri = cl.load_sample("genins")
    df = tri.to_frame(origin_as_datetime=False).reset_index()
    long_df = df.melt(id_vars=["origin"], var_name="development", value_name="value")
    long_df.rename(columns={"origin": "accident_year"}, inplace=True)
    long_df["development"] = pd.to_numeric(long_df["development"], errors="coerce")
    long_df["accident_year"] = pd.to_numeric(long_df["accident_year"], errors="coerce").astype("Int64")
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df.dropna(subset=["accident_year", "development", "value"], inplace=True)
    return long_df.sort_values(["accident_year", "development"]).reset_index(drop=True)
