from __future__ import annotations

import csv
import os
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(os.environ.get('GALATEA_M1_OUTPUT_DIR','m1-results')).resolve()
TOOLS = ROOT / "server-tools"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)


def read_signalp() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    source = TOOLS / "signalp6-slow" / "prediction_results.txt"
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            product_id = parts[0].split()[0]
            result[product_id] = {
                "signalp_prediction": parts[1],
                "signalp_other_probability": parts[2],
                "signalp_sp_probability": parts[3],
                "signalp_cleavage_site": parts[4] if len(parts) > 4 else "",
            }
    return result


def read_tmhmm() -> dict[str, dict[str, str | int]]:
    result: dict[str, dict[str, str | int]] = {}
    source = TOOLS / "deeptmhmm-run2" / "TMRs.gff3"
    current = None
    for line in source.read_text(encoding="utf-8").splitlines():
        if line.startswith("# ") and " Length:" in line:
            current = line[2:].split()[0]
            result[current] = {"deeptmhmm_predicted_tmrs": 0, "deeptmhmm_topology": "", "deeptmhmm_tm_regions": ""}
        elif line.startswith("# ") and "Number of predicted TMRs:" in line and current:
            result[current]["deeptmhmm_predicted_tmrs"] = int(line.rsplit(":", 1)[1].strip())
        elif line and not line.startswith("#") and line != "//" and current:
            fields = line.split("\t")
            if len(fields) >= 2:
                previous = str(result[current]["deeptmhmm_topology"])
                result[current]["deeptmhmm_topology"] = ";".join(filter(None, [previous, f"{fields[1]}:{fields[2]}-{fields[3]}"]))
                if fields[1] == "TMhelix":
                    previous_tm = str(result[current]["deeptmhmm_tm_regions"])
                    result[current]["deeptmhmm_tm_regions"] = ";".join(filter(None, [previous_tm, f"{fields[2]}-{fields[3]}"]))
    return result


def read_psipred() -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for path in sorted((TOOLS / "psipred-single").glob("*.ss2")):
        states: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) >= 3:
                states.append(fields[2])
        counts = Counter(states)
        length = len(states)
        result[path.stem] = {
            "psipred_length": length,
            "psipred_coil_fraction": counts["C"] / length,
            "psipred_helix_fraction": counts["H"] / length,
            "psipred_sheet_fraction": counts["E"] / length,
        }
    return result


products = pd.read_csv(ROOT / "protein_products.csv")
signalp = read_signalp()
tmhmm = read_tmhmm()
psipred = read_psipred()

rows: list[dict[str, object]] = []
for record in products.to_dict(orient="records"):
    product_id = str(record["product_id"])
    merged = dict(record)
    merged.update(signalp.get(product_id, {}))
    merged.update(tmhmm.get(product_id, {}))
    merged.update(psipred.get(product_id, {}))
    rows.append(merged)

fieldnames: list[str] = []
for row in rows:
    for key in row:
        if key not in fieldnames:
            fieldnames.append(key)
with (ROOT / "protein_products_complete.csv").open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

unique = pd.DataFrame(rows).loc[lambda frame: frame["duplicate_of"].fillna("") == ""].copy()
for column in [
    "length_aa",
    "gravy",
    "iupred_mean",
    "theoretical_pi",
    "psipred_coil_fraction",
    "psipred_helix_fraction",
    "psipred_sheet_fraction",
    "deeptmhmm_predicted_tmrs",
]:
    unique[column] = pd.to_numeric(unique[column])

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.labelcolor": "#2f3542",
        "xtick.color": "#596275",
        "ytick.color": "#596275",
    }
)
fig, ax = plt.subplots(figsize=(8.4, 5.0), dpi=180)
sizes = 28 + 90 * (unique["length_aa"] / unique["length_aa"].max()) ** 0.55
scatter = ax.scatter(
    unique["gravy"],
    unique["iupred_mean"],
    s=sizes,
    c=unique["theoretical_pi"],
    cmap="PuBu",
    alpha=0.84,
    linewidth=0.6,
    edgecolor="white",
)
annotations = [
    (["Q03_P01", "Q09_P02"], "Q03_P01 / Q09_P02", (-36, 12)),
    (["Q10_P02"], "Q10_P02", (10, 12)),
    (["Q13_P02"], "Q13_P02", (12, -12)),
    (["Q04_P01"], "Q04_P01", (-4, -18)),
    (["Q01_P01"], "Q01_P01", (6, 4)),
]
for product_ids, label, offset in annotations:
    group = unique[unique["product_id"].isin(product_ids)]
    ax.annotate(label, (group["gravy"].mean(), group["iupred_mean"].mean()),
                xytext=offset, textcoords="offset points", fontsize=7,
                arrowprops={"arrowstyle": "-", "color": "#8b8290", "linewidth": 0.6})
