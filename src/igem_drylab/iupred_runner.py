"""Thin optional IUPred2 wrapper; no replacement disorder model or weights."""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fasta", type=Path, required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--mode", choices=["long", "short", "glob"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from Bio import SeqIO
    from iupred import iupred

    records = [record for record in SeqIO.parse(args.fasta, "fasta") if record.id == args.record]
    if len(records) != 1:
        raise ValueError("Select exactly one unique FASTA record")
    sequence = str(records[0].seq).upper()
    scores, glob_text = iupred(sequence, mode=args.mode)
    if len(scores) != len(sequence):
        raise ValueError("IUPred returned an incomplete residue prediction")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("# IUPred2 mode=" + args.mode + "\n" + "".join(
        f"{index}\t{residue}\t{float(score)!r}\n"
        for index, (residue, score) in enumerate(zip(sequence, scores), 1)
    ), encoding="utf-8")
    manifest = dict(tool_name="IUPred2A", tool_version=version("iupred"), mode=args.mode,
        origin="automated", command=[sys.executable, *sys.argv], returncode=0,
        fasta_record=args.record, sequence_sha256=sha256(sequence.encode("ascii")).hexdigest(),
        input_sha256=sha256(sequence.encode("ascii")).hexdigest(),
        input_file_sha256=sha256(args.fasta.read_bytes()).hexdigest(),
        output_sha256=sha256(args.output.read_bytes()).hexdigest(), glob_text=glob_text,
        source="https://github.com/saezlab/iupred", status="computed_not_a_formal_M1_pass")
    args.output.with_suffix(".run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(args.output.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
