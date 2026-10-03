from __future__ import annotations

from pathlib import Path
import sys

import yaml

from igem_drylab.external_tools import TEN_GIB, audit_deployment, tool_spec
from igem_drylab.pipeline.adapters import create_tool_adapter
from igem_drylab.pipeline.config import ToolConfig


def test_catalog_keeps_formal_route_and_scientific_boundary_together() -> None:
    assert tool_spec("colabfold").formal_stage == "M2"
    assert tool_spec("signalp").route == "licensed_local_or_api"
    assert tool_spec("unknown") is None


def test_deployment_audit_deduplicates_nested_roots(tmp_path: Path) -> None:
    root = tmp_path / "environment"
    nested = root / "models"
    nested.mkdir(parents=True)
    (root / "binary").write_bytes(b"1234")
    (nested / "weights").write_bytes(b"123456")

    result = audit_deployment([root, nested], budget_bytes=10)

    assert result.used_bytes == 10
    assert result.within_budget
    assert list(result.paths) == [str(root.resolve())]


def test_disabled_tool_never_executes_even_with_valid_command(tmp_path: Path) -> None:
    adapter = create_tool_adapter(
        "iupred2a",
        ToolConfig(enabled=False, mode="external", command=f'"{sys.executable}" --version'),
    )

    result = adapter.run(output_dir=tmp_path / "out")

    assert result.status == "disabled"
    assert result.argv == []


def test_missing_template_value_fails_before_subprocess(tmp_path: Path) -> None:
    adapter = create_tool_adapter(
        "iupred2a",
        ToolConfig(enabled=True, mode="external", command=f'"{sys.executable}" {{input_file}}'),
    )

    try:
        adapter.run(output_dir=tmp_path / "out")
    except ValueError as exc:
        assert "missing command value: input_file" in str(exc)
    else:
        raise AssertionError("missing command input was silently retained")


def test_mcp_deployment_audit_uses_unique_configured_paths(tmp_path: Path) -> None:
    from igem_drylab.mcp.registry import create_default_registry

    deployment = tmp_path / "tool-env"
    deployment.mkdir()
    (deployment / "payload").write_bytes(b"12345")
    fasta = tmp_path / "proteins.fasta"
    fasta.write_text(">placeholder\nAAAA\n", encoding="utf-8")
    config = {
        "run": {"id": "audit", "output_dir": str(tmp_path / "outputs")},
        "inputs": {
            "protein_fasta": str(fasta),
            "enzymes": [],
            "scaffolds": [],
            "linkers": [],
        },
        "tools": {
            "freesasa": {
                "enabled": True,
                "mode": "external",
                "command": f'"{sys.executable}" --version',
                "deployment_paths": [str(deployment)],
            },
            "autodock_vina": {
                "enabled": True,
                "mode": "external",
                "command": f'"{sys.executable}" --version',
                "deployment_paths": [str(deployment)],
            },
        },
        "stages": {"m4_reaction": {"network_mode": "legacy_reduced"}},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    response = create_default_registry().call(
        "igem.compute.audit_deployment",
        {"config_path": str(config_path), "budget_bytes": TEN_GIB},
    )

    assert response.is_error is False
    assert response.structured_content["deployment"]["used_bytes"] == 5
