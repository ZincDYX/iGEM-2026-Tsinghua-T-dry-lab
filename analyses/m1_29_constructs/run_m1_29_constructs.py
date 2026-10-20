from __future__ import annotations

import csv
import os
from collections import Counter
from hashlib import sha256
import importlib.util
import json
from math import log2
from pathlib import Path
import re

from Bio import SeqIO, __version__ as biopython_version
from Bio.Seq import Seq
from Bio.SeqUtils.ProtParam import ProteinAnalysis


ROOT = Path(os.environ.get('GALATEA_M1_INPUT_DIR','m1-inputs')).resolve()
OVERRIDE_Q29 = Path(os.environ.get('GALATEA_Q29_OVERRIDE',str(ROOT/'Q29_override.dna')))
SOURCE_ZIP = Path(os.environ.get('GALATEA_CONSTRUCT_ARCHIVE',str(ROOT/'constructs.zip')))
IUPRED = Path(os.environ['GALATEA_IUPRED_LIBRARY'])
OUTPUT = Path(os.environ.get('GALATEA_M1_OUTPUT_DIR','m1-results')).resolve()


ORDER = [
    "CRISPR-Cas-int14，15.dna",
    "CRISPR-Cas9-int14，15.dna",
    "FUSN-SH3(3)-PDZ-FTH1（无荧光版本）.dna",
    "FUSN-SH3(3)-PDZ-mCherry-FTH1.dna",
    "OC-SH3+DMT-PDZ.dna",
    "OC-SH3+DMT-PDZ（无荧光蛋白版本）.dna",
    "sgRNA-int14，15.dna",
    "WT OC-SH3+DMT-PDZ（无荧光蛋白版本）.dna",
    "实验组 低表达delete N OC-正常表达LLPS.dna",
    "实验组 低表达delete N OC有抓手-正常表达ER anchor-LLPS.dna",
    "实验组 低表达delete N OC有抓手-正常表达LLPS.dna",
    "实验组 低表达delete N OC有荧光-正常表达LLPS.dna",
    "实验组 低表达delete N OC有荧光有抓手-正常表达ER anchor-LLPS.dna",
    "实验组 低表达delete N OC有荧光有抓手-正常表达LLPS.dna",
    "实验组 低表达DMT 抓手版本.dna",
    "实验组 低表达DMT 有荧光有抓手版本.dna",
    "实验组 低表达DMT 荧光版本.dna",
    "实验组 低表达DMT.dna",
    "实验组 正常delete N OC有荧光有抓手.dna",
    "实验组 正常表达delete N OC有抓手.dna",
    "实验组 正常表达delete N OC有荧光.dna",
    "实验组 正常表达DMT 有抓手版本.dna",
    "实验组 正常表达DMT 有荧光有抓手版本.dna",
    "实验组 正常表达DMT 荧光版本.dna",
    "实验组 高表达delete N OC有抓手.dna",
    "实验组 高表达DMT 有抓手版本.dna",
    "对照组 低表达delete N OC.dna",
    "对照组 低表达DMT.dna",
    "对照组正常表达DMT.dna",
    "对照组正常表达OC.dna",
]

STANDARD = set("ACDEFGHIKLMNPQRSTVWY")
HYDROPHOBIC = set("AVILMFWY")
AROMATIC = set("FWY")
CHARGED = set("DEKRH")
POLAR = set("STNQCY")
KD = {
    "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
    "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
    "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
    "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3,
}
TARGET_PATTERN = re.compile(r"(?i)(cas9|idr|fusn|llps|bbe006|ggoc1|dmt|scarlet|greenlantern|sh3|pdz|fth1|er anchor)")
SEED_PATTERN = re.compile(r"(?i)(^idr$|bbe006|ggoc1|dmt)")
MARKER_PATTERN = re.compile(r"(?i)(ampr|kanr|kanmx|specr|pbbR1)")
STOP = {"TAA", "TAG", "TGA"}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def feature_label(feature) -> str:
    for key in ("label", "gene", "product", "locus_tag", "name"):
        value = feature.qualifiers.get(key)
        if value:
            return str(value[0])
    return ""


