import { useState, type ReactNode } from "react";
import type { ModuleMethodView, ProjectView } from "../contracts/generated";
import { show } from "../contracts/resultAdapters";
import { ParameterTable } from "./ParameterTable";
import { BoundFormula } from "./BoundFormula";
import { object } from "../contracts/validation";

export function ModuleParameters({
  project,
  method,
  frozen,
  onChange,
  onScalarChange,
  onReview,
  renderFormula,
  onEditMethod,
}: {
  project: ProjectView;
  method: ModuleMethodView;
  frozen: boolean;
  onChange: (value: ProjectView) => Promise<void>;
  onScalarChange: (name: string, value: number, unit: string) => Promise<void>;
  onReview?: (id: string, name: string) => void;
  renderFormula?: (latex: string) => ReactNode;
  onEditMethod?: (methodId: string, formulaId: string) => void;
}) {
  const [binding, setBinding] = useState<string>(),
    [sourceId, setSourceId] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [context, setContext] = useState("");
  const rows = method.parameter_records.filter(
    (record) =>
      !method.parameter_records.some(
        (other) => other.supersedes === record.parameter_id,
      ),
  );
  const key = (row: Record<string, unknown>) =>
    JSON.stringify([row.construct_id ?? null, row.condition_id ?? null]);
  const contexts = [...new Set(rows.map(key))],
    chosen = contexts.includes(context) ? context : contexts[0];
  const boundRows = rows.filter((row) => key(row) === chosen);
  const formulaInputs = method.formula_inputs ?? [];
  const sourceLabel=(value:unknown)=>typeof value==='string'&&value.startsWith('asset:')?'Registered source file':show(value);
  const [formulaChoice,setFormulaChoice]=useState(''),[variantChoice,setVariantChoice]=useState('');
  const equations=method.methods.flatMap(definition=>definition.formulas.map(formula=>({definition,formula,key:definition.id+':'+formula.id})));
  const active=equations.find(item=>item.key===formulaChoice)??equations.find(item=>formulaInputs.some(binding=>binding.method_id===item.definition.id&&binding.formula_id===item.formula.id&&Array.isArray(binding.input_names)&&boundRows.some(row=>(binding.input_names as unknown[]).includes(row.name))))??equations[0];
  const variants=formulaInputs.filter(item=>item.method_id===active?.definition.id&&item.formula_id===active?.formula.id);
  const variant=variants.find(item=>item.symbol===variantChoice)??variants[0];
  const covered = new Set(
    formulaInputs.flatMap((item) =>
      Array.isArray(item.input_names)
        ? item.input_names.filter(
            (name): name is string => typeof name === "string",
          )
        : [],
    ),
  );
  const formulaRecords = Object.fromEntries(
    boundRows
      .filter(
        (row) => typeof row.value === "number" && covered.has(String(row.name))&&boundRows.filter(other=>other.name===row.name).length===1,
      )
      .map((row) => [String(row.name), row]),
  );
  const formulaVariables = Object.fromEntries(
    Object.entries(formulaRecords).map(([name, row]) => [
      name,
      {
        value: row.value as number,
        unit: String(row.unit),
        readOnly:
          row.binding_read_only === true || row.derivation_type === "model_fit",
      },
    ]),
  );
  async function publish(
    original: NonNullable<
      ProjectView["scientific_project"]
    >["config"]["parameters"][number],
    replacement: typeof original,
  ) {
    const scope = project.scientific_project!,
      config = structuredClone(scope.config);
    config.parameters.push(replacement);
    for (const path of method.parameter_model_paths?.[original.parameter_id] ??
      []) {
      let quantity: unknown = config;
      for (const key of path)
        quantity = (quantity as Record<string, unknown>)[key];
      if (
        !object(quantity) ||
        quantity.parameter_id !== original.parameter_id ||
        quantity.value !== original.value ||
        quantity.unit !== original.unit
      )
        throw Error(
          "The model binding changed. Reopen this module before editing.",
        );
      quantity.parameter_id = replacement.parameter_id;
      quantity.value = replacement.value;
      quantity.unit = replacement.unit;
      quantity.source_reference = replacement.source_reference;
    }
    await onChange({ ...project, scientific_project: { ...scope, config } });
  }
  async function save(id: string, value: number, unit: string) {
    const scope = project.scientific_project!;
    const original = scope.config.parameters.find(
      (p) => p.parameter_id === id,
    )!;
    const timestamp = new Date().toISOString();
    const replacement = {
      ...original,
      parameter_id: crypto.randomUUID(),
      value,
      unit,
      parameter_version: original.parameter_version + 1,
      supersedes: original.parameter_id,
      review_status: "extracted" as const,
      approved_by: null,
      uncertainty: null,
      validation_flags: ["requires_human_approval_before_model_use"],
      updated_at: timestamp,
      created_at: timestamp,
      notes: `${original.notes}\nUnreviewed value override: ${original.value} ${original.unit} → ${value} ${unit}. Original source retained for comparison, not confirmation of this value.`,
    };
    await publish(original, replacement);
  }
  async function bindSource() {
    const scope = project.scientific_project!;
    const original = scope.config.parameters.find(
      (p) => p.parameter_id === binding,
    )!;
    const source = scope.config.parameters.find(
      (p) => p.parameter_id === sourceId,
    )!;
    const timestamp = new Date().toISOString();
    setBusy(true);
    setError("");
    try {
      const replacement = {
        ...source,
        parameter_id: crypto.randomUUID(),
        parameter_version: original.parameter_version + 1,
        supersedes: original.parameter_id,
        review_status: "extracted" as const,
        approved_by: null,
        validation_flags: ["requires_human_approval_before_model_use"],
        created_at: timestamp,
        updated_at: timestamp,
        notes: `${source.notes}\nRebound from existing compatible evidence; review this new version before formal use.`,
      };
      await publish(original, replacement);
      setBinding(undefined);
      setSourceId("");
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }
  const scalar = method.scalar_method?.execution_spec;
  return (
    <section aria-label="Module parameters">
      {error && <p role="alert">{error}</p>}
      {!!formulaInputs.length && contexts.length > 1 && (
        <label>
          Model context
          <select
            aria-label="Formula model context"
            value={chosen}
            onChange={(event) => setContext(event.target.value)}
          >
            {contexts.map((value, index) => (
              <option key={value} value={value}>
                {String(
                  rows.find((row) => key(row) === value)?.construct_id ??
                    "Shared model",
                )}{" "}
                — condition group {index + 1}
              </option>
            ))}
          </select>
        </label>
      )}
      {renderFormula&&equations.length>1&&<label>Formula<select aria-label="Formula" value={active.key} onChange={event=>{setFormulaChoice(event.target.value);setVariantChoice('');}}>{equations.map(item=><option key={item.key} value={item.key}>{item.formula.title}</option>)}</select></label>}
      {renderFormula &&
        method.methods.filter(definition=>definition.id===active?.definition.id).map((definition) => (
          <section key={definition.id}>
            {definition.formulas.filter(formula=>formula.id===active?.formula.id).map((formula) => (
              <section key={formula.id}>
                <h4>{formula.title}</h4>
                {renderFormula(formula.latex)}
                {!!formula.assumptions.length&&<p>{formula.assumptions.join(' ')}</p>}
                {variants.length>1&&<label>Relation<select aria-label="Formula relation" value={String(variant?.symbol??'')} onChange={event=>setVariantChoice(event.target.value)}>{variants.map(item=><option key={String(item.symbol)} value={String(item.symbol)}>{String(item.symbol)}</option>)}</select></label>}
                {formulaInputs
                  .filter(
                    (item) =>
                      item.method_id === definition.id &&
                      item.formula_id === formula.id &&
                      item.symbol===variant?.symbol&&
                      object(item.tree),
                  )
                  .map((item, index) => (
                    <div key={index}>
                      <span>{String(item.symbol)} =</span>
                      <BoundFormula
                        tree={item.tree as Record<string, unknown>}
                        variables={formulaVariables}
                        missing=""
                        frozen={frozen}
                        onSave={(name, value, unit) =>
                          save(
                            String(formulaRecords[name].parameter_id),
                            value,
                            unit,
                          )
                        }
                        actions={(name) => {
                          const record = formulaRecords[name];
                          return (
                            record && (
                              <span><small>{['extracted','validated'].includes(String(record.review_status))?'Pending review':`v${show(record.parameter_version)}`}</small><details>
                                <summary>Source: {name}</summary>
                                <p>
                                  {sourceLabel(record.source_reference)}; version{" "}
                                  {show(record.parameter_version)} —{" "}
                                  {show(record.review_status)}
                                </p>
                                {!frozen &&
                                  ["extracted", "validated"].includes(
                                    String(record.review_status),
                                  ) &&
                                  onReview && (
                                    <button
                                      onClick={() =>
                                        onReview(
                                          String(record.parameter_id),
                                          name,
                                        )
                                      }
                                    >
                                      Review this value
                                    </button>
                                  )}
                                {!frozen &&
                                  !record.binding_read_only &&
                                  !!method.parameter_source_options?.[
                                    String(record.parameter_id)
                                  ]?.length && (
                                    <button
                                      onClick={() => {
                                        setBinding(String(record.parameter_id));
                                        setSourceId("");
                                      }}
                                    >
                                      Choose existing source
                                    </button>
                                  )}
                              </details></span>
                            )
                          );
                        }}
                      />
                    </div>
                  ))}
                {!frozen &&
                  formula.status !== "undefined_in_source" &&
                  onEditMethod && (
                    <button
                      onClick={() => onEditMethod(definition.id, formula.id)}
                    >
                      Edit method: {formula.title}
                    </button>
                  )}
              </section>
            ))}
          </section>
        ))}
      {scalar ? (
        <ParameterTable
          frozen={frozen}
          rows={Object.entries(scalar.variables).map(([name, v]) => ({
            id: name,
            name,
            ...v,
            status: "exploratory",
          }))}
          onSave={onScalarChange}
        />
      ) : (
        <ParameterTable
          frozen={frozen}
          rows={[
            ...rows
              .filter((record) => formulaRecords[String(record.name)]?.parameter_id !== record.parameter_id)
              .map((record) => ({
                id: String(record.parameter_id),
                name: String(record.name),
                value:
                  typeof record.value === "number"
                    ? record.value
                    : show(record.value),
                unit: show(record.unit),
                source: `${sourceLabel(record.source_reference)}. ${show(record.review_status)}; version ${show(record.parameter_version)}.${record.binding_reason ? " " + record.binding_reason : ""}`,
                readOnly:
                  record.derivation_type === "model_fit" ||
                  record.binding_read_only === true,
                status:
                  record.binding_read_only === true
                    ? "versioned model binding · read-only"
                    : record.derivation_type === "model_fit"
                      ? "calculated result"
                      : ["extracted", "validated"].includes(
                            String(record.review_status),
                          )
                        ? "pending review · not used yet"
                        : undefined,
              })),
            ...method.parameter_requirements
              .filter(
                (requirement) => !rows.some((p) => p.name === requirement.name),
              )
              .map((requirement) => ({
                id: String(requirement.name),
                name: String(requirement.name),
                value: "Required · add evidence in Inputs",
                unit: show(requirement.canonical_unit),
                readOnly: true,
              })),
          ]}
          onSave={save}
          sourceActions={(row) =>
            !frozen &&
            !row.readOnly && (
              <>
                {!!method.parameter_source_options?.[row.id]?.length && (
                  <button
                    disabled={busy}
                    onClick={() => {
                      setBinding(row.id);
                      setSourceId("");
                    }}
                  >
                    Choose existing source
                  </button>
                )}
                {row.status === "pending review · not used yet" && onReview && (
                  <button onClick={() => onReview(row.id, row.name)}>
                    Review this value
                  </button>
                )}
              </>
            )
          }
        />
      )}
      {binding && (
        <fieldset disabled={busy}>
          <legend>Choose existing compatible evidence</legend>
          <label>
            Source
            <select
              aria-label="Parameter source"
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
            >
              <option value="">Choose a reviewed source</option>
              {project.scientific_project?.config.parameters
                .filter((p) =>
                  method.parameter_source_options?.[binding]?.includes(
                    p.parameter_id,
                  ),
                )
                .map((p) => (
                  <option key={p.parameter_id} value={p.parameter_id}>
                    {p.source_reference ?? p.name} · {p.value} {p.unit}
                  </option>
                ))}
            </select>
          </label>
          <button disabled={!sourceId} onClick={() => void bindSource()}>
            Bind source as new version
          </button>
          <button onClick={() => setBinding(undefined)}>Cancel</button>
          <p>
            Only compatible reviewed sources are offered. Import new evidence in
            Inputs. This new version still requires review.
          </p>
        </fieldset>
      )}
      {!scalar &&
        !rows.length &&
        !method.parameter_requirements.length &&
        !method.workflow_numeric_inputs?.length && (
          <p>
            No editable parameter bindings in this module. Fixed baseline rules
            and imported model definitions remain read-only; changing their
            display would not change execution.
          </p>
        )}
    </section>
  );
}
