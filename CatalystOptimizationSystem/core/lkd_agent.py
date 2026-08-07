from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from CatalystOptimizationSystem.core.literature_qa import (
    DEFAULT_EVIDENCE_CSV,
    LiteratureQASystem,
    clean,
    is_unknown,
    low,
    short,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORE_DATABASE = PROJECT_ROOT / "essay" / "optimized_core_experimental_database_with_supplementary_excel_friendly.csv"


def _existing_default_database() -> Path:
    for candidate in (
        DEFAULT_EVIDENCE_CSV,
        PROJECT_ROOT / "essay" / "project_conditioned_evidence_database.csv",
        DEFAULT_CORE_DATABASE,
        PROJECT_ROOT / "essay" / "known_clean_database_for_showcase.csv",
        PROJECT_ROOT / "essay" / "aggregated_analysis_ready_database_with_supplementary.csv",
    ):
        if candidate.exists():
            return candidate
    return DEFAULT_EVIDENCE_CSV


UNKNOWN_TEXT = {"", "unknown", "nan", "none", "null", "n/a", "na", "not reported", "not specified"}


def _as_bool(value: Any) -> bool:
    return low(value) in {"true", "1", "yes", "y"}


def _num(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    if isinstance(value, (int, float)) and not pd.isna(value):
        return float(value)
    text = clean(value).replace(",", "")
    if not text or text.lower() in UNKNOWN_TEXT:
        return default
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not match:
        return default
    try:
        return float(match.group(0))
    except ValueError:
        return default


def _norm01(value: float, low_v: float, high_v: float, reverse: bool = False) -> float:
    if high_v <= low_v:
        return 0.0
    score = (value - low_v) / (high_v - low_v)
    score = max(0.0, min(1.0, score))
    return 1.0 - score if reverse else score


def _first(row: pd.Series, names: Iterable[str]) -> str:
    for name in names:
        if name in row:
            value = clean(row.get(name))
            if value and not is_unknown(value):
                return value
    return ""


def _row_text(row: pd.Series) -> str:
    fields = [
        "doi", "title", "title_clean", "project_tier", "project_subset_flags",
        "primary_result_metric", "primary_result_value", "primary_result_unit",
        "primary_result_evidence", "best_product_family", "best_canonical_host",
        "best_llps_component_value", "best_llps_trigger_value", "design_action_tags",
        "defect_risk_tags", "llps_transferability_class",
    ]
    return " ".join(clean(row.get(c)) for c in fields if c in row)


@dataclass(frozen=True)
class Component:
    component_id: str
    name: str
    category: str
    sequence: str
    source: str
    length: int
    evidence: str
    yeast_used: str
    llps_evidence: str
    reversibility_evidence: str
    growth_risk: str
    recommended_use: str
    priority: int

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


DEFAULT_COMPONENTS = [
    Component(
        "seed_fth1_core",
        "FTH1 24-mer Corelet seed",
        "nucleation_scaffold",
        "",
        "Corelets / ferritin-based multivalent seed literature",
        183,
        "Protocol 5.2 names FTH1 24-mer / Corelet seed as the primary nucleation scaffold.",
        "needs project validation in yeast",
        "high: multivalent seed lowers apparent phase-separation threshold",
        "light-dependent Corelets are reversible in source systems; project needs direct FRAP/perturbation validation",
        "medium: oligomeric burden and expression level must be tuned",
        "Use as the first scaffold seed; tune expression before adding enzymes.",
        1,
    ),
    Component(
        "idr_fusn",
        "FUS N-terminal low-complexity IDR",
        "idr_llps_driver",
        "",
        "FUS LC / FUSN LLPS literature",
        163,
        "Protocol 3.1 and 5.2 use FUSn IDR as the LLPS-driving module.",
        "reported in yeast models but project fusion context needs validation",
        "high: canonical low-complexity LLPS driver",
        "medium: fluidity depends on expression, phosphorylation state, partner and salt",
        "medium-high: overexpression can create aggregation-like puncta",
        "Use short/medium/long variants and require OFF-state microscopy before pathway integration.",
        1,
    ),
    Component(
        "recruit_ilid_sspb",
        "iLID-SspB",
        "controllable_recruitment",
        "",
        "Corelets optogenetic recruitment literature",
        125,
        "Protocol 5.2 lists iLID-SspB as a controllable recruitment module and 4.7 treats light control as backup.",
        "yeast use requires illumination and expression calibration",
        "indirect: recruits clients to multivalent scaffolds rather than being an LLPS driver alone",
        "high under illumination; persistence after light removal must be tested",
        "medium: light schedule and phototoxicity confound production assays",
        "Use as mechanism-control route, not first production route unless substrate sensing fails.",
        3,
    ),
    Component(
        "recruit_cry2",
        "CRY2-based optogenetic clustering",
        "controllable_recruitment",
        "",
        "Optogenetic clustering literature",
        498,
        "Protocol 5.2 lists CRY2 as an alternative controllable recruitment module.",
        "possible but must be calibrated in the selected chassis",
        "medium: clustering can nucleate condensates depending on fusion context",
        "medium: reversibility varies by variant and illumination",
        "medium-high: large domain can disturb enzyme fusion",
        "Keep as a backup mechanism-control route.",
        4,
    ),
    Component(
        "scaffold_sh3_pdz_gbd",
        "SH3/PDZ/GBD synthetic scaffold",
        "synthetic_scaffold",
        "",
        "Dueber-style synthetic scaffold literature",
        80,
        "Protocol 5.2 names SH3/PDZ/GBD scaffolds as multivalent scaffold options.",
        "mostly bacterial literature; yeast transfer needs calibration",
        "low-medium: scaffold colocalization is strong but not necessarily LLPS",
        "not an LLPS reversibility module by itself",
        "low-medium: modular but can over-recruit and lower flux",
        "Use as non-LLPS colocalization control or recruitment comparator.",
        2,
    ),
    Component(
        "linker_gs_flexible",
        "Flexible GS linker family",
        "linker",
        "GGGGS",
        "Protocol linker candidates and Dueber-style GS linkers",
        5,
        "Protocol 4.1 and 5.3 provide GS-rich linker candidates.",
        "generic",
        "not an LLPS component",
        "not applicable",
        "low: flexible but may lower effective localization if too long",
        "Use 10/15/20 aa variants for first-pass topology screen.",
        1,
    ),
    Component(
        "linker_eaaak_semirigid",
        "Semi-rigid EAAAK linker family",
        "linker",
        "EAAAK",
        "Common fusion-protein linker design prior",
        5,
        "Protocol 5.3 explicitly includes semi-rigid EAAAK linkers.",
        "generic",
        "not an LLPS component",
        "not applicable",
        "medium: rigidity can improve spacing but can constrain folding",
        "Use when GS linkers appear to occlude pockets or create excessive flexibility.",
        2,
    ),
]


class LkdAgent:
    """Protocol-aware local agent for dry-lab sections 5.1-5.6."""

    def __init__(self, evidence_csv: str | Path | None = None):
        self.evidence_csv = Path(evidence_csv or _existing_default_database())
        self.qa = LiteratureQASystem(self.evidence_csv)
        self.df = self.qa.df

    def status(self) -> dict[str, Any]:
        fields = {
            "5.1_literature_database": self.evidence_csv.exists(),
            "5.2_component_library": True,
            "5.3_linker_topology_library": True,
            "5.4_structure_safety_screen": True,
            "5.5_llps_propensity_screen": True,
            "5.6_partition_local_concentration_model": True,
        }
        return {
            "agent_status": "implemented_protocol_scaffold",
            "evidence_csv": str(self.evidence_csv),
            "evidence_rows": int(len(self.df)),
            "implemented_sections": fields,
            "note": (
                "Sections 5.2-5.6 are implemented as deterministic design and scoring modules. "
                "They produce ranked candidates and assumptions, but wet-lab calibration is still required."
            ),
        }

    def evidence(self, question: str, top_k: int = 8, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.qa.answer(question, top_k=top_k, filters=filters)

    def components(self, query: str = "", top_k: int = 20, include_defaults: bool = True) -> dict[str, Any]:
        query_low = low(query)
        items = [c.to_dict() for c in DEFAULT_COMPONENTS] if include_defaults else []
        evidence_hits = []
        if query:
            evidence_hits = self.qa.answer(query, top_k=min(top_k, 12), filters={"project_only": False})["evidence"]
        elif "best_llps_component_value" in self.df.columns:
            comp_rows = self.df[self.df["best_llps_component_value"].astype(str).str.strip().ne("")]
            for _, row in comp_rows.head(max(0, top_k - len(items))).iterrows():
                name = _first(row, ["best_llps_component_value", "llps_component_value", "llps_component"])
                if name and low(name) not in {low(x["name"]) for x in items}:
                    items.append({
                        "component_id": "evidence_" + str(abs(hash(name)))[:10],
                        "name": name,
                        "category": "evidence_mined_component",
                        "sequence": "",
                        "source": _first(row, ["doi", "title_clean", "title"]),
                        "length": None,
                        "evidence": short(_first(row, ["best_llps_component_evidence", "primary_result_evidence"]), 500),
                        "yeast_used": _first(row, ["best_canonical_host", "best_expression_host_value", "best_host_group"]),
                        "llps_evidence": _first(row, ["best_llps_state_value", "phase_regulation_direction_value"]),
                        "reversibility_evidence": "",
                        "growth_risk": _first(row, ["defect_risk_tags"]),
                        "recommended_use": _first(row, ["design_action_tags"]),
                        "priority": 5,
                    })
                    if len(items) >= top_k:
                        break
        if query_low:
            items = [
                item for item in items
                if query_low in low(" ".join(str(v) for v in item.values())) or not item.get("component_id", "").startswith("seed_")
            ][:top_k]
        return {
            "section": "5.2 LLPS component candidate library",
            "components": items[:top_k],
            "evidence_hits": evidence_hits,
            "selection_rule": "Prefer experimental evidence, simple constructs, short/low-burden modules and yeast-compatible records.",
        }

    def constructs(
        self,
        enzyme: str = "GgDMT1",
        top_k: int = 20,
        include_oc: bool = False,
        sbd_candidates: list[str] | None = None,
    ) -> dict[str, Any]:
        enzymes = [enzyme]
        if include_oc:
            enzymes.append("DeltaTM-GgOC1")
        sbd_candidates = sbd_candidates or ["SBD_candidate_A", "SBD_candidate_B"]
        linker_specs = [
            ("GS10", "GGGGSGGGGS", "flexible", 10),
            ("GS15", "GGGGSGGGGSGGGGS", "flexible", 15),
            ("GS20", "GGGGSGGGGSGGGGSGGGGS", "flexible", 20),
            ("EAAAK10", "EAAAKEAAAK", "semi_rigid", 10),
        ]
        topologies = []
        for enz in enzymes:
            tag_positions = ["N_terminal", "C_terminal"] if "DMT" in enz.upper() else ["C_terminal"]
            for tag_position in tag_positions:
                for linker_name, linker_sequence, linker_type, linker_length in linker_specs:
                    for recruitment in ["medium_affinity_ligand", "weak_affinity_ligand", "SspB_control"]:
                        for sbd in sbd_candidates if "DMT" in enz.upper() else ["not_applicable"]:
                            risk = []
                            if linker_type == "semi_rigid":
                                risk.append("rigid_linker_may_constrain_fold")
                            if tag_position == "N_terminal" and "OC" in enz.upper():
                                risk.append("OC_N_terminal_TM_boundary_risk")
                            if recruitment == "SspB_control":
                                risk.append("light_control_backup_not_main_substrate_sensor")
                            expected = []
                            if "DMT" in enz.upper():
                                expected.append("reduce_free_DMT_activity_in_OFF_state")
                                expected.append("increase_dense_phase_DMT_after_LLPS_ON")
                            else:
                                expected.append("keep_OC_near_core_without_forcing_OC_into_condensate")
                            score = 100
                            score -= 8 if linker_type == "semi_rigid" else 0
                            score -= 12 if recruitment == "SspB_control" else 0
                            score -= 5 if tag_position == "N_terminal" else 0
                            construct_id = f"{enz}_{tag_position}_{linker_name}_{recruitment}_{sbd}".replace(" ", "_")
                            topologies.append({
                                "construct_id": construct_id,
                                "enzyme": enz,
                                "tag_position": tag_position,
                                "linker_name": linker_name,
                                "linker_sequence": linker_sequence,
                                "linker_type": linker_type,
                                "linker_length_aa": linker_length,
                                "llps_component": "FUSn-SBD-autoinhibitory scaffold" if "DMT" in enz.upper() else "FTH1-Core proximal ligand",
                                "recruitment_module": recruitment,
                                "sbd_candidate": sbd,
                                "expected_effect": "; ".join(expected),
                                "risk_note": "; ".join(risk) if risk else "first_round_reasonable",
                                "priority_score": score,
                            })
        topologies.sort(key=lambda x: (-x["priority_score"], x["construct_id"]))
        return {
            "section": "5.3 linker and fusion-topology library",
            "constructs": topologies[:top_k],
            "controls": [
                "free_DMT_no_LLPS",
                "tagged_DMT_no_IDR",
                "empty_droplet",
                "constitutive_LLPS",
                "substrate_sensing_LLPS_OFF",
                "substrate_sensing_LLPS_ON",
            ],
            "rule": "First round keeps DMT as the primary recruited enzyme; OC fusion is treated cautiously and preferably C-terminal only.",
        }

    def structure_screen(self, candidates: list[dict[str, Any]] | None = None, top_k: int = 20) -> dict[str, Any]:
        candidates = candidates or self.constructs(top_k=top_k)["constructs"]
        screened = []
        for item in candidates:
            linker_len = _num(item.get("linker_length_aa"), 10.0) or 10.0
            pocket_sasa_ratio = _num(item.get("pocket_sasa_ratio"), None)
            pocket_rmsd = _num(item.get("pocket_rmsd_angstrom"), None)
            pae = _num(item.get("interdomain_pae_mean"), None)
            d_center = _num(item.get("d_center_nm"), None)
            clash = _num(item.get("clash_score"), 0.0) or 0.0

            penalties = []
            score = 100.0
            if pocket_sasa_ratio is not None and pocket_sasa_ratio < 0.85:
                score -= 30
                penalties.append("pocket_sasa_drop_gt_15_percent")
            if pocket_rmsd is not None and pocket_rmsd > 1.5:
                score -= 25
                penalties.append("pocket_rmsd_gt_1_5A")
            if d_center is not None and d_center < 3.0:
                score -= 20
                penalties.append("active_site_too_close_to_scaffold")
            if clash > 0:
                score -= min(30, clash * 5)
                penalties.append("steric_clash")
            if linker_len < 10:
                score -= 10
                penalties.append("linker_too_short")
            if linker_len > 25:
                score -= 6
                penalties.append("linker_may_reduce_localization")
            if pae is not None and pae > 20:
                score -= 5
                penalties.append("high_interdomain_pae_interpret_as_flexibility_or_uncertainty")

            out = dict(item)
            out.update({
                "structure_score": round(max(0.0, score), 2),
                "structure_decision": "pass" if score >= 70 else "review" if score >= 45 else "reject",
                "structure_flags": penalties,
                "required_inputs_for_strict_screen": [
                    "reference_pdb", "fusion_model_pdb", "active_site_residues",
                    "pocket_sasa_ratio", "pocket_rmsd_angstrom", "interdomain_pae_mean",
                    "d_center_nm", "clash_score",
                ],
            })
            screened.append(out)
        screened.sort(key=lambda x: (-x["structure_score"], x.get("construct_id", "")))
        return {
            "section": "5.4 structure safety screen",
            "screened_candidates": screened[:top_k],
            "interpretation": "This is a rule-based triage layer. AF3/structure-derived metrics must be supplied before a strict structural claim.",
        }

    def llps_score(self, sequences: list[dict[str, str]] | None = None) -> dict[str, Any]:
        if not sequences:
            sequences = [
                {"id": "FUSn_reference", "sequence": "SYGQQS" * 20 + "RGG" * 12},
                {"id": "GS_linker_control", "sequence": "GGGGSGGGGSGGGGS"},
                {"id": "EAAAK_linker_control", "sequence": "EAAAKEAAAK"},
            ]
        out = []
        for item in sequences:
            seq = re.sub(r"[^A-Za-z]", "", item.get("sequence", "")).upper()
            n = max(1, len(seq))
            gly = seq.count("G") / n
            arg = seq.count("R") / n
            aromatic = sum(seq.count(x) for x in "YFW") / n
            charged = sum(seq.count(x) for x in "DEKR") / n
            hydrophobic = sum(seq.count(x) for x in "AILMVPFWY") / n
            rgg = len(re.findall(r"RGG|RGR|GRG", seq))
            low_complexity = max(pd.Series(list(seq)).value_counts(normalize=True).max() if seq else 0.0, gly)
            idr_proxy = min(1.0, 0.35 + gly + 0.5 * low_complexity + 0.03 * rgg)
            sticker_score = min(1.0, 3.5 * aromatic + 0.05 * rgg)
            hydrophobic_penalty = max(0.0, hydrophobic - 0.38)
            score = 100 * (0.35 * idr_proxy + 0.25 * sticker_score + 0.2 * min(1, rgg / 8) + 0.2 * low_complexity)
            score -= 100 * hydrophobic_penalty
            if n < 20:
                score *= 0.55
            decision = "candidate_llps_driver" if score >= 55 else "weak_or_control" if score >= 25 else "unlikely_llps_driver"
            out.append({
                "id": item.get("id") or item.get("name") or "sequence",
                "length": len(seq),
                "idr_fraction_proxy": round(idr_proxy, 3),
                "low_complexity_score": round(float(low_complexity), 3),
                "aromatic_sticker_score": round(sticker_score, 3),
                "rgg_or_rgr_motif_count": int(rgg),
                "charge_fraction": round(charged, 3),
                "hydrophobic_fraction": round(hydrophobic, 3),
                "hydrophobic_penalty": round(hydrophobic_penalty, 3),
                "llps_compatibility_score": round(max(0.0, min(100.0, score)), 2),
                "decision": decision,
                "caveat": "Sequence heuristic only; use PSAP/Mpipi or measured phase diagrams for strict claims.",
            })
        out.sort(key=lambda x: -x["llps_compatibility_score"])
        return {
            "section": "5.5 LLPS propensity and phase-diagram pre-screen",
            "scores": out,
            "risk_flags": [
                "high_score_plus_high_hydrophobicity_may_be_aggregation",
                "low_score_but_structure_safe_can_be_negative_control",
                "high_LLPS_can_reduce_diffusion_or_sequester_enzyme",
            ],
        }

    def partition_model(
        self,
        enzyme_total: float = 1.0,
        phi_values: list[float] | None = None,
        kp_values: list[float] | None = None,
        free_activity_threshold: float = 0.25,
    ) -> dict[str, Any]:
        phi_values = phi_values or [0.01, 0.03, 0.05, 0.10]
        kp_values = kp_values or [5, 10, 50, 100, 200]
        rows = []
        for phi in phi_values:
            for kp in kp_values:
                if not 0 <= phi < 1 or kp <= 0:
                    continue
                dilute = enzyme_total / ((1 - phi) + kp * phi)
                dense = kp * dilute
                dense_share = (kp * dilute * phi) / enzyme_total if enzyme_total else 0.0
                leakage_risk = "high_free_DMT" if dilute > free_activity_threshold else "acceptable_free_DMT"
                saturation_risk = "dense_phase_overload" if dense > enzyme_total * 20 else "moderate"
                diffusion_risk = "large_phi_diffusion_risk" if phi >= 0.10 else "moderate"
                rows.append({
                    "phi": float(phi),
                    "Kp": float(kp),
                    "enzyme_total": float(enzyme_total),
                    "dense_DMT": round(float(dense), 6),
                    "dilute_DMT": round(float(dilute), 6),
                    "dense_fraction_of_total": round(float(dense_share), 6),
                    "saturation_risk": saturation_risk,
                    "diffusion_risk": diffusion_risk,
                    "leakage_risk": leakage_risk,
                })
        return {
            "section": "5.6 recruitment, partition and local-concentration model",
            "model": "[E]_dilute = [E]_total / ((1 - phi) + Kp * phi); [E]_dense = Kp * [E]_dilute",
            "rows": rows,
            "interpretation": "Use as a design plausibility filter. It does not prove yield improvement without kcat/Km, substrate partition and wet-lab calibration.",
        }

    def design(self, question: str = "Design a substrate-sensing LLPS system for Glabridin in yeast", top_k: int = 8) -> dict[str, Any]:
        evidence = self.evidence(question, top_k=top_k, filters={"project_only": True})
        components = self.components("FUS Corelet scaffold yeast LLPS enzyme", top_k=8)
        constructs = self.constructs(top_k=12)
        screened = self.structure_screen(constructs["constructs"], top_k=8)
        partition = self.partition_model()
        return {
            "agent": "LLPS-LKD-AI protocol agent",
            "question": question,
            "sections_used": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6"],
            "evidence_summary": evidence["answer"],
            "evidence": evidence["evidence"],
            "recommended_components": components["components"][:5],
            "recommended_constructs": screened["screened_candidates"][:5],
            "partition_prior": partition["rows"],
            "wet_lab_decision_gates": [
                "Do not enter pathway integration until free OC/DMT activity is confirmed.",
                "Reject designs with high OFF-state droplets before SBD switch optimization.",
                "Treat DMT as the first recruited enzyme; keep OC fusion conservative.",
                "Require FRAP or perturbation evidence before calling puncta LLPS.",
            ],
            "not_yet_automated": [
                "Boltz2 structure generation",
                "small-molecule docking for SBD candidates",
                "Mpipi/PSAP external execution",
                "closed-loop wet-lab result ingestion",
            ],
        }

    def agent_run(
        self,
        goal: str = "Design a substrate-sensing LLPS system for Glabridin in yeast",
        top_k: int = 8,
        run_external: bool = False,
        tool_inputs: dict[str, Any] | None = None,
        network_check: bool = False,
        max_steps: int = 10,
    ) -> dict[str, Any]:
        """Bounded tool-using agent loop for protocol 5.1-5.6.

        This differs from design(): each step is selected from current state,
        records observations, checks missing inputs, and can call external tools
        when strict inputs are present.
        """
        from CatalystOptimizationSystem.core.external_tools import ExternalToolRegistry

        registry = ExternalToolRegistry()
        trace: list[dict[str, Any]] = []
        state: dict[str, Any] = {
            "goal": goal,
            "tool_inputs": tool_inputs or {},
            "missing_inputs": [],
            "external_results": {},
        }

        def add(step: str, action: str, observation: Any, decision: str = "continue"):
            trace.append({
                "step": len(trace) + 1,
                "module": step,
                "action": action,
                "decision": decision,
                "observation": observation,
            })

        while len(trace) < max_steps:
            if "evidence" not in state:
                evidence = self.evidence(goal, top_k=top_k, filters={"project_only": True})
                state["evidence"] = evidence
                add("5.1", "retrieve_project_conditioned_evidence", {
                    "hits": len(evidence.get("evidence", [])),
                    "answer_prefix": short(evidence.get("answer"), 500),
                })
                continue

            if "components" not in state:
                components = self.components("FUS Corelet scaffold yeast LLPS enzyme", top_k=max(8, top_k))
                state["components"] = components
                add("5.2", "select_llps_components", {
                    "components": [x.get("name") for x in components.get("components", [])[:5]],
                })
                continue

            if "constructs" not in state:
                constructs = self.constructs(top_k=max(12, top_k))
                state["constructs"] = constructs
                add("5.3", "enumerate_constructs_and_linkers", {
                    "construct_count": len(constructs.get("constructs", [])),
                    "top_construct": (constructs.get("constructs") or [{}])[0].get("construct_id"),
                })
                continue

            if "tool_health" not in state:
                health = registry.health(network=network_check)
                state["tool_health"] = health
                probes = health.get("external_tool_probes", {})
                callable_tools = [name for name, item in probes.items() if item.get("callable")]
                missing_tools = [name for name, item in probes.items() if not item.get("available")]
                add("tool_registry", "probe_external_tools", {
                    "callable_tools": callable_tools,
                    "missing_tools": missing_tools,
                    "network_checked": network_check,
                })
                continue

            if run_external and "external_execution" not in state:
                requested = set((tool_inputs or {}).keys())
                if not requested:
                    state["missing_inputs"].extend([
                        "boltz2.sequence or boltz2.chains for structure generation",
                        "mpipi/psap.sequences for strict LLPS prediction",
                        "autodock_vina receptor_pdbqt, ligand_pdbqt, center for docking",
                    ])
                    state["external_execution"] = {"run_external": True, "results": {}}
                    add("tool_executor", "skip_external_tools_missing_inputs", state["missing_inputs"], "need_user_or_file_inputs")
                else:
                    external = registry.run_requested_tools(tool_inputs or {}, run_external=True)
                    state["external_execution"] = external
                    state["external_results"] = external.get("results", {})
                    add("tool_executor", "run_requested_external_tools", {
                        name: {
                            "ok": item.get("ok"),
                            "status": item.get("status"),
                            "error_type": item.get("error_type"),
                            "output_dir": item.get("output_dir"),
                        }
                        for name, item in state["external_results"].items()
                    })
                continue

            if "structure_screen" not in state:
                candidates = state["constructs"]["constructs"]
                state["structure_screen"] = self.structure_screen(candidates, top_k=top_k)
                add("5.4", "screen_structure_safety", {
                    "top_decision": (state["structure_screen"].get("screened_candidates") or [{}])[0].get("structure_decision"),
                    "strict_external_metrics_used": bool(state.get("external_results", {}).get("boltz2", {}).get("ok")),
                })
                continue

            if "llps_score" not in state:
                llps_sequences = None
                for key in ("mpipi", "psap"):
                    if key in (tool_inputs or {}):
                        llps_sequences = (tool_inputs or {}).get(key, {}).get("sequences")
                        break
                state["llps_score"] = self.llps_score(llps_sequences)
                add("5.5", "score_llps_propensity", {
                    "score_count": len(state["llps_score"].get("scores", [])),
                    "strict_external_prediction_used": any(
                        state.get("external_results", {}).get(k, {}).get("ok") for k in ("mpipi", "psap")
                    ),
                })
                continue

            if "partition_model" not in state:
                state["partition_model"] = self.partition_model()
                add("5.6", "model_partition_and_local_concentration", {
                    "grid_rows": len(state["partition_model"].get("rows", [])),
                })
                continue

            break

        evidence = state.get("evidence", {})
        screened = state.get("structure_screen", {})
        partition = state.get("partition_model", {})
        return {
            "agent": "LLPS-LKD-AI autonomous tool-using agent",
            "goal": goal,
            "mode": "agent_loop_with_tool_registry",
            "run_external": run_external,
            "network_check": network_check,
            "trace": trace,
            "final_answer": {
                "evidence_summary": evidence.get("answer"),
                "recommended_constructs": screened.get("screened_candidates", [])[:5],
                "llps_scores": state.get("llps_score", {}).get("scores", [])[:5],
                "partition_prior": partition.get("rows", [])[:10],
                "missing_inputs": state.get("missing_inputs", []),
                "external_results": state.get("external_results", {}),
            },
            "agentic_features": [
                "plans next action from current state",
                "probes tool availability before execution",
                "executes only tools with explicit inputs",
                "records trace observations and stop decisions",
                "keeps missing-input list instead of fabricating external results",
            ],
        }


_CACHE: dict[str, LkdAgent] = {}


def get_agent(evidence_csv: str | Path | None = None) -> LkdAgent:
    path = str(Path(evidence_csv or _existing_default_database()).resolve())
    agent = _CACHE.get(path)
    if agent is None:
        agent = LkdAgent(path)
        _CACHE[path] = agent
    return agent
