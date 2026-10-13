import { useEffect, useRef, useState } from "react";
import temml from "temml";
import "temml/dist/Temml-Local.css";
import type {
  MethodDefinition,
  MethodDraftView,
  ModuleMethodView,
  ProjectView,
  Workflow,
} from "../contracts/generated";
import { requestJson } from "../api";
import { parsePublicAsync } from "../contracts/validation";
import { ModuleParameters } from "./ModuleParameters";
import { BoundFormula } from "./BoundFormula";
import { ParameterTable } from "./ParameterTable";
import * as client from "./client";

export function Formula({ latex }: { latex: string }) {
  const element = useRef<HTMLDivElement>(null),
    [error, setError] = useState("");
  useEffect(() => {
    setError("");
    try {
      const markup = temml.renderToString(latex, {
        displayMode: true,
        xml: true,
        trust: false,
        throwOnError: true,
        maxExpand: 1000,
        maxSize: [20, 200],
      });
      const parsed = new DOMParser().parseFromString(markup, "application/xml");
      if (
        parsed.documentElement.localName !== "math" ||
        parsed.querySelector("parsererror")
      )
        throw Error("Invalid MathML output.");
      element.current!.replaceChildren(
        document.importNode(parsed.documentElement, true),
      );
    } catch {
      element.current!.replaceChildren();
      setError(
        "Formula display unavailable. The stored method and calculation are unchanged.",
      );
    }
  }, [latex]);
  return (
    <>
      <div ref={element} className="method-formula" />
      {error && <p role="alert">{error}</p>}
    </>
  );
}

