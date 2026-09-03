"""Tests for integration metadata."""
from __future__ import annotations

import json
from pathlib import Path


def test_manifest_metadata() -> None:
    manifest = json.loads(Path("custom_components/bticino_myhome/manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == "bticino_myhome"
    assert manifest["version"] == "0.1.13"
    assert manifest["requirements"] == ["OWNd==0.7.49"]
    assert manifest["codeowners"] == ["@donatomontrone"]
    assert manifest["ssdp"] == [{"st": "upnp:rootdevice", "manufacturer": "BTicino S.p.A.", "modelName": "MH201"}]
    assert "manifest_version" not in manifest
