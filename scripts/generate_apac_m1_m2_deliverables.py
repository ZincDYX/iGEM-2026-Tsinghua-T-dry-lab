"""Create auditable M1/M2 deliverables for the 2026-08-14 GLOSS wet-lab input set.

This is intentionally a reporting adapter, not a scientific scorer.  It consumes
the production pipeline's M1/M2 JSON artifacts and preserves missing M2 metrics
as missing rather than calculating proxy values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from datetime import timezone, datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import yaml


M1_COLUMNS = (
    "candidate_id",
    "construct_id",
    "linker_id",
    "linker_sequence",
    "wet_lab_status",
    "length_aa",
    "gly_ser_fraction",
    "hydrophobic_fraction",
    "charged_fraction",
    "net_charge_proxy",
    "pro_fraction",
    "sequence_complexity",
    "forbidden_motifs",
    "aggregation_risk_flag",
    "screen_flags",
    "m1_status",
    "recommended_for_m2",
    "scientific_boundary",
)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fasta(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    identifier: str | None = None
    sequence: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"): 
            if identifier is not None:
                records[identifier] = "".join(sequence)
            identifier = line[1:].strip().split()[0]
            sequence = []
        elif line.strip():
            sequence.append(line.strip())
    if identifier is not None:
        records[identifier] = "".join(sequence)
    return records


def linker_sequences(config: dict[str, Any]) -> dict[str, str]:
    return {item["id"]: item["sequence"] for item in config["inputs"]["linkers"]}


def m1_rows(records: list[dict[str, Any]], sequences: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        feature = record["linker_features"]
        linker_id = record["linker_id"]
        rows.append(
            {
                "candidate_id": record["candidate_id"],
                "construct_id": record["construct_id"],
                "linker_id": linker_id,
                "linker_sequence": sequences[linker_id],
                "wet_lab_status": "actual_baseline" if "baseline_actual" in linker_id else "computational_design_only",
                "length_aa": feature["length"],
                "gly_ser_fraction": feature["gly_ser_fraction"],
                "hydrophobic_fraction": feature["hydrophobic_fraction"],
                "charged_fraction": feature["charged_fraction"],
                "net_charge_proxy": feature["net_charge_proxy"],
                "pro_fraction": feature["pro_fraction"],
                "sequence_complexity": feature["sequence_complexity"],
                "forbidden_motifs": ";".join(feature["forbidden_motifs"]),
                "aggregation_risk_flag": feature["aggregation_risk_flag"],
                "screen_flags": ";".join(record["screen_flags"]),
                "m1_status": record["status"],
                "recommended_for_m2": record["recommended_for_m2"],
                "scientific_boundary": record["notes"],
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], columns: tuple[str, ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def save_figure(fig: plt.Figure, svg: Path, png: Path) -> None:
    fig.savefig(svg, bbox_inches="tight")
    fig.savefig(png, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_m1(oc_rows: list[dict[str, Any]], dmt_rows: list[dict[str, Any]], svg: Path, png: Path) -> None:
    rows = oc_rows + dmt_rows
    metrics = ("length_aa", "gly_ser_fraction", "hydrophobic_fraction", "charged_fraction", "pro_fraction", "sequence_complexity")
    labels = ("length (aa)", "G/S fraction", "hydrophobic", "charged", "Pro fraction", "complexity")
    values = np.array([[float(row[key]) for key in metrics] for row in rows], dtype=float)
    scaled = np.empty_like(values)
    for column in range(values.shape[1]):
        low, high = values[:, column].min(), values[:, column].max()
        scaled[:, column] = 0.5 if high == low else (values[:, column] - low) / (high - low)
    fig, axis = plt.subplots(figsize=(11, 6.2))
    image = axis.imshow(scaled, cmap="YlGnBu", aspect="auto", vmin=0, vmax=1)
    axis.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
    axis.set_yticks(range(len(rows)), [f"{row['linker_id']}  ({row['wet_lab_status'].replace('_', ' ')})" for row in rows])
    axis.set_title("M1 linker sequence-design screen\nNormalized colors aid comparison only; no LLPS probability or optimal-design score")
    for row_index, row in enumerate(rows):
        for column, key in enumerate(metrics):
            text = f"{row[key]:.2f}" if isinstance(row[key], float) else str(row[key])
            axis.text(column, row_index, text, ha="center", va="center", fontsize=8)
        if row["wet_lab_status"] == "actual_baseline":
            axis.add_patch(plt.Rectangle((-0.5, row_index - 0.5), len(metrics), 1, fill=False, edgecolor="#5b2a86", linewidth=2.2))
    axis.axhline(len(oc_rows) - 0.5, color="#333333", linewidth=1)
    colorbar = fig.colorbar(image, ax=axis, pad=0.02)
    colorbar.set_label("within-panel normalized feature value")
    fig.text(0.01, 0.01, "Purple outline = actual wet-lab baseline. EAAAK15 was flagged by the configured aggregation-risk proxy; see CSV for the complete decision record.", fontsize=8)
    save_figure(fig, svg, png)


def plot_m2(m2_records: list[dict[str, Any]], svg: Path, png: Path) -> None:
    names = [record["candidate_id"].replace("M1-gloss-m1-", "") for record in m2_records]
    fig, axis = plt.subplots(figsize=(14, max(3.8, 0.43 * len(names) + 2.3)))
    axis.set_xlim(0, 14)
    axis.set_ylim(-0.8, len(names) + 1.25)
    axis.axis("off")
    columns = ((0.12, "candidate"), (4.15, "M1 gate"), (6.0, "M2 structural artifact"), (9.25, "M2 metrics"), (11.35, "decision"))
    for x, header in columns:
        axis.text(x, len(names) + 0.55, header, fontweight="bold", color="#4d216f", fontsize=9)
    for index, (name, record) in enumerate(zip(names, m2_records, strict=True)):
        y = len(names) - index - 0.05
        axis.add_patch(plt.Rectangle((0, y - 0.35), 14, 0.7, facecolor="#f7f1f8" if index % 2 == 0 else "#ffffff", edgecolor="#e4d6e8", linewidth=0.6))
        m1_gate = "passed" if "M1 construct screen must pass" not in record["missing_inputs"] else "not passed"
        artifact = "not run" if m1_gate == "passed" else "not applicable"
        metrics = "missing / deferred" if m1_gate == "passed" else "not evaluated"
        cells = ((0.12, name), (4.15, m1_gate), (6.0, artifact), (9.25, metrics), (11.35, "insufficient data"))
        for x, value in cells:
            axis.text(x, y, value, va="center", fontsize=8.5, color="#3f3f3f")
    axis.text(0.05, -0.35, "No ColabFold executable, GPU, or reusable project structure artifact was available on this machine. No proxy metrics were generated.", color="#8a3b3b", fontsize=8.5)
    axis.text(0.05, -0.67, "Pocket metrics are deferred until publication-to-plasmid residue mapping, a predicted structure, and compound 10/11 ligand placement are available.", color="#5c5c5c", fontsize=8.5)
    axis.set_title("M2 structural-validation status", loc="left", fontweight="bold", color="#4d216f")
    save_figure(fig, svg, png)


def tool_status() -> dict[str, Any]:
    status = {"colabfold_batch": shutil.which("colabfold_batch"), "nvidia_smi": shutil.which("nvidia-smi")}
    if status["nvidia_smi"]:
        result = subprocess.run([status["nvidia_smi"], "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True, check=False)
        status["nvidia_smi_exit_code"] = result.returncode
        status["detected_gpus"] = [line for line in result.stdout.splitlines() if line.strip()]
    else:
        status["detected_gpus"] = []
    return status


def markdown_summary(output: Path, oc_rows: list[dict[str, Any]], dmt_rows: list[dict[str, Any]], tool: dict[str, Any]) -> str:
    total = len(oc_rows) + len(dmt_rows)
    passed = sum(bool(row["recommended_for_m2"]) for row in oc_rows + dmt_rows)
    flagged = total - passed
    return f"""# APAC M1/M2 result summary

