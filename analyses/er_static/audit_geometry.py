"""Audit the ten actual ER-scaffold 24-mers before membrane insertion.

This script does not turn a rigid AlphaFold/template assembly into an observed
membrane conformation.  It measures whether the saved coordinates can share a
single planar membrane and whether the declared flexible N-terminal segment has
enough contour length to connect a tangent membrane to every structured body.
"""

from __future__ import annotations

from hashlib import sha256
import json
import os
import math
from pathlib import Path
import sys

import numpy as np


BASE = Path(os.environ.get('GALATEA_ER_ROOT','er-study')).resolve()
SOURCE = Path(__file__).resolve().parents[2] / 'src'
sys.path.insert(0, str(SOURCE))

from igem_drylab.structure_metrics import read_pdb_atoms  # noqa: E402


OUT = BASE / "r55-er-anchor-full-assembly-audit"
ASSEMBLIES = BASE / "r43-actual-scaffold-assemblies-v2"
GEOMETRY = BASE / "r47-actual-full-assembly-geometry-v3"

SPECS = {
    "WP07": {
        "wetlab_id": "Q10_P02",
        "length": 888,
        "tm_start": 22,
        "tm_end": 38,
        "topology": "outside:1-21;TMhelix:22-38;inside:39-888",
        "first_structured_residue": 319,
    },
    "WP08": {
        "wetlab_id": "Q13_P02",
        "length": 868,
        "tm_start": 22,
        "tm_end": 35,
        "topology": "outside:1-21;TMhelix:22-35;inside:36-868",
        "first_structured_residue": 299,
    },
}


def fibonacci_normals(count: int = 4096) -> np.ndarray:
    i = np.arange(count, dtype=float)
    phi = (1 + 5**0.5) / 2
    z = 1 - 2 * (i + 0.5) / count
    r = np.sqrt(np.maximum(0.0, 1 - z * z))
    theta = 2 * np.pi * i / phi
    return np.column_stack((r * np.cos(theta), r * np.sin(theta), z))


def pca_axis(xyz: np.ndarray) -> np.ndarray:
    centered = xyz - xyz.mean(axis=0)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    return vh[0] / np.linalg.norm(vh[0])


def load_existing_clashes() -> dict[tuple[str, str], dict]:
    progress = json.loads((GEOMETRY / "progress-private.json").read_text())
    return {(row["protein_id"], row["model_sha256"]): row for row in progress["models"]}


def direct_planar_fit(tm_xyz: list[np.ndarray], normals: np.ndarray, thickness: float) -> dict:
    """Find whether every saved TM segment can span one common planar slab."""
    best = None
    half = thickness / 2
    for normal in normals:
        intervals = []
        spans = []
        for xyz in tm_xyz:
            projected = xyz @ normal
            lo, hi = float(projected.min()), float(projected.max())
            spans.append(hi - lo)
            intervals.append((lo + half, hi - half))
        lower = max(row[0] for row in intervals)
        upper = min(row[1] for row in intervals)
        gap = lower - upper
        score = max(0.0, gap) + sum(max(0.0, thickness - span) for span in spans)
        if best is None or score < best[0]:
            center = (lower + upper) / 2
            best = (score, normal.copy(), center, spans, gap)
    assert best is not None
    score, normal, center, spans, gap = best
    return {
        "thickness_angstrom": thickness,
        "common_plane_exists_for_saved_coordinates": bool(gap <= 0 and min(spans) >= thickness),
        "best_normal": normal.tolist(),
        "best_plane_origin_projection_angstrom": float(center),
        "common_interval_gap_angstrom": float(max(0.0, gap)),
        "tm_projected_span_range_angstrom": [float(min(spans)), float(max(spans))],
        "optimization_score_angstrom": float(score),
    }


def flexible_tether_fit(atoms, chains: list[str], spec: dict, normals: np.ndarray, half_thickness: float = 15.0) -> dict:
    """Find a tangent plane with all structured atoms on the cytosolic side."""
    structured = np.array([
        atom.coordinate
        for atom in atoms
        if atom.element not in {"H", "D"} and atom.residue >= spec["first_structured_residue"]
    ])
    ca = {
        (atom.chain, atom.residue): atom.coordinate
        for atom in atoms
        if atom.name == "CA" and atom.insertion == ""
    }
    tether_residues = spec["first_structured_residue"] - spec["tm_end"] - 1
    contour = tether_residues * 3.8
    best = None
    for normal in normals:
        projection = structured @ normal
        # Put the cytosolic membrane surface 2 A below the nearest structured atom.
        surface = float(projection.min() - 2.0)
        distances = [float(ca[(chain, spec["first_structured_residue"])] @ normal - surface) for chain in chains]
        ratio = max(distances) / contour
        if best is None or ratio < best[0]:
            best = (ratio, normal.copy(), surface, distances)
    assert best is not None
    ratio, normal, surface, distances = best
    centers = []
    for chain in chains:
        point = ca[(chain, spec["first_structured_residue"])]
        centers.append(point - (point @ normal - surface) * normal)
    lateral = []
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            lateral.append(float(np.linalg.norm(centers[i] - centers[j])))
    return {
        "best_tangent_normal": normal.tolist(),
        "cytosolic_surface_projection_angstrom": float(surface),
        "membrane_center_projection_angstrom": float(surface - half_thickness),
        "flexible_segment_residue_count": tether_residues,
        "maximum_contour_length_angstrom": float(contour),
        "required_normal_distance_range_angstrom": [float(min(distances)), float(max(distances))],
        "maximum_required_to_contour_ratio": float(ratio),
        "all_tethers_within_maximum_contour_bound": bool(ratio <= 1.0),
        "projected_attachment_separation_range_angstrom": [float(min(lateral)), float(max(lateral))],
        "interpretation": "necessary reachability bound only; no 24-chain linker conformations were generated",
    }


