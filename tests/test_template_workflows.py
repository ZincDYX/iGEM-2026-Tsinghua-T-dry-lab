"""Rigid coordinate, FreeSASA and conflict oracles; synthetic not biological."""
from pathlib import Path
import numpy as np
import pytest

from igem_drylab.structure_metrics import read_pdb_atoms
from igem_drylab.template_geometry import (StructureInput, CAMapping, RecruitmentGeometryInput,
    calculate_recruitment_geometry, AssemblyExpansionInput, expand_actual_fusion, atom_sasa)
from igem_drylab.structural_workflow import M2EnzymeComparisonInput, compare_fusion_to_reference


def write_structure(path, entries):
    lines = []
    for chain, residue, xyz in entries:
        x, y, z = xyz
        lines.append(f"ATOM  {len(lines)+1:5d}  CA  ALA {chain}{residue:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 90.00           C")
    path.write_text("\n".join(lines)+"\nEND\n")
    return StructureInput(path=path, source_kind="experimental", source_reference="synthetic_coordinate_fixture_not_experiment")


def points(offset=0):
    return [(offset, 0, 0), (offset+3, 0, 0), (offset, 3, 0)]


def mapping(ref, mob):
    return CAMapping(reference_chain=ref, mobile_chain=mob, residue_pairs=[(1,1),(2,2),(3,3)],
                     reviewed_reference="synthetic_1_to_1_fixture")


def geometry_input(tmp_path):
    scaffold = write_structure(tmp_path/"scaffold.pdb", [("S", i, xyz) for i, xyz in enumerate(points(), 1)])
    template = write_structure(tmp_path/"template.pdb", [(c, i, xyz) for c, off in (("D",10),("L",30))
        for i, xyz in enumerate(points(off), 1)])
    enzyme = write_structure(tmp_path/"enzyme.pdb", [("E", i, xyz) for i, xyz in enumerate(points(5), 1)]+[("E",10,(65,0,0))])
    placement = dict(site_id="site1", species="OC", template=template, enzyme=enzyme,
                     template_domain_to_scaffold=mapping("S","D"), enzyme_ligand_to_template=mapping("L","E"),
                     enzyme_pocket=dict(chain="E", residues=[10]))
    return RecruitmentGeometryInput(scaffold=scaffold, scaffold_id="synthetic", placements=[placement],
        clash_cutoff_angstrom=2.5, clash_rule_reference="M2_original_coarse_rule_fixture", pocket_retention_cutoff=.7,
        pocket_rule_reference="synthetic_occlusion_rule_not_project_review")


def test_two_template_transforms_place_entire_enzyme_not_only_peptide(tmp_path):
    pytest.importorskip("freesasa")
    payload = geometry_input(tmp_path)
    result = calculate_recruitment_geometry(payload)
    coords = result["placed_coordinates"]["site1"]
    # Domain template at x=10 moves to x=0; peptide at x=30 moves to x=20.
    np.testing.assert_allclose([r["xyz_angstrom"] for r in coords[:3]], points(20), atol=1e-10, rtol=0)
    np.testing.assert_allclose(coords[3]["xyz_angstrom"], [80,0,0], atol=1e-10, rtol=0)
    assert result["placements"][0]["scaffold_clashes"]["clash_count"] == 0
    assert not result["cooccupancy"]["m3_ready"]  # unconfirmed real assembly


def test_actual_overlapping_enzymes_generate_species_specific_conflict_edge(tmp_path):
    pytest.importorskip("freesasa")
    payload = geometry_input(tmp_path)
    payload.placements.append(payload.placements[0].model_copy(update={"site_id":"site2", "species":"DMT"}))
    result = calculate_recruitment_geometry(payload)
    assert result["conflict_graph"]["conflict_edges"] == [["site1","site2"]]
    assert result["cooccupancy"]["maximum_total_cooccupancy"] == 1
    combinations = result["cooccupancy"]["pareto_cooccupancy_combinations"]
    assert {(r["oc_count"],r["dmt_count"]) for r in combinations} == {(1,0),(0,1)}
    assert result["joint_occupancy_independent"] is False


def test_in_memory_FreeSASA_matches_independent_library_file_route(tmp_path):
    freesasa = pytest.importorskip("freesasa")
    payload = geometry_input(tmp_path)
    atoms = read_pdb_atoms(payload.scaffold.path)
    measured = sum(atom_sasa({"fixture":atoms}).values())
    expected = freesasa.calc(freesasa.Structure(str(payload.scaffold.path))).totalArea()
    assert measured == pytest.approx(expected, abs=1e-8)