ax.axhline(0.5, color="#c3a6c8", linestyle="--", linewidth=1, label="IUPred mean = 0.5")
ax.set_xlabel("Mean hydropathy (GRAVY)")
ax.set_ylabel("Mean IUPred2A disorder score")
ax.set_title("Sequence-level profile of 21 unique recovered products", loc="left", fontweight="bold", pad=10)
ax.grid(color="#e8e6eb", linewidth=0.7, alpha=0.8)
colorbar = fig.colorbar(scatter, ax=ax, pad=0.02)
colorbar.set_label("Theoretical pI")
ax.legend(frameon=False, loc="upper right")
fig.tight_layout()
fig.savefig(FIGURES / "m1_sequence_profile.png", bbox_inches="tight")
plt.close(fig)

fragments = pd.read_csv(ROOT / "m1_fragments.csv")
fragment_unique = fragments.drop_duplicates("sequence_sha256").copy()
fragment_unique = fragment_unique.sort_values(["kind", "length_aa"], ascending=[True, False])
kind_counts: dict[str, int] = defaultdict(int)
labels = []
for kind in fragment_unique["kind"]:
    kind_counts[kind] += 1
    labels.append(f"{kind.upper()} {kind_counts[kind]}")
fragment_unique["label_display"] = labels
fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.8), dpi=180, gridspec_kw={"wspace": 0.34})
colors = ["#7a86a8" if kind == "idr" else "#b19ab7" for kind in fragment_unique["kind"]]
axes[0].barh(fragment_unique["label_display"], fragment_unique["iupred_mean"], color=colors)
axes[0].axvline(0.5, color="#d0a24c", linestyle="--", linewidth=1)
axes[0].set_xlim(0, 1.03)
axes[0].set_xlabel("Mean IUPred2A score")
axes[0].set_title("Disorder", loc="left", fontweight="bold")
axes[1].barh(fragment_unique["label_display"], fragment_unique["hydrophobic_fraction"], color=colors)
axes[1].axvline(0.35, color="#d0a24c", linestyle="--", linewidth=1, label="IDR screen 0.35")
axes[1].axvline(0.40, color="#bd5b5b", linestyle=":", linewidth=1, label="Linker screen 0.40")
axes[1].set_xlim(0, 0.45)
axes[1].set_xlabel("Hydrophobic residue fraction")
axes[1].set_title("Hydrophobicity screen", loc="left", fontweight="bold")
axes[1].legend(frameon=False, fontsize=7, loc="lower right")
for ax in axes:
    ax.grid(axis="x", color="#e8e6eb", linewidth=0.7, alpha=0.8)
    ax.invert_yaxis()
fig.suptitle("Unique annotated M1 fragments (n = 12)", x=0.08, ha="left", fontweight="bold")
fig.savefig(FIGURES / "m1_fragment_checks.png", bbox_inches="tight")
plt.close(fig)

signalp_counts = Counter(item["signalp_prediction"] for item in signalp.values())
tmr_counts = Counter(int(item["deeptmhmm_predicted_tmrs"]) for item in tmhmm.values())
psipred_ranges = {
    name: [float(unique[name].min()), float(unique[name].max())]
    for name in ["psipred_coil_fraction", "psipred_helix_fraction", "psipred_sheet_fraction"]
}
completion = {
    "included_constructs": 29,
    "excluded_constructs": ["Q08"],
    "recovered_protein_products": len(products),
    "unique_protein_sequences": len(unique),
    "signalp_predictions": dict(signalp_counts),
    "deeptmhmm_predicted_tmr_counts": {str(key): value for key, value in sorted(tmr_counts.items())},
    "psipred_fraction_ranges": psipred_ranges,
    "unique_fragments": len(fragment_unique),
    "fragment_protocol_flags": int((fragments["project_protocol_flags"].fillna("") != "").sum()),
}
(ROOT / "completion_summary.json").write_text(json.dumps(completion, ensure_ascii=False, indent=2), encoding="utf-8")

