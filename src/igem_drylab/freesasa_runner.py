"""Write stable, parser-compatible residue SASA JSON via the FreeSASA Python API."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from igem_drylab.structure_metrics import calculate_sasa_structure


def calculate_residue_sasa(pdb: Path, output: Path, *, model_id: int | None = None,
                           altloc: str | None = None) -> dict[str, object]:
    try:
        import freesasa
    except ImportError as exc:  # pragma: no cover - optional environment boundary
        raise RuntimeError("install the 'sasa' optional dependency to run FreeSASA") from exc

    parameters = freesasa.Parameters()
    selected_model, result = calculate_sasa_structure(pdb, model_id=model_id, altloc=altloc, parameters=parameters)
    configuration = {"algorithm":parameters.algorithm(),"probe_radius_angstrom":parameters.probeRadius(),
                     "n_points":parameters.nPoints(),"n_slices":parameters.nSlices(),"n_threads":parameters.nThreads(),
                     "structure_options":freesasa.Structure.defaultOptions,
                     "classifier":"built_in_default_bound_to_recorded_FreeSASA_version"}
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
        "model_id": selected_model,
        "altloc": altloc,
        "residue_numbering": "author",
        "input_pdb_sha256":sha256(pdb.read_bytes()).hexdigest(),
        "tool_name":"FreeSASA","tool_version":version("freesasa"),
        "sasa_configuration":configuration,
        "sasa_configuration_sha256":sha256(json.dumps(configuration,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
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
    parser.add_argument("--model-id", type=int)
    parser.add_argument("--altloc")
    args = parser.parse_args()
    record = calculate_residue_sasa(args.pdb, args.output, model_id=args.model_id, altloc=args.altloc)
    print(json.dumps({"output": str(args.output.resolve()), "totalArea": record["totalArea"]}))


if __name__ == "__main__":
    main()
