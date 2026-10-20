"""Call the author's unmodified PScore implementation and retain raw output."""
import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import sys


def parse_pscore_output(output: Path, *, sequence: str) -> dict:
    """Read the author's global score, without repairing its raw residue table."""
    record = json.loads(output.with_suffix(".run.json").read_text())
    if record["input_sha256"] != sha256(sequence.encode()).hexdigest() or record["input_length"] != len(sequence):
        raise ValueError("PScore input identity mismatch")
    if record["output_sha256"] != sha256(output.read_bytes()).hexdigest():
        raise ValueError("PScore raw output changed")
    matches = re.findall(r"(?:^|<br>)\s*PScore:\s*(-?\d+(?:\.\d+)?)\s*$", output.read_text())
    if len(matches) != 1:
        raise ValueError("Exactly one original global PScore is required")
    return dict(tool_name="PScore", tool_version=record["tool_version"],
                pscore=float(matches[0]), source=record["source"],
                interpretation=record["interpretation"], formal_ranking=None)


def main():
    from Bio import SeqIO
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--fasta", type=Path, required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [row for row in SeqIO.parse(args.fasta, "fasta") if row.id == args.record]
    if len(records) != 1:
        raise ValueError("Select exactly one full FASTA record")
    sequence = str(records[0].seq)
    if len(sequence) < 140 or any(aa not in "ACDEFGHIKLMNPQRSTVWY" for aa in sequence):
        raise ValueError("Original PScore supports standard-amino-acid sequences of at least 140 residues")
    source = args.source.resolve()
    deployment = json.loads((source / "deployment.json").read_text())
    for row in deployment["files"]:
        if sha256((source / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("PScore author file changed: " + row["path"])
    spec = importlib.util.spec_from_file_location("author_pscore_table", source / "cgi-bin/pscore_table.py")
    author = importlib.util.module_from_spec(spec)
    previous = Path.cwd()
    try:
        os.chdir(source)
        spec.loader.exec_module(author)
        raw = author.table(sequence)
    finally:
        os.chdir(previous)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("PScore did not return a real result")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(raw, encoding="utf-8")
    record = dict(tool_name="PScore", tool_version=deployment["commit"],
        source=deployment["source"], origin="automated", command=[sys.executable, *sys.argv], returncode=0,
        input_sha256=sha256(sequence.encode()).hexdigest(), input_length=len(sequence),
        input_file_sha256=sha256(args.fasta.read_bytes()).hexdigest(),
        output_sha256=sha256(args.output.read_bytes()).hexdigest(),
        interpretation="Author predictor output, not LLPS proof. Artificial fusions and cropped IDRs are unvalidated extrapolations.")
    args.output.with_suffix(".run.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(dict(raw_output=str(args.output), input_length=len(sequence), status="computed_not_formal_ranking")))


if __name__ == "__main__":
    main()