def load_iupred():
    spec = importlib.util.spec_from_file_location("galatea_iupred2a_native", IUPRED)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.iupred


def longest_run(values: list[bool]) -> int:
    best = current = 0
    for value in values:
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def sequence_metrics(sequence: str, iupred, mode: str) -> dict:
    sequence = sequence.rstrip("*").upper()
    if not sequence or set(sequence) - STANDARD:
        raise ValueError(f"Non-standard protein sequence: {set(sequence) - STANDARD}")
    counts = Counter(sequence)
    length = len(sequence)
    analysis = ProteinAnalysis(sequence)
    disorder, _ = iupred(sequence, mode)
    disordered = [float(value) >= 0.5 for value in disorder]
    hydrophobic_run = longest_run([residue in HYDROPHOBIC for residue in sequence])
    entropy = -sum((count / length) * log2(count / length) for count in counts.values())
    ordered = sorted(counts.values(), reverse=True)
    helix_propensity, turn_propensity, sheet_propensity = analysis.secondary_structure_fraction()
    return {
        "sequence_sha256": sha256(sequence.encode("ascii")).hexdigest(),
        "length_aa": length,
        "molecular_weight_da": round(analysis.molecular_weight(), 3),
        "theoretical_pi": round(analysis.isoelectric_point(), 4),
        "charge_at_ph7": round(analysis.charge_at_pH(7.0), 4),
        "gravy": round(analysis.gravy(), 6),
        "instability_index": round(analysis.instability_index(), 4),
        "aromaticity": round(analysis.aromaticity(), 6),
        "gs_fraction": round((counts["G"] + counts["S"]) / length, 6),
        "pro_fraction": round(counts["P"] / length, 6),
        "aromatic_fraction": round(sum(counts[aa] for aa in AROMATIC) / length, 6),
        "hydrophobic_fraction": round(sum(counts[aa] for aa in HYDROPHOBIC) / length, 6),
        "charged_fraction": round(sum(counts[aa] for aa in CHARGED) / length, 6),
        "polar_fraction": round(sum(counts[aa] for aa in POLAR) / length, 6),
        "ncpr_proxy": round((counts["K"] + counts["R"] - counts["D"] - counts["E"]) / length, 6),
        "shannon_entropy_bits": round(entropy, 6),
        "top2_fraction": round(sum(ordered[:2]) / length, 6),
        "max_hydrophobic_run": hydrophobic_run,
        "mean_kd_hydropathy": round(sum(KD[aa] for aa in sequence) / length, 6),
        "iupred_mode": mode,
        "iupred_mean": round(sum(disorder) / length, 6),
        "iupred_fraction_ge_0_5": round(sum(disordered) / length, 6),
        "iupred_longest_disordered_run": longest_run(disordered),
        "iupred_longest_ordered_run": longest_run([not value for value in disordered]),
        # These are composition propensities from ProtParam, not a secondary-structure prediction.
        "protparam_helix_propensity_fraction": round(helix_propensity, 6),
        "protparam_turn_propensity_fraction": round(turn_propensity, 6),
        "protparam_sheet_propensity_fraction": round(sheet_propensity, 6),
    }


