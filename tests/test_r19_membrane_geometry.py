"""Synthetic coordinate/topology oracles; numerical tests run server-only."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import numpy as np
import pytest

from igem_drylab.compartments import MembraneTopologyEvidence,evaluate_topology
from igem_drylab.membrane_geometry import MembraneGeometryInput,calculate_membrane_geometry


def artifact(path):
    return dict(path=path,sha256=sha256(path.read_bytes()).hexdigest())


def topology(tmp_path):
    raw = tmp_path/"SYNTHETIC.3line"
    raw.write_text(">fixture | TM\nAAAAAAAA\nIMMIIIII\n")
    return dict(evidence_id="synthetic-topology",construct_id="fixture",construct_version="synthetic-v1",condition_id="fixture",
        input_sequence_sha256=sha256(b"AAAAAAAA").hexdigest(),anchor=dict(start=2,end=3),anchor_source_record="synthetic-only",
        tool="DeepTMHMM",tool_version="synthetic-native-format-not-executed-tool",native_record_id="fixture",native_output=artifact(raw),
        body_side="cytosolic",orientation_source="synthetic-test-claim",cleavage_state="not_cleaved",body_removed_by_cleavage=False,
        cleavage_source="synthetic",evidence_level="predicted",raw_references=[artifact(raw)])


def write_pdb(path,transform=lambda points:points):
    points = transform(np.array([[0.,0.,-3.],[0.,0.,3.],[0.,0.,6.],[0.,0.,8.],[1.,0.,8.],[8.,0.,0.]]))
    indices = [2,3,4,5,6,8]
    lines = [f"ATOM  {i:5d}  CA  ALA A{res:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 90.00           C  "
        for i,(res,(x,y,z)) in enumerate(zip(indices,points),1)]
    path.write_text("\n".join(lines)+"\nEND\n")


def membrane(tmp_path):
    pdb = tmp_path/"SYNTHETIC.pdb"; write_pdb(pdb)
    source = tmp_path/"SYNTHETIC-frame.txt"; source.write_text("synthetic planar membrane, not actual ER")
    select = lambda residues:dict(chain="A",residues=residues)
    return dict(construct_id="fixture",condition_id="fixture",topology=topology(tmp_path),subunit_composition={"subunit-a":True},
        assembly_applicability_source="synthetic-test-only",anchor_count_basis="explicit_subunit_composition",
        conformers=[dict(model_id="synthetic",conformer_id="synthetic",structure=dict(path=pdb,source_kind="experimental",source_reference="SYNTHETIC PDB FOR MATHEMATICAL TEST; NOT AN EXPERIMENTAL STRUCTURE"),
            frame=dict(frame_id="synthetic",origin_angstrom=[0,0,0],unit_normal=[0,0,1],thickness_angstrom=4,positive_side="cytosolic",body_side="cytosolic",source_reference="synthetic",raw_reference=artifact(source),atom_radii_angstrom={"C":.5}),
            tethers=[dict(subunit_id="subunit-a",anchor=select([2,3]),linker=select([4]),attached_body=select([5]),contour_length_angstrom=10,contour_length_source="synthetic")],
            scaffold=select([2,3,4,5,6]),domains={"SH3":select([6])},pockets={"enzyme":select([8])},recruited_enzymes={"enzyme":select([8])},
            sampling_method="synthetic rigid coordinate oracle",sampling_scope="no flexibility sampling claimed",coordinate_transform_reference="synthetic identity")],
        heavy_atom_clash_cutoff_angstrom=2.5,clash_rule_source="synthetic-test-only")


def test_expected_anchor_not_rejected_and_unknown_side_not_quantitatively_promoted(tmp_path):
    raw = topology(tmp_path)
    result = evaluate_topology(MembraneTopologyEvidence.model_validate(raw),"AAAAAAAA")
    assert result["unexpected_segments"] == []
    assert result["status"] == "prediction_consistent_with_design"
    assert result["quantitative_ER_ready"] is False
    raw["body_side"]="unknown"; raw["orientation_source"]=None
    result = evaluate_topology(MembraneTopologyEvidence.model_validate(raw),"AAAAAAAA")
    assert "scaffold_body_side_not_established" in result["flags"]
    source=Path(raw["native_output"]["path"]); source.write_text(">fixture | TM\nAAAAAAAA\nIMMIMIII\n")
    raw["native_output"]=artifact(source);raw["raw_references"]=[artifact(source)]
    result = evaluate_topology(MembraneTopologyEvidence.model_validate(raw),"AAAAAAAA")
    assert result["unexpected_segments"] == [{"start":5,"end":5,"before_label":"I","after_label":"I"}]


def test_membrane_exclusion_and_domains_are_invariant_under_joint_rigid_transform(tmp_path):
    raw = membrane(tmp_path)
    result = calculate_membrane_geometry(MembraneGeometryInput.model_validate(raw))
    row = result["conformers"][0]
    assert row["membrane_clashes"]["count"] == 1
    assert row['eligibility']=='excluded'
    assert 'domain_or_pocket_wrong_side_or_membrane_occlusion' in row['eligibility_reasons']
    assert row["domains_on_accessible_side"]["SH3"]["accessible"] is True
    assert row["pocket_accessibility_in_membrane_context"]["enzyme"]["accessible"] is False
    assert row["tether_assembly_feasibility"][0]["anchor_spans_declared_membrane"] is True
    rotation = np.array([[0.,0.,1.],[0.,1.,0.],[-1.,0.,0.]])
    translation = np.array([10.,20.,30.])
    pdb = tmp_path/"SYNTHETIC-transformed.pdb";write_pdb(pdb,lambda p:p@rotation+translation)
    raw["conformers"][0]["structure"]["path"]=pdb
    raw["conformers"][0]["frame"].update(origin_angstrom=translation.tolist(),unit_normal=(np.array([0.,0.,1.])@rotation).tolist())
    transformed=calculate_membrane_geometry(MembraneGeometryInput.model_validate(raw))["conformers"][0]
    for field in ("membrane_clashes","domains_on_accessible_side","pocket_accessibility_in_membrane_context","tether_assembly_feasibility"):
        assert transformed[field] == row[field]


def test_24_anchored_subunits_cannot_be_replaced_by_one_cage_tether(tmp_path):
    raw = membrane(tmp_path)
    raw["subunit_composition"]={f"subunit-{i}":True for i in range(24)}
    with pytest.raises(ValueError,match="each_anchor_subunit"):
        MembraneGeometryInput.model_validate(raw)
