"""Validation helpers for reserving inputs."""

from __future__ import annotations

import pandas as pd

from src.data_ingestion import DataIngestionError, MappingConfig


REQUIRED_MAP_FIELDS = ("accident_year_col", "development_col", "value_col")


def validate_mapping(df: pd.DataFrame, mapping: MappingConfig) -> None:
    for field in REQUIRED_MAP_FIELDS:
        col = getattr(mapping, field)
        if col not in df.columns:
            raise DataIngestionError(f"Mapped column '{col}' is missing from the uploaded data.")


def prepare_and_validate_data(df: pd.DataFrame, mapping: MappingConfig) -> pd.DataFrame:
    validate_mapping(df, mapping)
    work = df.copy()
    ay = mapping.accident_year_col
    dev = mapping.development_col
    val = mapping.value_col

    work = work.rename(columns={ay: "accident_year", dev: "development", val: "value"})
    work["accident_year"] = pd.to_numeric(work["accident_year"], errors="coerce")
    work["development"] = pd.to_numeric(work["development"], errors="coerce")
    work["value"] = pd.to_numeric(work["value"], errors="coerce")

    if work[["accident_year", "development", "value"]].isna().any().any():
        raise DataIngestionError("Accident year, development, and value fields must be valid numeric values.")

    work["accident_year"] = work["accident_year"].astype(int)
    work["development"] = work["development"].astype(int)

    if (work["development"] <= 0).any():
        raise DataIngestionError("Development period must be positive.")

    if (work["value"] < 0).any():
        raise DataIngestionError("Negative values detected; please verify incurred/paid values.")

    dup_cols = ["accident_year", "development"]
    work = work.groupby(dup_cols, as_index=False)["value"].sum()
    work = work.sort_values(dup_cols).reset_index(drop=True)

    # Monotonicity check for cumulative style data.
    cum_check = work.pivot(index="accident_year", columns="development", values="value").sort_index(axis=1)
    for _, row in cum_check.iterrows():
        vals = row.dropna().values
        if len(vals) >= 2 and (pd.Series(vals).diff().dropna() < 0).any():
            raise DataIngestionError(
                "Values decrease across development ages for at least one Accident Year;"
                " this tool expects cumulative development values."
            )

    return work