def annotated_product(record, feature) -> tuple[str, tuple[int, int, int]] | None:
    sequence = str(record.seq).upper()
    strand = feature.location.strand or 1
    left, right = int(feature.location.start), int(feature.location.end)
    if strand == 1:
        if sequence[left:left + 3] == "ATG":
            start = left
        elif left >= 3 and sequence[left - 3:left] == "ATG":
            start = left - 3
        else:
            return None
        coding = sequence[start:]
        coordinate = (start, right, strand)
    else:
        first = str(Seq(sequence[right - 3:right]).reverse_complement())
        prefix = str(Seq(sequence[right:right + 3]).reverse_complement()) if right + 3 <= len(sequence) else ""
        if first == "ATG":
            end = right
        elif prefix == "ATG":
            end = right + 3
        else:
            return None
        coding = str(Seq(sequence[:end]).reverse_complement())
        coordinate = (left, end, strand)
    codon_start = int((feature.qualifiers.get("codon_start") or [1])[0]) - 1
    if codon_start and ((strand == 1 and start == left) or (strand == -1 and end == right)):
        coding = coding[codon_start:]
    protein = []
    for index in range(0, len(coding) - 2, 3):
        codon = coding[index:index + 3]
        if codon in STOP:
            break
        protein.append(str(Seq(codon).translate()))
    return "".join(protein), coordinate


def enumerate_orfs(record, minimum: int = 300):
    sequence = str(record.seq).upper()
    size = len(sequence)
    for strand, oriented in ((1, sequence), (-1, str(Seq(sequence).reverse_complement()))):
        for frame in range(3):
            start = None
            for position in range(frame, len(oriented) - 2, 3):
                codon = oriented[position:position + 3]
                if start is None:
                    if codon == "ATG":
                        start = position
                elif codon in STOP:
                    protein = str(Seq(oriented[start:position]).translate())
                    if len(protein) >= minimum:
                        if strand == 1:
                            left, right = start, position + 3
                        else:
                            left, right = size - position - 3, size - start
                        yield protein, (left, right, strand)
                    start = None


def overlapping_labels(record, coordinate) -> list[str]:
    left, right, strand = coordinate
    labels = []
    for feature in record.features:
        f_left, f_right = int(feature.location.start), int(feature.location.end)
        label = feature_label(feature)
        if label and min(right, f_right) > max(left, f_left):
            labels.append(label)
    return list(dict.fromkeys(labels))


def target_products(record) -> list[dict]:
    products = []
    for feature in record.features:
        label = feature_label(feature)
        if feature.type == "CDS" and SEED_PATTERN.search(label) and not MARKER_PATTERN.search(label):
            recovered = annotated_product(record, feature)
            if recovered is None:
                continue
            protein, coordinate = recovered
            if len(protein) >= 100:
                products.append({"sequence": protein, "coordinate": coordinate, "seed_label": label})
    for protein, coordinate in enumerate_orfs(record):
        labels = overlapping_labels(record, coordinate)
        if any(TARGET_PATTERN.search(label) and not MARKER_PATTERN.search(label) for label in labels):
            products.append({"sequence": protein, "coordinate": coordinate, "seed_label": "ORF:" + "+".join(labels)})
    unique = {}
    for product in products:
        unique.setdefault(product["sequence"], product)
    candidates = list(unique.values())
    pruned = []
    for product in candidates:
        left, right, strand = product["coordinate"]
        nested = any(
            product["seed_label"].startswith("ORF:")
            and other is not product
            and other["coordinate"][2] == strand
            and other["coordinate"][0] <= left
            and other["coordinate"][1] >= right
            and len(other["sequence"]) > len(product["sequence"])
            for other in candidates
        )
        if not nested:
            pruned.append(product)
    return sorted(pruned, key=lambda item: (item["coordinate"][0], item["coordinate"][2], -len(item["sequence"])))