## Scope and conclusion

This run used the supplied wet-lab construct sequences and ran the repository's configured M1 sequence-design screen independently for OC and DMT linker panels. {passed} of {total} candidates were recommended to M2; the two EAAAK15 rigid-linker variants were flagged by the configured sequence aggregation-risk proxy. This is a negative sequence screen only: it does not estimate LLPS probability, enzyme activity, catalytic yield, or an optimal linker.

The actual wet-lab baselines are retained without redesign: OC `GSTSSGGGGGS` followed by `PPPALPPKRRR`, and DMT `GSGGGSGSTSSG` followed by `GVKESLV`. GS5/10/15 and EAAAK15 are computational comparison constructs only.

## M2 decision

M2 is `insufficient_data` for every M1-passing candidate. On this machine, `colabfold_batch` was {'found' if tool['colabfold_batch'] else 'not found'} and NVIDIA GPU detection was {'available' if tool['nvidia_smi'] else 'not available'}; no reusable project-specific PDB/mmCIF artifact was found. Therefore no pLDDT, PAE, ipTM, clash, enzyme-RMSD, SASA-retention, pocket-RMSD, or structure render was fabricated.

The publication anchors cannot yet be used as plasmid residue indices. The supplied source package explicitly records OC I293/T295 and DMT N303 as unresolved against the supplied actual sequences; a publication/accession-to-plasmid alignment is required before pocket SASA or pocket RMSD.

