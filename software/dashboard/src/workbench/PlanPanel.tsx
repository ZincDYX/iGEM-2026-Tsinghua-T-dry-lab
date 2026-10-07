import type { Workflow, RunSummaryView } from "../contracts/generated";
import type { WorkflowNode } from "../contracts/Workflow.generated";

import { jobLabels } from "./messages.en";
export const statusLabel = (value: string) => jobLabels[value] ?? value;
export function dependencies(node: WorkflowNode) {
  const values = [
    ...Object.values(node.inputs),
    ...(node.map ? [node.map.items] : []),
  ];
  return [
    ...new Set([
      ...node.depends_on,
      ...values.flatMap((value) =>
        value.kind === "node" ? [value.node_id] : [],
      ),
    ]),
  ];
}
export function PlanPanel({
  workflow,
  run,
  selected,
  onSelect,
}: {
  workflow?: Workflow;
  run?: RunSummaryView;
  selected: string;
  onSelect: (id: string) => void;
}) {
  if (!workflow)
    return (
      <div className="empty-panel">
        <h2>Workflow</h2>
        <p>
          Select a project, check inputs, then review a fixed pipeline or
          controlled Agent proposal. No example scientific values are supplied.
        </p>
      </div>
    );
  return (
    <section>
      <header className="panel-heading">
        <h2>{workflow.name}</h2>
        <span>{workflow.nodes.length} stages</span>
      </header>
      <p>{workflow.description}</p>
      <table className="plan-table">
        <thead>
          <tr>
            <th>Stage</th>
            <th>Actual tool</th>
            <th>Dependencies</th>
            <th>Job status</th>
            <th>Checkpoints</th>
          </tr>
        </thead>
        <tbody>
          {workflow.nodes.map((node) => {
            const state = run?.nodes.find((value) => value.id === node.id);
            const policy = workflow.execution_policy;
            return (
              <tr
                key={node.id}
                className={selected === node.id ? "selected-row" : ""}
              >
                <td>
                  <button
                    aria-pressed={selected === node.id}
                    onClick={() => onSelect(node.id)}
                  >
                    {node.label}
                  </button>
                </td>
                <td>{node.tool_id}</td>
                <td>{dependencies(node).join(" → ") || "No dependencies"}</td>
                <td>{statusLabel(state?.status ?? "pending")}</td>
                <td>
                  {[
                    policy.checkpoints_before.includes(node.id)
                      ? "before"
                      : null,
                    policy.checkpoints_after.includes(node.id) ? "after" : null,
                  ]
                    .filter(Boolean)
                    .join(" / ") || "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="subtle">
        Scope:{" "}
        {workflow.execution_policy.target_node_id ?? "All planned stages"} ·
        Stages per dispatch:{" "}
        {workflow.execution_policy.max_completed_stages ??
          "Continuous within authorized scope"}{" "}
        · Tool call budget: {workflow.execution_policy.max_tool_calls} · Hard
        memory limit: unsupported.
      </p>
      <p className="subtle">
        Existing scientific gates block missing evidence. Job completion is not
        numerical validity, evidence approval or experimental validation.
      </p>
    </section>
  );
}
