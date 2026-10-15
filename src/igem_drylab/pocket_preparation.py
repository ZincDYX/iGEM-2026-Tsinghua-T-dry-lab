"""Derive a reproducible pocket selection from a sourced ligand pose.

No pocket, distance cutoff, ligand pose, or affinity is inferred from functional
anchors. Output is a computational contact neighborhood requiring biological
review before use as the original M2 pocket definition.
"""
from hashlib import sha256
from pathlib import Path

import numpy as np
from pydantic import Field, model_validator
from scipy.spatial import cKDTree

from .design_analysis import ScientificAnalysisInput
from .structure_metrics import read_pdb_atoms
from .template_geometry import StructureInput, ResidueSelection, selected_atoms


class PocketPredictionInput(ScientificAnalysisInput):
    """Read native P2Rank candidates; no automatic catalytic-pocket approval."""
    structure: StructureInput
    predictions_file: Path
    execution_record: Path


def read_pocket_candidates(payload: PocketPredictionInput) -> dict:
    import csv
    import json
    atoms,_=payload.structure.read()
    record=json.loads(payload.execution_record.read_text())
    if (record.get('tool_name')!='P2Rank' or record.get('returncode')!=0 or not record.get('command')
            or not record.get('tool_version') or record.get('input_sha256')!=sha256(payload.structure.path.read_bytes()).hexdigest()
            or record.get('output_sha256')!=sha256(payload.predictions_file.read_bytes()).hexdigest()):
        raise ValueError('P2Rank_requires_matching_native_execution_and_output')
    if payload.structure.source_kind=='prediction' and record.get('profile')!='alphafold':
        raise ValueError('predicted_structure_requires_P2Rank_alphafold_profile_not_B_factor_features')
    ca={(a.chain,str(a.residue)+a.insertion) for a in atoms if a.name=='CA' and not a.is_hetero}
    candidates=[]
    with payload.predictions_file.open(newline='',encoding='utf-8-sig') as stream:
        for raw in csv.DictReader(stream):
            row={k.strip():v.strip() for k,v in raw.items()}
            residues=[]
            for key in row['residue_ids'].split():
                chain,residue=key.split('_',1)
                if (chain,residue) not in ca:raise ValueError('P2Rank_residue_not_in_exact_input_model')
                residues.append(dict(chain=chain,residue=residue))
            values=[float(row[k]) for k in ('score','probability','center_x','center_y','center_z')]
            if not np.isfinite(values).all() or not 0<=values[1]<=1:
                raise ValueError('P2Rank_nonfinite_or_invalid_native_output')
            candidates.append(dict(name=row['name'],rank=int(row['rank']),score=values[0],
                native_ligand_site_probability=values[1],center_angstrom=values[2:],residues=residues,
                catalytic_pocket_confirmed=False))
    return dict(schema_version='m2-native-pocket-candidates-v1',tool='P2Rank',tool_version=record['tool_version'],
        status='native_candidates_require_target_review',candidates=candidates,
        input_structure_sha256=record['input_sha256'],predictions_file=str(payload.predictions_file),
        chemical_topology_ready=False,production_ready=False,
        scope='predicted_ligandable_neighborhoods_not_verified_target_catalysis_or_ligand_poses')


class PocketPreparationInput(ScientificAnalysisInput):
    reference: StructureInput
    protein: ResidueSelection
    ligand_pose_path: Path
    ligand: ResidueSelection
    pose_model_id: int | None = None
    pose_altloc: str | None = None
    pose_source_reference: str = Field(min_length=1)
    pose_method_version: str = Field(min_length=1)
    pose_in_reference_frame_evidence: str = Field(min_length=1)
    contact_cutoff_angstrom: float = Field(gt=0)
    contact_rule_reference: str = Field(min_length=1)
    functional_anchors: ResidueSelection | None = None

    @model_validator(mode="after")
    def anchors_are_reference_protein(self):
        if self.functional_anchors and not self.functional_anchors.keys() <= self.protein.keys():
            raise ValueError("functional_anchors_must_map_into_reference_protein")
        return self


def prepare_pocket(payload: PocketPreparationInput) -> dict:
    atoms, confidence = payload.reference.read()
    protein = selected_atoms(atoms, payload.protein)
    # Require each declared reference position to be a protein residue with CA.
    ca_keys = {(a.chain, a.residue, a.insertion) for a in protein if a.name == "CA" and not a.is_hetero}
    if ca_keys != payload.protein.keys():
        raise ValueError("pocket_selection_requires_complete_protein_residue_mapping")
    pose_atoms = read_pdb_atoms(payload.ligand_pose_path, model_id=payload.pose_model_id, altloc=payload.pose_altloc)
    ligand = selected_atoms(pose_atoms, payload.ligand)
    distances = cKDTree([a.coordinate for a in ligand]).query([a.coordinate for a in protein], k=1)[0]
    closest = {}
    for atom, distance in zip(protein, distances, strict=True):
        key = (atom.chain, atom.residue, atom.insertion)
        closest[key] = min(float(distance), closest.get(key, float("inf")))
    selected = sorted(k for k, distance in closest.items() if distance < payload.contact_cutoff_angstrom)
    if not selected:
        raise ValueError("sourced_pose_has_no_contacts_with_declared_reference_protein")
    ids = [str(k[1]) + k[2] if k[2] else k[1] for k in selected]
    anchors = payload.functional_anchors.keys() if payload.functional_anchors else set()
    return {"schema_version": "m2-pocket-preparation-v1", "status": "computed_requires_pocket_review",
        "reference_pocket_selection": {"chain": payload.protein.chain, "residues": ids},
        "residue_contacts": [dict(chain=k[0], residue=ids[i], minimum_ligand_distance_angstrom=closest[k],
            mean_plddt=None if confidence is None else confidence[k]) for i, k in enumerate(selected)],
        "anchors_outside_contact_neighborhood": [dict(chain=k[0], residue=str(k[1])+k[2]) for k in sorted(anchors-set(selected))],
        "reference_structure_sha256": sha256(payload.reference.path.read_bytes()).hexdigest(),
        "ligand_pose_sha256": sha256(payload.ligand_pose_path.read_bytes()).hexdigest(),
        "definition": {"distance": "minimum heavy-atom distance", "operator": "strict_less_than",
            "cutoff_angstrom": payload.contact_cutoff_angstrom, "rule_reference": payload.contact_rule_reference,
            "pose_source": payload.pose_source_reference, "pose_method": payload.pose_method_version,
            "pose_frame_evidence": payload.pose_in_reference_frame_evidence},
        "claim_scope": "computed_contacts_not_experimentally_established_pocket_or_binding_affinity"}