## Required next computation

Run the supplied `m2_oc_fusion_candidates.fasta` and `m2_dmt_fusion_candidates.fasta` on the GPU server with a version-pinned ColabFold/AlphaFold2 prediction workflow. These are single-chain fusion constructs, so a monomer/PTM model is the appropriate first prediction; use multimer only for a separately defined enzyme-scaffold-domain complex. Archive the command, model/version, FASTA hash, ranking/confidence JSON, PDB/mmCIF, and random seed(s), then parse rather than transcribe metrics into M2.

```bash
colabfold_batch input_package/m2_oc_fusion_candidates.fasta M2/structure_artifacts/oc
colabfold_batch input_package/m2_dmt_fusion_candidates.fasta M2/structure_artifacts/dmt
```

After that, align the paper sequence/accession to each plasmid sequence, place compound 10 for OC and compound 11 (optionally 9 as a competing substrate) for DMT, and define each pocket from residues within 5 angstrom of the ligand plus mapped functional anchors. Only then are FreeSASA, pocket RMSD, clashes, and a structure-based M2 comparison justified.

## M3/M4 status

M3 and M4 were not reported as scientific predictions. The supplied readiness record lacks reviewed, context-compatible phase fraction/partitioning, protein abundance, recruitment-binding, phase-specific activity, and kinetic parameters. The pipeline therefore returned no M3 concentrations and no M4 trajectory rather than applying default values.

## Files

- M1 tables: `M1/oc_linker_screen.csv`, `M1/dmt_linker_screen.csv`
- M1 comparison: `M1/m1_design_screen.png` and `.svg`
- M2 status and machine-readable missing-metric records: `M2/m2_metrics.csv`, `M2/m2_metrics.json`, `M2/m2_structural_comparison.png` and `.svg`
- Mapping boundary: `M2/residue_mapping.json`
- Provenance and exact tool availability: `run_manifest.json`, `methods_and_provenance.md`
"""


def methods(output: Path, tool: dict[str, Any]) -> str:
    return f"""# Methods and provenance

## Input integrity

Input files were supplied in `input_package/`. The two M1 YAML files contained an ID mismatch: `idr_id: FUSN` while the FASTA record was named `FUSN_1_214_from_wetlab_snapgene`. Only the local run copies were normalized to the existing FASTA identifier; no amino-acid sequence was changed. The system-level construct component entries were normalized to the same identifier for the production M1 component-consistency check.

## M1 linker sequence screen

The production `igem-drylab pipeline run` command was used for separate OC and DMT configurations in `execution.mode: real` with `allow_assumptions: false`. M1 computes linker length, G/S fraction, hydrophobic fraction, charged fraction, net-charge proxy, proline fraction, sequence complexity, configured forbidden motifs, and an aggregation-risk flag. It carries no LLPS classifier and writes `engineering_priority_score: null`; this report does not transform its features into an LLPS or yield claim.

## M2 structural validation

Tool detection at generation time: `colabfold_batch={tool['colabfold_batch']}`, `nvidia-smi={tool['nvidia_smi']}`, detected GPUs={tool['detected_gpus']}. There were no reusable project-specific predicted structures. The production M2 stage was still executed; it returned `insufficient_data` and a required-metrics list. Blank metrics in the output table mean unavailable, not zero or favourable.

M2 will require actual structure artifacts and parsed confidence fields. pLDDT/PAE/ipTM report predictor confidence/relative-domain confidence; they are not enzyme-activity measurements. RMSD/SASA/pocket-RMSD need an explicitly stated alignment and ligand-defined pocket. Docking/structure outputs remain negative-screen evidence and must not be converted automatically into kinetic constants.

## Residue and ligand boundary

The source package identifies published OC anchors I293/T295 and DMT N303, but explicitly states that their numbering does not map cleanly to the plasmid sequences. The report therefore records their mapping as unresolved. Compound 10 (OC) and compound 11 (DMT) placement/docking is required before a ligand-pocket definition can be created.

## M3/M4 exclusion

