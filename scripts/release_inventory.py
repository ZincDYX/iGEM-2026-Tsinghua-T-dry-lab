"""Inventory installed release dependencies; no installation or scientific calls.

Inputs: pnpm licenses --json, cargo metadata --locked --filter-platform <target>,
and the exact Python site-packages directory selected for packaging. This is a
component inventory, not proof of binary reachability or license compliance.
OSV querying is optional and sends only public ecosystem/name/version tuples.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import distributions
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def component(ecosystem, name, version, license_text=None):
    kind = {"npm": "npm", "PyPI": "pypi", "crates.io": "cargo"}[ecosystem]
    normalized = name.lower().replace("_", "-") if kind == "pypi" else name
    purl = f"pkg:{kind}/{quote(normalized, safe='/')}@{quote(version, safe='')}"
    result = {"type": "library", "bom-ref": purl, "name": name,
              "version": version, "purl": purl,
              "properties": [{"name": "fusionlab:ecosystem", "value": ecosystem}]}
    if license_text:
        # Declared metadata is not a concluded SPDX/legal assessment.
        result["licenses"] = [{"license": {"name": license_text}}]
    return result


def inventory(frontend, cargo, site_packages):
    found = {}
    def add(value):
        found[value["bom-ref"]] = value
    for packages in frontend.values():
        for package in packages:
            for version in package["versions"]:
                add(component("npm", package["name"], version, package.get("license")))
    resolved = {node["id"] for node in cargo["resolve"]["nodes"]}
    for package in cargo["packages"]:
        if package["id"] in resolved and package["source"] is not None:
            add(component("crates.io", package["name"], package["version"], package.get("license")))
    for package in distributions(path=[str(site_packages)]):
        license_text = package.metadata.get("License-Expression") or package.metadata.get("License")
        if license_text and len(license_text) > 200:
            license_text = "Declared license text in packaged distribution metadata"
        add(component("PyPI", package.metadata["Name"], package.version, license_text))
    return sorted(found.values(), key=lambda c: c["bom-ref"])


def osv_queries(components):
    return [{"package": {"ecosystem": c["properties"][0]["value"], "name": c["name"]},
             "version": c["version"]} for c in components]


def audit(components):
    queries = osv_queries(components)
    results = []
    for start in range(0, len(queries), 100):
        batch = queries[start:start+100]
        request = Request("https://api.osv.dev/v1/querybatch",
                          data=json.dumps({"queries": batch}).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=45) as response:
            data = json.load(response)
        if len(data["results"]) != len(batch):
            raise ValueError("OSV result count differs from submitted public package tuples")
        for query, result in zip(batch, data["results"], strict=True):
            results.append({**query, "advisories": result.get("vulns", [])})
    return {"source": "https://api.osv.dev/v1/querybatch", "results": results,
            "scope": "dated_database_matches_not_exploitability_or_universal_safety"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend-licenses", type=Path, required=True)
    parser.add_argument("--cargo-metadata", type=Path, required=True)
    parser.add_argument("--site-packages", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--osv", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve previous release inventory; select a new output directory")
    frontend = json.loads(args.frontend_licenses.read_text(encoding="utf-8-sig"))
    cargo = json.loads(args.cargo_metadata.read_text(encoding="utf-8-sig"))
    components = inventory(frontend, cargo, args.site_packages)
    timestamp = datetime.now(timezone.utc).isoformat()
    metadata = {"timestamp": timestamp, "component": {"type": "application",
                "name": "FusionLab", "version": args.commit}, "properties": [
        {"name": "fusionlab:scope", "value": "installed_frontend_including_dev_windows_cargo_resolve_packaged_python_inventory_not_binary_reachability"},
        {"name": "fusionlab:frontend_inventory_sha256", "value": sha256(args.frontend_licenses.read_bytes()).hexdigest()},
        {"name": "fusionlab:cargo_metadata_sha256", "value": sha256(args.cargo_metadata.read_bytes()).hexdigest()}]}
    bom = {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
           "metadata": metadata, "components": components}
    # No filesystem paths or guessed dependency edges are exported.
    args.output.mkdir(parents=True)
    (args.output/"SBOM.cdx.json").write_text(json.dumps(bom, indent=2), encoding="utf-8")
    if args.osv:
        report = {"timestamp": timestamp, "commit": args.commit, **audit(components)}
        (args.output/"OSV-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"components": len(components), "osv_requested": args.osv}))


if __name__ == "__main__":
    main()
