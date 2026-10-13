"""Independent coordinate/identity oracles; fixtures are not biological data."""
import asyncio
import csv
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

from igem_drylab.pocket_preparation import PocketPreparationInput, prepare_pocket


def atom(number, residue, x, *, chain="A", insertion="", hetero=False):
    record = "HETATM" if hetero else "ATOM  "
    name, residue_name, element = ("C1", "LIG", "C") if hetero else ("CA", "ALA", "C")
    return f"{record}{number:5d} {name:^4s} {residue_name} {chain}{residue:4d}{insertion:1s}   {x:8.3f}{0.:8.3f}{0.:8.3f}  1.00 90.00          {element:>2s}\n"


def pocket_request(tmp_path):
    reference = tmp_path / "SYNTHETIC_reference.pdb"
    reference.write_text(atom(1, 10, 0)+atom(2, 10, 2, insertion="A")+atom(3, 11, 3)+"END\n")
    pose = tmp_path / "SYNTHETIC_ligand.pdb"
    pose.write_text(atom(1, 1, 0, chain="L", hetero=True)+"END\n")
    return dict(reference=dict(path=reference, source_kind="experimental", source_reference="SYNTHETIC coordinate oracle; not an experiment"),
        protein=dict(chain="A", residues=[10, "10A", 11]), ligand_pose_path=pose, ligand=dict(chain="L", residues=[1]),
        pose_source_reference="synthetic", pose_method_version="synthetic_identity_pose",
        pose_in_reference_frame_evidence="synthetic same coordinate frame", contact_cutoff_angstrom=3,
        contact_rule_reference="synthetic oracle cutoff, not a project default",
        functional_anchors=dict(chain="A", residues=[11]))


def test_pocket_contacts_preserve_insertions_and_strict_boundary(tmp_path):
    result = prepare_pocket(PocketPreparationInput.model_validate(pocket_request(tmp_path)))
    assert result["reference_pocket_selection"] == {"chain":"A", "residues":[10, "10A"]}
    assert [r["minimum_ligand_distance_angstrom"] for r in result["residue_contacts"]] == [0., 2.]
    assert result["anchors_outside_contact_neighborhood"] == [dict(chain="A", residue="11")]
    assert result["status"] == "computed_requires_pocket_review"


@pytest.mark.parametrize("field", ["contact_cutoff_angstrom", "contact_rule_reference", "pose_in_reference_frame_evidence"])
def test_no_guessed_cutoff_rule_or_pose_alignment(tmp_path, field):
    request = pocket_request(tmp_path);request.pop(field)
    with pytest.raises(ValidationError): PocketPreparationInput.model_validate(request)


def test_missing_protein_mapping_or_far_pose_is_not_a_pocket(tmp_path):
    raw = pocket_request(tmp_path);raw["protein"]["residues"].append(99)
    with pytest.raises(ValueError, match="incomplete_geometry"): prepare_pocket(PocketPreparationInput.model_validate(raw))
    raw = pocket_request(tmp_path)
    Path(raw["ligand_pose_path"]).write_text(atom(1, 1, 100, chain="L", hetero=True)+"END\n")
    with pytest.raises(ValueError, match="no_contacts"): prepare_pocket(PocketPreparationInput.model_validate(raw))


def test_pocket_tool_is_callable_over_real_stdio(tmp_path):
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    payload = PocketPreparationInput.model_validate(pocket_request(tmp_path)).model_dump(mode="json")
    root = Path(__file__).parents[1]
    async def run():
        parameters = StdioServerParameters(command=sys.executable, args=["-B", "-m", "igem_drylab.mcp.server"],
            cwd=root, env={"PYTHONPATH":str(root/"src")})
        async with Client(parameters, read_timeout_seconds=30) as client:
            result = await client.call_tool("igem.m2.prepare_pocket", {"payload":payload})
            assert not result.is_error
            assert result.structured_content["result"]["reference_pocket_selection"]["residues"] == [10, "10A"]
    asyncio.run(run())


def inventory_module():
    spec = importlib.util.spec_from_file_location("m2_inventory", Path(__file__).parents[1]/"scripts/prepare_m2_models.py")
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_inventory_matches_complete_sequence_and_rejects_mispaired_confidence(tmp_path):
    from test_region_assessment import prediction
    request = prediction(tmp_path)
    fasta = tmp_path / "inputs.fasta";fasta.write_text(">expected\nAAAA\n>absent\nAAAG\n")
    targets = tmp_path / "M2_prediction_targets.csv"
    with targets.open("w", newline="") as out:
        writer=csv.DictWriter(out,fieldnames=["record_id","aa_length","source_fasta"]);writer.writeheader()
        writer.writerows([dict(record_id=i, aa_length=4, source_fasta=fasta.name) for i in ["expected","absent"]])
    module = inventory_module();report = module.inventory(targets, tmp_path, [tmp_path])
    assert report["targets"][0]["status"] == "paired_models_available"
    assert report["targets"][1]["status"] == "needs_prediction"
    assert not report["model_inputs_ready"]
    raw=json.loads(request.confidence_file.read_text());raw["plddt"][0]=80;request.confidence_file.write_text(json.dumps(raw))
    report=module.inventory(targets, tmp_path, [tmp_path])
    assert all(not row["models"] for row in report["targets"])
    assert report["invalid_pairs"][0]["reason"] == "coordinate_confidence_does_not_match_paired_scores"
