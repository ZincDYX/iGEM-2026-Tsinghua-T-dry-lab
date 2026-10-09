"""Template-based geometric expansion of a local FTH1 fusion arm.

This module deliberately does not attempt to co-fold a ferritin 24-mer with
disordered regions and recruited enzymes.  Instead, it uses a supplied
24-subunit FTH1 template as a rigid coordinate frame, maps one locally
predicted fusion arm to every subunit, and reports geometry-only exclusion
metrics.  Its accessibility result is *not* solvent accessible surface area.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from string import ascii_letters, digits

import numpy as np
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scipy.spatial import cKDTree

from .interface_metrics import read_pdb_atoms
from .models import AtomRecord


class Fth1ExpansionResult(BaseModel):
    template_pdb: Path
    local_arm_pdb: Path
    reference_core_chain: str
    subunit_count: int = Field(ge=1)
    arm_atoms_per_subunit: int = Field(ge=1)
    total_expanded_arm_atoms: int = Field(ge=1)
    core_arm_clash_pairs: int = Field(ge=0)
    arm_arm_clash_pairs: int = Field(ge=0)
    minimum_core_arm_distance_angstrom: float
    minimum_arm_arm_distance_angstrom: float | None
    accessible_probe_atoms: int = Field(ge=0)
    accessible_probe_fraction: float = Field(ge=0, le=1)
    crowding_score: float = Field(ge=0, le=1)
    assessment: str
    assembled_pdb: Path | None = None


@dataclass(frozen=True)
class _CoordinateAtom:
    source_chain: str
    residue_id: int
    residue_name: str
    atom_name: str
    coordinate: np.ndarray


def expand_fth1_arms(
    *,
    template_pdb: Path,
    local_arm_pdb: Path,
    reference_core_chain: str,
    core_anchor_residue: int,
    core_anchor_atom: str,
    core_orientation_atom: str,
    arm_anchor_chain: str,
    arm_anchor_residue: int,
    arm_anchor_atom: str,
    arm_orientation_atom: str,
    probe_chain: str | None = None,
    probe_residue_ids: list[int] | None = None,
    clash_cutoff_angstrom: float = 2.0,
    exposure_cutoff_angstrom: float = 5.0,
    expected_subunits: int = 24,
    output_pdb: Path | None = None,
) -> Fth1ExpansionResult:
    """Expand one fusion arm around a rigid FTH1 cage and score steric risk.

    ``core_orientation_atom`` and ``arm_orientation_atom`` define the outward
    direction at the attachment point.  They must not coincide with their
    corresponding anchor atom.  The local-arm PDB should contain only the
    appendage, not a duplicate FTH1 subunit.
    """
    if clash_cutoff_angstrom <= 0 or exposure_cutoff_angstrom <= clash_cutoff_angstrom:
        raise ValueError("Require positive cutoffs and exposure_cutoff_angstrom > clash_cutoff_angstrom")

    core_atoms = read_pdb_atoms(template_pdb)
    arm_records = read_pdb_atoms(local_arm_pdb)
    if not core_atoms:
        raise ValueError(f"No atoms found in template PDB: {template_pdb}")
    if not arm_records:
        raise ValueError(f"No atoms found in local arm PDB: {local_arm_pdb}")

    core_chains = sorted({atom.chain_id for atom in core_atoms if atom.chain_id})
    if reference_core_chain not in core_chains:
        raise ValueError(f"Reference chain '{reference_core_chain}' not found in template")
    if expected_subunits > 0 and len(core_chains) != expected_subunits:
        raise ValueError(
            f"Template contains {len(core_chains)} protein chains; expected {expected_subunits}. "
            "Use a complete FTH1 24-mer template or explicitly set expected_subunits."
        )

    core_centroid = _centroid(core_atoms)
    reference_frame = _core_frame(
        core_atoms, reference_core_chain, core_anchor_residue, core_anchor_atom, core_orientation_atom, core_centroid
    )
    arm_atoms = [_to_coordinate_atom(atom) for atom in arm_records]
    arm_anchor = _find_coordinate_atom(arm_atoms, arm_anchor_chain, arm_anchor_residue, arm_anchor_atom)
    arm_orientation = _find_coordinate_atom(arm_atoms, arm_anchor_chain, arm_anchor_residue, arm_orientation_atom)
    arm_frame = _frame_from_anchor_and_direction(arm_anchor.coordinate, arm_orientation.coordinate - arm_anchor.coordinate)

    expanded: list[list[_CoordinateAtom]] = []
    for chain_id in core_chains:
        target_frame = _core_frame(
            core_atoms, chain_id, core_anchor_residue, core_anchor_atom, core_orientation_atom, core_centroid
        )
        rotation = target_frame @ arm_frame.T
        target_anchor = _find_atom(core_atoms, chain_id, core_anchor_residue, core_anchor_atom)
        transformed = [
            _CoordinateAtom(
                source_chain=atom.source_chain,
                residue_id=atom.residue_id,
                residue_name=atom.residue_name,
                atom_name=atom.atom_name,
                coordinate=rotation @ (atom.coordinate - arm_anchor.coordinate) + _xyz(target_anchor),
            )
            for atom in arm_atoms
        ]
        expanded.append(transformed)

    core_xyz = np.array([_xyz(atom) for atom in core_atoms])
    arm_xyz = [np.array([atom.coordinate for atom in arm]) for arm in expanded]
    from scipy.spatial import cKDTree
    core_tree = cKDTree(core_xyz)
    core_arm_pairs, min_core_arm = _core_arm_metrics(
        core_atoms, core_chains, arm_xyz, core_anchor_residue, core_anchor_atom, clash_cutoff_angstrom
    )
    arm_arm_pairs, min_arm_arm = _between_arm_metrics(arm_xyz, clash_cutoff_angstrom)

    probe_indices = _probe_indices(arm_atoms, probe_chain, probe_residue_ids)
    accessible_count, accessible_fraction = _probe_accessibility(
        expanded, probe_indices, core_tree, exposure_cutoff_angstrom
    )
    total_possible_pairs = max(1, len(core_atoms) * len(arm_atoms) * len(expanded))
    clash_fraction = min(1.0, (core_arm_pairs + arm_arm_pairs) / total_possible_pairs)
    crowding_score = round(min(1.0, 0.7 * (1.0 - accessible_fraction) + 0.3 * clash_fraction), 4)
    assessment = _assess(core_arm_pairs, arm_arm_pairs, accessible_fraction)

    assembled_path = None
    if output_pdb is not None:
        output_pdb.parent.mkdir(parents=True, exist_ok=True)
        _write_assembled_pdb(output_pdb, core_atoms, expanded)
        assembled_path = output_pdb

    return Fth1ExpansionResult(
        template_pdb=template_pdb,
        local_arm_pdb=local_arm_pdb,
        reference_core_chain=reference_core_chain,
        subunit_count=len(core_chains),
        arm_atoms_per_subunit=len(arm_atoms),
        total_expanded_arm_atoms=len(arm_atoms) * len(expanded),
        core_arm_clash_pairs=core_arm_pairs,
        arm_arm_clash_pairs=arm_arm_pairs,
        minimum_core_arm_distance_angstrom=round(min_core_arm, 3),
        minimum_arm_arm_distance_angstrom=None if min_arm_arm is None else round(min_arm_arm, 3),
        accessible_probe_atoms=accessible_count,
        accessible_probe_fraction=round(accessible_fraction, 4),
        crowding_score=crowding_score,
        assessment=assessment,
        assembled_pdb=assembled_path,
    )


def _core_frame(
    atoms: list[AtomRecord], chain: str, residue_id: int, anchor_name: str, orientation_name: str, centroid: np.ndarray
) -> np.ndarray:
    anchor = _find_atom(atoms, chain, residue_id, anchor_name)
    orientation = _find_atom(atoms, chain, residue_id, orientation_name)
    radial = _xyz(anchor) - centroid
    direction = _xyz(orientation) - _xyz(anchor)
    # Prefer an explicitly outward anchor orientation.  If it points inward,
    # flip it so every appendage maps to the cage exterior.
    if float(np.dot(direction, radial)) < 0:
        direction = -direction
    return _frame_from_anchor_and_direction(_xyz(anchor), direction)


def _frame_from_anchor_and_direction(anchor: np.ndarray, direction: np.ndarray) -> np.ndarray:
    z_axis = _normalise(direction)
    reference = np.array([1.0, 0.0, 0.0]) if abs(z_axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x_axis = _normalise(np.cross(reference, z_axis))
    y_axis = _normalise(np.cross(z_axis, x_axis))
    return np.column_stack((x_axis, y_axis, z_axis))


def _normalise(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        raise ValueError("Anchor and orientation atoms must have different coordinates")
    return vector / norm


def _centroid(atoms: list[AtomRecord]) -> np.ndarray:
    return np.mean(np.array([_xyz(atom) for atom in atoms]), axis=0)


def _xyz(atom: AtomRecord) -> np.ndarray:
    return np.array([atom.x, atom.y, atom.z], dtype=float)


def _to_coordinate_atom(atom: AtomRecord) -> _CoordinateAtom:
    return _CoordinateAtom(atom.chain_id, atom.residue_id, atom.residue_name, atom.atom_name, _xyz(atom))


def _find_atom(atoms: list[AtomRecord], chain: str, residue_id: int, atom_name: str) -> AtomRecord:
    for atom in atoms:
        if atom.chain_id == chain and atom.residue_id == residue_id and atom.atom_name == atom_name:
            return atom
    raise ValueError(f"Atom {chain}:{residue_id}:{atom_name} was not found")


def _find_coordinate_atom(atoms: list[_CoordinateAtom], chain: str, residue_id: int, atom_name: str) -> _CoordinateAtom:
    for atom in atoms:
        if atom.source_chain == chain and atom.residue_id == residue_id and atom.atom_name == atom_name:
            return atom
    raise ValueError(f"Local-arm atom {chain}:{residue_id}:{atom_name} was not found")


def _core_arm_metrics(
    core_atoms: list[AtomRecord],
    core_chains: list[str],
    arms: list[np.ndarray],
    anchor_residue: int,
    anchor_atom: str,
    cutoff: float,
) -> tuple[int, float]:
    """Score each arm against the cage, excluding its intended anchor atom.

    The atom at the covalent attachment point necessarily coincides in the
    mapped representation. Counting it as a steric clash would reject every
    valid fusion. All other template atoms, including other subunits' anchors,
    remain in the exclusion calculation.
    """
    pair_count = 0
    minimum: float | None = None
    for chain_id, arm_xyz in zip(core_chains, arms, strict=True):
        other_core = [
            atom
            for atom in core_atoms
            if not (atom.chain_id == chain_id and atom.residue_id == anchor_residue and atom.atom_name == anchor_atom)
        ]
        from scipy.spatial import cKDTree
        tree = cKDTree(np.array([_xyz(atom) for atom in other_core]))
        distances, _ = tree.query(arm_xyz, k=1)
        pair_count += sum(len(items) for items in tree.query_ball_point(arm_xyz, r=cutoff))
        arm_minimum = float(np.min(distances))
        minimum = arm_minimum if minimum is None else min(minimum, arm_minimum)
    return pair_count, minimum if minimum is not None else float("inf")


def _between_arm_metrics(arms: list[np.ndarray], cutoff: float) -> tuple[int, float | None]:
    pair_count = 0
    minimum: float | None = None
    for left_index, left in enumerate(arms):
        for right in arms[left_index + 1 :]:
            from scipy.spatial import cKDTree
            tree = cKDTree(right)
            distances, _ = tree.query(left, k=1)
            pair_count += sum(len(items) for items in tree.query_ball_point(left, r=cutoff))
            pair_minimum = float(np.min(distances))
            minimum = pair_minimum if minimum is None else min(minimum, pair_minimum)
    return pair_count, minimum


def _probe_indices(atoms: list[_CoordinateAtom], chain: str | None, residues: list[int] | None) -> list[int]:
    if chain is None and not residues:
        return list(range(len(atoms)))
    residue_set = set(residues or [])
    return [
        index
        for index, atom in enumerate(atoms)
        if (chain is None or atom.source_chain == chain) and (not residue_set or atom.residue_id in residue_set)
    ]


def _probe_accessibility(
    expanded: list[list[_CoordinateAtom]], probe_indices: list[int], core_tree: cKDTree, cutoff: float
) -> tuple[int, float]:
    if not probe_indices:
        raise ValueError("No probe atoms selected; check probe_chain and probe_residue_ids")
    total = len(probe_indices) * len(expanded)
    accessible = 0
    all_xyz = [np.array([atom.coordinate for atom in arm]) for arm in expanded]
    for arm_index, arm in enumerate(expanded):
        other_arms = np.vstack([xyz for index, xyz in enumerate(all_xyz) if index != arm_index])
        from scipy.spatial import cKDTree
        other_tree = cKDTree(other_arms)
        for probe_index in probe_indices:
            point = arm[probe_index].coordinate
            core_distance = float(core_tree.query(point, k=1)[0])
            arm_distance = float(other_tree.query(point, k=1)[0])
            if min(core_distance, arm_distance) >= cutoff:
                accessible += 1
    return accessible, accessible / total


def _assess(core_clashes: int, arm_clashes: int, accessible_fraction: float) -> str:
    if core_clashes or arm_clashes:
        return "reject_geometry"
    if accessible_fraction < 0.5:
        return "crowded_iterate"
    return "geometry_pass"


def _write_assembled_pdb(path: Path, core_atoms: list[AtomRecord], expanded: list[list[_CoordinateAtom]]) -> None:
    labels = ascii_letters + digits
    if len(expanded) > len(labels):
        raise ValueError("PDB output supports at most 62 expanded arm chain labels")
    lines: list[str] = []
    serial = 1
    for atom in core_atoms:
        lines.append(_pdb_line(serial, atom.atom_name, atom.residue_name, atom.chain_id, atom.residue_id, _xyz(atom)))
        serial += 1
    for arm_index, arm in enumerate(expanded):
        chain_id = labels[arm_index]
        for atom in arm:
            lines.append(_pdb_line(serial, atom.atom_name, atom.residue_name, chain_id, atom.residue_id, atom.coordinate))
            serial += 1
    lines.append("END")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pdb_line(serial: int, atom_name: str, residue_name: str, chain_id: str, residue_id: int, xyz: np.ndarray) -> str:
    return (
        f"ATOM  {serial:5d} {atom_name:>4s} {residue_name:>3s} {chain_id:1s}{residue_id:4d}    "
        f"{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}  1.00  0.00           C"
    )
