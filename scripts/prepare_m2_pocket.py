"""Run sourced pose-contact selection; no parameter or coordinate defaults."""
import argparse
import json
from pathlib import Path
from igem_drylab.pocket_preparation import PocketPreparationInput, prepare_pocket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.request.read_text())
    for item, key in ((raw, "ligand_pose_path"), (raw["reference"], "path"), (raw["reference"], "confidence_file")):
        if item.get(key) and not Path(item[key]).is_absolute():
            item[key] = str((args.request.parent / item[key]).resolve())
    result = prepare_pocket(PocketPreparationInput.model_validate(raw))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "residues": result["reference_pocket_selection"]}))


if __name__ == "__main__":
    main()
