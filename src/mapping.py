"""Column mapping helpers for UI and downstream modules."""

from __future__ import annotations

from src.data_ingestion import MappingConfig


def mapping_to_dict(mapping: MappingConfig) -> dict[str, str]:
    return {
        "accident_year": mapping.accident_year_col,
        "development": mapping.development_col,
        "value": mapping.value_col,
    }
