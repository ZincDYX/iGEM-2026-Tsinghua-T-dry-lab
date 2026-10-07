"""Read-only, lineage-authorized comparisons using the existing F3 contract."""
from hashlib import sha256
import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from .models import Contract, Project, WorkflowError
from .store import canonical
from .display_resources import digest_file


class LineageRun(Contract):
    project_id: str
    name: str = ""
    created_at: str = ""
    run_id: str
    snapshot_hash: str
    revision: int
    status: str


class LineagePage(Contract):
    schema_version: Literal["run-lineage-v1"] = "run-lineage-v1"
    project_id: str
    offset: int
    total: int
    has_more: bool
    items: list[LineageRun]


class ComparedValue(Contract):
    record_id: str
    construct_id: str | None
    condition_id: str | None
    sequence_identity_sha256: str | None
    status: str
    claim_scope: str | None
    numerically_solved: bool
    evidence_ready: bool
    artifact_id: str
    artifact_sha256: str
    node_id: str
    attempt: int
    value: float | None


class CompareRow(Contract):
    module: str
    left: ComparedValue | None
    right: ComparedValue | None
    comparable: bool
    reason_codes: list[str]
    metric_definition: str | None
    metric_unit: str | None
    comparison_contract_left: dict | None
    comparison_contract_right: dict | None


class ComparePage(Contract):
    schema_version: Literal["scientific-comparison-v1"] = "scientific-comparison-v1"
    left: LineageRun
    right: LineageRun
    offset: int
    total: int
    has_more: bool
    input_changed_fields: list[str]
    input_diff_truncated: bool
    rows: list[CompareRow]
    ranking_performed: Literal[False] = False
    claim_scope: Literal["record_comparison_not_new_prediction_or_validation"] = "record_comparison_not_new_prediction_or_validation"


