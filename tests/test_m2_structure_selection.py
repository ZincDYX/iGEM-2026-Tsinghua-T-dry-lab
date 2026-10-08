"""Parser regressions; numerical tests run on the scientific execution host."""
from pathlib import Path
import json
import os

import numpy as np
import pytest

from igem_drylab.parsers.freesasa import compute_pocket_sasa_retention, parse_freesasa_json, sum_residue_areas
from igem_drylab.structure_metrics import read_pdb_atoms, count_inter_module_clashes, _pair_distances


def atom(serial=1, residue=10, insertion="", altloc="", x=0.0, chain="A"):
    return f"ATOM  {serial:5d}  CA {altloc:1s}ALA {chain}{residue:4d}{insertion:1s}   {x:8.3f}{0.:8.3f}{0.:8.3f}  1.00 20.00           C  \n"


def test_models_never_mix_and_choice_is_explicit(tmp_path):
    pdb = tmp_path / "ensemble.pdb"
    pdb.write_text("MODEL        1\n" + atom(1, 10, x=0) + atom(2, 11, x=10) + "ENDMDL\nMODEL        2\n" + atom(1, 10, x=10) + atom(2, 11, x=0) + "ENDMDL\n")
    with pytest.raises(ValueError, match="multiple structure models"):
        read_pdb_atoms(pdb)
    for model in (1, 2):
        assert len(read_pdb_atoms(pdb, model_id=model)) == 2
        result = count_inter_module_clashes(pdb, model_id=model, first_chain="A", first_residues=[10], second_chain="A", second_residues=[11], cutoff_angstrom=2.5)
        assert result["clash_count"] == 0
        assert result["minimum_distance_angstrom"] == 10
    with pytest.raises(ValueError, match="not present"):
        read_pdb_atoms(pdb, model_id=3)


def test_altloc_is_not_an_implicit_A_selection(tmp_path):
    pdb = tmp_path / "alt.pdb"
    pdb.write_text(atom(1, altloc="A", x=1) + atom(2, altloc="B", x=9))
    with pytest.raises(ValueError, match="alternate locations"):
        read_pdb_atoms(pdb)
    assert read_pdb_atoms(pdb, altloc="B")[0].coordinate[0] == 9


def test_atoms_after_endmdl_are_not_assigned_to_the_previous_model(tmp_path):
    pdb = tmp_path / "invalid.pdb"
    pdb.write_text("MODEL        1\n" + atom() + "ENDMDL\n" + atom(2, residue=11))
    with pytest.raises(ValueError, match="outside MODEL/ENDMDL"):
        read_pdb_atoms(pdb, model_id=1)


def test_missing_sasa_cannot_publish_a_passing_ratio(tmp_path):
    model, reference = tmp_path / "model.json", tmp_path / "reference.json"
    model.write_text(json.dumps([dict(chain="A", residue=10, total=200)]))
    reference.write_text(json.dumps([dict(chain="A", residue=i, total=100) for i in (10, 11)]))
    result = compute_pocket_sasa_retention(model_json=model, reference_json=reference, chain="A", residues=[10, 11], model_configuration_hash="same", reference_configuration_hash="same")
    assert result.status == "insufficient_data"
    assert result.retention is None and result.passes is None and result.model_sasa is None
    assert [item.residue for item in result.missing_model_residues] == [11]
    with pytest.raises(ValueError, match="missing declared"):
        sum_residue_areas(parse_freesasa_json(model), chain="A", residues=[10, 11])


def test_sasa_mapping_preserves_insertion_chain_model_and_true_zero(tmp_path):
    model, reference = tmp_path / "m.json", tmp_path / "r.json"
    model.write_text(json.dumps([dict(chain="B", residue=-2, insertion="A", model_id=7, total=0)]))
    reference.write_text(json.dumps([dict(chain="A", residue="10B", model_id=2, total=100)]))
    result = compute_pocket_sasa_retention(model_json=model, reference_json=reference, chain="A", residues=["10B"], residue_mapping=[dict(reference=dict(chain="A", residue=10, insertion="B", model_id=2), model=dict(chain="B", residue=-2, insertion="A", model_id=7))], model_configuration_hash="same", reference_configuration_hash="same")
    assert result.retention == 0 and result.model_sasa == 0 and result.passes is False
    assert result.residue_mapping[0].model.model_id == 7
    model.write_text(json.dumps([dict(chain="B", residue=-2, insertion="A", model_id=7, total=0)] * 2))
    with pytest.raises(ValueError, match="duplicate"):
        sum_residue_areas(parse_freesasa_json(model), chain="B", residues=["-2A"], model_id=7)


