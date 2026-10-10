"""Bounded, public read models; the immutable execution ledger stays private."""
from __future__ import annotations

import json
from typing import Any
from pydantic import Field

from .disclosure import ArtifactView
from .models import Contract, WorkflowError, Workflow


class ProjectSummaryView(Contract):
    id: str
    name: str
    revision: int
    scientific: bool
    sequence_count: int
    scientific_sequence_count: int | None
    scientific_sequence_index_status: str


class ScientificStageSummary(Contract):
    module: str
    record_count: int
    status_counts: dict[str, int]
    numerically_solved_count: int
    evidence_ready_count: int
    missing_input_count: int
    claim_scope: str | None


class NodeStateView(Contract):
    id: str
    parent_id: str | None
    status: str
    attempts: int
    tool_id: str | None
    label: str
    scientific_summary: ScientificStageSummary | None = None


class RunSummaryView(Contract):
    id: str
    name: str = ""
    project_id: str
    status: str
    snapshot_hash: str
    created_at: str
    updated_at: str
    control: str | None
    heartbeat: str | None
    state_version: int
    event_cursor: int
    project_revision: int
    workflow: Workflow
    tools: dict[str, Any]
    nodes: list[NodeStateView]
    artifacts: list[ArtifactView]
    scientific_assessment: dict[str,str] = Field(default_factory=dict)