class LineageComparison:
    def __init__(self, store, boundary):
        self.store, self.boundary = store, boundary

    def family(self, project_id):
        self.store.project(project_id)
        with self.store.connection() as db:
            # Edges require the server-owned parent run and its exact snapshot.
            edges = db.execute("""SELECT p.id AS child, r.project_id AS parent
                FROM projects p JOIN runs r
                ON r.id=json_extract(p.payload,'$.parent_run_id')
                AND r.snapshot_hash=json_extract(p.payload,'$.parent_snapshot_sha256')""").fetchall()
        family = {project_id}
        while True:
            updated = family | {e["child"] for e in edges if e["parent"] in family} | {e["parent"] for e in edges if e["child"] in family}
            if updated == family:
                return family
            family = updated

    def authorize(self, project_id, run_id):
        run = self.store.run(run_id)
        if run["project_id"] not in self.family(project_id):
            raise WorkflowError("comparison_lineage_not_authorized", status_code=403)
        if sha256(canonical(run["snapshot"]).encode()).hexdigest() != run["snapshot_hash"]:
            raise WorkflowError("comparison_snapshot_identity_changed", status_code=409)
        return run

    @staticmethod
    def identity(run):
        return LineageRun(project_id=run["project_id"], name=run["snapshot"]["project"]["name"], created_at=run["created_at"], run_id=run["id"], snapshot_hash=run["snapshot_hash"], revision=run["snapshot"]["project"]["revision"], status=run["status"])

    def lineage(self, project_id, offset, limit):
        family = self.family(project_id)
        with self.store.connection() as db:
            ids = [r["id"] for r in db.execute("SELECT id,project_id FROM runs ORDER BY created_at DESC") if r["project_id"] in family]
        result = LineagePage(project_id=project_id, offset=offset, total=len(ids), has_more=offset + limit < len(ids), items=[self.identity(self.authorize(project_id, i)) for i in ids[offset:offset + limit]]).model_dump(mode="json")
        self.boundary.check(result)
        return result

    _rows_sql = """SELECT n.id AS node_id, n.attempts, n.output,
        json_extract(n.output,'$.module') AS module, j.value AS record,
        CAST(COALESCE(json_extract(j.value,'$.candidate_id'),
          json_extract(j.value,'$.experiment_id'), j.key) AS TEXT) AS record_key
        FROM nodes n, json_each(n.output,'$.records') j
        WHERE n.run_id=? AND n.status='succeeded'
        AND json_extract(n.output,'$.schema_version')
          IN ('scientific-stage-v1','scientific-stage-v2')"""

    def record_keys(self, left, right, offset, limit):
        with self.store.connection() as db:
            query = f"WITH items AS ({self._rows_sql} UNION ALL {self._rows_sql})"
            args = (left["id"], right["id"])
            total = db.execute(query + " SELECT COUNT(*) FROM (SELECT module,record_key FROM items GROUP BY module,record_key)", args).fetchone()[0]
            keys = db.execute(query + " SELECT module,record_key FROM items GROUP BY module,record_key ORDER BY module,record_key LIMIT ? OFFSET ?", (*args, limit, offset)).fetchall()
        return [(r["module"], r["record_key"]) for r in keys], total

    def records(self, run, keys):
        result = {}
        verified = {}
        with self.store.connection() as db:
            for module, key in keys:
                items = db.execute(f"SELECT * FROM ({self._rows_sql}) WHERE module=? AND record_key=?", (run["id"], module, key)).fetchall()
                if len(items) > 1:
                    raise WorkflowError("ambiguous_comparison_record_identity", status_code=409)
                if not items:
                    continue
                node = items[0]
                if node["node_id"] not in verified:
                    artifact = db.execute("SELECT id,hash,path FROM artifacts WHERE run_id=? AND node_id=? AND json_extract(metadata,'$.attempt')=?", (run["id"], node["node_id"], node["attempts"])).fetchone()
                    if not artifact or digest_file(Path(artifact["path"])) != artifact["hash"]:
                        raise WorkflowError("artifact_hash_mismatch", status_code=409)
                    if sha256(node["output"].encode()).hexdigest() != artifact["hash"]:
                        raise WorkflowError("comparison_ledger_identity_changed", status_code=409)
                    verified[node["node_id"]] = artifact
                result[(module, key)] = (module, json.loads(node["record"]), verified[node["node_id"]], {"id":node["node_id"], "attempts":node["attempts"]})
        return result

    @staticmethod
    def construct_hash(run, record):
        science = run["snapshot"]["project"].get("scientific_project")
        if not science or not record.get("construct_id"):
            return None
        inputs = science["config"]["inputs"]
        definitions = [r for r in inputs.get("constructs", []) if r.get("id") == record["construct_id"]]
        sequences = [r for r in inputs.get("construct_records", []) if r.get("construct_id", r.get("id")) == record["construct_id"]]
        # An ID alone is never a build oracle; require sequence-derived evidence.
        context = record.get("candidate_context") or record.get("m4_candidate_context") or {}
        sequence_hash = context.get("enzyme_sequence_sha256") or context.get("sequence_sha256") or record.get("sequence_sha256")
        declared_sequences = any(r.get("sequences") or any(p.get("sequence") for p in r.get("parts", [])) for r in definitions)
        if not sequence_hash and not sequences and not declared_sequences:
            return None
        return sha256(canonical({"definitions": definitions, "sequences": sequences, "sequence_sha256": sequence_hash}).encode()).hexdigest()

    def compare(self, project_id, left_id, right_id, offset, limit, objective="yield_abs"):
        left = self.authorize(project_id, left_id)
        right = self.authorize(project_id, right_id)
        keys, total = self.record_keys(left, right, offset, limit)
        a = self.records(left, keys)
        b = self.records(right, keys)
        rows = []
        for index, key in enumerate(keys):
            pair = [a.get(key), b.get(key)]
            values, contracts, reasons = [], [], []
            module = pair[0][0] if pair[0] else pair[1][0]
            for run, item in zip((left, right), pair):
                if item is None:
                    values.append(None)
                    contracts.append(None)
                    reasons.append("missing_record")
                    continue
                stage, record, artifact, node = item
                identity_hash = self.construct_hash(run, record)
                values.append(ComparedValue(record_id=str(record.get("candidate_id", record.get("experiment_id", index + offset))), construct_id=record.get("construct_id"), condition_id=record.get("condition_id"), sequence_identity_sha256=identity_hash, status=record["status"], claim_scope=record.get("claim_scope"), numerically_solved=record["numerically_solved"], evidence_ready=record["evidence_ready"], artifact_id=artifact["id"], artifact_sha256=artifact["hash"], node_id=node["id"], attempt=node["attempts"], value=None))
                contract = None
                if stage != "m4" or module != "m4":
                    reasons.append("descriptive_stage_only_no_F3_metric")
                else:
                    from igem_drylab.design_analysis import _candidate_comparison
                    context = record.get("candidate_context") or {}
                    if any(context.get(k) != record.get(k) for k in ("candidate_id", "construct_id", "condition_id")):
                        reasons.append("M3_M4_candidate_identity_mismatch")
                    if record["status"] != "valid" or not record["evidence_ready"] or not context.get("evidence_ready") or record.get("data_quality") not in {"measured", "fitted", "literature", "mixed"} or record.get("claim_scope") != "conditional_mechanism" or context.get("claim_scope") != "conditional_mechanism" or record.get("provenance_summary", {}).get("assumption", 0) or context.get("provenance_summary", {}).get("assumption", 0):
                        reasons.append("candidate_not_formally_eligible")
                    try:
                        contract = _candidate_comparison(SimpleNamespace(simulation_inputs=record.get("simulation_inputs", {})), objective).model_dump(mode="json")
                    except (ValueError, KeyError, TypeError):
                        reasons.append("formal_comparison_contract_missing_or_invalid")
                    if identity_hash is None:
                        reasons.append("construct_sequence_identity_not_registered")
                contracts.append(contract)
            if contracts[0] is not None and contracts[1] is not None:
                differences = [k for k in contracts[0] if k != "steady_state_observation_reference" and contracts[0][k] != contracts[1][k]]
                reasons.extend("incompatible_" + k for k in differences)
            if values[0] and values[1] and values[0].sequence_identity_sha256 != values[1].sequence_identity_sha256:
                # No implicit approval of varying design factors from text IDs.
                reasons.append("construct_identity_changed_requires_reviewed_design_plan")
            comparable = not reasons and all(contracts)
            if comparable:
                for value, item in zip(values, pair):
                    metric = item[1].get(objective)
                    if isinstance(metric, bool) or not isinstance(metric, (int, float)) or not math.isfinite(metric):
                        reasons.append("metric_not_recorded")
                    else:
                        value.value = metric
                comparable = not reasons
            if not comparable:
                for value in values:
                    if value:
                        value.value = None
            rows.append(CompareRow(module=module, left=values[0], right=values[1], comparable=comparable, reason_codes=sorted(set(reasons)), metric_definition=contracts[0]["metric_definition"] if comparable else None, metric_unit=contracts[0]["metric_unit"] if comparable else None, comparison_contract_left=contracts[0], comparison_contract_right=contracts[1]))
        before = self.boundary.project(Project.model_validate(left["snapshot"]["project"]))
        after = self.boundary.project(Project.model_validate(right["snapshot"]["project"]))
        with self.store.connection() as db:
            grants = {"asset:" + r["id"]: r["hash"] for r in db.execute("SELECT id,hash FROM file_assets WHERE project_id IN (?,?)", (left["project_id"], right["project_id"]))}
        def semantic(value):
            if isinstance(value, str):
                return "sha256:" + grants[value] if value in grants else value
            if isinstance(value, dict):
                if {"file_id", "sha256", "path"} <= value.keys():
                    return {"content_sha256":value["sha256"]}
                return {k:semantic(v) for k,v in value.items()}
            if isinstance(value, list):
                return [semantic(v) for v in value]
            return value
        before, after = semantic(before), semantic(after)
        changed = []
        def diff(a, b, field):
            if isinstance(a, dict) and isinstance(b, dict):
                for key in sorted(a.keys() | b.keys()):
                    if key not in {"id", "revision", "parent_run_id", "parent_snapshot_sha256", "sequence_index"}:
                        diff(a.get(key), b.get(key), field + [key])
            elif a != b:
                changed.append(".".join(field))
        diff(before, after, [])
        result = ComparePage(left=self.identity(left), right=self.identity(right), offset=offset, total=total, has_more=offset + limit < total, input_changed_fields=changed[:200], input_diff_truncated=len(changed) > 200, rows=rows).model_dump(mode="json")
        self.boundary.check(result)
        return result
