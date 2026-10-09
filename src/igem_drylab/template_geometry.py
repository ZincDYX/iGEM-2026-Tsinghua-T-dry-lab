"""Q3/Q4 rigid template placement and coordinate-derived site conflict graphs.

These are explicit static scenarios, not binding predictions. Flexible
coordinates never become a biological rejection or a scalar binding efficiency.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from itertools import combinations
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator
from scipy.spatial import cKDTree

from .design_analysis import ScientificAnalysisInput
from .structure_metrics import Atom, read_pdb_atoms, residue_key, kabsch_transform
from .scoring.m2_site_geometry import M2SiteGeometryInput, analyse_site_cooccupancy


class StructureInput(ScientificAnalysisInput):
    path: Path
    model_id: int | None = None
    altloc: str | None = None
    source_kind: Literal["experimental", "prediction"]
    source_reference: str = Field(min_length=1)
    confidence_file: Path | None = None
    expected_sequence: str | None = None

    @model_validator(mode="after")
    def predicted_identity(self):
        if self.source_kind == "prediction" and (self.confidence_file is None or not self.expected_sequence):
            raise ValueError("predicted_geometry_requires_paired_confidence_and_complete_sequence")
        return self

    def read(self):
        atoms = read_pdb_atoms(self.path, model_id=self.model_id, altloc=self.altloc)
        confidence = None
        if self.source_kind == "prediction":
            from .region_assessment import assess_regions, RegionAssessmentInput, Region
            observed = assess_regions(RegionAssessmentInput(candidate_id="geometry", sequence=self.expected_sequence,
                tool_input_id=self.confidence_file.name.partition("_scores_rank_")[0],
                confidence_file=self.confidence_file, regions=[Region(name="complete", role="diagnostic",
                start=1, end=len(self.expected_sequence))], calculate_accessibility=False))
            if observed["model_sha256"] != sha256(self.path.read_bytes()).hexdigest():
                raise ValueError("geometry_structure_is_not_paired_confidence_model")
            import json
            values = json.loads(self.confidence_file.read_text())["plddt"]
            ca = [a for a in atoms if a.name == "CA"]
            if len(ca) != len(values):
                raise ValueError("confidence_must_cover_every_selected_CA")
            confidence = {(a.chain, a.residue, a.insertion): float(v) for a, v in zip(ca, values, strict=True)}
        return atoms, confidence


class ResidueSelection(ScientificAnalysisInput):
    chain: str
    residues: list[int | str] = Field(min_length=1)

    def keys(self):
        keys = {(self.chain, *residue_key(r)) for r in self.residues}
        if len(keys) != len(self.residues):
            raise ValueError("residue_selection_must_be_unique")
        return keys


class CAMapping(ScientificAnalysisInput):
    reference_chain: str
    mobile_chain: str
    residue_pairs: list[tuple[int | str, int | str]] = Field(min_length=3)
    reviewed_reference: str = Field(min_length=1)

    def fit(self, reference: list[Atom], mobile: list[Atom]):
        pairs = [(residue_key(a), residue_key(b)) for a, b in self.residue_pairs]
        if len({p[0] for p in pairs}) != len(pairs) or len({p[1] for p in pairs}) != len(pairs):
            raise ValueError("placement_mapping_must_be_one_to_one")
        ref = {(a.residue, a.insertion): a.coordinate for a in reference if a.chain == self.reference_chain and a.name == "CA"}
        mob = {(a.residue, a.insertion): a.coordinate for a in mobile if a.chain == self.mobile_chain and a.name == "CA"}
        if any(a not in ref or b not in mob for a, b in pairs):
            raise ValueError("placement_mapping_missing_declared_CA")
        x, y = np.vstack([ref[a] for a, _ in pairs]), np.vstack([mob[b] for _, b in pairs])
        if np.linalg.matrix_rank(x-x.mean(axis=0)) < 2 or np.linalg.matrix_rank(y-y.mean(axis=0)) < 2:
            raise ValueError("collinear_template_mapping_has_no_unique_orientation")
        rotation, translation = kabsch_transform(x, y)
        rmsd = float(np.sqrt(np.mean(np.sum((y@rotation+translation-x)**2, axis=1))))
        return rotation, translation, rmsd


def transform_atoms(atoms, rotation, translation):
    return [replace(a, coordinate=a.coordinate@rotation+translation, pdb_line=None) for a in atoms]


def _gate(confidence, keys):
    if confidence is None:
        return "experimental_template"
    if not keys <= confidence.keys():
        raise ValueError("missing_selection_confidence")
    mean = float(np.mean([confidence[k] for k in keys]))
    return "high" if mean > 70 else "medium" if mean >= 50 else "low"


def selected_atoms(atoms, selection):
    keys = selection.keys()
    selected = [a for a in atoms if (a.chain, a.residue, a.insertion) in keys and a.element not in {"H", "D"}]
    if {(a.chain, a.residue, a.insertion) for a in selected} != keys:
        raise ValueError("incomplete_geometry_residue_selection")
    return selected


def _identity(atom):
    return atom.chain, str(atom.residue)+atom.insertion, atom.name


def clashes(first, second, cutoff, exclusions=()):
    first = [a for a in first if a.element not in {"H", "D"}]
    second = [a for a in second if a.element not in {"H", "D"}]
    excluded = {(tuple(a), tuple(b)) for a, b in exclusions}
    if not first or not second:
        raise ValueError("clash_modules_must_contain_heavy_atoms")
    if any(a not in {_identity(v) for v in first} or b not in {_identity(v) for v in second} for a, b in excluded):
        raise ValueError("intentional_contact_exclusion_not_present_in_actual_structures")
    tree = cKDTree([a.coordinate for a in second])
    count, pocket_atoms = 0, set()
    minimum = float(tree.query([a.coordinate for a in first], k=1)[0].min())
    for atom in first:
        for index in tree.query_ball_point(atom.coordinate, cutoff):
            other = second[index]
            if np.linalg.norm(atom.coordinate-other.coordinate) < cutoff and (_identity(atom), _identity(other)) not in excluded:
                count += 1
                pocket_atoms.add(_identity(atom))
    return {"clash_count": count, "minimum_distance_angstrom": minimum,
            "first_clashing_atom_ids": sorted(pocket_atoms), "cutoff_angstrom": cutoff,
            "intentional_contact_exclusions": len(excluded)}


def atom_sasa(objects: dict[str, list[Atom]], parameters=None):
    """Exact coordinates through FreeSASA addAtom, no lossy PDB reserialization."""
    import freesasa
    structure = freesasa.Structure()
    aliases = {}
    ids = []
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    for name, atoms in objects.items():
        for atom in atoms:
            if atom.element in {"H", "D"} or atom.is_hetero:
                continue
            key = (name, atom.chain)
            if key not in aliases:
                if len(aliases) == len(alphabet):
                    raise ValueError("SASA_context_exceeds_explicit_chain_alias_capacity")
                aliases[key] = alphabet[len(aliases)]
            before = structure.nAtoms()
            structure.addAtom(atom.name, atom.residue_name, str(atom.residue)+atom.insertion,
                              aliases[key], *map(float, atom.coordinate))
            if structure.nAtoms() != before+1:
                raise ValueError("FreeSASA_did_not_accept_declared_atom")
            ids.append((name, *_identity(atom)))
    result = freesasa.calc(structure, parameters or freesasa.Parameters())
    return {key: float(result.atomArea(i)) for i, key in enumerate(ids)}


def selected_sasa(areas, name, selection):
    keys = selection.keys()
    present = {(chain, *residue_key(residue)) for obj, chain, residue, atom in areas if obj == name}
    if not keys <= present:
        raise ValueError("incomplete_selected_SASA_atoms")
    return sum(area for (obj, chain, residue, _), area in areas.items()
               if obj == name and (chain, *residue_key(residue)) in keys)


class AssemblyExpansionInput(ScientificAnalysisInput):
    template: StructureInput
    actual_fusion: StructureInput
    target_chains: list[str] = Field(min_length=1)
    core_mapping: CAMapping
    interface_residues: list[int | str] = Field(min_length=1)
    interface_contact_cutoff_angstrom: float = Field(gt=0)
    rule_reference: str = Field(min_length=1)
    assembly_applicability_reference: str | None = None
    extension_clash_cutoff_angstrom: float | None = Field(default=None, gt=0)
    extension_clash_rule_reference: str | None = None

    @model_validator(mode="after")
    def extension_rule(self):
        if (self.extension_clash_cutoff_angstrom is None) != (self.extension_clash_rule_reference is None):
            raise ValueError("extension_clash_cutoff_requires_reviewed_rule")
        return self

    def read(self):
        result = expand_actual_fusion(self)
        _, original_confidence = self.actual_fusion.read()
        atoms, confidence = [], {} if original_confidence is not None else None
        for chain, rows in result["copies"].items():
            for row in rows:
                residue, insertion = residue_key(row["residue"])
                atoms.append(Atom(chain=chain, residue=residue, insertion=insertion, name=row["atom"],
                    element=row["element"], coordinate=np.asarray(row["xyz_angstrom"]),
                    residue_name=row["residue_name"]))
                if confidence is not None:
                    confidence[(chain,residue,insertion)] = original_confidence[(self.core_mapping.mobile_chain,residue,insertion)]
        return atoms, confidence


def expand_actual_fusion(payload: AssemblyExpansionInput) -> dict:
    template, _ = payload.template.read()
    mobile, confidence = payload.actual_fusion.read()
    if {a.chain for a in mobile} != {payload.core_mapping.mobile_chain}:
        raise ValueError("actual_fusion_expansion_requires_one_complete_chain")
    if len(set(payload.target_chains)) != len(payload.target_chains):
        raise ValueError("duplicate_assembly_target_chain")
    # Core CAs must include every specified interface residue.
    declared = {residue_key(a) for a, _ in payload.core_mapping.residue_pairs}
    if not {residue_key(r) for r in payload.interface_residues} <= declared:
        raise ValueError("assembly_core_mapping_must_cover_declared_interface")
    copies, transforms = {}, []
    gates = []
    for chain in payload.target_chains:
        mapping = payload.core_mapping.model_copy(update={"reference_chain": chain})
        rotation, translation, rmsd = mapping.fit(template, mobile)
        copies[chain] = transform_atoms(mobile, rotation, translation)
        gates.append(_gate(confidence, {(mapping.mobile_chain, *residue_key(r)) for _, r in mapping.residue_pairs}))
        transforms.append({"target_chain": chain, "rotation": rotation.tolist(), "translation_angstrom": translation.tolist(),
                           "core_CA_RMSD_angstrom": rmsd})
    interfaces = []
    template_keys = {(a.chain, a.residue, a.insertion, a.name): a for a in template if a.name == "CA"}
    mobile_keys = {(a.chain, a.residue, a.insertion, a.name): a for a in mobile if a.name == "CA"}
    mapped = {residue_key(a): residue_key(b) for a, b in payload.core_mapping.residue_pairs}
    for first, second in combinations(payload.target_chains, 2):
        for a in payload.interface_residues:
            for b in payload.interface_residues:
                ka, kb = residue_key(a), residue_key(b)
                ref_a = template_keys.get((first, *ka, "CA")); ref_b = template_keys.get((second, *kb, "CA"))
                if ref_a is None or ref_b is None:
                    raise ValueError("declared_assembly_interface_residue_missing")
                distance = float(np.linalg.norm(ref_a.coordinate-ref_b.coordinate))
                if distance < payload.interface_contact_cutoff_angstrom:
                    ta, tb = transforms[payload.target_chains.index(first)], transforms[payload.target_chains.index(second)]
                    xa = mobile_keys[(payload.core_mapping.mobile_chain, *mapped[ka], "CA")].coordinate
                    xb = mobile_keys[(payload.core_mapping.mobile_chain, *mapped[kb], "CA")].coordinate
                    new_distance = float(np.linalg.norm(xa@np.asarray(ta["rotation"])+ta["translation_angstrom"]-
                        (xb@np.asarray(tb["rotation"])+tb["translation_angstrom"])))
                    interfaces.append({"first_chain": first, "second_chain": second, "reference_residues": [a, b],
                                       "reference_CA_distance_angstrom": distance, "fusion_CA_distance_angstrom": new_distance})
    if not interfaces:
        raise ValueError("declared_interface_contains_no_reference_contacts_at_reviewed_cutoff")
    extension_keys = {(payload.core_mapping.mobile_chain, *residue_key(r)) for _, r in payload.core_mapping.residue_pairs}
    interface_overlaps = []
    for first, second in combinations(copies, 2):
        # Source core contacts are expected. Report clashes involving at least
        # one introduced residue, without making a rigid clash a hard rejection.
        ext_first = [a for a in copies[first] if (a.chain,a.residue,a.insertion) not in extension_keys]
        ext_second = [a for a in copies[second] if (a.chain,a.residue,a.insertion) not in extension_keys]
        if (ext_first or ext_second) and payload.extension_clash_cutoff_angstrom is not None:
            observations = []
            if ext_first:
                observations.append(clashes(ext_first, copies[second], payload.extension_clash_cutoff_angstrom))
            if ext_second:
                core_first = [a for a in copies[first] if (a.chain,a.residue,a.insertion) in extension_keys]
                observations.append(clashes(core_first, ext_second, payload.extension_clash_cutoff_angstrom))
            interface_overlaps.append({"first_chain":first,"second_chain":second,"extension_contact_observations":observations})
    return {"schema_version": "m2-core-template-expansion-v1", "copies": _coordinates(copies), "transforms": transforms,
            "interface_contacts": interfaces, "confidence_gates": gates, "subunit_count": len(copies),
            "extension_contact_observations": interface_overlaps,
            "extension_clash_rule_reference": payload.extension_clash_rule_reference,
            "assembly_applicability_confirmed": bool(payload.assembly_applicability_reference),
            "scope": "rigid_core_template_compatibility_not_observed_24mer_assembly",
            "source_hashes": _hashes(payload.template, payload.actual_fusion)}


def _coordinates(objects):
    return {name: [{"chain": a.chain, "residue": str(a.residue)+a.insertion, "atom": a.name,
                    "element": a.element, "residue_name": a.residue_name, "xyz_angstrom": a.coordinate.tolist()} for a in atoms]
            for name, atoms in objects.items()}


def _hashes(*structures):
    result = []
    for s in structures:
        if isinstance(s, AssemblyExpansionInput):
            result.extend(_hashes(s.template, s.actual_fusion))
        else:
            result.append({"path": str(s.path), "sha256": sha256(s.path.read_bytes()).hexdigest(),
                "model_id": s.model_id, "altloc": s.altloc, "source_reference": s.source_reference})
    return result


class RecruitmentPlacement(ScientificAnalysisInput):
    site_id: str
    species: Literal["OC", "DMT"]
    template: StructureInput
    enzyme: StructureInput
    template_domain_to_scaffold: CAMapping  # reference = scaffold, mobile = template domain
    enzyme_ligand_to_template: CAMapping    # reference = template peptide, mobile = enzyme ligand
    enzyme_pocket: ResidueSelection
    intentional_enzyme_scaffold_contacts: list[tuple[tuple[str, str, str], tuple[str, str, str]]] = Field(default_factory=list)


class RecruitmentGeometryInput(ScientificAnalysisInput):
    scaffold: StructureInput | AssemblyExpansionInput
    scaffold_id: str
    placements: list[RecruitmentPlacement] = Field(min_length=1)
    clash_cutoff_angstrom: float = Field(gt=0)
    clash_rule_reference: str = Field(min_length=1)
    pocket_retention_cutoff: float | None = Field(default=None, ge=0, le=1)
    pocket_rule_reference: str | None = None
    assembly_applicability_reference: str | None = None
    assembly_subunit_count: int | None = Field(default=None, ge=1)
    sh3_per_subunit: int | None = Field(default=None, ge=0)
    pdz_per_subunit: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def reviewed_graph_rules(self):
        if (self.pocket_retention_cutoff is None) != (self.pocket_rule_reference is None):
            raise ValueError("pocket_occlusion_cutoff_requires_explicit_reviewed_rule")
        if len({s.site_id for s in self.placements}) != len(self.placements):
            raise ValueError("placement_site_ids_must_be_unique")
        return self


def calculate_recruitment_geometry(payload: RecruitmentGeometryInput) -> dict:
    scaffold, scaffold_confidence = payload.scaffold.read()
    poses, rows, selections = {}, [], {}
    for placement in payload.placements:
        template, template_confidence = placement.template.read()
        enzyme, enzyme_confidence = placement.enzyme.read()
        r_domain, t_domain, domain_rmsd = placement.template_domain_to_scaffold.fit(scaffold, template)
        r_ligand, t_ligand, ligand_rmsd = placement.enzyme_ligand_to_template.fit(template, enzyme)
        rotation = r_ligand@r_domain
        translation = t_ligand@r_domain+t_domain
        pose = transform_atoms(enzyme, rotation, translation)
        selected_atoms(pose, placement.enzyme_pocket)
        poses[placement.site_id] = pose
        selections[placement.site_id] = placement.enzyme_pocket
        domain_keys = {(placement.template_domain_to_scaffold.reference_chain, *residue_key(r))
                       for r, _ in placement.template_domain_to_scaffold.residue_pairs}
        ligand_keys = {(placement.enzyme_ligand_to_template.mobile_chain, *residue_key(r))
                       for _, r in placement.enzyme_ligand_to_template.residue_pairs}
        gates = [_gate(scaffold_confidence, domain_keys), _gate(enzyme_confidence, ligand_keys),
                 _gate(enzyme_confidence, placement.enzyme_pocket.keys()),
                 _gate(template_confidence, {(placement.template_domain_to_scaffold.mobile_chain, *residue_key(r))
                    for _, r in placement.template_domain_to_scaffold.residue_pairs}),
                 _gate(template_confidence, {(placement.enzyme_ligand_to_template.reference_chain, *residue_key(r))
                    for r, _ in placement.enzyme_ligand_to_template.residue_pairs})]
        collision = clashes(pose, scaffold, payload.clash_cutoff_angstrom, placement.intentional_enzyme_scaffold_contacts)
        rows.append({"site_id": placement.site_id, "species": placement.species, "domain_CA_RMSD_angstrom": domain_rmsd,
                     "ligand_CA_RMSD_angstrom": ligand_rmsd, "rotation": rotation.tolist(),
                     "translation_angstrom": translation.tolist(), "confidence_gates": gates,
                     "scaffold_clashes": collision, "source_hashes": _hashes(placement.template, placement.enzyme)})
    import freesasa
    parameters = freesasa.Parameters()
    baseline = {}
    for name, pose in poses.items():
        areas = atom_sasa({"scaffold": scaffold, name: pose}, parameters)
        baseline[name] = selected_sasa(areas, name, selections[name])
    conflicts, pair_rows = [], []
    for first, second in combinations(poses, 2):
        collision = clashes(poses[first], poses[second], payload.clash_cutoff_angstrom)
        areas = atom_sasa({"scaffold": scaffold, first: poses[first], second: poses[second]}, parameters)
        retention = {name: selected_sasa(areas, name, selections[name])/baseline[name] if baseline[name] > 0 else None
                     for name in (first, second)}
        occluded = any(v is not None and v < payload.pocket_retention_cutoff for v in retention.values()) if payload.pocket_retention_cutoff is not None else None
        if collision["clash_count"] or occluded is True:
            conflicts.append((first, second))
        pair_rows.append({"first_site": first, "second_site": second, "enzyme_clashes": collision,
                          "pocket_SASA_retention_against_single_enzyme_context": retention,
                          "pocket_interference_at_declared_cutoff": occluded})
    confident = all(all(g in {"high", "experimental_template"} for g in row["confidence_gates"]) for row in rows)
    graph = M2SiteGeometryInput(scaffold_id=payload.scaffold_id,
        assembly_applicability_confirmed=bool(payload.assembly_applicability_reference),
        assembly_subunit_count=payload.assembly_subunit_count, sh3_sites_per_subunit=payload.sh3_per_subunit,
        pdz_sites_per_subunit=payload.pdz_per_subunit,
        sites=[dict(site_id=row["site_id"], species=row["species"], geometrically_accessible=row["scaffold_clashes"]["clash_count"] == 0) for row in rows],
        conflict_edges=conflicts, model_ids=[str(payload.scaffold.path if isinstance(payload.scaffold,StructureInput) else payload.scaffold.actual_fusion.path)], clash_rule_provenance=payload.clash_rule_reference)
    occupancy = analyse_site_cooccupancy(graph).model_dump(mode="json")
    occupancy["m3_ready"] = occupancy["m3_ready"] and confident and payload.pocket_retention_cutoff is not None
    return {"schema_version": "m2-template-recruitment-v1", "placements": rows, "pair_observations": pair_rows,
            "conflict_graph": graph.model_dump(mode="json"), "cooccupancy": occupancy,
            "placed_coordinates": _coordinates(poses), "source_hashes": _hashes(payload.scaffold),
            "formal_verdict": "review" if confident else "blocked", "pose_confidence_sufficient": confident,
            "scope": "one_declared_rigid_scenario_not_affinity_or_global_flexible_ensemble",
            "joint_occupancy_independent": not conflicts and all(s.geometrically_accessible for s in graph.sites) and occupancy["m3_ready"]}


class RecruitmentEnsembleInput(ScientificAnalysisInput):
    scenarios: list[RecruitmentGeometryInput] = Field(min_length=2)
    independence_reference: str = Field(min_length=1)


def calculate_recruitment_ensemble(payload: RecruitmentEnsembleInput) -> dict:
    first = payload.scenarios[0]
    def identity(scenario):
        return (scenario.scaffold_id, [(p.site_id,p.species,p.enzyme.expected_sequence) for p in scenario.placements],
            scenario.clash_cutoff_angstrom, scenario.pocket_retention_cutoff, scenario.assembly_applicability_reference,
            scenario.assembly_subunit_count, scenario.sh3_per_subunit, scenario.pdz_per_subunit)
    if any(identity(row) != identity(first) for row in payload.scenarios[1:]):
        raise ValueError("ensemble_requires_same_construct_sites_species_and_decision_rules")
    rows = [calculate_recruitment_geometry(row) for row in payload.scenarios]
    for row in rows:
        row.pop("placed_coordinates")  # individual workflow can export poses
    persistent_edges = set(map(tuple, rows[0]["conflict_graph"]["conflict_edges"]))
    for row in rows[1:]:
        persistent_edges &= set(map(tuple, row["conflict_graph"]["conflict_edges"]))
    intervals = {}
    for key in ("maximum_total_cooccupancy", "eta_acc_sh3", "eta_acc_pdz"):
        values = [r["cooccupancy"].get(key) for r in rows]
        intervals[key] = {"minimum":min(values),"maximum":max(values)} if all(v is not None for v in values) else None
    return {"schema_version":"m2-recruitment-ensemble-v1","scaffold_id":first.scaffold_id,
        "scenarios":rows,"persistent_conflict_edges":sorted(persistent_edges),"observed_geometry_intervals":intervals,
        "independence_reference":payload.independence_reference,"formal_verdict":"review",
        "scope":"observed_declared_conformations_not_global_flexible_ensemble_or_binding_affinity",
        "m3_ready":False,"m3_blocker":"Choose a reviewed occupancy model/conditional scenario; no average eta is fabricated."}