def target_fragments(record) -> list[dict]:
    rows = []
    for feature in record.features:
        if feature.type not in {"CDS", "misc_feature"}:
            continue
        label = feature_label(feature)
        label_lower = label.casefold()
        if "linker" not in label_lower and label_lower not in {"idr", "llps-idr"}:
            continue
        nucleotide = feature.extract(record.seq)
        trim = len(nucleotide) - len(nucleotide) % 3
        sequence = str(nucleotide[:trim].translate()).rstrip("*")
        if not sequence or set(sequence) - STANDARD:
            continue
        kind = "idr" if "idr" in label_lower else "linker"
        rows.append({"label": label, "kind": kind, "sequence": sequence})
    unique = {}
    for row in rows:
        unique.setdefault((row["kind"], row["sequence"]), row)
    return list(unique.values())


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_fasta(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(f">{row['product_id']} construct={row['q_id']} source={row['source_file']}\n")
            sequence = row["sequence"]
            handle.write("\n".join(sequence[index:index + 80] for index in range(0, len(sequence), 80)) + "\n")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "figures").mkdir(exist_ok=True)
    iupred = load_iupred()
    manifest = []
    product_rows = []
    fragment_rows = []
    seen_products = {}
    anomalies = []
    for ordinal, name in enumerate(ORDER, 1):
        q_id = f"Q{ordinal:02d}"
        included = q_id != "Q08"
        path = OVERRIDE_Q29 if q_id == "Q29" else ROOT / name
        record = SeqIO.read(path, "snapgene")
        products = target_products(record) if included else []
        fragments = target_fragments(record) if included else []
        if included and not products and "sgRNA" not in name:
            anomalies.append(f"{q_id}: no project protein ORF was recovered from annotations and sequence.")
        content_labels = " ".join(
            feature_label(feature) for feature in record.features if feature_label(feature)
        ).casefold()
        if "delete n oc" in name.casefold() and "dmt_z" in content_labels and "bbe006" not in content_labels:
            anomalies.append(f"{q_id}: the filename says delete-N OC, but the encoded project enzyme annotation is DMT.")
        if "dmt" in name.casefold() and "bbe006" in content_labels and "dmt_z" not in content_labels:
            anomalies.append(f"{q_id}: the filename says DMT, but the encoded project enzyme annotation is delete-N OC/BBE006.")
        for product in products:
            if not product["seed_label"].startswith("ORF:"):
                continue
            left, right, _strand = product["coordinate"]
            for feature in record.features:
                label = feature_label(feature)
                if feature.type != "CDS" or "dmt_z" not in label.casefold():
                    continue
                f_left, f_right = int(feature.location.start), int(feature.location.end)
                overlap = max(0, min(right, f_right) - max(left, f_left))
                if overlap / max(1, f_right - f_left) < 0.95 and overlap:
                    anomalies.append(
                        f"{q_id}: the only AUG-initiated ORF overlapping annotated DMT covers "
                        f"{overlap}/{f_right - f_left} nt of that CDS; full-length DMT translation is not supported by this plasmid sequence."
                    )
        if q_id == "Q29":
            archive = ROOT / name
            if archive.exists() and archive.read_bytes() != path.read_bytes():
                anomalies.append(
                    f"Q29: the standalone DMT file overrides the archive copy ({len(record.seq)} bp versus "
                    f"{len(SeqIO.read(archive, 'snapgene').seq)} bp); only the standalone file contains the complete annotated DMT CDS."
                )
        manifest.append({
            "q_id": q_id,
            "included": included,
            "source_file": name if q_id != "Q29" else OVERRIDE_Q29.name,
            "source_role": "standalone_override" if q_id == "Q29" else "archive_entry",
            "plasmid_bp": len(record.seq),
            "project_protein_products": len(products),
            "m1_fragments": len(fragments),
            "note": "excluded_not_physically_constructed" if q_id == "Q08" else ("noncoding_sgrna_construct" if not products else ""),
        })
        for product_number, product in enumerate(products, 1):
            sequence = product.pop("sequence")
            sequence_hash = sha256(sequence.encode("ascii")).hexdigest()
            duplicate_of = seen_products.get(sequence_hash, "")
            product_id = f"{q_id}_P{product_number:02d}"
            if not duplicate_of:
                seen_products[sequence_hash] = product_id
            labels = overlapping_labels(record, product["coordinate"])
            metrics = sequence_metrics(sequence, iupred, "long")
            product_rows.append({
                "q_id": q_id,
                "product_id": product_id,
                "source_file": path.name,
                "seed_label": product["seed_label"],
                "feature_labels": "; ".join(labels),
                "coordinate_1based": f"{product['coordinate'][0] + 1}-{product['coordinate'][1]}",
                "strand": product["coordinate"][2],
                "duplicate_of": duplicate_of,
                "sequence": sequence,
                **metrics,
            })
        for fragment_number, fragment in enumerate(fragments, 1):
            sequence = fragment.pop("sequence")
            metrics = sequence_metrics(sequence, iupred, "long" if fragment["kind"] == "idr" else "short")
            hard_flags = []
            if fragment["kind"] == "linker":
                if metrics["length_aa"] < 5 or metrics["length_aa"] > 25:
                    hard_flags.append("linker_length_outside_5_25")
                if metrics["hydrophobic_fraction"] >= 0.40:
                    hard_flags.append("linker_hydrophobic_fraction_ge_0_40")
                if metrics["max_hydrophobic_run"] >= 5:
                    hard_flags.append("hydrophobic_run_ge_5")
            else:
                if metrics["hydrophobic_fraction"] >= 0.35:
                    hard_flags.append("idr_hydrophobic_fraction_ge_0_35")
                if metrics["iupred_mean"] < 0.5:
                    hard_flags.append("idr_iupred_mean_lt_0_5")
                if metrics["iupred_longest_disordered_run"] < 20:
                    hard_flags.append("idr_disordered_run_lt_20")
                if metrics["iupred_longest_ordered_run"] > 10:
                    hard_flags.append("idr_ordered_run_gt_10")
            fragment_rows.append({
                "q_id": q_id,
                "fragment_id": f"{q_id}_F{fragment_number:02d}",
                "source_file": path.name,
                "label": fragment["label"],
                "kind": fragment["kind"],
                "sequence": sequence,
                "project_protocol_flags": ";".join(hard_flags),
                **metrics,
            })

    if sum(row["included"] for row in manifest) != 29:
        raise AssertionError("The manifest must contain exactly 29 included constructs")
    write_csv(OUTPUT / "construct_manifest.csv", manifest)
    write_csv(OUTPUT / "protein_products.csv", product_rows)
    write_csv(OUTPUT / "m1_fragments.csv", fragment_rows)
    write_fasta(OUTPUT / "protein_products.fasta", product_rows)
    write_fasta(OUTPUT / "unique_protein_products.fasta", [row for row in product_rows if not row["duplicate_of"]])
    (OUTPUT / "anomalies.txt").write_text("\n".join(anomalies) + "\n", encoding="utf-8")
    provenance = {
        "schema_version": "galatea-private-m1-provenance-v1",
        "source_zip": str(SOURCE_ZIP),
        "source_zip_sha256": digest(SOURCE_ZIP),
        "q29_override": str(OVERRIDE_Q29),
        "q29_override_sha256": digest(OVERRIDE_Q29),
        "excluded_construct": "Q08",
        "included_construct_count": 29,
        "biopython_version": biopython_version,
        "iupred_source": "IUPred2A native academic distribution",
        "iupred_script_sha256": digest(IUPRED),
        "threshold_scope": "Project-declared M1 v3 negative-screen thresholds; not universal biological laws.",
        "not_run_here": ["PSIPRED/JPred", "SignalP 6", "DeepTMHMM", "TANGO/PASTA2", "restriction-site policy without an approved motif list"],
    }
    (OUTPUT / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "included_constructs": 29,
        "excluded_constructs": ["Q08"],
        "protein_products": len(product_rows),
        "unique_protein_sequences": len(seen_products),
        "noncoding_constructs": [row["q_id"] for row in manifest if row["included"] and row["note"] == "noncoding_sgrna_construct"],
        "fragments": len(fragment_rows),
        "unique_fragment_sequences": len({row["sequence"] for row in fragment_rows}),
        "flagged_fragment_records": sum(bool(row["project_protocol_flags"]) for row in fragment_rows),
        "anomalies": anomalies,
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
