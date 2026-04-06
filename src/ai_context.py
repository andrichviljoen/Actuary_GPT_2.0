"""AI context persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, pd.DataFrame):
            return o.to_dict(orient="records")
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def build_context_payload(
    mapping: dict,
    settings: dict,
    diagnostics: dict,
    chain_ladder: dict,
    bootstrap: dict | None,
    exclusions: list[tuple[int, int]] | None,
) -> dict:
    return {
        "metadata": {"tool": "IBNR Reserving Tool", "version": "1.0.0", "scope": "Accident Year only"},
        "mapping": mapping,
        "settings": settings,
        "exclusions": exclusions or [],
        "diagnostics": diagnostics,
        "chain_ladder": chain_ladder,
        "bootstrap": bootstrap,
    }


def save_context_json(payload: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, cls=EnhancedJSONEncoder), encoding="utf-8")
    return out_path
