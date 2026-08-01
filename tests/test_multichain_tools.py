from __future__ import annotations

from pathlib import Path

from igem_drylab.mcp import create_default_registry
from igem_drylab.multichain import assess_interface, build_multichain_input, solve_binding_equilibrium
from igem_drylab.multichain.models import ProteinChain


def test_build_multichain_input_writes_fasta_and_manifest(tmp_path):
    result = build_multichain_input(
        complex_id="demo",
        output_dir=tmp_path,
        chains=[
            ProteinChain(chain_id="A", name="core", sequence="MAGA", role="core"),
            ProteinChain(chain_id="B", name="client", sequence="GGGG", role="client"),
        ],
    )

    assert result.fasta_file.exists()
    assert result.manifest_file.exists()
    text = result.fasta_file.read_text(encoding="utf-8")
    assert ">A name=core role=core" in text
    assert ">B name=client role=client" in text


def test_binding_equilibrium_handles_multivalent_core():
    result = solve_binding_equilibrium(
        receptor="FTH1-iLID",
        ligand="SspB-IDR",
        receptor_total=1.0,
        ligand_total=10.0,
        kd=0.5,
        receptor_valency=24,
        ligand_valency=1,
    )

    assert result.receptor_site_total == 24.0
    assert result.ligand_site_total == 10.0
    assert 0 < result.bound_site_concentration < 10.0
    assert result.limiting_component == "SspB-IDR"


def test_assess_interface_counts_contacts_without_clashes():
    result = assess_interface(
        pdb_file=Path("examples/multichain/two_chain_interface.pdb"),
        chain_a="A",
        chain_b="B",
        contact_cutoff_angstrom=5.0,
        clash_cutoff_angstrom=2.0,
    )

    assert result.interface_contact_count > 0
    assert result.clash_count == 0
    assert result.assessment in {"weak_contact", "well_contacted"}


def test_multichain_mcp_tools(tmp_path):
    registry = create_default_registry()
    build_result = registry.call(
        "igem.multichain.build_input",
        {
            "complex_id": "tool_demo",
            "output_dir": str(tmp_path / "complex"),
            "chains": [
                {"chain_id": "A", "name": "core", "sequence": "MAGA", "role": "core"},
                {"chain_id": "B", "name": "module", "sequence": "GGGG", "role": "module"},
            ],
        },
    ).as_protocol_dict()["structuredContent"]

    assert build_result["ok"] is True
    assert Path(build_result["result"]["fasta_file"]).exists()

    binding_result = registry.call(
        "igem.multichain.binding_equilibrium",
        {
            "receptor": "core sites",
            "ligand": "module",
            "receptor_total": 1.0,
            "ligand_total": 2.0,
            "kd": 0.1,
            "receptor_valency": 24,
            "ligand_valency": 1,
        },
    ).as_protocol_dict()["structuredContent"]
    assert binding_result["ok"] is True
    assert binding_result["result"]["bound_site_concentration"] > 0

    interface_result = registry.call(
        "igem.multichain.assess_interface",
        {
            "pdb_file": "examples/multichain/two_chain_interface.pdb",
            "chain_a": "A",
            "chain_b": "B",
        },
    ).as_protocol_dict()["structuredContent"]
    assert interface_result["ok"] is True
    assert interface_result["result"]["interface_contact_count"] > 0
