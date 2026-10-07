import type { ProposalView, RuntimeInfoView } from "../contracts/generated";
import type { Goal } from "../types";
import { LazyJson } from "../contracts/LazyJson";

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
              value === "scientific_pipeline"
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
          <h4>Evidence identities</h4>
          {p.evidence.length ? (
            <ul>
              {p.evidence.map((hash) => (
                <li key={hash}>
                  <code>{hash}</code>
                </li>
              ))}
            </ul>
          ) : (
            <p>No additional evidence cited.</p>
          )}
          <ul>
            {p.limitations.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
          <LazyJson
            value={p.review_identity}
            label="Reviewed tool / environment identity (private paths/configuration omitted)"
          />
          {p.previous_review_identity && (
            <LazyJson
              value={p.previous_review_identity}
              label="Original run tool / environment identity (review differences before acceptance)"
            />
          )}
          {p.confirmation && (
            <p className="subtle">
              Project revision {p.confirmation.project_revision} · Inputs{" "}
              {p.confirmation.project_input_sha256.slice(0, 12)} · Workflow{" "}
              {p.confirmation.workflow_sha256.slice(0, 12)}
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
