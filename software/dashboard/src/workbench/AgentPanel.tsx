import { useEffect, useRef, useState, type ReactNode } from "react";
import type {
  AssistantPage,
  ProposalDiff,
  ProposalView,
  RuntimeInfoView,
} from "../contracts/generated";
import type { Goal } from "../types";
import * as client from "./client";
import {object} from '../contracts/validation';

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
  onGoal: (value: Goal) => void;
  onObjective: (value: string) => void;
  onMode: (value: "template" | "hybrid") => void;
  onPermission: (value: boolean) => void;
  onPropose: () => void;
  onDecision: (value: "accept" | "reject") => void;
  onRevise?: (prompt: string) => Promise<void>;
  onOpenProposal?: (id: string) => Promise<void>;
  onSettings?: () => void;
  inputCheck?: ReactNode;
  intent?: "new" | "modify";
  onIntent?: (value: "new" | "modify") => void;
}) {
  const p = props.proposal;
  const [history, setHistory] = useState<AssistantPage>(),
    [diff, setDiff] = useState<ProposalDiff>();
  const changeGroups=new Map<string,ProposalDiff['changes']>();
  for(const change of diff?.changes??[]){const id=change.node_id??'';changeGroups.set(id,[...(changeGroups.get(id)??[]),change]);}
  const [localIntent, setLocalIntent] = useState<"new" | "modify">("new"),
    [error, setError] = useState("");
  const intent = props.intent ?? localIntent,
    setIntent = props.onIntent ?? setLocalIntent;
  const composer = useRef<HTMLTextAreaElement>(null),
    epoch = useRef(0);
  useEffect(() => {
    const stamp = ++epoch.current,
      controller = new AbortController();
    setError("");
    if (props.projectId)
      void client
        .assistantHistory(props.projectId, controller.signal)
        .then((value) => {
          if (!controller.signal.aborted && stamp === epoch.current)
            setHistory(value);
        })
        .catch((reason) => {
          if (!controller.signal.aborted) setError(String(reason));
        });
    return () => {
      ++epoch.current;
      controller.abort();
    };
  }, [props.projectId, props.projectRevision, p?.id, p?.status]);
  useEffect(() => {
    const controller = new AbortController();
    setDiff(undefined);
    if (p && props.projectId)
      void client
        .proposalDiff(p.id, controller.signal)
        .then((value) => {
          if (!controller.signal.aborted) setDiff(value);
        })
        .catch((reason) => {
          if (!controller.signal.aborted) setError(String(reason));
        });
    return () => controller.abort();
  }, [props.projectId, p?.id]);
  function send() {
    if (intent === "modify" && p && props.onRevise)
      void props.onRevise(props.objective.trim());
    else props.onPropose();
  }
  return (
    <section aria-label="Assistant conversation">
      <header className="panel-heading">
        <span>
          {props.mode === "template"
            ? "Built-in planner · registered tasks only"
            : props.info?.capabilities.hybrid_planning === "ready"
              ? "Configured model"
              : "Model not verified"}
        </span>
        {props.onSettings && (
          <button aria-label="Assistant settings" onClick={props.onSettings}>
            Settings
          </button>
        )}
      </header>
      <p>{props.context ?? "Project"}</p>
      {error && <p role="alert">{error}</p>}
      <div className="conversation-messages">
        {history?.messages
          .filter(
            (message) =>
              message.proposal_id !== p?.id || message.role === "user",
          )
          .map((message) => (
            <article key={message.seq}>
              <strong>{message.role === "user" ? "You" : "Assistant"}</strong>
              <p>{message.text}</p>
              {message.role === "assistant" && props.onOpenProposal && (
                <button
                  disabled={props.busy}
                  onClick={() =>
                    void props.onOpenProposal!(message.proposal_id)
                  }
                >
                  Open recorded proposal
                </button>
              )}
            </article>
          ))}
        {history?.has_more && (
          <button
            disabled={props.busy}
            onClick={() => {
              const stamp = epoch.current;
              void client
                .assistantHistory(
                  props.projectId!,
                  undefined,
                  history.messages[0]?.seq,
                )
                .then((value) => {
                  if (stamp === epoch.current)
                    setHistory({
                      ...value,
                      messages: [...value.messages, ...history.messages],
                    });
                })
                .catch((reason) => setError(String(reason)));
            }}
          >
            Earlier messages
          </button>
        )}
      </div>
      {p && (
        <article className="proposal" aria-label="Current proposal">
          <h3>
            {p.status === "accepted"
              ? "Approved plan"
              : p.status === "blocked"
                ? "Plan needs data"
                : p.status==='rejected'?'Rejected plan':"Changes to review"}
          </h3>
          <p>{p.rationale}</p>
          {diff && (
            <section aria-label="Proposed changes">
              {diff.changes.length ? (
                <ul>
                  {[...changeGroups].map(([id,changes])=>{
                    if(!id)return <li key="scope">Execution scope and tool permissions: {p.workflow?.nodes.find(node=>node.id===p.workflow?.execution_policy.target_node_id)?.label??'all modules'}.</li>;
                    const node=p.workflow?.nodes.find(node=>node.id===id),spec=node?.tool_id==='workflow.custom_formula'&&node.inputs.spec?.kind==='literal'?node.inputs.spec.value:undefined;
                    const inputs=object(spec)&&object(spec.variables)?Object.entries(spec.variables).map(([name,value])=>object(value)?`${name} = ${value.value} ${value.unit}`:name):[...new Set(changes.filter(change=>change.kind==='binding').map(change=>change.input_name).filter((name):name is string=>!!name))].map(name=>({project:'scientific input plan',upstream_result:'previous module result',sequence:'selected sequence',results:'module results',package_file_id:'selected demonstration package'}[name]??name.replaceAll('_',' ')));
                    return <li key={id}>{node?.label??changes.find(change=>change.kind==='node')?.before??'Removed module'}{inputs.length?` — inputs: ${inputs.join('; ')}`:''}{changes.some(change=>change.kind==='tool')?' — calculation changed':''}{changes.some(change=>change.kind==='dependency')?' — dependencies updated':''}</li>;
                  })}
                </ul>
              ) : (
                <p>
                  No graph or permission changes. This prompt did not edit
                  scientific parameters.
                </p>
              )}
            </section>
          )}
          {!!p.missing_inputs.length && (
            <ul>
              {[...new Set(p.missing_inputs)].map((value) => (
                <li key={value}>{value.replaceAll("_", " ")}</li>
              ))}
            </ul>
          )}
          <button
            disabled={props.busy || p.status !== "proposed"}
            onClick={() => props.onDecision("accept")}
          >
            Accept changes
          </button>
          <button
            disabled={
              props.busy || !["proposed", "accepted"].includes(p.status)
            }
            onClick={() => props.onDecision("reject")}
          >
            Reject
          </button>
          {props.onRevise && (
            <button
              disabled={
                props.busy ||
                !["proposed", "accepted", "blocked"].includes(p.status)
              }
              onClick={() => {
                setIntent("modify");
                composer.current?.focus();
              }}
            >
              Modify
            </button>
          )}
        </article>
      )}
      {props.inputCheck}
      <label>
        {intent === "modify" && p ? "Modify this proposal" : "New request"}
        <textarea
          ref={composer}
          aria-label="Assistant message"
          value={props.objective}
          maxLength={8000}
          onChange={(event) => props.onObjective(event.target.value)}
          placeholder={
            props.mode === "template"
              ? "Request a registered task; this planner does not create arbitrary scientific models."
              : "Describe the task or change."
          }
        />
      </label>
      {props.mode === "hybrid" && (
        <label>
          <input
            type="checkbox"
            checked={props.permission}
            onChange={(event) => props.onPermission(event.target.checked)}
          />
          Allow this message and public evidence summary to be sent to the
          configured model
        </label>
      )}
      <button
        disabled={
          props.busy ||
          !props.canPlan ||
          (intent === "modify" && !props.objective.trim())
        }
        onClick={send}
      >
        Send
      </button>
      {intent === "modify" && (
        <button onClick={() => setIntent("new")}>New request instead</button>
      )}
    </section>
  );
}
