"""Example tool knows only the JSON file protocol, not the platform package."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
payload = json.loads(args.input.read_text(encoding="utf-8"))
sequence = "".join(payload["sequence"].split()).upper()
if not sequence or set(sequence) - set("ACDEFGHIKLMNPQRSTVWY"):
    raise ValueError("only standard amino acids are supported")
args.output.write_text(json.dumps({"length": len(sequence), "counts": dict(Counter(sequence)), "python_prefix": sys.prefix}), encoding="utf-8")
