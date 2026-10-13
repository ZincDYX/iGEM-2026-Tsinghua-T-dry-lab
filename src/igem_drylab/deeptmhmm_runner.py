"""Adapt the unmodified academic DeepTMHMM CLI to workflow output directories."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--program-dir", type=Path, required=True)
    parser.add_argument("--fasta", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "auto"), default="cpu")
    args = parser.parse_args()

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    native = output / "native"
    if native.exists():
        raise FileExistsError("DeepTMHMM native output exists; preserve the original job.")

    # The original CLI requires a nonexistent output directory; the workflow
    # adapter creates its own directory before invoking any external command.
    # Keep the original source and its native outputs unchanged.
    environment = dict(os.environ)
    if args.device == "cpu":
        environment["CUDA_VISIBLE_DEVICES"] = ""
    subprocess.run(
        [
            str(args.python.resolve()),
            str(args.program_dir.resolve() / "predict.py"),
            "--fasta", str(args.fasta.resolve()),
            "--output-dir", str(native),
        ],
        cwd=args.program_dir.resolve(),
        env=environment,
        check=True,
    )
    # Publish the small documented outputs where the existing native parser
    # expects them; do not duplicate model weights or generated embeddings.
    for name in ("predicted_topologies.3line", "TMRs.gff3", "deeptmhmm_results.md"):
        shutil.copyfile(native / name, output / name)


if __name__ == "__main__":
    main()
