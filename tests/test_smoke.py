from pathlib import Path


def test_project_structure_exists():
    assert Path('app.py').exists()
    assert Path('src/reserving.py').exists()
