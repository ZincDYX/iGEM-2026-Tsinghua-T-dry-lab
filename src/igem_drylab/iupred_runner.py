"""Thin optional IUPred2 wrapper; no replacement disorder model or weights."""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import sys
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fasta", type=Path, required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--mode", choices=["long", "short", "glob"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native-script", type=Path,
        help="Installed original IUPred2A script; its adjacent library/data are used unchanged.")
    args = parser.parse_args()
    from Bio import SeqIO

    records = [record for record in SeqIO.parse(args.fasta, "fasta") if record.id == args.record]
    if len(records) != 1:
        raise ValueError("Select exactly one unique FASTA record")
    sequence = str(records[0].seq).upper()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    native_hashes = None
    command = [sys.executable, *sys.argv]
    glob_text = None
    if args.native_script is not None:
        script = args.native_script.resolve(strict=True)
        root = script.parent
        required = [script, root / "iupred2a_lib.py", *sorted((root / "data").glob("*"))]
        if not (root / "iupred2a_lib.py").is_file() or not (root / "data").is_dir():
            raise ValueError("original_IUPred2A_library_and_data_required")
        native_hashes = {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
                         for path in required if path.is_file()}
        tool_version = "IUPred2A-native-sha256-" + sha256(
            json.dumps(native_hashes, sort_keys=True).encode("utf-8")).hexdigest()
        single = args.output.with_suffix(".input.fasta")
        single.write_text(">sequence_input\n" + sequence + "\n", encoding="utf-8")
        command = [sys.executable, str(script), str(single), args.mode]
        completed = subprocess.run(command, capture_output=True, check=True)
        args.output.write_bytes(completed.stdout)
        args.output.with_suffix(".stderr.txt").write_bytes(completed.stderr)
        source = "https://github.com/doszilab/iupred2a"
    else:
        from iupred import iupred
        scores, glob_text = iupred(sequence, mode=args.mode)
        if len(scores) != len(sequence):
            raise ValueError("IUPred returned an incomplete residue prediction")
        args.output.write_text("# IUPred2 mode=" + args.mode + "\n" + "".join(
            f"{index}\t{residue}\t{float(score)!r}\n"
            for index, (residue, score) in enumerate(zip(sequence, scores), 1)
        ), encoding="utf-8")
        tool_version = version("iupred")
        source = "https://github.com/saezlab/iupred"
    manifest = dict(tool_name="IUPred2A", tool_version=tool_version, mode=args.mode,
        origin="automated", command=command, returncode=0,
        fasta_record=args.record, sequence_sha256=sha256(sequence.encode("ascii")).hexdigest(),
        input_sha256=sha256(sequence.encode("ascii")).hexdigest(),
        input_file_sha256=sha256(args.fasta.read_bytes()).hexdigest(),
        output_sha256=sha256(args.output.read_bytes()).hexdigest(), glob_text=glob_text,
        source=source, native_bundle_hashes=native_hashes,
        status="computed_not_a_formal_M1_pass")
    args.output.with_suffix(".run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if args.mode != "glob":
        from igem_drylab.constructs.linker_features import parse_iupred2a_output
        parse_iupred2a_output(args.output, tool_version=tool_version,
                             input_sha256=manifest["input_sha256"])
    print(args.output.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
