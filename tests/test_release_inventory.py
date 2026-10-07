"""Software inventory oracle: no package install, network or scientific call."""
import importlib.util
from pathlib import Path


def test_inventory_projects_versions_licenses_without_private_paths_or_guessing(monkeypatch):
    source = Path(__file__).resolve().parents[1]/"scripts/release_inventory.py"
    spec = importlib.util.spec_from_file_location("release_inventory", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "distributions", lambda **kwargs: [])
    frontend = {"MIT": [{"name": "@scope/library", "versions": ["1.2.3"], "license": "MIT", "paths": ["PRIVATE_PATH"]}]}
    cargo = {"resolve": {"nodes": [{"id": "used"}]}, "packages": [
        {"id": "used", "source": "registry", "name": "used", "version": "2.0.0", "license": "MIT OR Apache-2.0"},
        {"id": "unused", "source": "registry", "name": "unused", "version": "9.0.0", "license": None}]}
    result = module.inventory(frontend, cargo, Path("unused"))
    assert {c["purl"] for c in result} == {"pkg:npm/%40scope/library@1.2.3", "pkg:cargo/used@2.0.0"}
    assert "PRIVATE_PATH" not in str(result) and "unused" not in str(result)
    assert module.osv_queries(result) == [
        {"package": {"ecosystem": "crates.io", "name": "used"}, "version": "2.0.0"},
        {"package": {"ecosystem": "npm", "name": "@scope/library"}, "version": "1.2.3"}]
