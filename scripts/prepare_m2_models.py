"""Inventory exact full-length ColabFold pairs before starting formal M2.

This preparation command does not approve pockets or run a predictor. It reports
which original jobs can be reused so the execution host only predicts missing
targets. Search roots are explicit scientific-output directories, never inferred
private server locations.
"""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

from Bio import SeqIO
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1

from igem_drylab.parsers.structure_prediction import parse_structure_prediction_output
from igem_drylab.region_assessment import Region, RegionAssessmentInput, assess_regions


def inventory(targets_file, input_pack, roots):
    with targets_file.open(encoding="utf-8-sig") as stream:
        targets = list(csv.DictReader(stream))
    if not targets or len({target["record_id"] for target in targets}) != len(targets):
        raise ValueError("prediction_targets_require_unique_record_ids")
    sequences = {}
    for target in targets:
        source = input_pack / target["source_fasta"]
        if source not in sequences:
            rows = list(SeqIO.parse(source, "fasta"))
            if len({row.id for row in rows}) != len(rows):
                raise ValueError("prediction_fasta_requires_unique_record_ids")
            sequences[source] = {r.id: str(r.seq).upper() for r in rows}
    records = []
    for target in targets:
        identifier = target["record_id"]
        sequence = sequences[input_pack / target["source_fasta"]][identifier]
        if len(sequence) != int(target["aa_length"]):
            raise ValueError("prediction_target_sequence_length_mismatch")
        records.append(dict(record_id=identifier, sequence=sequence, sequence_sha256=sha256(sequence.encode()).hexdigest(),
                            models=[], status="needs_prediction"))
    matches_by_sequence = {}
    for record in records:
        matches_by_sequence.setdefault(record["sequence"], []).append(record)
    invalid = []
    parser = PDBParser(QUIET=True)
    seen = set()
    for root_index, root in enumerate(roots):
        for score in sorted(root.rglob("*_scores_rank_*.json")):
            if score.resolve() in seen:
                continue
            seen.add(score.resolve())
            provenance = dict(root_index=root_index, confidence_relative_path=str(score.relative_to(root)))
            try:
                prefix = score.name.split("_scores_rank_", 1)[0]
                summary = parse_structure_prediction_output(score, candidate_id=prefix)
                structure = parser.get_structure(prefix, summary.model_file)
                models = list(structure.get_models())
                if len(models) != 1 or len(list(models[0].get_chains())) != 1:
                    raise ValueError("requires_single_complete_protein_chain")
                residues = [r for r in next(models[0].get_chains()).get_residues() if r.id[0] == " "]
                sequence = "".join(seq1(r.resname) for r in residues)
                if sequence not in matches_by_sequence:
                    continue
                observed = assess_regions(RegionAssessmentInput(candidate_id=prefix, tool_input_id=prefix,
                    sequence=sequence, confidence_file=score,
                    regions=[Region(name="complete", role="diagnostic", start=1, end=len(sequence))],
                    calculate_accessibility=False))
                row = {**provenance, "model_relative_path": str(summary.model_file.relative_to(root)),
                    "model_rank": summary.model_rank, "model_sha256": observed["model_sha256"],
                    "confidence_sha256": observed["confidence_sha256"], "sequence_exact_match": True,
                    "complete_pair_verified": True, "mean_plddt": observed["regions"][0]["mean_plddt"]}
                for record in matches_by_sequence[sequence]:
                    record["models"].append(row)
                    record["status"] = "paired_models_available"
            except (ValueError, OSError, KeyError, StopIteration) as error:
                invalid.append({**provenance, "error_type": type(error).__name__,
                    "reason": str(error)})
    for record in records:
        record.pop("sequence")
    return {"schema_version": "m2-model-preparation-v1", "targets": records, "invalid_pairs": invalid,
        "model_inputs_ready": all(r["models"] for r in records),
        "scope": "exact_structure_and_confidence_pair_inventory_not_pocket_or_full_M2_acceptance"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-pack", type=Path, required=True)
    p.add_argument("--models-root", type=Path, action="append", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--require-models-ready", action="store_true")
    args = p.parse_args()
    pack = args.input_pack.resolve()
    roots = [root.resolve(strict=True) for root in args.models_root]
    if any(not root.is_dir() for root in roots):
        raise ValueError("models_root_must_be_a_scientific_output_directory")
    report = inventory(pack / "M2_prediction_targets.csv", pack, roots)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"model_inputs_ready": report["model_inputs_ready"],
        "reuse_targets": [r["record_id"] for r in report["targets"] if r["models"]],
        "predict_targets": [r["record_id"] for r in report["targets"] if not r["models"]]}, ensure_ascii=False))
    if args.require_models_ready and not report["model_inputs_ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
