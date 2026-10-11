import type { ProposalView, RuntimeInfoView } from "../contracts/generated";
import type { Goal } from "../types";
import { useEffect, useState, useRef } from 'react';
import type { AssistantPage, ProposalDiff } from '../contracts/generated';
import * as client from './client';

export function AgentPanel(props: {
  proposal?: ProposalView;
  projectId?: string;
  projectRevision?: number;
  context?: string;
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
  onRevise?: (prompt: string) => Promise<void>;
  onOpenProposal?: (id:string) => Promise<void>;
}) {
  const p = props.proposal;
  const [history, setHistory] = useState<AssistantPage>();
  const [diff, setDiff] = useState<ProposalDiff>();
  const [prompt, setPrompt] = useState('');
  const [error, setError] = useState('');
  const epoch = useRef(0);
  useEffect(() => {
    epoch.current++;
    const controller = new AbortController();
    setHistory(undefined); setDiff(undefined); setPrompt(''); setError('');
    if (props.projectId && props.projectRevision) void client.assistantHistory(props.projectId, controller.signal)
      .then(value => {if (!controller.signal.aborted) setHistory(value);})
      .catch(reason => {if (!controller.signal.aborted) setError(String(reason));});
    if (p && props.projectId) void client.proposalDiff(p.id, controller.signal)
      .then(value => {if (!controller.signal.aborted) setDiff(value);})
      .catch(reason => {if (!controller.signal.aborted) setError(String(reason));});
    return () => controller.abort();
  }, [props.projectId, props.projectRevision, p?.id, p?.status]);
  return (
    <section aria-label="Agent Plan proposal">
      <h2>Assistant</h2>
      <p>{props.context ?? 'Project context'}</p>
      {error && <p role="alert">{error}</p>}
      {history && <section aria-label="Assistant conversation">
        {history.messages.map(message => <div key={message.seq}><p><strong>{message.role === 'user' ? 'You' : 'Assistant'}</strong> · project revision {message.project_revision}<br/>{message.text}</p>
          {message.role === 'assistant' && props.onOpenProposal && message.proposal_id !== p?.id && <button disabled={props.busy}
            onClick={() => void props.onOpenProposal!(message.proposal_id)}>Open recorded proposal</button>}</div>)}
        {history.has_more && <button disabled={props.busy} onClick={() => {const stamp=epoch.current;
          void client.assistantHistory(props.projectId!, undefined, history.messages[0]?.seq)
          .then(value => {if(stamp===epoch.current) setHistory({...value, messages: [...value.messages, ...history.messages]});})
          .catch(reason => {if(stamp===epoch.current) setError(String(reason));});}}>Load earlier conversation</button>}
      </section>}
      <label>
        Research objective
        <textarea
          aria-label="Research objective"
          value={props.objective}
          onChange={(event) => props.onObjective(event.target.value)}
          placeholder="Describe the goal or data changes; do not invent parameters"
        />
      </label>
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
          {diff && <section aria-label="Proposed changes">
            <h3>Changes to review</h3>
            {!diff.changes.length && <p>No graph or permission changes. This prompt did not edit scientific parameters.</p>}
            {diff.changes.map((change, index) => <details key={index}><summary>{change.kind} · {change.target}</summary>
              <p>Before: {change.before ?? 'Not present'}</p><p>After: {change.after ?? 'Removed'}</p></details>)}
          </section>}
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
          {props.onRevise && <><label>Additional revision request<textarea aria-label="Additional revision request" value={prompt}
            maxLength={8000} disabled={props.busy} onChange={event => setPrompt(event.target.value)}/></label>
            <p>Manual/template mode uses the actual edited workflow, not invented parameter changes. A new proposal must be accepted again.</p>
            <button disabled={props.busy || !prompt.trim() || !['proposed','accepted','blocked'].includes(p.status)}
              onClick={() => void props.onRevise!(prompt.trim())}>Revise proposal</button></>}
          <p className="subtle">
            Changing goal, policy or inputs invalidates this proposal.
            Regenerate and accept; this is not scientific parameter approval.
          </p>
        </article>
      )}
    </section>
  );
}
