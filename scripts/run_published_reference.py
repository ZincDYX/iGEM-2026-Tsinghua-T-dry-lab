"""Run only the immutable uploaded author model in author-native units."""
from __future__ import annotations

import argparse
from pathlib import Path

from igem_drylab.published_reference import run_published_reference, write_published_reference_reproduction


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, default=Path("published_reference/published_reference_reproduction.csv"))
    args = parser.parse_args()
    root = args.repository_root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    trajectory = write_published_reference_reproduction(root, output)
    first, second = run_published_reference(root), run_published_reference(root)
    maximum_difference = abs(first.state - second.state).max()
    validation = output.with_name("published_reference_validation.md")
    validation.write_text(
        "# Published reference reproduction\n\n"
        "The adapter imports and executes the immutable uploaded author `reaction_kinetics` function with author-native "
        "parameters and LSODA. Two independent adapter invocations used the same source hash and had maximum absolute "
        f"trajectory difference `{maximum_difference:.3e}`. This checks deterministic reproduction of the uploaded "
        "author model, not physical-unit calibration or experimental validity.\n",
        encoding="utf-8",
    )
    print(trajectory)
    print(validation)


if __name__ == "__main__":
    main()