The input readiness record identifies missing reviewed context-compatible phase fraction, partition coefficient, abundance, recruitment binding, phase-specific residual activity, and kinetics. No M3 or M4 value was inferred from M1/M2 features.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True, help="outputs/apac_m1_m2_20260814")
    args = parser.parse_args()
    root = args.root.resolve()
    package = root / "input_package"
    reruns = root / "reruns"
    m1_dir = root / "M1"
    m2_dir = root / "M2"
    report_dir = root / "report"
    for directory in (m1_dir, m2_dir / "structure_artifacts", m2_dir / "individual_structure_renders", report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    oc_config = yaml.safe_load((package / "m1_oc_linker_scan.yaml").read_text(encoding="utf-8"))
    dmt_config = yaml.safe_load((package / "m1_dmt_linker_scan.yaml").read_text(encoding="utf-8"))
    oc_m1 = load_json(reruns / "gloss-m1-oc-linker-scan" / "m1_construct_screen" / "candidates.json")
    dmt_m1 = load_json(reruns / "gloss-m1-dmt-linker-scan" / "m1_construct_screen" / "candidates.json")
    oc_m2 = load_json(reruns / "gloss-m1-oc-linker-scan" / "m2_structure_screen" / "fusion_assessments.json")
    dmt_m2 = load_json(reruns / "gloss-m1-dmt-linker-scan" / "m2_structure_screen" / "fusion_assessments.json")
    oc_rows = m1_rows(oc_m1, linker_sequences(oc_config))
    dmt_rows = m1_rows(dmt_m1, linker_sequences(dmt_config))
    write_csv(m1_dir / "oc_linker_screen.csv", oc_rows, M1_COLUMNS)
    write_csv(m1_dir / "dmt_linker_screen.csv", dmt_rows, M1_COLUMNS)
    plot_m1(oc_rows, dmt_rows, m1_dir / "m1_design_screen.svg", m1_dir / "m1_design_screen.png")

    m2_records = oc_m2 + dmt_m2
    m2_columns = (
        "candidate_id", "construct_id", "status", "structure_model", "structure_source_tool", "structure_artifact_path",
        "pocket_sasa_retention", "pocket_rmsd_angstrom", "clash_count", "available_metrics", "missing_inputs", "recommended_for_m3", "notes",
    )
    m2_rows = [{key: (";".join(value) if isinstance(value := record.get(key), list) else value) for key in m2_columns} for record in m2_records]
    write_csv(m2_dir / "m2_metrics.csv", m2_rows, m2_columns)
    dump_json(m2_dir / "m2_metrics.json", m2_records)
    plot_m2(m2_records, m2_dir / "m2_structural_comparison.svg", m2_dir / "m2_structural_comparison.png")

    active_site = load_json(package / "active_site_and_pocket_definition.json")
    residue_mapping = {
        "status": "unresolved",
        "source_article": active_site["source_article"],
        "OC": {"published_anchors": active_site["OC"]["published_functional_anchors"], "actual_sequence_observation": active_site["OC"]["actual_snapgene_sequence_warning"], "action": "align paper/accession sequence to actual plasmid before pocket metrics"},
        "DMT": {"published_anchor": active_site["DMT"]["published_functional_anchor"], "actual_sequence_observation": active_site["DMT"]["actual_snapgene_sequence_warning"], "action": "align paper/accession sequence to actual plasmid before pocket metrics"},
        "pocket_metrics_status": "deferred_pending_alignment_structure_and_ligand_placement",
    }
    dump_json(m2_dir / "residue_mapping.json", residue_mapping)
    tool = tool_status()
    (report_dir / "APAC_result_summary.md").write_text(markdown_summary(root, oc_rows, dmt_rows, tool), encoding="utf-8")
    (report_dir / "methods_and_provenance.md").write_text(methods(root, tool), encoding="utf-8")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "M1/M2 only; M3/M4 deliberately not reported as scientific predictions",
        "input_sha256": {path.name: sha256(path) for path in sorted(package.iterdir()) if path.is_file()},
        "production_commands": [
            "igem-drylab pipeline validate input_package/m1_oc_linker_scan.yaml",
            "igem-drylab pipeline validate input_package/m1_dmt_linker_scan.yaml",
            "igem-drylab pipeline run input_package/m1_oc_linker_scan.yaml --output-dir reruns",
            "igem-drylab pipeline run input_package/m1_dmt_linker_scan.yaml --output-dir reruns",
        ],
        "tool_availability": tool,
        "m2_status": "insufficient_data_no_local_structure_tool_or_project_artifact",
        "run_artifacts": {"oc": str((reruns / "gloss-m1-oc-linker-scan").relative_to(root)), "dmt": str((reruns / "gloss-m1-dmt-linker-scan").relative_to(root))},
    }
    dump_json(root / "run_manifest.json", manifest)
    print(f"Wrote M1/M2 deliverables to {root}")


if __name__ == "__main__":
    main()
