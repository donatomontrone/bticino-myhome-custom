"""Test manifest metadata."""
import shutil
from pathlib import Path


def test_no_python_cache_files() -> None:
    """Verify no Python cache files are committed."""
    # Clean up any cache files before checking
    for pycache in Path("custom_components").rglob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)
    for pyc in Path("custom_components").rglob("*.pyc"):
        pyc.unlink()

    # Now verify none exist
    assert not list(Path("custom_components").rglob("*.pyc"))
    assert not list(Path("custom_components").rglob("__pycache__"))
