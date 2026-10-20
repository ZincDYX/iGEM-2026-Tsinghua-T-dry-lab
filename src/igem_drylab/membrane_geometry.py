"""Versioned, coordinate-derived membrane checks for declared conformations.

This supplements Q1–Q4; it never infers contact probabilities, assembly in vivo,
Kd or catalytic activity. All coordinates and the membrane frame share units.
"""
from itertools import combinations
from hashlib import sha256
from typing import Literal
import numpy as np
from pydantic import Field, model_validator

from .compartments import CompartmentContract, ArtifactReference, MembraneTopologyEvidence
from .template_geometry import StructureInput, ResidueSelection, selected_atoms, clashes, _gate
from .structure_metrics import residue_key


class MembraneFrame(CompartmentContract):
    frame_id: str
    origin_angstrom: tuple[float,float,float]
    unit_normal: tuple[float,float,float]
    thickness_angstrom: float = Field(gt=0)
    positive_side: Literal["cytosolic", "luminal"]
    body_side: Literal["cytosolic", "luminal", "unknown"]
    source_reference: str = Field(min_length=1)
    raw_reference: ArtifactReference
    atom_radii_angstrom: dict[str,float]

    @model_validator(mode="after")
    def frame(self):
        if abs(float(np.linalg.norm(self.unit_normal))-1) > 1e-10:
            raise ValueError("membrane_normal_must_be_explicitly_unit_length")
        if not self.atom_radii_angstrom or any(value <= 0 for value in self.atom_radii_angstrom.values()):
            raise ValueError("membrane_exclusion_requires_sourced_positive_atomic_radii")
        return self


class TetherGeometry(CompartmentContract):
    subunit_id: str
    anchor: ResidueSelection
    linker: ResidueSelection
    attached_body: ResidueSelection
    contour_length_angstrom: float = Field(gt=0)
    contour_length_source: str = Field(min_length=1)


class MembraneSiteIdentity(CompartmentContract):
    species: Literal['OC','DMT']
    enzyme_construct_id: str
    enzyme_fusion_sequence_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    ligand_id: str
    binding_domain: str
    binding_pair_ref: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)


class MembraneConformer(CompartmentContract):
    model_id: str
    conformer_id: str
    structure: StructureInput
    frame: MembraneFrame
    tethers: list[TetherGeometry] = Field(min_length=1)
    scaffold: ResidueSelection
    domains: dict[str,ResidueSelection]
    pockets: dict[str,ResidueSelection]
    recruited_enzymes: dict[str,ResidueSelection]
    site_identities: dict[str,MembraneSiteIdentity] = Field(default_factory=dict)
    sampling_method: str = Field(min_length=1)
    sampling_scope: str = Field(min_length=1)
    coordinate_transform_reference: str = Field(min_length=1)


class MembraneGeometryInput(CompartmentContract):
    """ER M2 membrane ensemble with explicit geometry and subunit composition."""
    formula_version: Literal["m2-er-membrane-v1-2026-10-10"] = "m2-er-membrane-v1-2026-10-10"
    construct_id: str
    condition_id: str
    topology: MembraneTopologyEvidence
    subunit_composition: dict[str,bool]  # Concrete ID -> carries an anchor.
    assembly_applicability_source: str = Field(min_length=1)
    anchor_count_basis: Literal["explicit_subunit_composition"]
    conformers: list[MembraneConformer] = Field(min_length=1)
    heavy_atom_clash_cutoff_angstrom: float = Field(gt=0)
    clash_rule_source: str = Field(min_length=1)

    @model_validator(mode="after")
    def composition(self):
        if self.topology.construct_id != self.construct_id or self.topology.condition_id != self.condition_id:
            raise ValueError("membrane_topology_construct_or_condition_mismatch")
        anchored = {identifier for identifier, present in self.subunit_composition.items() if present}
        if not self.subunit_composition or not anchored:
            raise ValueError("ER_assembly_requires_explicit_nonempty_anchor_composition")
        if len({(c.model_id,c.conformer_id) for c in self.conformers}) != len(self.conformers):
            raise ValueError("membrane_conformers_must_have_unique_identifiers")
        for conformer in self.conformers:
            if {t.subunit_id for t in conformer.tethers} != anchored or len(conformer.tethers) != len(anchored):
                raise ValueError("each_anchor_subunit_requires_its_own_tether_not_one_per_cage")
            if conformer.frame.body_side != self.topology.body_side:
                raise ValueError("membrane_frame_and_topology_body_side_mismatch")
        return self


