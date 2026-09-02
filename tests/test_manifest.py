"""Test manifest."""
import json
from pathlib import Path


def test_manifest_ownd_version():
    manifest = json.loads(Path("custom_components/bticino_myhome/manifest.json").read_text())
    assert manifest["requirements"] == ["OWNd==0.7.49"]
    assert manifest["version"] == "0.1.5"


def test_no_python_cache_files():
    assert not list(Path("custom_components").rglob("*.pyc"))
