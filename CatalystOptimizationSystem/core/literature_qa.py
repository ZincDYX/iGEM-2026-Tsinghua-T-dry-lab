from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE_CSV = PROJECT_ROOT / "essay" / "project_conditioned_evidence_database.csv"

UNKNOWN = {"", "unknown", "none", "null", "nan", "n/a", "na", "not specified", "not available"}


def clean(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def low(value: object) -> str:
    return clean(value).lower()


def is_unknown(value: object) -> bool:
    return low(value) in UNKNOWN


def first_known(row: pd.Series, *fields: str) -> str:
    for field in fields:
        if field in row:
            value = clean(row.get(field))
            if value and not is_unknown(value):
                return value
    return ""


def short(text: object, limit: int = 420) -> str:
    value = clean(text)
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


def parse_bool(value: object) -> bool:
    return low(value) in {"true", "1", "yes", "y"}


@dataclass
class EvidenceHit:
    row_index: int
    score: float
    title: str
    doi: str
    project_tier: str
    flags: str
    metric: str
    value: str
    unit: str
    evidence: str
    design_actions: str
    defect_risks: str
    transferability: str
    trigger_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_index": self.row_index,
            "score": round(float(self.score), 4),
            "title": self.title,
            "doi": self.doi,
            "project_tier": self.project_tier,
            "project_subset_flags": self.flags,
            "primary_result_metric": self.metric,
            "primary_result_value": self.value,
            "primary_result_unit": self.unit,
            "evidence": self.evidence,
            "design_action_tags": self.design_actions,
            "defect_risk_tags": self.defect_risks,
            "llps_transferability_class": self.transferability,
            "llps_project_trigger_class": self.trigger_class,
        }