def test_Q1_identity_reference_has_zero_core_RMSD_and_unit_pocket_retention(tmp_path):
    pytest.importorskip("freesasa")
    structure = write_structure(tmp_path/"same.pdb", [("A",i,xyz) for i,xyz in enumerate(points(),1)])
    payload = M2EnzymeComparisonInput(candidate_id="fixture", reference=structure, fusion=structure,
        core_mapping=mapping("A","A"), pocket_mapping=[(1,1),(2,2)], pocket_definition_reference="synthetic_fixture",
        clash_cutoff_angstrom=2.5, clash_rule_reference="M2_original_rule")
    result = compare_fusion_to_reference(payload)
    assert result["core_ca_rmsd_angstrom"] == pytest.approx(0, abs=1e-10)
    assert result["pocket_sasa_retention"] == pytest.approx(1, abs=1e-10)
    assert result["q1_verdict"] == "pass" and result["formal_verdict"] == "blocked"


def test_assembly_core_mapping_preserves_interface_distances_not_24mer_claim(tmp_path):
    template = write_structure(tmp_path/"two.pdb", [(c,i,xyz) for c,off in (("A",0),("B",10)) for i,xyz in enumerate(points(off),1)])
    mobile = write_structure(tmp_path/"one.pdb", [("M",i,xyz) for i,xyz in enumerate(points(20),1)])
    payload = AssemblyExpansionInput(template=template, actual_fusion=mobile, target_chains=["A","B"],
        core_mapping=mapping("A","M"), interface_residues=[1,2,3], interface_contact_cutoff_angstrom=20,
        rule_reference="synthetic_CA_contact_rule")
    result = expand_actual_fusion(payload)
    assert result["subunit_count"] == 2
    assert not result["assembly_applicability_confirmed"]
    for row in result["interface_contacts"]:
        assert row["fusion_CA_distance_angstrom"] == pytest.approx(row["reference_CA_distance_angstrom"], abs=1e-10)


def test_missing_or_collinear_mapping_does_not_choose_arbitrary_rotation(tmp_path):
    structure = write_structure(tmp_path/"line.pdb", [("A",i,(i,0,0)) for i in (1,2,3)])
    atoms = read_pdb_atoms(structure.path)
    with pytest.raises(ValueError, match="collinear"):
        mapping("A","A").fit(atoms,atoms)
    with pytest.raises(ValueError, match="missing"):
        mapping("A","B").fit(atoms,atoms)


def test_real_stdio_calls_new_Q1_workflow_and_exports_matching_input_schema(tmp_path):
    pytest.importorskip("freesasa")
    import asyncio
    import sys
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    structure = write_structure(tmp_path/"same.pdb", [("A",i,xyz) for i,xyz in enumerate(points(),1)])
    payload = M2EnzymeComparisonInput(candidate_id="fixture", reference=structure, fusion=structure,
        core_mapping=mapping("A","A"), pocket_mapping=[(1,1),(2,2)], pocket_definition_reference="synthetic_fixture",
        clash_cutoff_angstrom=2.5, clash_rule_reference="M2_original_rule")
    async def exercise():
        root = Path(__file__).resolve().parents[1]
        params = StdioServerParameters(command=sys.executable, args=["-m","igem_drylab.mcp.server"],
            cwd=root, env={"PYTHONPATH": str(root/"src")})
        async with Client(params, read_timeout_seconds=30) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert {"igem.m2.compare_enzyme","igem.m2.expand_fusion","igem.m2.place_recruitment"} <= names
            response = await client.call_tool("igem.m2.compare_enzyme", {"payload":payload.model_dump(mode="json")})
            assert not response.is_error
            assert response.structured_content["result"]["pocket_sasa_retention"] == pytest.approx(1, abs=1e-10)
    asyncio.run(exercise())


def test_expansion_is_directly_readable_with_actual_template_chain_ids(tmp_path):
    template = write_structure(tmp_path/"two.pdb", [(c,i,xyz) for c,off in (("A",0),("B",10)) for i,xyz in enumerate(points(off),1)])
    mobile = write_structure(tmp_path/"one.pdb", [("M",i,xyz) for i,xyz in enumerate(points(20),1)])
    payload = AssemblyExpansionInput(template=template, actual_fusion=mobile, target_chains=["A","B"],
        core_mapping=mapping("A","M"), interface_residues=[1,2,3], interface_contact_cutoff_angstrom=20,
        rule_reference="synthetic_CA_contact_rule")
    atoms, confidence = payload.read()
    assert {a.chain for a in atoms} == {"A","B"} and confidence is None
    np.testing.assert_allclose([a.coordinate for a in atoms if a.chain=="B"],points(10),rtol=0,atol=1e-10)


