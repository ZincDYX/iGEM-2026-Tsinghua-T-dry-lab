import { useEffect, useState } from "react";
import { requestJson } from "../api";
import { parseList, parsePublicAsync as parsePublic } from "../contracts/validation";
import type {
  PredictionToolView,
  ProjectView,
  Workflow,
  SequencePage,
} from "../contracts/generated";
import { defaultPolicy } from "./client";

export function PredictionTools({
  project,
  busy,
  onPlan,
  onOpenResource,
  catalog = [],
}: {
  project: ProjectView;
  catalog?: import("../contracts/ToolCatalogPage.generated").ModuleTool[];
  busy: boolean;
  onPlan: (workflow: Workflow) => void;
  onOpenResource: (fileId: string) => void;
}) {
  const [rows, setRows] = useState<PredictionToolView[]>([]);
  const [sequences, setSequences] = useState<SequencePage>();
  const [offset, setOffset] = useState(0);
  const [sequenceId, setSequenceId] = useState("");
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setSequences(undefined);
    setSequenceId("");
    void requestJson(`/projects/${encodeURIComponent(project.id)}/sequences?offset=${offset}&limit=100`, undefined, controller.signal)
      .then(async raw => {
        const page = await parsePublic("SequencePage", raw);
        if (!controller.signal.aborted) {
          setSequences(page);
          setSequenceId(page.items.length ? "0" : "");
        }
      }).catch(reason => { if (!controller.signal.aborted) setError(String(reason)); });
    return () => controller.abort();
  }, [project.id, project.revision, offset]);
  useEffect(() => {
    const controller = new AbortController();
    void requestJson(
      `/projects/${encodeURIComponent(project.id)}/prediction-tools`,
      undefined,
      controller.signal,
    )
      .then(async (raw) => {
        const value=await parseList('PredictionToolView',raw);
        if (!controller.signal.aborted) setRows(value);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Tool availability could not be checked on the connected backend.",
          );
      });
    return () => controller.abort();
  }, [project.id, project.revision, revision]);
  return (
    <section aria-label="Scientific prediction tools">
      <h2>Tools</h2>
      <p>
        Real jobs run on the connected backend and are saved in the workflow
        ledger. These diagnostic tasks do not approve M1/M2 evidence.
      </p>
      {error && <p role="alert">{error}</p>}
      <label>
        Selected sequence
        <select
          aria-label="Prediction input"
          value={sequenceId}
          onChange={(e) => setSequenceId(e.target.value)}
        >
          <option value="">Select imported input</option>
          {sequences?.items.map((item, index) => (
            <option key={`${item.ref.source}:${item.ref.file_id}:${item.ref.record_id}`} value={String(index)}>
              {item.label} ({item.length} aa; {item.role})
            </option>
          ))}
        </select>
      </label>
      {sequences && sequences.total > 100 && <nav aria-label="Sequence pages">
        <button disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 100))}>Previous sequences</button>
        <span>{offset + 1}–{offset + sequences.items.length} of {sequences.total}</span>
        <button disabled={offset + 100 >= sequences.total} onClick={() => setOffset(value => value + 100)}>Next sequences</button>
      </nav>}
      <button
        disabled={busy}
        onClick={() => {
          setError("");
          setRevision((value) => value + 1);
        }}
      >
        Check availability
      </button>
      <table>
        <thead>
          <tr>
            <th>Tool</th>
            <th>Purpose</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {catalog.filter(tool=>!rows.some(row=>row.id===tool.id)).map(tool=><tr key={tool.id}><td>{tool.name}</td><td>{tool.description}</td><td>Registered · not tested</td><td>{tool.id==="fusion.sequence_metrics"?<button disabled={busy||!sequenceId} onClick={()=>{const input=sequences?.items[Number(sequenceId)];if(input)onPlan({id:"sequence-statistics",name:input.label,version:"1",description:"Sequence statistics",execution_policy:defaultPolicy(),nodes:[{id:"metrics",label:"Sequence statistics",tool_id:tool.id,inputs:{item:input.ref},depends_on:[],map:null}]});}}>Run</button>:<span>Configure this module in Workflow</span>}</td></tr>)}
          {rows.map((row) => (
            <tr key={row.id}>
              <td>
                <a href={row.source_reference} target="_blank" rel="noreferrer">
                  {row.name}
                </a>
              </td><td>{catalog.find(tool=>tool.id===row.id)?.description??"Sequence prediction"}</td>
              <td>
                {
                  {
                    not_configured: "Not configured",
                    configured_unverified: "Configured; real job not verified",
                    available: "Real output produced and parsed",
                    failed: "Last real job failed",
                  }[row.status]
                }
                {row.status==="not_configured"&&<p>Ask the deployment administrator to install or configure this predictor. A license may be required.</p>}
                {row.status==="failed"&&<><p>{row.failure_step??'Last job'}: {row.problem?.message??'Job incomplete. Open Jobs → Problems for its diagnostic.'}</p>
                  {row.problem?.actions.map(action=><p key={action}>{action}</p>)}</>}
              </td>
              <td>
                <button
                  disabled={
                    busy || !sequenceId || row.status === "not_configured"
                  }
                  onClick={() => {
                    const input = sequences?.items[Number(sequenceId)];
                    if (!input || sequences?.project_revision !== project.revision) return;
                    onPlan({
                      id: "sequence-prediction",
                      name: `${row.name}: ${input.label}`,
                      version: "1",
                      description:
                        "Diagnostic tool job; formal M1/M2 screening remains a separate evidence-gated step.",
                      execution_policy: defaultPolicy(),
                      nodes: [
                        {
                          id: "prediction",
                          label: row.name,
                          tool_id: row.id,
                          inputs: {
                            item: input.ref,
                          },
                          depends_on: [],
                          map: null,
                        },
                      ],
                    });
                  }}
                >
                  Run
                </button>
                {row.latest_file_id && (
                  <button onClick={() => onOpenResource(row.latest_file_id!)}>
                    View output
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>
        Executable paths, credentials and route configuration stay in private
        backend settings. License-restricted predictors are not substituted by
        these tools.
      </p>
    </section>
  );
}
