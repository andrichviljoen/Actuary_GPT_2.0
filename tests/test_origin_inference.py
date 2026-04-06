import pytest

pd = pytest.importorskip("pandas")

from src.data_ingestion import ensure_origin_column


def test_ensure_origin_when_present():
    df = pd.DataFrame({"origin": [2000, 2001], "12": [100, 120]})
    out = ensure_origin_column(df)
    assert "origin" in out.columns
    assert out.columns[0] == "origin"


def test_ensure_origin_from_named_index():
    df = pd.DataFrame({"12": [100, 120]}, index=pd.Index([2000, 2001], name="origin"))
    out = ensure_origin_column(df)
    assert "origin" in out.columns
    assert out["origin"].tolist() == [2000, 2001]


def test_ensure_origin_from_unnamed_index():
    df = pd.DataFrame({"12": [100, 120]}, index=[2000, 2001])
    out = ensure_origin_column(df)
    assert "origin" in out.columns
    assert out["origin"].tolist() == [2000, 2001]


def test_ensure_origin_with_unexpected_first_column_name():
    df = pd.DataFrame({"AccidentYear": [2000, 2001], "12": [100, 120]})
    out = ensure_origin_column(df)
    assert "origin" in out.columns
    assert out["origin"].tolist() == [2000, 2001]
