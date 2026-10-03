"""Small, explicit CLI boundary around the official AutoDock Vina Python API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence


def run_vina(
    *,
    receptor: Path,
    ligand: Path,
    output: Path,
    summary: Path,
    center: Sequence[float],
    size: Sequence[float],
    exhaustiveness: int,
    num_modes: int,
    seed: int,
) -> dict[str, object]:
    """Dock one prepared ligand and preserve the exact run inputs and energies."""

    if len(center) != 3 or len(size) != 3:
        raise ValueError("center_and_size_require_exactly_three_values")
    if exhaustiveness < 1 or num_modes < 1:
        raise ValueError("exhaustiveness_and_num_modes_must_be_positive")
    try:
        from vina import Vina
    except ImportError as exc:  # pragma: no cover - exercised only without the optional dependency
        raise RuntimeError("install the 'docking' optional dependency to run AutoDock Vina") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    summary.parent.mkdir(parents=True, exist_ok=True)
    engine = Vina(sf_name="vina", seed=seed, verbosity=0)
    engine.set_receptor(str(receptor))
    engine.set_ligand_from_file(str(ligand))
    engine.compute_vina_maps(center=list(center), box_size=list(size))
    engine.dock(exhaustiveness=exhaustiveness, n_poses=num_modes)
    engine.write_poses(str(output), n_poses=num_modes, overwrite=True)
    energies = engine.energies(n_poses=num_modes).tolist()
    record: dict[str, object] = {
        "scoring_function": "vina",
        "receptor": str(receptor.resolve()),
        "ligand": str(ligand.resolve()),
        "output": str(output.resolve()),
        "center_angstrom": list(center),
        "size_angstrom": list(size),
        "exhaustiveness": exhaustiveness,
        "num_modes": num_modes,
        "seed": seed,
        "energies_kcal_per_mol": energies,
    }
    summary.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receptor", type=Path, required=True)
    parser.add_argument("--ligand", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--center", type=float, nargs=3, metavar=("X", "Y", "Z"), required=True)
    parser.add_argument("--size", type=float, nargs=3, metavar=("X", "Y", "Z"), required=True)
    parser.add_argument("--exhaustiveness", type=int, default=8)
    parser.add_argument("--num-modes", type=int, default=9)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    record = run_vina(
        receptor=args.receptor,
        ligand=args.ligand,
        output=args.output,
        summary=args.summary,
        center=args.center,
        size=args.size,
        exhaustiveness=args.exhaustiveness,
        num_modes=args.num_modes,
        seed=args.seed,
    )
    print(json.dumps(record))


if __name__ == "__main__":
    main()
