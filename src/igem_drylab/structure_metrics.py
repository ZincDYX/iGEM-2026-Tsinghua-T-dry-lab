"""Quantitative metrics for fusion-protein screening.

Residue numbering must be consistent between reference and model. For AF3 models,
verify chain IDs and residue indices before interpreting any value.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
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
    model_id: int = 1
    altloc: str = ""
    label_chain: str | None = None
    label_residue: int | None = None
    pdb_line: str | None = None


def _read_atom_records(path: str | Path) -> list[Atom]:
    if Path(path).suffix.lower() in {".cif", ".mmcif"}:
        return _read_cif_atoms(path)
    atoms: list[Atom] = []
    model_id = 1
    explicit_models = False
    inside_model = False
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("MODEL "):
            if inside_model:
                raise ValueError("nested PDB MODEL records")
            explicit_models = True
            inside_model = True
            model_id = int(line[10:14])
            continue
        if line.startswith("ENDMDL"):
            if not inside_model:
                raise ValueError("PDB ENDMDL without MODEL")
            inside_model = False
            continue
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        if explicit_models and not inside_model:
            raise ValueError("PDB atom outside MODEL/ENDMDL scope")
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
                    model_id=model_id,
                    altloc=line[16:17].strip(),
                    pdb_line=line,
                )
            )
        except ValueError as exc:
            raise ValueError(f"invalid atom record in model {model_id}: {line[:30]}") from exc
    if not atoms:
        raise ValueError(f"no atoms parsed from {path}")
    return atoms


def _read_cif_atoms(path: str | Path) -> list[Atom]:
    from Bio.PDB.MMCIF2Dict import MMCIF2Dict

    data = MMCIF2Dict(str(path))
    count = len(data.get("_atom_site.id", []))
    def value(column: str, index: int, default: str = "") -> str:
        values = data.get(f"_atom_site.{column}")
        text = values[index] if values is not None else default
        return "" if text in {".", "?"} else text
    atoms = []
    for index in range(count):
        label_residue = value("label_seq_id", index)
        atoms.append(Atom(
            chain=value("auth_asym_id", index) or value("label_asym_id", index),
            residue=int(value("auth_seq_id", index) or label_residue),
            insertion=value("pdbx_PDB_ins_code", index),
            name=value("auth_atom_id", index) or value("label_atom_id", index),
            element=value("type_symbol", index).upper(),
            coordinate=np.array([float(value(f"Cartn_{axis}", index)) for axis in "xyz"]),
            model_id=int(value("pdbx_PDB_model_num", index, "1")),
            altloc=value("label_alt_id", index),
            label_chain=value("label_asym_id", index),
            label_residue=int(label_residue) if label_residue else None,
        ))
    if not atoms:
        raise ValueError(f"no atoms parsed from {path}")
    return atoms


def read_pdb_atoms(path: str | Path, *, model_id: int | None = None,
                   altloc: str | None = None) -> list[Atom]:
    """Read one declared model in author numbering, preserving label identity.

    A multi-model or alternate-location structure requires an explicit choice.
    Blank altloc atoms are shared by the selected conformer, never summed with
    competing alternate atoms. PDB has no label numbering: those fields stay null.
    """
    atoms = _read_atom_records(path)
    models = sorted({atom.model_id for atom in atoms})
    if model_id is None:
        if len(models) != 1:
            raise ValueError(f"multiple structure models {models}; select model_id explicitly")
        model_id = models[0]
    selected = [atom for atom in atoms if atom.model_id == model_id]
    if not selected:
        raise ValueError(f"model_id {model_id} not present; available models: {models}")
    alternatives = sorted({atom.altloc for atom in selected if atom.altloc})
    if alternatives and altloc is None:
        raise ValueError(f"alternate locations {alternatives}; select altloc explicitly")
    if altloc is not None and len(altloc) != 1:
        raise ValueError("altloc must be a single conformer identifier")
    if alternatives and altloc not in alternatives:
        raise ValueError(f"altloc {altloc} not present; available conformers: {alternatives}")
    selected = [atom for atom in selected if not atom.altloc or atom.altloc == altloc]
    identities = [(atom.chain, atom.residue, atom.insertion, atom.name) for atom in selected]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate atom identities in selected model/conformer")
    if any(not np.all(np.isfinite(atom.coordinate)) for atom in selected):
        raise ValueError("non-finite atom coordinates")
    return selected


def residue_key(value: int | str) -> tuple[int, str]:
    """Author residue number plus insertion code; never strip an insertion code."""
    match = re.fullmatch(r"(-?\d+)([A-Za-z]?)", str(value))
    if match is None:
        raise ValueError(f"invalid author residue identifier: {value}")
    return int(match[1]), match[2]


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
    core_residues: Iterable[int | str],
    pocket_residues: Iterable[int | str],
    core_residue_mapping: Iterable[tuple[int | str, int | str]] | None = None,
    pocket_residue_mapping: Iterable[tuple[int | str, int | str]] | None = None,
    reference_model_id: int | None = None,
    model_id: int | None = None,
    reference_altloc: str | None = None,
    model_altloc: str | None = None,
) -> dict[str, float | int]:
    """Calculate the contract's core and pocket C-alpha RMSD equations.

    Mapping pairs are ``(reference_residue, model_residue)``. When omitted,
    the declared residue numbers are treated as identity mappings. Every
    declared pair must be present; missing coordinates are never silently
    removed from the formula.
    """

    reference = read_pdb_atoms(reference_pdb, model_id=reference_model_id, altloc=reference_altloc)
    model = read_pdb_atoms(model_pdb, model_id=model_id, altloc=model_altloc)
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
        "reference_model_id": reference[0].model_id,
        "model_id": model[0].model_id,
    }


def tail_pocket_min_distance(
    model_pdb: str | Path,
    *,
    chain: str,
    tail_residues: Iterable[int | str],
    pocket_residues: Iterable[int | str],
    model_id: int | None = None,
    altloc: str | None = None,
) -> float:
    """Minimum heavy-atom distance between an introduced tail and pocket."""

    atoms = read_pdb_atoms(model_pdb, model_id=model_id, altloc=altloc)
    tail = _selected_heavy_coordinates(atoms, chain=chain, residues=set(tail_residues))
    pocket = _selected_heavy_coordinates(atoms, chain=chain, residues=set(pocket_residues))
    if not len(tail) or not len(pocket):
        raise ValueError("tail and pocket selections must each contain at least one heavy atom")
    return _pair_distances(tail, pocket)[1]


def count_inter_module_clashes(
    pdb_path: str | Path,
    *,
    first_chain: str,
    first_residues: Iterable[int | str],
    second_chain: str,
    second_residues: Iterable[int | str],
    cutoff_angstrom: float,
    model_id: int | None = None,
    altloc: str | None = None,
) -> dict[str, float | int]:
    """Count explicit inter-module heavy-atom pairs below ``cutoff_angstrom``."""

    if not np.isfinite(cutoff_angstrom) or cutoff_angstrom <= 0:
        raise ValueError("cutoff_angstrom must be positive")
    first_residue_set = {residue_key(value) for value in first_residues}
    second_residue_set = {residue_key(value) for value in second_residues}
    if first_chain == second_chain and first_residue_set & second_residue_set:
        raise ValueError("inter-module clash selections must not overlap")
    atoms = read_pdb_atoms(pdb_path, model_id=model_id, altloc=altloc)
    first = _selected_heavy_coordinates(atoms, chain=first_chain, residues=first_residue_set)
    second = _selected_heavy_coordinates(atoms, chain=second_chain, residues=second_residue_set)
    if not len(first) or not len(second):
        raise ValueError("both module selections must contain at least one heavy atom")
    clash_count, minimum_distance = _pair_distances(first, second, cutoff_angstrom)
    return {
        "clash_count": clash_count,
        "minimum_distance_angstrom": minimum_distance,
        "clash_cutoff_angstrom": float(cutoff_angstrom),
        "first_heavy_atom_count": len(first),
        "second_heavy_atom_count": len(second),
    }


def _ca_map(atoms: Iterable[Atom], chain: str, residues: set[tuple[int, str]]) -> dict[tuple[int, str], np.ndarray]:
    return {
        (atom.residue, atom.insertion): atom.coordinate
        for atom in atoms
        if atom.chain == chain and (atom.residue, atom.insertion) in residues and atom.name == "CA"
    }


def _normalise_residue_mapping(
    identity_residues: Iterable[int | str],
    mapping: Iterable[tuple[int | str, int | str]] | None,
    label: str,
) -> list[tuple[tuple[int, str], tuple[int, str]]]:
    declared = [residue_key(value) for value in identity_residues]
    pairs = [(residue_key(first), residue_key(second)) for first, second in mapping] if mapping is not None else [(value, value) for value in declared]
    if not pairs:
        raise ValueError(f"{label} residue mapping must not be empty")
    if len(set(pairs)) != len(pairs):
        raise ValueError(f"{label} residue mapping contains duplicate pairs")
    if len({pair[0] for pair in pairs}) != len(pairs) or len({pair[1] for pair in pairs}) != len(pairs):
        raise ValueError(f"{label} residue mapping must be one-to-one")
    if declared and (len(set(declared)) != len(declared) or set(declared) != {pair[0] for pair in pairs}):
        raise ValueError(f"{label} mapping must cover every declared reference residue exactly once")
    return pairs


def _mapped_ca_coordinates(
    reference_atoms: Iterable[Atom],
    model_atoms: Iterable[Atom],
    *,
    reference_chain: str,
    model_chain: str,
    mapping: list[tuple[tuple[int, str], tuple[int, str]]],
    label: str,
) -> tuple[np.ndarray, np.ndarray]:
    reference_map = _ca_map(reference_atoms, reference_chain, {pair[0] for pair in mapping})
    model_map = _ca_map(model_atoms, model_chain, {pair[1] for pair in mapping})
    missing = [pair for pair in mapping if pair[0] not in reference_map or pair[1] not in model_map]
    if missing:
        raise ValueError(f"missing {label} C-alpha coordinates for mapped residue pairs: {missing}")
    return (
        np.vstack([reference_map[reference_residue] for reference_residue, _ in mapping]),
        np.vstack([model_map[model_residue] for _, model_residue in mapping]),
    )


def _selected_heavy_coordinates(atoms: Iterable[Atom], *, chain: str, residues: set) -> np.ndarray:
    keys = {value if isinstance(value, tuple) else residue_key(value) for value in residues}
    selected = [
        atom.coordinate
        for atom in atoms
        if atom.chain == chain and (atom.residue, atom.insertion) in keys and atom.element not in {"H", "D"}
    ]
    present = {(atom.residue, atom.insertion) for atom in atoms if atom.chain == chain and atom.element not in {"H", "D"}}
    if keys - present:
        raise ValueError(f"missing declared heavy-atom residues in chain {chain}: {sorted(keys - present)}")
    return np.vstack(selected) if selected else np.empty((0, 3), dtype=float)


def _pair_distances(first: np.ndarray, second: np.ndarray, cutoff: float | None = None) -> tuple[int, float]:
    """Exact original Euclidean distances, with bounded temporary matrices."""
    count, minimum = 0, float("inf")
    for start in range(0, len(first), 256):
        for other in range(0, len(second), 1024):
            distances = np.linalg.norm(first[start:start + 256, None, :] - second[None, other:other + 1024, :], axis=2)
            minimum = min(minimum, float(np.min(distances)))
            if cutoff is not None:
                count += int(np.sum(distances < cutoff))
    return count, minimum


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
    minimum_atom_distance = _pair_distances(pocket, cage)[1]
    return {
        "radial_clearance_angstrom": radial_clearance,
        "minimum_atom_distance_angstrom": minimum_atom_distance,
        "cage_radius_angstrom": cage_radius,
    }


def calculate_sasa_structure(pdb_path: str | Path, *, model_id: int | None = None,
                             altloc: str | None = None, parameters=None):
    try:
        import freesasa
    except ImportError as exc:
        raise RuntimeError("install the optional 'sasa' dependencies to calculate SASA") from exc
    atoms = read_pdb_atoms(pdb_path, model_id=model_id, altloc=altloc)
    if any(atom.pdb_line is None for atom in atoms):
        raise ValueError("FreeSASA PDB route requires PDB input; mmCIF identity must be mapped before conversion")
    # Keep library PDB/classifier semantics, but supply only the chosen model
    # and conformer. FreeSASA's implicit first-model choice is never used.
    with TemporaryDirectory(prefix="fusionlab-sasa-") as temporary:
        selected_path = Path(temporary) / "selected.pdb"
        selected_path.write_text("\n".join(atom.pdb_line[:16] + " " + atom.pdb_line[17:] for atom in atoms) + "\n", encoding="utf-8")
        structure = freesasa.Structure(str(selected_path))
        result = freesasa.calc(structure, parameters or freesasa.Parameters())
    return atoms[0].model_id, result


def residue_sasa_areas(pdb_path: str | Path, *, model_id: int | None = None,
                      altloc: str | None = None, parameters=None) -> tuple[int, dict[tuple[str, int, str], float]]:
    selected_model, result = calculate_sasa_structure(pdb_path, model_id=model_id, altloc=altloc, parameters=parameters)
    areas = {}
    for chain_id, chain_areas in result.residueAreas().items():
        for residue_number, area in chain_areas.items():
            number, insertion = residue_key(str(residue_number).strip())
            areas[(chain_id.strip() or "_", number, insertion)] = float(area.total)
    return selected_model, areas


def residue_sasa(pdb_path: str | Path, chain: str, residues: Iterable[int | str],
                 *, model_id: int | None = None, altloc: str | None = None) -> float:
    _, areas = residue_sasa_areas(pdb_path, model_id=model_id, altloc=altloc)
    keys = [(chain, *residue_key(value)) for value in residues]
    missing = [key for key in keys if key not in areas]
    if not keys or len(set(keys)) != len(keys) or missing:
        raise ValueError(f"SASA selection must be complete and unique; missing residues: {missing}")
    return float(sum(areas[key] for key in keys))