def calculate_membrane_geometry(payload: MembraneGeometryInput) -> dict:
    for artifact in [payload.topology.native_output, *payload.topology.raw_references]:
        artifact.verify()
    observations = []
    for conformer in payload.conformers:
        frame = conformer.frame
        frame.raw_reference.verify()
        atoms, confidence = conformer.structure.read()
        atoms = [atom for atom in atoms if atom.element not in {"H","D"}]
        if set(atom.element for atom in atoms) - frame.atom_radii_angstrom.keys():
            raise ValueError("membrane_atomic_radius_missing_for_selected_element")
        normal, origin = np.array(frame.unit_normal), np.array(frame.origin_angstrom)
        signed = lambda atom: float(np.dot(atom.coordinate-origin,normal))
        half = frame.thickness_angstrom/2
        anchor_keys = set().union(*(tether.anchor.keys() for tether in conformer.tethers))
        if not anchor_keys <= conformer.scaffold.keys():
            raise ValueError("declared_anchors_must_belong_to_scaffold_selection")
        membrane_atoms = [atom for atom in atoms if (atom.chain,atom.residue,atom.insertion) not in anchor_keys
            and abs(signed(atom))-frame.atom_radii_angstrom[atom.element] < half]
        def accessible(selection):
            selected = selected_atoms(atoms,selection)
            if frame.body_side == "unknown":
                return {"accessible":None,"reason":"scaffold_body_side_not_established","confidence":_gate(confidence,selection.keys())}
            sign = 1 if frame.body_side == frame.positive_side else -1
            margin = min(sign*signed(atom)-frame.atom_radii_angstrom[atom.element]-half for atom in selected)
            return {"accessible":margin >= 0,"minimum_clearance_angstrom":margin,"confidence":_gate(confidence,selection.keys())}
        tether_records = []
        for tether in conformer.tethers:
            anchor = selected_atoms(atoms,tether.anchor)
            selected_atoms(atoms,tether.linker)  # Complete linker mapping is mandatory.
            attached = selected_atoms(atoms,tether.attached_body)
            anchor_endpoint = (tether.anchor.chain, *residue_key(tether.anchor.residues[-1]))
            body_endpoint = (tether.attached_body.chain, *residue_key(tether.attached_body.residues[0]))
            ca_anchor = next((atom for atom in anchor if atom.name == "CA" and
                (atom.chain,atom.residue,atom.insertion) == anchor_endpoint), None)
            ca_body = next((atom for atom in attached if atom.name == "CA" and
                (atom.chain,atom.residue,atom.insertion) == body_endpoint), None)
            if ca_anchor is None or ca_body is None:
                raise ValueError("tether_requires_mapped_anchor_and_attachment_CA")
            distance = float(np.linalg.norm(ca_anchor.coordinate-ca_body.coordinate))
            depths = [signed(atom) for atom in anchor]
            tether_records.append({"subunit_id":tether.subunit_id,"attachment_distance_angstrom":distance,
                "within_declared_contour_bound":distance <= tether.contour_length_angstrom,
                "anchor_spans_declared_membrane":min(depths) <= -half and max(depths) >= half,
                "confidence":_gate(confidence,tether.anchor.keys() | tether.attached_body.keys()),
                "scope":"necessary_static_geometry_not_a_flexibility_probability"})
        placed = {identifier:selected_atoms(atoms,selection) for identifier,selection in conformer.recruited_enzymes.items()}
        scaffold = selected_atoms(atoms,conformer.scaffold)
        scaffold_clashes = {}
        for identifier,selection in conformer.recruited_enzymes.items():
            if selection.keys() & conformer.scaffold.keys():
                raise ValueError("enzyme_and_scaffold_selections_must_be_disjoint")
            scaffold_clashes[identifier] = clashes(placed[identifier],scaffold,payload.heavy_atom_clash_cutoff_angstrom)
        conflicts = []
        for first,second in combinations(placed,2):
            observation = clashes(placed[first],placed[second],payload.heavy_atom_clash_cutoff_angstrom)
            if observation["clash_count"]:
                conflicts.append({"first":first,"second":second,**observation})
        domain_access = {name:accessible(selection) for name,selection in conformer.domains.items()}
        pocket_access = {name:accessible(selection) for name,selection in conformer.pockets.items()}
        reasons = []
        if membrane_atoms: reasons.append('non_anchor_membrane_exclusion')
        if any(row['clash_count'] for row in scaffold_clashes.values()): reasons.append('enzyme_scaffold_clash')
        if any(row['accessible'] is False for row in [*domain_access.values(),*pocket_access.values()]):
            reasons.append('domain_or_pocket_wrong_side_or_membrane_occlusion')
        if any(not row['within_declared_contour_bound'] or not row['anchor_spans_declared_membrane'] for row in tether_records):
            reasons.append('tether_static_feasibility_failed')
        gates = [row['confidence'] for row in [*domain_access.values(),*pocket_access.values(),*tether_records]]
        uncertain = frame.body_side == 'unknown' or any(gate not in {'high','experimental_template'} for gate in gates)
        eligibility = 'conditional' if uncertain else 'excluded' if reasons else 'eligible'
        if uncertain: reasons.append('side_or_confidence_not_quantitatively_resolved')
        observations.append({"model_id":conformer.model_id,"conformer_id":conformer.conformer_id,
            'eligibility':eligibility,'eligibility_reasons':reasons,
            'eligibility_rule_source':payload.clash_rule_source,
            'site_identities':{name:identity.model_dump(mode='json') for name,identity in conformer.site_identities.items()},
            "structure_sha256":sha256(conformer.structure.path.read_bytes()).hexdigest(),
            "membrane_frame":frame.model_dump(mode="json"),
            "membrane_clashes":{"count":len(membrane_atoms),"atoms":[{"chain":a.chain,"residue":a.residue,"atom":a.name} for a in membrane_atoms]},
            "domains_on_accessible_side":domain_access,
            "pocket_accessibility_in_membrane_context":pocket_access,
            "tether_assembly_feasibility":tether_records,"site_conflict_graph":conflicts,
            "enzyme_scaffold_clashes":scaffold_clashes,
            "sampling_method":conformer.sampling_method,"sampling_scope":conformer.sampling_scope,
            "coordinate_transform_reference":conformer.coordinate_transform_reference,
            "interpretation":"static_geometry_review_only_not_global_biological_rejection"})
    counts = [item["membrane_clashes"]["count"] for item in observations]
    return {"schema_version":"m2-er-membrane-v1","formula_version":payload.formula_version,
        "construct_id":payload.construct_id,"condition_id":payload.condition_id,"conformers":observations,
        "anchor_count":sum(payload.subunit_composition.values()),"anchor_count_basis":payload.anchor_count_basis,
        "membrane_clash_range":{"min":min(counts),"max":max(counts)},
        "status":"review","claim_scope":"predicted_membrane_geometry_not_binding_activity_or_dynamic_feasibility"}
