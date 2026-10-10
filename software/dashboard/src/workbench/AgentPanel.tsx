import type { ProposalView, RuntimeInfoView } from "../contracts/generated";
import type { Goal } from "../types";

export function AgentPanel(props: {
  proposal?: ProposalView;
  info?: RuntimeInfoView;
  goal: Goal;
  objective: string;
  mode: "template" | "hybrid";
  permission: boolean;
  busy: boolean;
  canPlan: boolean;
  onGoal: (goal: Goal) => void;
  onObjective: (value: string) => void;
  onMode: (mode: "template" | "hybrid") => void;
  onPermission: (value: boolean) => void;
  onPropose: () => void;
  onDecision: (action: "accept" | "reject") => void;
}) {
  const p = props.proposal;
  return (
    <section aria-label="Agent Plan proposal">
      <h2>Agent / Plan proposal</h2>
      <label>
        Research objective
        <textarea
          aria-label="Research objective"
          value={props.objective}
          onChange={(event) => props.onObjective(event.target.value)}
          placeholder="Describe the goal or data changes; do not invent parameters"
        />
      </label>
      <label>
        Analysis entry point
        <select
          aria-label="Analysis entry point"
          value={props.goal}
          onChange={(event) => {
            const value = event.target.value;
            if (
              value === "fusion_screen" ||
              value === "assembly_review" ||
              value === "pathway_simulation" ||
              value === "scientific_pipeline" ||
              value === "m1_sequence_checks"
            )
              props.onGoal(value);
          }}
        >
          <option value="fusion_screen">Fusion sequence statistics</option>
          <option value="assembly_review">Assembly inventory check</option>
          <option value="pathway_simulation">
            Uploaded pathway steady state
          </option>
          <option value="scientific_pipeline">
            M1–M5 Original-formula scientific pipeline
          </option>
          <option value="m1_sequence_checks">
            M1 sequence checks — real tools and missing steps
          </option>
        </select>
      </label>
      <label>
        Planner source
        <select
          aria-label="Planner source"
          value={props.mode}
          onChange={(event) =>
            props.onMode(
              event.target.value === "hybrid" ? "hybrid" : "template",
            )
          }
        >
          <option value="template">Template planner (no LLM）</option>
          <option
            value="hybrid"
            disabled={props.info?.capabilities.hybrid_planning !== "ready"}
          >
            Hybrid semantic / deterministic compiler
          </option>
        </select>
      </label>
      {props.info?.capabilities.hybrid_planning !== "ready" && (
        <p className="subtle">
          Hybrid planner not configured. Credentials are not read or displayed;
          no model call is claimed.
        </p>
      )}
      {props.mode === "hybrid" && (
        <label>
          <input
            type="checkbox"
            checked={props.permission}
            onChange={(e) => props.onPermission(e.target.checked)}
          />
          Allow this objective and public evidence summary to be sent to the
          privately configured model
        </label>
      )}
      <button disabled={props.busy || !props.canPlan} onClick={props.onPropose}>
        Generate proposal
      </button>
      {p && (
        <article className="proposal">
          <h3>
            {p.source === "validated_template"
              ? "Template proposal"
              : p.source === "hybrid_semantic_compiler"
                ? "Hybrid proposal"
                : "User workflow proposal"}{" "}
            · {p.status}
          </h3>
          <p>{p.rationale}</p>
          <p>
            Change types:{" "}
            {p.change_types.join(", ") ||
              "Template / User DAG; no LLM semantic classification"}
          </p>
          <dl>
            <dt>Requested stages</dt>
            <dd>{p.requested_stages.join(" → ") || "No executable stages"}</dd>
            <dt>Execution scope (including dependencies)</dt>
            <dd>{p.execution_stages.join(" → ") || "Blocked"}</dd>
            <dt>Verified reuse</dt>
            <dd>
              {p.reused_artifacts.join(", ") || "None; no automatic reuse"}
            </dd>
            <dt>Missing evidence</dt>
            <dd>
              {p.missing_inputs.join("; ") ||
                "No proposal-reported omissions; scientific stage gates recheck"}
            </dd>
          </dl>
          <p>{p.evidence.length} additional evidence references</p>
          <ul>
            {p.limitations.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
          <details>
            <summary>Reviewed tools and versions</summary>
            <ul>{p.reviewed_tool_labels.map(label => <li key={label}>{label}</li>)}</ul>
            <p>Backend checks tool, input and environment identity again before execution.</p>
          </details>
          {p.observation && <section aria-label="Scientific observation and proposed actions">
            <h4>Observed project state</h4>
            <p>{p.observation.prepared_through ? `Prepared through ${p.observation.prepared_through.toUpperCase()}` : "Scientific inputs not prepared"} · {p.observation.gaps.length + p.observation.omitted_gap_count} declared gaps</p>
            <ul>{p.observation.gaps.map((gap,i) => <li key={`${gap.stage}-${gap.code}-${i}`}>
              {gap.stage.toUpperCase()} · {gap.construct_id || "Project"} · Required: {gap.code.replaceAll("_"," ")} · {gap.reasons.map(reason => reason.replaceAll("_"," ")).join("; ")}
            </li>)}</ul>
            {p.observation.omitted_gap_count > 0 && <p>{p.observation.omitted_gap_count} additional gaps omitted from this bounded summary; inspect the project precheck for details.</p>}
            <h4>Recorded results</h4>
            {p.observation.recorded_results.length ? <ul>{p.observation.recorded_results.map(result => <li key={`${result.run_id}-${result.node_id}`}>
              {result.stage.toUpperCase()} · {result.node_status} · {result.current_project_revision ? "Current saved inputs" : "Historical inputs — not authorized for reuse"} · {result.numerically_solved_count ?? "Not recorded"} numerically solved / {result.evidence_ready_count ?? "Not recorded"} evidence-ready records
            </li>)}</ul> : <p>No recorded stage results; nothing has been calculated by this proposal.</p>}
            <h4>Recorded jobs</h4>
            {p.observation.recorded_jobs.length ? <ul>{p.observation.recorded_jobs.map(job => <li key={`${job.run_id}-${job.node_id}`}>
              {job.tool_id.replaceAll("."," ")} · {job.node_status}{job.remote_status ? ` · Remote: ${job.remote_status.replaceAll("_"," ")}` : ""}
              {job.remote_status && <span> · Local cancellation does not confirm cancellation at the remote service.</span>}
            </li>)}</ul> : <p>No recorded jobs.</p>}
            <h4>Proposed actions — no execution yet</h4>
            <ol>{p.scientific_actions.map((action,i) => <li key={`${action.kind}-${i}`}>
              {action.kind.replaceAll("_"," ")} · {action.reason}
              {action.kind === "propose_experiment" && <p>Hypothesis: {action.hypothesis}. Controls: {action.controls.join("; ")}. Observe: {action.observable}. Refute if: {action.refutation_criterion}. Human review required.</p>}
            </li>)}</ol>
          </section>}
          {p.confirmation && (
            <p className="subtle">
              Proposal checked against saved inputs{" "}
              {p.confirmation.project_revision}
            </p>
          )}
          <button
            disabled={props.busy || p.status !== "proposed"}
            onClick={() => props.onDecision("accept")}
          >
            Accept proposal (does not start computation)
          </button>
          <button
            disabled={
              props.busy || !["proposed", "accepted"].includes(p.status)
            }
            onClick={() => props.onDecision("reject")}
          >
            Reject proposal
          </button>
          <p className="subtle">
            Changing goal, policy or inputs invalidates this proposal.
            Regenerate and accept; this is not scientific parameter approval.
          </p>
        </article>
      )}
    </section>
  );
}
