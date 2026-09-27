"""Quantitative metrics for fusion-protein screening.

Residue numbering must be consistent between reference and model. For AF3 models,
verify chain IDs and residue indices before interpreting any value.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class Atom:
    chain: str
    residue: int
    insertion: str
    name: str
    element: str
    coordinate: np.ndarray


def read_pdb_atoms(path: str | Path) -> list[Atom]:
    atoms: list[Atom] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        altloc = line[16:17]
        if altloc not in (" ", "A"):
            continue
        try:
            atoms.append(
                Atom(
                    chain=line[21:22].strip() or "_",
                    residue=int(line[22:26]),
                    insertion=line[26:27].strip(),
                    name=line[12:16].strip(),
                    element=(line[76:78].strip() or line[12:14].strip()).upper(),
                    coordinate=np.array(
                        [float(line[30:38]), float(line[38:46]), float(line[46:54])]
                    ),
                )
            )
        except ValueError:
            continue
    if not atoms:
        raise ValueError(f"no atoms parsed from {path}")
    return atoms


def _atom_map(
    atoms: Iterable[Atom], chain: str, residues: set[int], names: set[str] | None = None
) -> dict[tuple[int, str, str], np.ndarray]:
    return {
        (atom.residue, atom.insertion, atom.name): atom.coordinate
        for atom in atoms
        if atom.chain == chain
        and atom.residue in residues
        and (names is None or atom.name in names)
        and atom.element != "H"
    }


def kabsch_transform(reference: np.ndarray, mobile: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if reference.shape != mobile.shape or reference.ndim != 2 or reference.shape[1] != 3:
        raise ValueError("reference and mobile coordinates must have shape (N, 3)")
    if len(reference) < 3:
        raise ValueError("at least three matched atoms are required")
    ref_center = reference.mean(axis=0)
    mob_center = mobile.mean(axis=0)
    covariance = (mobile - mob_center).T @ (reference - ref_center)
    u, _singular_values, vt = np.linalg.svd(covariance)
    correction = np.eye(3)
    correction[-1, -1] = np.sign(np.linalg.det(u @ vt))
    rotation = u @ correction @ vt
    translation = ref_center - mob_center @ rotation
    return rotation, translation


def aligned_pocket_rmsd(
    reference_pdb: str | Path,
    model_pdb: str | Path,
    chain: str,
    alignment_residues: Iterable[int],
    pocket_residues: Iterable[int],
) -> float:
    """Return pocket C-alpha RMSD after C-alpha core alignment.

    This legacy function now follows the M2 V2 formula; it no longer mixes all
    pocket heavy atoms into a quantity labelled as pocket C-alpha RMSD.
    """

    return aligned_ca_rmsds(
        reference_pdb=reference_pdb,
        model_pdb=model_pdb,
        reference_chain=chain,
        model_chain=chain,
        core_residues=alignment_residues,
        pocket_residues=pocket_residues,
    )["pocket_ca_rmsd_angstrom"]


def aligned_ca_rmsds(
    reference_pdb: str | Path,
    model_pdb: str | Path,
    *,
    reference_chain: str,
    model_chain: str,
    core_residues: Iterable[int],
    pocket_residues: Iterable[int],
    core_residue_mapping: Iterable[tuple[int, int]] | None = None,
    pocket_residue_mapping: Iterable[tuple[int, int]] | None = None,
) -> dict[str, float | int]:
    """Calculate the contract's core and pocket C-alpha RMSD equations.

    Mapping pairs are ``(reference_residue, model_residue)``. When omitted,
    the declared residue numbers are treated as identity mappings. Every
    declared pair must be present; missing coordinates are never silently
    removed from the formula.
    """

    reference = read_pdb_atoms(reference_pdb)
    model = read_pdb_atoms(model_pdb)
    core_pairs = _normalise_residue_mapping(core_residues, core_residue_mapping, "core")
    pocket_pairs = _normalise_residue_mapping(pocket_residues, pocket_residue_mapping, "pocket")
    if len(core_pairs) < 3:
        raise ValueError("at least three mapped core C-alpha atoms are required for alignment")
    ref_align, mob_align = _mapped_ca_coordinates(
        reference,
        model,
        reference_chain=reference_chain,
        model_chain=model_chain,
        mapping=core_pairs,
        label="core",
    )
    rotation, translation = kabsch_transform(
        ref_align,
        mob_align,
    )
    ref_core_xyz = ref_align
    mob_core_xyz = mob_align @ rotation + translation
    core_rmsd = float(np.sqrt(np.mean(np.sum((ref_core_xyz - mob_core_xyz) ** 2, axis=1))))

    ref_xyz, mob_xyz_unaligned = _mapped_ca_coordinates(
        reference,
        model,
        reference_chain=reference_chain,
        model_chain=model_chain,
        mapping=pocket_pairs,
        label="pocket",
    )
    mob_xyz = mob_xyz_unaligned @ rotation + translation
    pocket_rmsd = float(np.sqrt(np.mean(np.sum((ref_xyz - mob_xyz) ** 2, axis=1))))
    return {
        "core_ca_rmsd_angstrom": core_rmsd,
        "pocket_ca_rmsd_angstrom": pocket_rmsd,
        "matched_core_ca_count": len(core_pairs),
        "matched_pocket_ca_count": len(pocket_pairs),
    }


def tail_pocket_min_distance(
    model_pdb: str | Path,
    *,
    chain: str,
    tail_residues: Iterable[int],
    pocket_residues: Iterable[int],
) -> float:
    """Minimum heavy-atom distance between an introduced tail and pocket."""

    atoms = read_pdb_atoms(model_pdb)
    tail = _selected_heavy_coordinates(atoms, chain=chain, residues=set(tail_residues))
    pocket = _selected_heavy_coordinates(atoms, chain=chain, residues=set(pocket_residues))
    if not len(tail) or not len(pocket):
        raise ValueError("tail and pocket selections must each contain at least one heavy atom")
    return float(np.min(np.linalg.norm(tail[:, None, :] - pocket[None, :, :], axis=2)))


def count_inter_module_clashes(
    pdb_path: str | Path,
    *,
    first_chain: str,
    first_residues: Iterable[int],
    second_chain: str,
    second_residues: Iterable[int],
    cutoff_angstrom: float,
) -> dict[str, float | int]:
    """Count explicit inter-module heavy-atom pairs below ``cutoff_angstrom``."""

    if cutoff_angstrom <= 0:
        raise ValueError("cutoff_angstrom must be positive")
    first_residue_set = set(first_residues)
    second_residue_set = set(second_residues)
    if first_chain == second_chain and first_residue_set & second_residue_set:
        raise ValueError("inter-module clash selections must not overlap")
    atoms = read_pdb_atoms(pdb_path)
    first = _selected_heavy_coordinates(atoms, chain=first_chain, residues=first_residue_set)
    second = _selected_heavy_coordinates(atoms, chain=second_chain, residues=second_residue_set)
    if not len(first) or not len(second):
        raise ValueError("both module selections must contain at least one heavy atom")
    distances = np.linalg.norm(first[:, None, :] - second[None, :, :], axis=2)
    return {
        "clash_count": int(np.sum(distances < cutoff_angstrom)),
        "minimum_distance_angstrom": float(np.min(distances)),
        "clash_cutoff_angstrom": float(cutoff_angstrom),
        "first_heavy_atom_count": len(first),
        "second_heavy_atom_count": len(second),
    }


def _ca_map(atoms: Iterable[Atom], chain: str, residues: set[int]) -> dict[tuple[int, str], np.ndarray]:
    return {
        (atom.residue, atom.insertion): atom.coordinate
        for atom in atoms
        if atom.chain == chain and atom.residue in residues and atom.name == "CA"
    }


def _normalise_residue_mapping(
    identity_residues: Iterable[int],
    mapping: Iterable[tuple[int, int]] | None,
    label: str,
) -> list[tuple[int, int]]:
    pairs = list(mapping) if mapping is not None else [(value, value) for value in identity_residues]
    if not pairs:
        raise ValueError(f"{label} residue mapping must not be empty")
    if len(set(pairs)) != len(pairs):
        raise ValueError(f"{label} residue mapping contains duplicate pairs")
    if len({pair[0] for pair in pairs}) != len(pairs) or len({pair[1] for pair in pairs}) != len(pairs):
        raise ValueError(f"{label} residue mapping must be one-to-one")
    return pairs


def _mapped_ca_coordinates(
    reference_atoms: Iterable[Atom],
    model_atoms: Iterable[Atom],
    *,
    reference_chain: str,
    model_chain: str,
    mapping: list[tuple[int, int]],
    label: str,
) -> tuple[np.ndarray, np.ndarray]:
    reference_map = _ca_map(reference_atoms, reference_chain, {pair[0] for pair in mapping})
    model_map = _ca_map(model_atoms, model_chain, {pair[1] for pair in mapping})
    reference_by_number = {residue: xyz for (residue, _insertion), xyz in reference_map.items()}
    model_by_number = {residue: xyz for (residue, _insertion), xyz in model_map.items()}
    missing = [pair for pair in mapping if pair[0] not in reference_by_number or pair[1] not in model_by_number]
    if missing:
        raise ValueError(f"missing {label} C-alpha coordinates for mapped residue pairs: {missing}")
    return (
        np.vstack([reference_by_number[reference_residue] for reference_residue, _ in mapping]),
        np.vstack([model_by_number[model_residue] for _, model_residue in mapping]),
    )


def _selected_heavy_coordinates(atoms: Iterable[Atom], *, chain: str, residues: set[int]) -> np.ndarray:
    selected = [
        atom.coordinate
        for atom in atoms
        if atom.chain == chain and atom.residue in residues and atom.element != "H"
    ]
    return np.vstack(selected) if selected else np.empty((0, 3), dtype=float)


def load_pae(path: str | Path) -> np.ndarray:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        if not payload:
            raise ValueError("empty JSON list")
        payload = payload[0]
    for key in ("pae", "predicted_aligned_error"):
        if key in payload:
            matrix = np.asarray(payload[key], dtype=float)
            break
    else:
        raise KeyError("PAE matrix not found; expected 'pae' or 'predicted_aligned_error'")
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("PAE must be a square matrix")
    return matrix


def interdomain_pae(
    pae: np.ndarray, first_indices: Iterable[int], second_indices: Iterable[int]
) -> dict[str, float]:
    first = np.asarray(list(first_indices), dtype=int)
    second = np.asarray(list(second_indices), dtype=int)
    if first.size == 0 or second.size == 0:
        raise ValueError("both domains need at least one zero-based residue index")
    values = np.concatenate((pae[np.ix_(first, second)].ravel(), pae[np.ix_(second, first)].ravel()))
    return {
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "p90": float(np.quantile(values, 0.90)),
        "pairs": float(values.size),
    }


def cage_clearance(
    pocket_coordinates: np.ndarray,
    cage_coordinates: np.ndarray,
    cage_center: np.ndarray | None = None,
) -> dict[str, float]:
    """Approximate pocket-to-cage clearance in angstrom.

    The radial surface uses the 95th percentile cage radius and is only meaningful
    for a complete, approximately spherical FTH1 assembly. The minimum atom distance
    is also returned and should be preferred for steric screening.
    """
    pocket = np.asarray(pocket_coordinates, dtype=float)
    cage = np.asarray(cage_coordinates, dtype=float)
    center = cage.mean(axis=0) if cage_center is None else np.asarray(cage_center, dtype=float)
    pocket_center = pocket.mean(axis=0)
    cage_radius = float(np.quantile(np.linalg.norm(cage - center, axis=1), 0.95))
    radial_clearance = float(np.linalg.norm(pocket_center - center) - cage_radius)
    minimum_atom_distance = float(
        np.min(np.linalg.norm(pocket[:, None, :] - cage[None, :, :], axis=2))
    )
    return {
        "radial_clearance_angstrom": radial_clearance,
        "minimum_atom_distance_angstrom": minimum_atom_distance,
        "cage_radius_angstrom": cage_radius,
    }


def residue_sasa(pdb_path: str | Path, chain: str, residues: Iterable[int]) -> float:
    try:
        import freesasa
    except ImportError as exc:
        raise RuntimeError("install the optional 'sasa' dependencies to calculate SASA") from exc
    structure = freesasa.Structure(str(pdb_path))
    result = freesasa.calc(structure)
    residue_set = set(residues)
    total = 0.0
    for chain_id, chain_areas in result.residueAreas().items():
        if chain_id != chain:
            continue
        for residue_number, area in chain_areas.items():
            try:
                number = int("".join(character for character in residue_number if character.isdigit()))
            except ValueError:
                continue
            if number in residue_set:
                total += float(area.total)
    return total
