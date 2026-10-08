import { useEffect, useState } from "react";
import { requestJson } from "../api";
import { parseList } from "../contracts/validation";
import type {
  PredictionToolView,
  ProjectView,
  Workflow,
} from "../contracts/generated";
import { defaultPolicy } from "./client";

export function PredictionTools({
  project,
  busy,
  onPlan,
  onOpenResource,
}: {
  project: ProjectView;
  busy: boolean;
  onPlan: (workflow: Workflow) => void;
  onOpenResource: (fileId: string) => void;
}) {
  const [rows, setRows] = useState<PredictionToolView[]>([]);
  const [sequenceId, setSequenceId] = useState(project.sequences[0]?.id ?? "");
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    void requestJson(
      `/projects/${encodeURIComponent(project.id)}/prediction-tools`,
      undefined,
      controller.signal,
    )
      .then((raw) => {
        if (!controller.signal.aborted)
          setRows(parseList("PredictionToolView", raw));
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
      <h2>Prediction tools</h2>
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
          {project.sequences.map((item) => (
            <option key={item.id} value={item.id}>
              {item.id} ({item.sequence.length} aa)
            </option>
          ))}
        </select>
      </label>
      <button
        disabled={busy}
        onClick={() => {
          setError("");
          setRevision((value) => value + 1);
        }}
      >
        Check configured routes
      </button>
      <table>
        <thead>
          <tr>
            <th>Tool</th>
            <th>Availability</th>
            <th>Version</th>
            <th>Last real check</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>
                <a href={row.source_reference} target="_blank" rel="noreferrer">
                  {row.name}
                </a>
              </td>
              <td>
                {
                  {
                    not_configured: "Not configured",
                    configured_unverified: "Configured; real job not verified",
                    available: "Real output produced and parsed",
                    failed: "Last real job failed",
                  }[row.status]
                }
              </td>
              <td>
                {row.version && /^[0-9a-f]{40}$/.test(row.version)
                  ? "Author source revision recorded in backend"
                  : (row.version ?? "Not recorded")}
              </td>
              <td>{row.last_real_check ?? "Not run"}</td>
              <td>
                <button
                  disabled={
                    busy || !sequenceId || row.status === "not_configured"
                  }
                  onClick={() => {
                    const index = project.sequences.findIndex(
                      (item) => item.id === sequenceId,
                    );
                    if (index < 0) return;
                    onPlan({
                      id: "sequence-prediction",
                      name: `${row.name}: ${sequenceId}`,
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
                            item: {
                              kind: "project",
                              path: ["sequences", index],
                            },
                          },
                          depends_on: [],
                          map: null,
                        },
                      ],
                    });
                  }}
                >
                  Prepare run on selected input
                </button>
                {row.latest_file_id && (
                  <button onClick={() => onOpenResource(row.latest_file_id!)}>
                    Open latest output
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
