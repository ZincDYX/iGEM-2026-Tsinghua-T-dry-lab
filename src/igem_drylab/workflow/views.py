"""Bounded, public read models; the immutable execution ledger stays private."""
from __future__ import annotations

import json
from typing import Any

from .disclosure import ArtifactView
from .models import Contract, WorkflowError, Workflow


class ProjectSummaryView(Contract):
    id: str
    name: str
    revision: int
    scientific: bool
    sequence_count: int


class NodeStateView(Contract):
    id: str
    parent_id: str | None
    status: str
    attempts: int
    tool_id: str | None
    label: str


class RunSummaryView(Contract):
    id: str
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


class PublicReads:
    def __init__(self, store, boundary):
        self.store, self.boundary = store, boundary

    def projects(self, offset: int, limit: int):
        with self.store.connection() as db:
            rows = db.execute("SELECT id,revision,json_extract(payload,'$.name') AS name,json_type(payload,'$.scientific_project') AS scientific,json_array_length(payload,'$.sequences') AS sequence_count FROM projects ORDER BY rowid DESC LIMIT ? OFFSET ?", (limit,offset))
            result = [ProjectSummaryView(**{**dict(row),"scientific":row["scientific"] == "object"}).model_dump(mode="json") for row in rows]
        self.boundary.check(result)
        return result

    def summary(self, run_id: str):
        with self.store.connection() as db:
            db.execute("BEGIN")
            row = db.execute("SELECT id,project_id,status,snapshot_hash,created_at,updated_at,control,heartbeat,json_extract(snapshot,'$.project.revision') AS project_revision,json_extract(snapshot,'$.workflow') AS workflow,json_extract(snapshot,'$.tools') AS tools FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None: raise KeyError(run_id)
            result = dict(row)
            workflow = json.loads(result["workflow"])
            definitions = {node["id"]:node for node in workflow["nodes"]}
            result["workflow"] = workflow
            result["tools"] = {key:{field:value[field] for field in ("version","runtime","plugin_hash","implementation_sha256")} for key,value in json.loads(result["tools"]).items()}
            result["event_cursor"] = result["state_version"] = db.execute("SELECT COALESCE(MAX(seq),0) FROM events WHERE run_id=?", (run_id,)).fetchone()[0]
            result["nodes"] = []
            for node in db.execute("SELECT id,parent_id,status,attempts FROM nodes WHERE run_id=? ORDER BY rowid", (run_id,)):
                definition = definitions.get(node["parent_id"] or node["id"],{})
                result["nodes"].append({**dict(node),"tool_id":definition.get("tool_id"),"label":definition.get("label",node["id"])})
            result["artifacts"] = [{**dict(row),"upstream":json.loads(row["upstream"]),"metadata":json.loads(row["metadata"]),"name":"result.json"}
                for row in db.execute("SELECT id,run_id,node_id,hash,upstream,metadata FROM artifacts WHERE run_id=?",(run_id,))]
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
        with self.store.connection() as db:
            db.execute("BEGIN")
            run = db.execute("SELECT project_id FROM runs WHERE id=?",(run_id,)).fetchone()
            if run is None: raise KeyError(run_id)
            node = db.execute("SELECT id,parent_id,status,attempts,error,json_extract(output,'$.schema_version') AS schema_version FROM nodes WHERE run_id=? AND id=?",(run_id,node_id)).fetchone()
            if node is None: raise KeyError(node_id)
            if node["schema_version"] in {"scientific-stage-v1","scientific-stage-v2"}:
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
            artifact = db.execute("SELECT id,hash FROM artifacts WHERE run_id=? AND node_id=?",(run_id,node_id)).fetchone()
        result = self.boundary.node({**dict(node),"output":output,"error":json.loads(node["error"]) if node["error"] else None},run["project_id"])
        return {"node":result,"offset":offset,"limit":limit,"total_records":count,"artifact":dict(artifact) if artifact else None}
