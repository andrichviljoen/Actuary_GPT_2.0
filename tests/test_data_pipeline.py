import json
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("chainladder")

from src.ai_context import build_context_payload, save_context_json
from src.data_ingestion import MappingConfig, load_demo_dataset
from src.outlier_detection import compute_link_ratio_table, selected_factors
from src.reserving import run_bootstrap_odp, run_chain_ladder
from src.triangle_builder import build_triangle, triangle_to_dataframe
from src.validation import DataIngestionError, prepare_and_validate_data


def test_demo_dataset_loads():
    df = load_demo_dataset()
    assert {"accident_year", "development", "value"}.issubset(df.columns)
    assert (df["value"] >= 0).all()


def test_duplicate_handling_and_sorting():
    raw = pd.DataFrame(
        {
            "ay": [2000, 2000, 2000, 2001],
            "dev": [12, 12, 24, 12],
            "inc": [100, 50, 170, 80],
        }
    )
    out = prepare_and_validate_data(raw, MappingConfig("ay", "dev", "inc"))
    assert len(out) == 3
    row = out[(out.accident_year == 2000) & (out.development == 12)]
    assert row["value"].iloc[0] == 150


def test_invalid_negative_values_rejected():
    raw = pd.DataFrame({"ay": [2000], "dev": [12], "inc": [-1]})
    with pytest.raises(DataIngestionError):
        prepare_and_validate_data(raw, MappingConfig("ay", "dev", "inc"))


def test_triangle_and_chain_ladder_execution():
    raw = load_demo_dataset()
    clean = prepare_and_validate_data(raw, MappingConfig("accident_year", "development", "value"))
    tri = build_triangle(clean)
    tri_df = triangle_to_dataframe(tri)
    assert "origin" in tri_df.columns

    res = run_chain_ladder(tri)
    assert "summary" in res and not res["summary"].empty
    assert res["total_reserve"] > 0


def test_bootstrap_execution_seeded():
    raw = load_demo_dataset()
    clean = prepare_and_validate_data(raw, MappingConfig("accident_year", "development", "value"))
    tri = build_triangle(clean)

    res = run_bootstrap_odp(tri, n_sims=120, random_state=1)
    assert not res["samples"].empty
    assert res["summary"].iloc[0]["std"] > 0


def test_selected_factors_with_exclusions():
    raw = load_demo_dataset()
    clean = prepare_and_validate_data(raw, MappingConfig("accident_year", "development", "value"))
    tri = build_triangle(clean)
    tri_df = triangle_to_dataframe(tri)
    lr = compute_link_ratio_table(tri_df)

    first = lr.iloc[0]
    fac_base = selected_factors(lr)
    fac_ex = selected_factors(lr, exclusions=[(int(first["origin"]), int(first["dev_from"]))])
    assert not fac_base.equals(fac_ex)


def test_context_json_generation(tmp_path: Path):
    payload = build_context_payload(
        mapping={"accident_year": "ay"},
        settings={"bootstrap": True},
        diagnostics={"calendar_summary": "ok"},
        chain_ladder={"total_reserve": 123.0},
        bootstrap={"summary": [{"mean": 120}]},
        exclusions=[(2001, 12)],
    )
    out = save_context_json(payload, tmp_path / "ctx.json")
    assert out.exists()
    loaded = json.loads(out.read_text())
    assert loaded["metadata"]["scope"] == "Accident Year only"
