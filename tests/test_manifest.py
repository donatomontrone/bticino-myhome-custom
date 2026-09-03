"""Test manifest metadata."""
from pathlib import Path


def test_no_python_cache_files() -> None:
    """Verify no Python cache files are committed."""
    assert not list(Path("custom_components").rglob("*.pyc"))
    assert not list(Path("custom_components").rglob("__pycache__"))
