"""Write stable, parser-compatible residue SASA JSON via the FreeSASA Python API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def calculate_residue_sasa(pdb: Path, output: Path) -> dict[str, object]:
    try:
        import freesasa
    except ImportError as exc:  # pragma: no cover - optional environment boundary
        raise RuntimeError("install the 'sasa' optional dependency to run FreeSASA") from exc

    structure = freesasa.Structure(str(pdb))
    result = freesasa.calc(structure)
    residue_areas = {
        chain: {
            residue: {
                "total": float(area.total),
                "polar": float(area.polar),
                "apolar": float(area.apolar),
                "relativeTotal": float(area.relativeTotal),
            }
            for residue, area in residues.items()
        }
        for chain, residues in result.residueAreas().items()
    }
    record: dict[str, object] = {
        "input_pdb": str(pdb.resolve()),
        "totalArea": float(result.totalArea()),
        "residueAreas": residue_areas,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = calculate_residue_sasa(args.pdb, args.output)
    print(json.dumps({"output": str(args.output.resolve()), "totalArea": record["totalArea"]}))


if __name__ == "__main__":
    main()