class PublicReads:
    def __init__(self, store, boundary):
        self.store, self.boundary = store, boundary

    def projects(self, offset: int, limit: int):
        from .sequence_index import stored_scientific_count
        with self.store.connection() as db:
            rows = db.execute("SELECT id,revision,json_extract(payload,'$.name') AS name,json_array_length(payload,'$.sequences') AS sequence_count,json_extract(payload,'$.scientific_project.config.inputs.protein_fasta') AS fasta,json_extract(payload,'$.scientific_project.evidence_files') AS evidence FROM projects ORDER BY rowid DESC LIMIT ? OFFSET ?", (limit,offset)).fetchall()
            result = []
            for row in rows:
                science = {"config": {"inputs": {"protein_fasta": row["fasta"]}}, "evidence_files": json.loads(row["evidence"])} if row["fasta"] else None
                project = {"scientific_project": science}
                count, status = stored_scientific_count(project, db)
                result.append(ProjectSummaryView(id=row["id"], name=row["name"], revision=row["revision"],
                    scientific=science is not None, sequence_count=row["sequence_count"] or 0,
                    scientific_sequence_count=count, scientific_sequence_index_status=status).model_dump(mode="json"))
        self.boundary.check(result)
        return result

    def summary(self, run_id: str):
        with self.store.connection() as db:
            db.execute("BEGIN")
            row = db.execute("SELECT id,project_id,status,snapshot_hash,created_at,updated_at,control,heartbeat,json_extract(snapshot,'$.project.name') AS name,json_extract(snapshot,'$.project.revision') AS project_revision,json_extract(snapshot,'$.workflow') AS workflow,json_extract(snapshot,'$.tools') AS tools FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None: raise KeyError(run_id)
            result = dict(row)
            workflow = json.loads(result["workflow"])
            definitions = {node["id"]:node for node in workflow["nodes"]}
            result["workflow"] = workflow
            result["tools"] = {key:{field:value[field] for field in ("version","runtime","plugin_hash","implementation_sha256")} for key,value in json.loads(result["tools"]).items()}
            result["event_cursor"] = result["state_version"] = db.execute("SELECT COALESCE(MAX(seq),0) FROM events WHERE run_id=?", (run_id,)).fetchone()[0]
            result["nodes"] = []
            for node in db.execute("SELECT id,parent_id,status,attempts,json_extract(output,'$.schema_version') AS output_schema,json_extract(output,'$.module') AS module,json_extract(output,'$.claim_scope') AS claim_scope FROM nodes WHERE run_id=? ORDER BY rowid", (run_id,)):
                definition = definitions.get(node["parent_id"] or node["id"],{})
                scientific = None
                if node["output_schema"] in {"scientific-stage-v1", "scientific-stage-v2"} and definition.get("tool_id") == "project." + str(node["module"]):
                    # Aggregate existing record dimensions in SQLite; do not load
                    # trajectories, infer approvals or recompute scientific gates.
                    counts = db.execute("""SELECT COUNT(*) AS record_count,
                        COALESCE(SUM(json_extract(value,'$.numerically_solved')=1),0) AS numerically_solved_count,
                        COALESCE(SUM(json_extract(value,'$.evidence_ready')=1),0) AS evidence_ready_count,
                        COALESCE(SUM(json_array_length(value,'$.missing_inputs')),0) AS missing_input_count
                        FROM nodes,json_each(nodes.output,'$.records') WHERE run_id=? AND nodes.id=?""", (run_id,node["id"])).fetchone()
                    statuses = db.execute("""SELECT json_extract(value,'$.status') AS status,COUNT(*) AS count
                        FROM nodes,json_each(nodes.output,'$.records') WHERE run_id=? AND nodes.id=?
                        GROUP BY json_extract(value,'$.status')""", (run_id,node["id"])).fetchall()
                    scientific = ScientificStageSummary(module=node["module"], claim_scope=node["claim_scope"], status_counts={str(r["status"]):r["count"] for r in statuses}, **dict(counts)).model_dump(mode="json")
                elif node['output_schema']=='synthetic-ps-v3-run-v1' and definition.get('tool_id')=='synthetic.ps_v3':
                    counts=db.execute("""SELECT COUNT(*) AS n,
                        COALESCE(SUM(json_extract(value,'$.m4.result.status')='numerically_solved'
                            AND json_extract(value,'$.m4.result.numerical_admission.conservation_valid')=1),0) AS solved
                        FROM nodes,json_each(nodes.output,'$.cases') WHERE run_id=? AND nodes.id=?""",(run_id,node['id'])).fetchone()
                    gaps=db.execute("SELECT COALESCE(json_array_length(output,'$.E3.missing_inputs'),0) FROM nodes WHERE run_id=? AND id=?",(run_id,node['id'])).fetchone()[0]
                    scientific=ScientificStageSummary(module='synthetic_m3_m4',record_count=counts['n']+1,
                        status_counts={'recorded_synthetic_scenarios':counts['n'],'blocked_E3':1},
                        numerically_solved_count=counts['solved'],evidence_ready_count=0,
                        missing_input_count=gaps,claim_scope=node['claim_scope']).model_dump(mode='json')
                result["nodes"].append({**{k:node[k] for k in ("id","parent_id","status","attempts")},"tool_id":definition.get("tool_id"),"label":definition.get("label",node["id"]), "scientific_summary":scientific})
            result["artifacts"] = [{**dict(row),"upstream":json.loads(row["upstream"]),"metadata":json.loads(row["metadata"]),"name":"result.json"}
                for row in db.execute("SELECT id,run_id,node_id,hash,upstream,metadata FROM artifacts WHERE run_id=?",(run_id,))]
        summaries=[node['scientific_summary'] for node in result['nodes'] if node['scientific_summary'] is not None]
        count=sum(s['record_count'] for s in summaries)
        numeric=sum(s['numerically_solved_count'] for s in summaries)
        evidence=sum(s['evidence_ready_count'] for s in summaries)
        missing=sum(s['missing_input_count'] for s in summaries)
        result['scientific_assessment']={
            'numerical_state':'all_recorded_solved' if count and numeric==count else 'partial_or_blocked' if count else 'not_recorded',
            'evidence_state':'all_recorded_ready' if count and evidence==count and not missing else 'partial_or_blocked' if count else 'not_recorded',
            # No verified independent experimental-validation contract is connected
            # yet. Job success and parameter approval cannot establish this state.
            'experimental_validation':'not_established'}
        result = RunSummaryView.model_validate(result).model_dump(mode="json")
        self.boundary.check(result)
        return result

    def events(self, run_id: str, after: int, limit: int):
        with self.store.connection() as db:
            if not db.execute("SELECT 1 FROM runs WHERE id=?", (run_id,)).fetchone(): raise KeyError(run_id)
            rows = db.execute("SELECT seq,node_id,event,payload,timestamp FROM events WHERE run_id=? AND seq>? ORDER BY seq LIMIT ?",(run_id,after,limit+1)).fetchall()
        items = []
        for row in rows[:limit]:
            payload = json.loads(row["payload"])
            public = {field:payload[field] for field in ("status","action","proposal_id","diagnostic_id","reason","position","actor") if field in payload}
            self.boundary.check(public)
            items.append({**dict(row),"payload":public})
        return {"items":items,"cursor":items[-1]["seq"] if items else after,"has_more":len(rows)>limit}

    def node(self, run_id: str, node_id: str, offset: int, limit: int):
        from .sequence_results import sequence_map
        with self.store.connection() as db:
            db.execute("BEGIN")
            run = db.execute("SELECT project_id FROM runs WHERE id=?",(run_id,)).fetchone()
            if run is None: raise KeyError(run_id)
            node = db.execute("SELECT id,parent_id,status,attempts,error,json_extract(output,'$.schema_version') AS schema_version FROM nodes WHERE run_id=? AND id=?",(run_id,node_id)).fetchone()
            if node is None: raise KeyError(node_id)
            sequences = sequence_map(db, run_id, node_id, offset, limit)
            if sequences is not None:
                output = None  # The bounded versioned view is separate from the immutable raw aggregate.
                count = sequences["total_count"]
            elif node["schema_version"] in {"scientific-stage-v1","scientific-stage-v2"}:
                # SQLite selects just the requested records, not other stages or
                # every candidate/trajectory into a Python/public response.
                meta = db.execute("SELECT json_remove(output,'$.records','$.trajectories') FROM nodes WHERE run_id=? AND id=?",(run_id,node_id)).fetchone()[0]
                count = db.execute("SELECT json_array_length(output,'$.records') FROM nodes WHERE run_id=? AND id=?",(run_id,node_id)).fetchone()[0]
                records = db.execute("SELECT value FROM nodes,json_each(nodes.output,'$.records') WHERE run_id=? AND nodes.id=? LIMIT ? OFFSET ?",(run_id,node_id,limit,offset))
                output = json.loads(meta)
                output["records"] = [json.loads(row[0]) for row in records]
            else:
                output = db.execute("SELECT output FROM nodes WHERE run_id=? AND id=?",(run_id,node_id)).fetchone()[0]
                output = json.loads(output) if output else None
                count = 0
            artifact = db.execute("SELECT id,hash FROM artifacts WHERE run_id=? AND node_id=? AND json_extract(metadata,'$.attempt')=?",(run_id,node_id,node["attempts"])).fetchone()
        result = self.boundary.node({**dict(node),"output":output,"error":json.loads(node["error"]) if node["error"] else None},run["project_id"])
        self.boundary.check(sequences)
        return {"node":result,"offset":offset,"limit":limit,"total_records":count,"artifact":dict(artifact) if artifact else None,"sequence_map":sequences}