class LiteratureQASystem:
    """Local evidence-grounded QA over the project-conditioned literature database."""

    def __init__(self, evidence_csv: str | Path = DEFAULT_EVIDENCE_CSV, max_rows: int | None = None):
        self.evidence_csv = Path(evidence_csv)
        if not self.evidence_csv.exists():
            raise FileNotFoundError(f"evidence csv not found: {self.evidence_csv}")
        self.df = pd.read_csv(self.evidence_csv, encoding="utf-8-sig", nrows=max_rows, low_memory=False)
        self.df = self.df.fillna("")
        self._prepare_text_index()

    def _prepare_text_index(self) -> None:
        searchable_cols = [
            "title_clean",
            "title",
            "doi",
            "project_tier",
            "project_subset_flags",
            "condition_prior_scope",
            "defect_risk_tags",
            "design_action_tags",
            "llps_transferability_class",
            "llps_project_trigger_class",
            "primary_result_metric",
            "primary_result_value",
            "primary_result_unit",
            "primary_result_evidence",
            "best_canonical_product",
            "best_product_family",
            "best_canonical_host",
            "best_host_group",
            "best_enzyme_name_value",
            "best_expression_host_value",
            "best_substrate_name_value",
            "best_main_product_name_value",
            "best_llps_component_value",
            "best_llps_state_value",
            "best_llps_trigger_value",
            "best_llps_component_evidence",
            "best_llps_state_evidence",
            "best_llps_trigger_evidence",
        ]
        cols = [c for c in searchable_cols if c in self.df.columns]
        text = self.df[cols].astype(str).agg(" ".join, axis=1) if cols else pd.Series([""] * len(self.df))
        self.search_text = text.tolist()
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            token_pattern=r"(?u)\b[\w\-/+.]+\b",
        )
        self.matrix = self.vectorizer.fit_transform(self.search_text)

    def answer(
        self,
        question: str,
        top_k: int = 8,
        filters: dict[str, Any] | None = None,
        llm_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        question = clean(question)
        if not question:
            raise ValueError("question required")
        filters = filters or {}
        top_k = max(1, min(int(top_k or 8), 30))
        mask = self._build_filter_mask(question, filters)
        hits = self._retrieve(question, top_k=top_k, mask=mask)
        decision = self._make_decision(question, hits, mask)
        local_answer = decision["answer"]
        result = {
            "question": question,
            "evidence_csv": str(self.evidence_csv),
            "answer": local_answer,
            "local_answer": local_answer,
            "recommendations": decision["recommendations"],
            "risks": decision["risks"],
            "suggested_next_experiments": decision["suggested_next_experiments"],
            "query_interpretation": decision["query_interpretation"],
            "evidence": [hit.to_dict() for hit in hits],
            "llm_used": False,
            "llm_model": "",
            "provenance_note": "Every evidence item keeps row_index, DOI/title and evidence text from the conditioned literature database.",
        }
        if llm_config and llm_config.get("use_llm"):
            try:
                llm_answer = self._answer_with_llm(question, hits, decision, llm_config)
                result["answer"] = llm_answer
                result["llm_answer"] = llm_answer
                result["llm_used"] = True
                result["llm_model"] = clean(llm_config.get("model") or "deepseek-chat")
            except Exception as ex:
                result["llm_error"] = str(ex)
        return result

    def _answer_with_llm(
        self,
        question: str,
        hits: list[EvidenceHit],
        decision: dict[str, Any],
        llm_config: dict[str, Any],
    ) -> str:
        api_key = clean(llm_config.get("api_key"))
        if not api_key:
            raise ValueError("llm api_key required when use_llm is true")
        if not hits:
            raise ValueError("no retrieved evidence available for grounded LLM answer")

        base_url = clean(llm_config.get("base_url")) or "https://api.deepseek.com/v1/chat/completions"
        model = clean(llm_config.get("model")) or "deepseek-chat"
        temperature = float(llm_config.get("temperature", 0.15))
        timeout = int(llm_config.get("timeout", 120))
        max_tokens = int(llm_config.get("max_tokens", 1600))

        evidence_block = self._format_evidence_block(hits)
        local_block = json.dumps(
            {
                "local_recommendations": decision["recommendations"],
                "local_risks": decision["risks"],
                "local_next_experiments": decision["suggested_next_experiments"],
                "query_interpretation": decision["query_interpretation"],
            },
            ensure_ascii=False,
            indent=2,
        )
        system = (
            "You are an evidence-grounded literature QA and design-support assistant for an iGEM "
            "Yeast + Glabridin + LLPS-enzyme project. Answer ONLY from the supplied retrieved evidence "
            "and the local rule summary. Do not use outside knowledge. Do not invent DOI, title, row_index, "
            "numeric values, mechanisms, or claims. If evidence is insufficient, state the limitation clearly. "
            "Cite supporting evidence inline using [row <row_index>; DOI <doi>] after each important claim. "
            "Return concise Chinese Markdown with sections: 结论, 决策建议, 风险与不确定性, 下一步实验, 证据溯源."
        )
        user = (
            f"用户问题:\n{question}\n\n"
            f"本地规则化摘要:\n{local_block}\n\n"
            f"检索到的证据包:\n{evidence_block}\n\n"
            "请只基于上面的证据回答。若某个建议没有证据支持，请明确标注为证据不足，不要补充证据外事实。"
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            base_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as ex:
            detail = ex.read().decode("utf-8", errors="replace")[:800]
            raise RuntimeError(f"DeepSeek API HTTP {ex.code}: {detail}") from ex
        except urllib.error.URLError as ex:
            raise RuntimeError(f"DeepSeek API request failed: {ex}") from ex

        try:
            parsed = json.loads(raw)
            return clean(parsed["choices"][0]["message"]["content"])
        except Exception as ex:
            raise RuntimeError(f"failed to parse DeepSeek response: {raw[:800]}") from ex

    def _format_evidence_block(self, hits: list[EvidenceHit]) -> str:
        blocks = []
        for hit in hits:
            blocks.append(
                "\n".join(
                    [
                        f"[row {hit.row_index}]",
                        f"score: {hit.score:.4f}",
                        f"title: {hit.title or 'NA'}",
                        f"doi: {hit.doi or 'NA'}",
                        f"tier: {hit.project_tier or 'NA'}",
                        f"flags: {hit.flags or 'NA'}",
                        f"metric: {hit.metric or 'NA'}",
                        f"value: {hit.value or 'NA'} {hit.unit or ''}".strip(),
                        f"evidence: {hit.evidence or 'NA'}",
                        f"design_actions: {hit.design_actions or 'NA'}",
                        f"defect_risks: {hit.defect_risks or 'NA'}",
                        f"llps_transferability: {hit.transferability or 'NA'}",
                        f"llps_trigger_class: {hit.trigger_class or 'NA'}",
                    ]
                )
            )
        return "\n\n---\n\n".join(blocks)

    def _build_filter_mask(self, question: str, filters: dict[str, Any]) -> pd.Series:
        mask = pd.Series(True, index=self.df.index)
        q = low(question)
        if filters.get("project_only", True):
            mask &= self._str_col("project_tier").ne("Background | broad literature prior")
        if filters.get("yeast") or any(x in q for x in ["yeast", "saccharomyces"]):
            mask &= self._bool_col("is_project_yeast")
        if filters.get("llps") or any(x in q for x in ["llps", "condensate", "phase separation", "phase transition", "droplet"]):
            mask &= self._bool_col("is_project_llps_related")
        if filters.get("llps_enzyme") or any(x in q for x in ["llps-enzyme", "enzyme condensate", "enzyme llps"]):
            mask &= self._bool_col("is_project_llps_enzyme")
        if filters.get("glabridin") or "glabridin" in q:
            mask &= self._bool_col("is_project_glabridin_direct")
        if filters.get("flavonoid") or any(x in q for x in ["flavonoid", "isoflavonoid", "pterocarpan"]):
            mask &= self._bool_col("is_project_flavonoid_related")
        if filters.get("high_transfer_llps"):
            mask &= self._bool_col("is_project_high_transfer_llps")
        trigger = filters.get("trigger_class")
        if trigger and "llps_project_trigger_class" in self.df.columns:
            mask &= self.df["llps_project_trigger_class"].astype(str).str.contains(str(trigger), case=False, na=False)
        if not mask.any():
            return pd.Series(True, index=self.df.index)
        return mask

    def _bool_col(self, name: str) -> pd.Series:
        if name not in self.df.columns:
            return pd.Series(False, index=self.df.index)
        return self.df[name].map(parse_bool)

    def _str_col(self, name: str) -> pd.Series:
        if name not in self.df.columns:
            return pd.Series("", index=self.df.index)
        return self.df[name].astype(str)

    def _retrieve(self, question: str, top_k: int, mask: pd.Series) -> list[EvidenceHit]:
        query_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(query_vec, self.matrix).ravel()
        if mask is not None:
            scores = scores.copy()
            scores[~mask.to_numpy()] = -1.0
        candidate_idx = scores.argsort()[::-1]
        hits: list[EvidenceHit] = []
        seen = set()
        for idx in candidate_idx:
            if scores[idx] < 0:
                continue
            row = self.df.iloc[int(idx)]
            key = (
                low(row.get("doi")),
                low(first_known(row, "title_clean", "title")),
                low(row.get("primary_result_evidence"))[:120],
            )
            if key in seen:
                continue
            seen.add(key)
            hits.append(self._row_to_hit(idx, row, float(scores[idx])))
            if len(hits) >= top_k:
                break
        return hits

    def _row_to_hit(self, idx: int, row: pd.Series, score: float) -> EvidenceHit:
        return EvidenceHit(
            row_index=int(idx),
            score=score,
            title=short(first_known(row, "title_clean", "title"), 240),
            doi=short(row.get("doi"), 120),
            project_tier=short(row.get("project_tier"), 160),
            flags=short(row.get("project_subset_flags"), 220),
            metric=short(first_known(row, "primary_result_metric", "schema_id"), 120),
            value=short(first_known(row, "primary_result_numeric_normalized", "primary_result_value"), 80),
            unit=short(first_known(row, "primary_result_unit_normalized", "primary_result_unit"), 80),
            evidence=short(first_known(row, "primary_result_evidence", "best_llps_trigger_evidence", "best_llps_component_evidence"), 520),
            design_actions=short(row.get("design_action_tags"), 240),
            defect_risks=short(row.get("defect_risk_tags"), 240),
            transferability=short(row.get("llps_transferability_class"), 80),
            trigger_class=short(row.get("llps_project_trigger_class"), 100),
        )

    def _make_decision(self, question: str, hits: list[EvidenceHit], mask: pd.Series) -> dict[str, Any]:
        q = low(question)
        interpretation = self._interpret_question(q)
        recs: list[str] = []
        risks: list[str] = []
        experiments: list[str] = []

        if any(x in q for x in ["ph", "temperature", "temp", "condition", "thermal"]):
            recs.append("Use pH/temperature distributions as host-compatible starting priors, not final LLPS optima.")
            recs.append("For a yeast-based system, start near 28-30 deg C and neutral pH, then re-test around condensate stability and catalytic activity.")
            risks.append("The apparent pH/temperature optimum can be confounded by host distribution; yeast-heavy literature does not prove the LLPS-enzyme optimum.")
            experiments.extend(["2D scan: temperature x pH with free enzyme and LLPS-enzyme controls", "Measure titer/conversion together with puncta count or droplet state."])
        if any(x in q for x in ["trigger", "substrate", "ligand", "induction", "responsive"]):
            recs.append("Prioritize project-compatible LLPS triggers: substrate/ligand response, expression or nutrient induction, concentration threshold, pH/temperature and ionic/crowding control.")
            risks.append("Stress or DNA-damage condensates should be treated as mechanism priors rather than direct design knobs.")
            experiments.extend(["Rank trigger classes by transferability before wet-lab testing.", "Compare substrate-responsive and expression-ratio designs under the same enzyme loading."])
        if any(x in q for x in ["defect", "risk", "partition", "frap", "diffusion", "activity", "trade-off"]):
            recs.append("Treat LLPS as a trade-off: enrichment can improve local concentration, but over-dense condensates can reduce turnover or mass transfer.")
            recs.append("Use multi-objective rules: maximize titer/conversion while constraining activity retention, partition and droplet fluidity.")
            risks.extend(["Activity loss after fusion or condensation", "Substrate/product partition mismatch", "Mass-transfer limitation in overly stable condensates"])
            experiments.extend(["Free enzyme vs LLPS enzyme kinetics", "Substrate/product partition assay", "FRAP or droplet-size constraint"])
        if any(x in q for x in ["glabridin", "isoflavonoid", "pterocarpan"]):
            recs.append("Separate direct Glabridin evidence from broader flavonoid/isoflavonoid priors; use direct evidence for claims and broader priors for search-space design.")
            risks.append("Direct Glabridin evidence is sparse relative to broader flavonoid evidence, so recommendations should expose uncertainty.")
            experiments.append("Benchmark project target against yeast + flavonoid/isoflavonoid subset, not only full-corpus statistics.")
        if any(x in q for x in ["titer", "yield", "production", "5 mg", "0.5"]):
            recs.append("Judge the 5 mg/L target against yeast-flavonoid/glabridin evidence rather than all extracted records.")
            risks.append("Full-corpus titer distribution can overstate feasibility if unrelated host/product systems dominate.")
            experiments.append("Use 0.5 mg/L and 5 mg/L as benchmark lines in a yeast-flavonoid conditional subset.")

        if not recs:
            recs.append("Use the evidence hierarchy first: Tier 1-3 records should drive project-specific decisions; background records only define broad priors.")
            recs.append("When a claim depends on pH, temperature, titer or LLPS trigger, compare all-corpus and project-conditioned subsets.")
            risks.append("A broad literature average may not migrate to Yeast + Glabridin + LLPS-enzyme without conditioning.")
            experiments.append("Define the condition-specific subset, then run a small validation experiment around the suggested prior.")

        tier_counts = pd.Series([h.project_tier for h in hits]).value_counts().to_dict() if hits else {}
        transfer_counts = pd.Series([h.transferability for h in hits if h.transferability]).value_counts().to_dict() if hits else {}

        answer = (
            "Decision summary: use project-conditioned evidence rather than whole-corpus averages. "
            "Prioritize Tier 1-3 records and high-transferability LLPS evidence; each recommendation is "
            "linked to row_index, DOI/title and source evidence text for traceability."
        )
        return {
            "answer": answer,
            "recommendations": list(dict.fromkeys(recs)),
            "risks": list(dict.fromkeys(risks)),
            "suggested_next_experiments": list(dict.fromkeys(experiments)),
            "query_interpretation": {
                "matched_rows": int(mask.sum()) if mask is not None else int(len(self.df)),
                "evidence_hits": len(hits),
                "tier_counts_in_hits": tier_counts,
                "transferability_counts_in_hits": transfer_counts,
                "mode": interpretation,
            },
        }

    def _interpret_question(self, q: str) -> str:
        parts = []
        if any(x in q for x in ["llps", "condensate", "phase separation", "phase transition", "droplet"]):
            parts.append("LLPS-specific")
        if any(x in q for x in ["yeast", "saccharomyces"]):
            parts.append("yeast-conditioned")
        if "glabridin" in q:
            parts.append("glabridin-direct")
        if any(x in q for x in ["ph", "temperature", "temp", "condition"]):
            parts.append("condition-window")
        if any(x in q for x in ["titer", "yield", "production"]):
            parts.append("titer-benchmark")
        if not parts:
            parts.append("general project-conditioned QA")
        return " + ".join(parts)


_CACHE: dict[str, LiteratureQASystem] = {}


def answer_literature_question(
    question: str,
    evidence_csv: str | Path | None = None,
    top_k: int = 8,
    filters: dict[str, Any] | None = None,
    llm_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = str(Path(evidence_csv or DEFAULT_EVIDENCE_CSV).resolve())
    qa = _CACHE.get(path)
    if qa is None:
        qa = LiteratureQASystem(path)
        _CACHE[path] = qa
    return qa.answer(question, top_k=top_k, filters=filters, llm_config=llm_config)