def test_independent_conformations_preserve_observed_graph_uncertainty(tmp_path):
    pytest.importorskip("freesasa")
    from igem_drylab.template_geometry import RecruitmentEnsembleInput, calculate_recruitment_ensemble
    first = geometry_input(tmp_path)
    second = first.model_copy(deep=True)
    output = calculate_recruitment_ensemble(RecruitmentEnsembleInput(scenarios=[first,second],
        independence_reference="synthetic_contract_only_not_independent_measured_models"))
    assert output["formal_verdict"] == "review" and not output["m3_ready"]
    second.placements[0].species = "DMT"
    with pytest.raises(ValueError,match="same_construct"):
        calculate_recruitment_ensemble(RecruitmentEnsembleInput(scenarios=[first,second], independence_reference="fixture"))


def test_calculation_file_runs_in_pipeline_without_promoting_blocked_M1(tmp_path):
    pytest.importorskip("freesasa")
    import json
    from igem_drylab.pipeline import load_config
    from igem_drylab.pipeline.models import M1Candidate
    from igem_drylab.pipeline.stages import run_m2
    structure = write_structure(tmp_path/"same.pdb", [("A",i,xyz) for i,xyz in enumerate(points(),1)])
    payload = M2EnzymeComparisonInput(candidate_id="fixture",reference=structure,fusion=structure,
        core_mapping=mapping("A","A"),pocket_mapping=[(1,1),(2,2)],pocket_definition_reference="fixture",
        clash_cutoff_angstrom=2.5,clash_rule_reference="fixture")
    requests = tmp_path/"calculations.json"
    requests.write_text(json.dumps([dict(kind="enzyme_comparison",candidate_id="fixture",payload=payload.model_dump(mode="json"))]))
    root=Path(__file__).resolve().parents[1]
    config=load_config(root/"configs/m1_m4_real_scoring_example.yaml")
    config.stages.m2_fusion.calculation_requests_file=requests
    config.stages.m2_fusion.structure_metrics_file=None
    candidate=M1Candidate(candidate_id="M1-fixture",construct_id="fixture",construct_definition={},status="insufficient_data")
    rows,_=run_m2(config,tmp_path/"run",[candidate])
    assert len(rows[0].calculation_reports)==1
    assert rows[0].calculation_reports[0]["M1_eligibility"]=="blocked"
    assert json.loads(Path(rows[0].calculation_reports[0]["artifact_path"]).read_text())["q1_verdict"]=="pass"
    assert not rows[0].recommended_for_m3


def test_predicted_structure_read_accepts_mapped_tool_ID_and_exact_sequence(tmp_path):
    from test_region_assessment import prediction
    from igem_drylab.parsers.structure_prediction import parse_structure_prediction_output
    request=prediction(tmp_path)
    summary=parse_structure_prediction_output(request.confidence_file,candidate_id=request.candidate_id)
    structure=StructureInput(path=summary.model_file,confidence_file=request.confidence_file,
        expected_sequence=request.sequence,source_kind="prediction",source_reference="synthetic_prediction_format_fixture")
    atoms,confidence=structure.read()
    assert len([a for a in atoms if a.name=="CA"])==4 and len(confidence)==4


def test_low_confidence_predicted_reference_cannot_pass_Q1(tmp_path, monkeypatch):
    reference=write_structure(tmp_path/"reference.pdb",[("A",i,xyz) for i,xyz in enumerate(points(),1)])
    fusion=write_structure(tmp_path/"fusion.pdb",[("A",i,xyz) for i,xyz in enumerate(points(),1)])
    # Explicit confidence-gate oracle, not real prediction output or a tool job.
    def read_fixture(self):
        atoms=read_pdb_atoms(self.path)
        score=40.0 if self.path==reference.path else 90.0
        return atoms,{(a.chain,a.residue,a.insertion):score for a in atoms}
    monkeypatch.setattr(StructureInput,"read",read_fixture)
    payload=M2EnzymeComparisonInput(candidate_id="fixture",reference=reference,fusion=fusion,
        core_mapping=mapping("A","A"),pocket_mapping=[(1,1),(2,2)],pocket_definition_reference="synthetic_fixture",
        clash_cutoff_angstrom=2.5,clash_rule_reference="fixture")
    result=compare_fusion_to_reference(payload)
    assert result["reference_region_mean_plddt"]==dict(core=40,pocket=40)
    assert result["region_mean_plddt"]==dict(core=90,pocket=90)
    assert result["confidence_gate"]=="low" and result["q1_verdict"]=="blocked"
    assert result["core_ca_rmsd_angstrom"] is None and result["pocket_sasa_retention"] is None