def audit_one(folder: Path, clashes: dict, normals: np.ndarray) -> dict | None:
    request_path = folder / "accessibility-request-private.json"
    if not request_path.exists():
        return None
    request = json.loads(request_path.read_text())
    protein_id = request["candidate_id"]
    if protein_id not in SPECS:
        return None
    spec = SPECS[protein_id]
    structure = Path(request["assembly_file"])
    digest = sha256(Path(request["actual_fusion"]["path"]).read_bytes()).hexdigest()
    atoms = read_pdb_atoms(structure)
    chains = sorted({atom.chain for atom in atoms if not atom.is_hetero})
    if len(chains) != 24:
        raise ValueError(f"{folder.name}: expected 24 chains, got {len(chains)}")
    ca = {(atom.chain, atom.residue): atom.coordinate for atom in atoms if atom.name == "CA" and atom.insertion == ""}
    tm_xyz = [np.array([ca[(chain, residue)] for residue in range(spec["tm_start"], spec["tm_end"] + 1)]) for chain in chains]
    axes = [pca_axis(xyz) for xyz in tm_xyz]
    axis_angles = []
    plane_fit = direct_planar_fit(tm_xyz, normals, 30.0)
    normal = np.array(plane_fit["best_normal"])
    for axis in axes:
        axis_angles.append(math.degrees(math.acos(np.clip(abs(float(axis @ normal)), 0.0, 1.0))))
    prior = clashes[(protein_id, digest)]
    return {
        "protein_id": protein_id,
        "wetlab_id": spec["wetlab_id"],
        "model_sha256": digest,
        "assembly_file": str(structure),
        "assembly_file_sha256": sha256(structure.read_bytes()).hexdigest(),
        "subunits": 24,
        "sequence_length": spec["length"],
        "topology_prediction": spec["topology"],
        "topology_scope": "DeepTMHMM prediction; inside is interpreted as cytosolic for computational placement, not experimental proof",
        "direct_saved_coordinate_planar_fit": {
            **plane_fit,
            "tm_axis_deviation_from_best_normal_degrees": {
                "min": float(min(axis_angles)),
                "median": float(np.median(axis_angles)),
                "max": float(max(axis_angles)),
            },
        },
        "flexible_tether_reachability": flexible_tether_fit(atoms, chains, spec, normals),
        "existing_rigid_copy_clashes": {
            "all_heavy_atom_pairs_below_2_5A": prior["heavy_atom_clashes_strictly_below_2_5A"],
            "mapped_FTH_core_pairs_below_2_5A": prior["mapped_core_heavy_clashes"],
            "outside_mapped_core_pairs_below_2_5A": prior["clashes_involving_atoms_outside_mapped_reference_core"],
        },
        "ready_for_direct_membrane_MD": False,
        "reason": "saved rigid-copy assembly contains severe non-core clashes and has no generated 24-chain membrane-compatible tether ensemble",
    }


def main() -> None:
    OUT.mkdir(exist_ok=False)
    normals = fibonacci_normals()
    clashes = load_existing_clashes()
    records = []
    for folder in sorted(path for path in ASSEMBLIES.iterdir() if path.is_dir()):
        record = audit_one(folder, clashes, normals)
        if record is not None:
            records.append(record)
    if len(records) != 10:
        raise ValueError(f"expected ten ER assembly models, got {len(records)}")
    by_construct = {}
    for protein_id in SPECS:
        rows = [row for row in records if row["protein_id"] == protein_id]
        by_construct[protein_id] = {
            "models": len(rows),
            "saved_coordinate_common_plane_models": sum(
                row["direct_saved_coordinate_planar_fit"]["common_plane_exists_for_saved_coordinates"] for row in rows
            ),
            "maximum_contour_bound_models": sum(
                row["flexible_tether_reachability"]["all_tethers_within_maximum_contour_bound"] for row in rows
            ),
            "minimum_noncore_clash_count": min(
                row["existing_rigid_copy_clashes"]["outside_mapped_core_pairs_below_2_5A"] for row in rows
            ),
        }
    result = {
        "status": "static_audit_complete_dynamic_system_not_admitted",
        "records": records,
        "summary": by_construct,
        "next_gate": "generate clash-resolved 24-chain conformers with all predicted TM helices in one membrane before topology generation",
        "formal_ER_validation_complete": False,
    }
    (OUT / "audit.json").write_text(json.dumps(result, indent=2))
    (OUT / "status.json").write_text(json.dumps({
        "status": result["status"],
        "models": len(records),
        "summary": by_construct,
        "formal_ER_validation_complete": False,
    }, indent=2))
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
