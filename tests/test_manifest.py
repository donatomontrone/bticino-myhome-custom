"""Test manifest."""
import json
from pathlib import Path


def test_manifest_ownd_version_and_release_version() -> None:
    manifest = json.loads(Path("custom_components/bticino_myhome/manifest.json").read_text())
    assert manifest["requirements"] == ["OWNd==0.7.49"]
    assert manifest["version"] == "0.1.11"


def test_no_python_cache_files() -> None:
    assert not list(Path("custom_components").rglob("*.pyc"))