report = f"""# M1 sequence-level assessment of the 29 constructed plasmids

## Scope

This run uses the 30-file SnapGene archive as the ordered construct inventory, excludes Q08 because it was not physically constructed, and analyzes Q01–Q07 and Q09–Q30. The separately supplied Q29 plasmid is used in place of the archive copy because it contains the complete annotated DMT coding region. The analysis is sequence based. It does not prove expression, folding, catalytic activity, localization, or phase separation in cells.

## What was computed

- SnapGene sequence and feature parsing for all 29 included plasmids.
- Recovery of AUG-initiated protein products supported by coding annotations and plasmid sequence.
- Molecular weight, theoretical pI, charge at pH 7, GRAVY, instability index, aromaticity, composition, sequence complexity, and hydrophobic-run statistics.
- Native IUPred2A long-mode predictions for full products and long annotated IDRs; short mode for annotated linkers.
- SignalP 6.0 slow-sequential eukaryotic predictions on the 21 unique products.
- DeepTMHMM 1.0 topology predictions on the 21 unique products.
- PSIPRED 4 single-sequence predictions on the 21 unique products.

## Main results

The 29 plasmids contain 35 recoverable annotated protein products representing 21 unique amino-acid sequences. Q07 is a non-coding sgRNA construct. The term *recoverable product* means that an AUG-initiated open reading frame can be reconstructed from the submitted plasmid and its annotations; it is not an expression claim.

SignalP classified all 21 unique products as `OTHER` (no N-terminal Sec/SPI signal peptide). DeepTMHMM predicted one transmembrane helix in each of Q10_P02 (residues 22–38) and Q13_P02 (residues 22–35), the two products annotated with an ER anchor. It predicted no transmembrane regions in the other 19 products. This is internally consistent with the design annotations, but it does not establish cellular localization experimentally.

Across the 12 unique annotated M1 fragments (two IDR sequences and ten linker sequences), no record crossed the project-declared negative-screen thresholds. Both IDRs are strongly disordered by IUPred2A: mean scores are 0.8040 and 0.8098, every residue is at or above 0.5, and their hydrophobic residue fractions are 0.1542 and 0.1502. The ten unique linker sequences are 5–20 aa long, have hydrophobic fraction 0, and have mean short-mode IUPred2A scores from 0.7776 to 1.0000. These thresholds are project-specific screens, not universal biological acceptance criteria.

PSIPRED was run in single-sequence mode because no sequence-profile database was used. Its full-product results are retained in `protein_products_complete.csv`, but short linker secondary-structure calls are not treated as reliable acceptance evidence; 5–20 aa peptides are too short for a defensible isolated PSIPRED screen.

## Sequence issues requiring human confirmation

1. **Q05:** the only AUG-initiated ORF overlapping the annotated DMT feature covers 633 of 1,080 nt. The submitted plasmid sequence therefore does not support a full-length DMT translation for that annotated region.
2. **Q21:** the filename says `delete N OC`, whereas the encoded project enzyme annotation is DMT.
3. **Q24:** the filename says DMT, whereas the encoded project enzyme annotation is `delete-N OC/BBE006`.
4. **Q29:** the standalone file is 5,320 bp and the archive copy is 5,314 bp. Only the standalone file contains the complete annotated DMT CDS, so it was used as the analysis source.

These are sequence/annotation conflicts. I cannot determine from the files alone whether the filenames or the encoded constructs reflect the wet-lab intent.

## Interpretation

The sequence-level design checks do not identify a hydrophobicity or signal-peptide reason to reject the recovered products. The only predicted transmembrane helices occur in the two explicitly ER-anchored products, at their N termini. The FUS-derived IDR segments have the expected strongly disordered, low-hydrophobicity character. The principal actionable result is construct identity: Q05, Q21, Q24, and the archive copy of Q29 should be reconciled against the wet-lab sample records before results are assigned to construct names.

## Files

- `construct_manifest.csv`: all 30 inventory entries and the Q08 exclusion.
- `protein_products_complete.csv`: complete per-product sequence metrics and three external-tool results.
- `m1_fragments.csv`: per-record IDR/linker metrics and project-protocol flags.
- `unique_protein_products.fasta`: input used for SignalP, DeepTMHMM, and PSIPRED.
- `server-tools/`: raw external-tool outputs.
- `figures/m1_sequence_profile.png` and `figures/m1_fragment_checks.png`: report-ready figures.
- `provenance.json`: software and threshold provenance.

## Reproducibility limits

The submitted `.dna` files are the source of truth for this run. SignalP and DeepTMHMM are licensed scientific tools and are therefore kept outside the public GALATEA repository. PSIPRED was run without sequence-profile generation, so it is explicitly reported as single-sequence prediction. No claim in this report substitutes for expression measurements or functional validation.
"""
(ROOT / "M1_REPORT.md").write_text(report, encoding="utf-8")

print(json.dumps(completion, ensure_ascii=False, indent=2))
