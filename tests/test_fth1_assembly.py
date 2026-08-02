from __future__ import annotations

from pathlib import Path
from string import ascii_uppercase

import pytest

from igem_drylab.mcp import create_default_registry
from igem_drylab.multichain import expand_fth1_arms


def _pdb_line(serial: int, atom: str, residue: str, chain: str, resid: int, x: float, y: float, z: float) -> str:
    return f"ATOM  {serial:5d} {atom:>4s} {residue:>3s} {chain}{resid:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C"


def _write_synthetic_cage(path: Path) -> None:
    lines: list[str] = []
    serial = 1
    for index, chain in enumerate(ascii_uppercase[:24]):
        x = float(index * 20)
        lines.append(_pdb_line(serial, "CA", "GLY", chain, 1, x, 0, 0)); serial += 1
        lines.append(_pdb_line(serial, "CB", "GLY", chain, 1, x, 0, 5)); serial += 1
    path.write_text("\n".join(lines) + "\nEND\n", encoding="utf-8")


def _write_local_arm(path: Path) -> None:
    lines = [
        _pdb_line(1, "CA", "GLY", "X", 1, 0, 0, 0),
        _pdb_line(2, "CB", "GLY", "X", 1, 0, 0, 5),
        _pdb_line(3, "CA", "GLY", "X", 2, 0, 0, 15),
    ]
    path.write_text("\n".join(lines) + "\nEND\n", encoding="utf-8")


def test_expand_fth1_arms_maps_one_local_arm_to_24_subunits(tmp_path):
    template = tmp_path / "cage.pdb"
    arm = tmp_path / "arm.pdb"
    assembled = tmp_path / "assembled.pdb"
    _write_synthetic_cage(template)
    _write_local_arm(arm)

    result = expand_fth1_arms(
        template_pdb=template, local_arm_pdb=arm, reference_core_chain="A",
        core_anchor_residue=1, core_anchor_atom="CA", core_orientation_atom="CB",
        arm_anchor_chain="X", arm_anchor_residue=1, arm_anchor_atom="CA", arm_orientation_atom="CB",
        probe_chain="X", probe_residue_ids=[2], output_pdb=assembled,
    )

    assert result.subunit_count == 24
    assert result.total_expanded_arm_atoms == 72
    assert result.assembled_pdb == assembled
    assert assembled.exists()
    assert result.accessible_probe_atoms == 24
    assert result.core_arm_clash_pairs == 0


def test_expand_fth1_arms_rejects_incomplete_template(tmp_path):
    template = tmp_path / "partial.pdb"
    arm = tmp_path / "arm.pdb"
    _write_synthetic_cage(template)
    template.write_text("\n".join(template.read_text(encoding="utf-8").splitlines()[:4]), encoding="utf-8")
    _write_local_arm(arm)
    with pytest.raises(ValueError, match="expected 24"):
        expand_fth1_arms(
            template_pdb=template, local_arm_pdb=arm, reference_core_chain="A",
            core_anchor_residue=1, core_anchor_atom="CA", core_orientation_atom="CB",
            arm_anchor_chain="X", arm_anchor_residue=1, arm_anchor_atom="CA", arm_orientation_atom="CB",
        )


def test_fth1_expansion_is_available_as_mcp_tool(tmp_path):
    template = tmp_path / "cage.pdb"
    arm = tmp_path / "arm.pdb"
    _write_synthetic_cage(template)
    _write_local_arm(arm)
    result = create_default_registry().call(
        "igem.multichain.expand_fth1_arms",
        {
            "template_pdb": str(template), "local_arm_pdb": str(arm), "reference_core_chain": "A",
            "core_anchor_residue": 1, "core_anchor_atom": "CA", "core_orientation_atom": "CB",
            "arm_anchor_chain": "X", "arm_anchor_residue": 1, "arm_anchor_atom": "CA", "arm_orientation_atom": "CB",
        },
    ).as_protocol_dict()["structuredContent"]
    assert result["ok"] is True
    assert result["result"]["subunit_count"] == 24
