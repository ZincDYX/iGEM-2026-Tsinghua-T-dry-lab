"""Mechanical schema export; never reads user profiles or scientific files."""
import argparse
import json
from pathlib import Path

from igem_drylab.software.public_contracts import public_schemas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(public_schemas(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")


if __name__ == "__main__": main()