function FormulaEditor({
  project,
  method,
  formulaId,
  initial,
  onSaved,
  onClose,
}: {
  project: ProjectView;
  method: MethodDefinition;
  formulaId: string;
  initial?: MethodDraftView;
  onSaved: (workflow: Workflow) => Promise<void>;
  onClose: () => void;
}) {
  const original = method.formulas.find((formula) => formula.id === formulaId)!;
  const [expression, setExpression] = useState(
      initial?.execution_spec?.expression ?? "",
    ),
    [unit, setUnit] = useState(initial?.execution_spec?.output_unit ?? "");
  const [title, setTitle] = useState(initial?.title ?? original.title),
    [reason, setReason] = useState(""),
    [source, setSource] = useState(initial?.source_reference ?? "");
  const [variables, setVariables] = useState(
    Object.entries(initial?.execution_spec?.variables ?? {}).map(
      ([name, v]) => ({ name, ...v, value: String(v.value) }),
    ),
  );
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const incomplete =
    !expression.trim() ||
    !unit.trim() ||
    !title.trim() ||
    !reason.trim() ||
    !source.trim() ||
    !variables.length ||
    variables.some(
      (v) =>
        !v.name ||
        !v.value.trim() ||
        !Number.isFinite(Number(v.value)) ||
        !v.unit,
    ) ||
    new Set(variables.map((v) => v.name)).size !== variables.length;
  async function save() {
    setBusy(true);
    setError("");
    try {
      const saved = await client.saveMethodDraft(project.id, {
        base_method_id: method.id,
        base_version: method.version,
        formula_id: formulaId,
        title,
        latex: original.latex,
        reason,
        source_reference: source,
        previous_id: initial?.id ?? null,
        expected_project_revision: project.revision,
        execution_spec: {
          expression,
          output_unit: unit,
          variables: Object.fromEntries(
            variables.map((v) => [
              v.name,
              {
                value: Number(v.value),
                unit: v.unit,
                source: v.source || source,
              },
            ]),
          ),
        },
      });
      await onSaved(await client.methodWorkflow(project.id, saved.id));
      onClose();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section aria-label="Edit method">
      <h4>New exploratory scalar version — {original.title}</h4>
      <Formula latex={original.latex} />
      <p>
        The baseline is unchanged. This editor supports scalar expressions, not
        arbitrary reaction networks or ODEs.
      </p>
      {error && <p role="alert">{error}</p>}
      <fieldset disabled={busy}>
        <label>
          Title
          <input
            aria-label="Custom formula title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <label>
          Expression
          <input
            aria-label="Executable scalar expression"
            value={expression}
            onChange={(event) => setExpression(event.target.value)}
          />
        </label>
        <label>
          Result unit
          <input
            aria-label="Formula result unit"
            value={unit}
            onChange={(event) => setUnit(event.target.value)}
          />
        </label>
        <table aria-label="Formula parameter bindings">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Value</th>
              <th>Unit</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {variables.map((v, index) => (
              <tr key={index}>
                {(["name", "value", "unit"] as const).map((field) => (
                  <td key={field}>
                    <input
                      aria-label={`Formula input ${index + 1} ${field}`}
                      value={v[field]}
                      onChange={(event) =>
                        setVariables((values) =>
                          values.map((row, i) =>
                            i === index
                              ? { ...row, [field]: event.target.value }
                              : row,
                          ),
                        )
                      }
                    />
                  </td>
                ))}
                <td>
                  <button
                    onClick={() =>
                      setVariables((values) =>
                        values.filter((_, i) => i !== index),
                      )
                    }
                  >
                    Remove input
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button
          disabled={variables.length >= 64}
          onClick={() =>
            setVariables((values) => [
              ...values,
              { name: "", value: "", unit: "", source: "" },
            ])
          }
        >
          Add formula input
        </button>
        <label>
          Source
          <input
            aria-label="Custom formula source"
            value={source}
            onChange={(event) => setSource(event.target.value)}
          />
        </label>
        <label>
          Change reason
          <textarea
            aria-label="Custom formula reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
        <button disabled={incomplete} onClick={() => void save()}>
          Save method version
        </button>
        <button onClick={onClose}>Cancel</button>
      </fieldset>
    </section>
  );
}

export function MethodPanel({
  project,
  toolId,
  runId,
  workflowId,
  nodeId,
  workflow,
  disabled,
  onChange,
  onReview,
  onPlan,
  onWorkflowChange,
  onEditDraft,
}: {
  project: ProjectView;
  toolId: string;
  runId?: string;
  workflowId?: string;
  nodeId: string;
  workflow?: Workflow;
  disabled: boolean;
  onChange: (value: ProjectView) => Promise<void>;
  onReview: (
    id: string,
    stage: "m3" | "m4",
    name: string,
    reviewer: string,
    reason: string,
  ) => Promise<void>;
  onPlan: (workflow: Workflow) => void;
  onWorkflowChange: (workflow: Workflow) => Promise<void>;
  onEditDraft: () => void;
}) {
  const [value, setValue] = useState<ModuleMethodView>(),
    [error, setError] = useState(""),
    [refresh, setRefresh] = useState(0);
  const [loading,setLoading]=useState(true);
  const [documentOpen, setDocumentOpen] = useState(false),
    [toolsOpen, setToolsOpen] = useState(false);
  const [versions,setVersions]=useState<Awaited<ReturnType<typeof client.methodDrafts>>>(),[versionsOpen,setVersionsOpen]=useState(false),[versionOffset,setVersionOffset]=useState(0);
  const [editor, setEditor] = useState<{
    method: MethodDefinition;
    formulaId: string;
  }>();
  const [review, setReview] = useState<{ id: string; name: string }>(),
    [reviewer, setReviewer] = useState(""),
    [reason, setReason] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setLoading(true);
    const query = new URLSearchParams({ tool_id: toolId, node_id: nodeId });
    if (runId) query.set("run_id", runId);
    else if (workflowId) query.set("workflow_id", workflowId);
    void requestJson(
      `/projects/${encodeURIComponent(project.id)}/module-method?${query}`,
      undefined,
      controller.signal,
    )
      .then((raw) => parsePublicAsync("ModuleMethodView", raw))
      .then((result) => {
        if (!controller.signal.aborted){setValue(result);setLoading(false);}
      })
      .catch((reason) => {
        if (!controller.signal.aborted){setError(String(reason));setValue(undefined);setLoading(false);}
      });
    return () => controller.abort();
  }, [
    project.id,
    project.revision,
    toolId,
    runId,
    workflowId,
    nodeId,
    refresh,
  ]);
  async function saveScalar(name: string, next: number, unit: string) {
    const original = value!.scalar_method!,
      spec = structuredClone(original.execution_spec!),
      before = spec.variables[name];
    spec.variables[name] = { ...before, value: next, unit };
    const saved = await client.saveMethodDraft(project.id, {
      base_method_id: original.base_method_id,
      base_version: original.base_version,
      formula_id: original.formula_id,
      title: original.title,
      latex: original.latex,
      reason: `User override of ${name}: ${before.value} ${before.unit} to ${next} ${unit}. Unvalidated exploratory input; source retained for comparison.`,
      source_reference: original.source_reference,
      previous_id: original.id,
      expected_project_revision: project.revision,
      execution_spec: spec,
    });
    await onWorkflowChange(await client.methodWorkflow(project.id, saved.id));
    setRefresh((value) => value + 1);
  }
  useEffect(()=>{
    if(!versionsOpen)return;let active=true;
    void client.methodDrafts(project.id,versionOffset).then(value=>{if(active)setVersions(value);}).catch(reason=>{if(active)setError(String(reason));});
    return()=>{active=false;};
  },[project.id,versionsOpen,versionOffset,refresh]);
  return (
    <section aria-label="Module method">
      {error && <p role="alert">{error}</p>}
      {runId && <p>Historical model — read-only.</p>}
      {loading&&<p>Updating model bindings…</p>}
      {value && (
        <>
          <header className="panel-heading">
            <h3>{value.scalar_method?.title ?? "Calculation"}</h3>
            <button onClick={() => setToolsOpen((value) => !value)}>
              Tools
            </button>
            <button onClick={() => setDocumentOpen((value) => !value)}>
              Method
            </button>
            <button onClick={()=>setVersionsOpen(value=>!value)}>Versions</button>
          </header>
          {toolsOpen && (
            <section>
              <h4>{value.tool.name}</h4>
              <p>{value.tool.description}</p>
              <p>
                {value.tool.runtime}; {value.tool.status.replaceAll("_", " ")}.{" "}
                {value.tool.license}
              </p>
            </section>
          )}
          {value.configured_mode&&<p>Configured model: {value.configured_mode.replaceAll('_',' ')}. Reference equations without an execution binding are read-only.</p>}
          {value.scalar_method?.execution_spec && value.scalar_expression ? (
            <>
              <Formula latex={value.scalar_method.latex} />
              <BoundFormula
                tree={value.scalar_expression}
                variables={value.scalar_method.execution_spec.variables}
                frozen={!!runId || disabled||loading}
                onSave={saveScalar}
              />
              <p>
                Version {value.scalar_method.version} — exploratory, not
                scientifically validated.
              </p>
              {!runId && (
                <button
                  disabled={disabled}
                  onClick={() =>
                    setEditor({
                      method: value.methods[0],
                      formulaId: value.scalar_method!.formula_id,
                    })
                  }
                >
                  Edit method
                </button>
              )}
            </>
          ) : (
            <>
              <ModuleParameters
                project={project}
                method={value}
                frozen={!!runId || disabled||loading}
                onChange={onChange}
                onScalarChange={saveScalar}
                onReview={(id, name) => {
                  setReview({ id, name });
                  setReviewer("");
                  setReason("");
                }}
                renderFormula={(latex) => <Formula latex={latex} />}
                onEditMethod={(methodId, formulaId) =>
                  setEditor({
                    method: value.methods.find((item) => item.id === methodId)!,
                    formulaId,
                  })
                }
              />
            </>
          )}
          {!!value.workflow_numeric_inputs?.length && workflow && (
            <ParameterTable
              frozen={!!runId || disabled||loading}
              rows={value.workflow_numeric_inputs.map((input) => ({
                id: String(input.name),
                name: String(input.name),
                value: Number(input.value),
                unit: String(input.unit),
              }))}
              onSave={async (name, next) => {
                const node = structuredClone(
                  workflow.nodes.find((node) => node.id === nodeId)!,
                );
                if (
                  node.inputs[name]?.kind !== "literal" ||
                  typeof node.inputs[name].value !== "number"
                )
                  throw Error("The input binding changed. Reopen the module.");
                node.inputs[name] = { kind: "literal", value: next };
                await onWorkflowChange({ ...workflow, nodes: [node] });
                setRefresh((value) => value + 1);
              }}
            />
          )}
          {documentOpen && (
            <section aria-label="Method document">
              {value.methods.map((method) => (
                <section key={method.id}>
                  <h4>{method.title}</h4>
                  <p>{method.scope}</p>
                  {method.formulas.map(formula=><section key={formula.id}><h5>{formula.title}</h5><Formula latex={formula.latex}/><p>{formula.assumptions.join(' ')}</p></section>)}
                  <p>
                    {method.source_reference} — {method.source_version}
                  </p>
                  <dl>
                    {Object.entries(method.symbols).map(
                      ([name, description]) => (
                        <div key={name}>
                          <dt>{name}</dt>
                          <dd>{description}</dd>
                        </div>
                      ),
                    )}
                  </dl>
                  {method.steps.map((step) => (
                    <p key={step.id}>
                      <strong>{step.title}</strong>: {step.description}
                    </p>
                  ))}
                  <p>{method.tools.join(", ")}</p>
                  {method.discrepancies.map((text) => (
                    <p key={text}>{text}</p>
                  ))}
                </section>
              ))}
            </section>
          )}
          {versionsOpen&&<section aria-label="Method versions"><h4>Saved method versions</h4>
            {versions?.items.filter(item=>value.methods.some(method=>method.id===item.base_method_id)).map(item=><article key={item.id}><h5>{item.title} — version {item.version}</h5><p>{item.reason}</p><p>{item.source_reference}; unvalidated exploratory method.</p>
              <Formula latex={item.latex}/>{!runId&&item.executable&&<button disabled={disabled} onClick={()=>void client.methodWorkflow(project.id,item.id).then(onPlan).catch(reason=>setError(String(reason)))}>Review this version as a new plan</button>}
            </article>)}
            {(versionOffset>0||versions?.has_more)&&<nav><button disabled={!versionOffset} onClick={()=>setVersionOffset(value=>Math.max(0,value-20))}>Previous method versions</button><button disabled={!versions?.has_more} onClick={()=>setVersionOffset(value=>value+20)}>Next method versions</button></nav>}
          </section>}
          {editor && !runId && (
            <FormulaEditor
              key={editor.method.id + editor.formulaId}
              project={project}
              {...editor}
              initial={value.scalar_method ?? undefined}
              onClose={() => setEditor(undefined)}
              onSaved={async (next) => {
                if (value.scalar_method) await onWorkflowChange(next);
                else onPlan(next);
                setRefresh((value) => value + 1);
              }}
            />
          )}
          {review && !runId && (
            <section aria-label="Human parameter review">
              <h4>Review {review.name}</h4>
              <p>
                Review this new value and its source/condition. Approval of a
                plan does not approve its scientific inputs.
              </p>
              <label>
                Reviewer
                <input
                  aria-label="Reviewer name"
                  value={reviewer}
                  onChange={(event) => setReviewer(event.target.value)}
                />
              </label>
              <label>
                Reason
                <textarea
                  aria-label="Scientific review reason"
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                />
              </label>
              <button
                disabled={disabled || !reviewer.trim() || !reason.trim()}
                onClick={() =>
                  void onReview(
                    review.id,
                    toolId === "project.m3" ? "m3" : "m4",
                    review.name,
                    reviewer.trim(),
                    reason.trim(),
                  )
                    .then(() => setReview(undefined))
                    .catch((reason) => setError(String(reason)))
                }
              >
                Review this value
              </button>
              <button onClick={() => setReview(undefined)}>Cancel</button>
            </section>
          )}
        </>
      )}
    </section>
  );
}
