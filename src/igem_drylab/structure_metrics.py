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
    reference = read_pdb_atoms(reference_pdb)
    model = read_pdb_atoms(model_pdb)
    alignment_set = set(alignment_residues)
    pocket_set = set(pocket_residues)

    ref_align = _atom_map(reference, chain, alignment_set, {"N", "CA", "C"})
    mob_align = _atom_map(model, chain, alignment_set, {"N", "CA", "C"})
    align_keys = sorted(set(ref_align) & set(mob_align))
    if len(align_keys) < 3:
        raise ValueError("fewer than three matching backbone atoms for alignment")
    rotation, translation = kabsch_transform(
        np.vstack([ref_align[key] for key in align_keys]),
        np.vstack([mob_align[key] for key in align_keys]),
    )

    ref_pocket = _atom_map(reference, chain, pocket_set)
    mob_pocket = _atom_map(model, chain, pocket_set)
    pocket_keys = sorted(set(ref_pocket) & set(mob_pocket))
    if not pocket_keys:
        raise ValueError("no matching pocket atoms")
    ref_xyz = np.vstack([ref_pocket[key] for key in pocket_keys])
    mob_xyz = np.vstack([mob_pocket[key] for key in pocket_keys]) @ rotation + translation
    return float(np.sqrt(np.mean(np.sum((ref_xyz - mob_xyz) ** 2, axis=1))))


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