def test_sasa_nonfinite_duplicate_selection_and_zero_denominator(tmp_path):
    path = tmp_path / "area.json"
    path.write_text('[{"chain":"A","residue":10,"total":NaN}]')
    with pytest.raises(ValueError):
        parse_freesasa_json(path)
    path.write_text('[{"chain":"A","residue":10,"total":0}]')
    with pytest.raises(ValueError, match="unique"):
        sum_residue_areas(parse_freesasa_json(path), chain="A", residues=[10, 10])
    result = compute_pocket_sasa_retention(model_json=path, reference_json=path, chain="A", residues=[10])
    assert result.retention is None and result.passes is None


def test_exact_chunked_distances_match_dense_and_strict_cutoff():
    rng = np.random.default_rng(21)
    first, second = rng.normal(size=(257, 3)), rng.normal(size=(1025, 3))
    dense = np.linalg.norm(first[:, None, :] - second[None, :, :], axis=2)
    count, minimum = _pair_distances(first, second, 2.5)
    assert count == int((dense < 2.5).sum())
    assert minimum == float(dense.min())
    assert _pair_distances(np.array([[0., 0., 0.]]), np.array([[2.5, 0., 0.]]), 2.5)[0] == 0


def test_real_2pdz_each_model_matches_independent_biopython():
    source = os.environ.get("FUSIONLAB_2PDZ_REFERENCE")
    if not source:
        pytest.skip("real 2PDZ supplied on the scientific host")
    from Bio.PDB import PDBParser
    structure = PDBParser(QUIET=True).get_structure("2PDZ", source)
    assert len(structure) == 15
    with pytest.raises(ValueError, match="multiple"):
        read_pdb_atoms(source)
    for independent in structure:
        atoms = read_pdb_atoms(source, model_id=independent.serial_num)
        expected = {(a.get_parent().get_parent().id, a.get_parent().id[1], a.get_parent().id[2].strip(), a.name): a.coord for a in independent.get_atoms()}
        assert len(atoms) == len(expected) == 1423
        for item in atoms:
            np.testing.assert_allclose(item.coordinate, expected[item.chain, item.residue, item.insertion, item.name], atol=1e-5, rtol=0)


def test_insertion_ca_mapping_does_not_collapse_numbers(tmp_path):
    from igem_drylab.structure_metrics import aligned_ca_rmsds
    pdb = tmp_path / "insert.pdb"
    pdb.write_text(atom(1, 10, x=0) + atom(2, 10, insertion="A", x=1) + atom(3, 11, x=3) + atom(4, 12, x=7))
    result = aligned_ca_rmsds(pdb, pdb, reference_chain="A", model_chain="A", core_residues=[10, "10A", 11], pocket_residues=[12])
    assert result["matched_core_ca_count"] == 3
    assert result["core_ca_rmsd_angstrom"] == pytest.approx(0, abs=1e-12)


def test_real_freesasa_selected_2pdz_model_matches_original_single_model(tmp_path):
    source = os.environ.get("FUSIONLAB_2PDZ_REFERENCE")
    if not source:
        pytest.skip("real 2PDZ supplied on the scientific host")
    freesasa = pytest.importorskip("freesasa")
    from igem_drylab.freesasa_runner import calculate_residue_sasa
    from Bio.PDB import PDBIO, PDBParser
    structure = PDBParser(QUIET=True).get_structure("2PDZ", source)
    independent = tmp_path / "model1.pdb"
    writer = PDBIO()
    writer.set_structure(structure[0])
    writer.save(str(independent))
    baseline = freesasa.calc(freesasa.Structure(str(independent)))
    result = calculate_residue_sasa(Path(source), tmp_path / "sasa.json", model_id=1)
    assert result["model_id"] == 1
    assert result["totalArea"] == pytest.approx(baseline.totalArea(), abs=1e-8)
    parsed = parse_freesasa_json(tmp_path / "sasa.json")
    assert {area.model_id for area in parsed} == {1}
    for area in parsed:
        assert area.total == pytest.approx(baseline.residueAreas()[area.chain][f"{area.residue}{area.insertion}"].total, abs=1e-8)
