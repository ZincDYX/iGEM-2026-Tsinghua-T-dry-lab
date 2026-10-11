import { useEffect, useRef, useState } from "react";
import type { ProjectView } from "../contracts/generated";
import { parsePublic } from "../contracts/validation";
import { requestJson } from "../api";
import { ScientificFields, type FieldSchema } from "./ScientificFields";
import type { InputIssue } from "./PrecheckPanel";

type Scope = NonNullable<ProjectView["scientific_project"]>;
type Parameter = Scope["config"]["parameters"][number];
function ParameterValueInput({
  label,
  value,
  onChange,
  fieldPath,
}: {
  label: string;
  value: number | string;
  onChange: (value: number | string) => void;
  fieldPath?: string;
}) {
  const [numeric, setNumeric] = useState(typeof value === "number");
  return (
    <div>
      <label>
        {label} type
        <select
          aria-label={`${label} type`}
          value={numeric ? "number" : "text"}
          onChange={(e) => setNumeric(e.target.value === "number")}
        >
          <option value="number">Numeric</option>
          <option value="text">Explicit text</option>
        </select>
      </label>
      <label>
        {label}
        <input
          type={numeric ? "number" : "text"}
          data-input-path={fieldPath}
          step="any"
          value={value}
          onChange={(e) =>
            onChange(
              numeric && e.target.value !== ""
                ? e.target.valueAsNumber
                : e.target.value,
            )
          }
        />
      </label>
    </div>
  );
}
export function ScientificInputForms({
  project,
  section,
  onChange,
  schema,
  inputTarget,
}: {
  project: ProjectView;
  section: "constructs" | "parameters";
  onChange: (value: ProjectView) => void;
  schema?: FieldSchema;
  inputTarget?: InputIssue;
}) {
  const scope = project.scientific_project;
  const currentProject = useRef(project);
  currentProject.current = project;
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const [error, setError] = useState(""),
    [pending, setPending] = useState(false);
  const [editingIds, setEditingIds] = useState<Set<string>>(new Set());
  const [reason, setReason] = useState('');
  useEffect(() => setEditingIds(new Set()), [project.id, project.revision]);
  const [id, setId] = useState(""),
    [components, setComponents] = useState("");
  const [name, setName] = useState(""),
    [value, setValue] = useState(""),
    [unit, setUnit] = useState("");
  const [sourceType, setSourceType] = useState(""),
    [reference, setReference] = useState(""),
    [doi, setDoi] = useState("");
  const [construct, setConstruct] = useState(""),
    [condition, setCondition] = useState("");
  const addPanel = useRef<HTMLDetailsElement>(null),
    container = useRef<HTMLElement>(null);
  useEffect(() => {
    if (
      section !== "parameters" ||
      !inputTarget?.field_path.endsWith(".parameters") ||
      !scope
    )
      return;
    const matches = scope.config.parameters.filter(
      (p) =>
        p.name === inputTarget.code &&
        (p.construct_id === null ||
          p.construct_id === inputTarget.construct_id) &&
        (p.condition_id === null ||
          p.condition_id === inputTarget.condition_id),
    );
    if (matches.length) {
      const matchedIds = new Set(matches.map((p) => p.parameter_id));
      const panels = Array.from(
        container.current!.querySelectorAll<HTMLElement>(
          "[data-parameter-name]",
        ),
      ).filter((e) => matchedIds.has(e.dataset.parameterId!));
      panels.forEach((e) => e.scrollIntoView({ block: "center" }));
      if (panels.length === 1)
        panels[0]?.querySelector<HTMLInputElement>("input")?.focus();
      else
        setError(
          "Several compatible parameter records match this issue; review their individual source and scope. No record was selected automatically.",
        );
    } else {
      setName(inputTarget.code);
      setId("");
      setValue("");
      setUnit("");
      setSourceType("");
      setReference("");
      setDoi("");
      setConstruct(inputTarget.construct_id ?? "");
      setCondition(inputTarget.condition_id ?? "");
      if (addPanel.current) {
        addPanel.current.open = true;
        addPanel.current.scrollIntoView({ block: "center" });
        addPanel.current.querySelector<HTMLInputElement>("input")?.focus();
      }
    }
  }, [inputTarget, section]);
  if (!scope)
    return (
      <p>
        Attach a typed scientific project first; display imports do not supply
        missing scientific configuration.
      </p>
    );
  function change(config: Scope["config"]) {
    onChange({ ...project, scientific_project: { ...scope!, config } });
  }
  function updateParameter(index: number, patch: Partial<Parameter>) {
    if (!editingIds.has(scope!.config.parameters[index].parameter_id)) return;
    change({
      ...scope!.config,
      parameters: scope!.config.parameters.map((p, i) =>
        i !== index
          ? p
          : {
              ...p,
              ...patch,
              review_status: "extracted",
              approved_by: null,
              validation_flags: [],
              parameter_version:
                p.review_status === "approved"
                  ? p.parameter_version + 1
                  : p.parameter_version,
            },
      ),
    });
  }
  function overrideParameter(p: Parameter) {
    if (!reason.trim()) {setError('Explain why this source record needs an override.'); return;}
    const replacementId = `${p.parameter_id}:override:${crypto.randomUUID()}`;
    const timestamp = new Date().toISOString();
    const replacement: Parameter = {...p, parameter_id: replacementId, parameter_version: p.parameter_version+1,
      supersedes: p.parameter_id, derived_from: [...(p.derived_from ?? []), p.parameter_id],
      review_status: 'extracted', approved_by: null, validation_flags: [], created_at: timestamp, updated_at: timestamp,
      notes: `${p.notes ?? ''}\nOverride reason: ${reason.trim()}`};
    setEditingIds(current => new Set([...current, replacementId]));
    change({...scope!.config, parameters: [...scope!.config.parameters, replacement]});
    setError('');
  }
  async function add() {
    setError("");
    setPending(true);
    try {
      const raw =
        section === "constructs"
          ? {
              id,
              components: components
                .split(",")
                .map((c) => c.trim())
                .filter(Boolean),
            }
          : {
              parameter_id: id,
              name,
              value: Number(value),
              unit,
              source_type: sourceType,
              source_reference: reference || null,
              doi: doi || null,
              construct_id: construct || null,
              condition_id: condition || null,
            };
      const record = parsePublic(
        "ScientificRecordView",
        await requestJson("/scientific-records/preview", {
          kind: section === "constructs" ? "construct" : "parameter",
          value: raw,
        }),
      );
      if (!mounted.current) return;
      if (currentProject.current !== project)
        throw Error(
          "Inputs changed while validating; retry against the current draft.",
        );
      if (section === "constructs" && record.construct_record) {
        if (scope!.config.inputs.constructs.some((c) => c.id === id))
          throw Error("Construct ID already exists.");
        change({
          ...scope!.config,
          inputs: {
            ...scope!.config.inputs,
            constructs: [
              ...scope!.config.inputs.constructs,
              record.construct_record,
            ],
          },
        });
      } else if (record.parameter) {
        if (scope!.config.parameters.some((p) => p.parameter_id === id))
          throw Error("Parameter ID already exists.");
        change({
          ...scope!.config,
          parameters: [...scope!.config.parameters, record.parameter],
        });
        setEditingIds(current => new Set([...current, record.parameter!.parameter_id]));
      }
      setId("");
      setValue("");
    } catch (e) {
      setError(String(e));
    } finally {
      setPending(false);
    }
  }
  return (
    <section
      ref={container}
      id={section === "parameters" ? "input-parameters" : undefined}
    >
      {error && <p role="alert">{error}</p>}
      {section === "constructs" ? (
        scope.config.inputs.constructs.map((c, index) => {
          const update = (patch: Partial<typeof c>) =>
            change({
              ...scope.config,
              inputs: {
                ...scope.config.inputs,
                constructs: scope.config.inputs.constructs.map((v, i) =>
                  i === index ? { ...v, ...patch, m1_review: null } : v,
                ),
              },
            });
          return (
            <fieldset key={c.id}>
              <legend>Construct {c.id}</legend>
              <p>
                Editing invalidates the stored construct M1 review; it does not
                infer topology.
              </p>
              {(
                [
                  "fusion_orientation",
                  "localization_design_evidence",
                  "coding_dna",
                  "sequence_source_ref",
                ] as const
              ).map((key) => (
                <label key={key}>
                  {c.id} {key}
                  <input
                    value={c[key] ?? ""}
                    onChange={(e) => update({ [key]: e.target.value || null })}
                  />
                </label>
              ))}
              <label>
                {c.id} localization
                <select
                  value={c.localization_context ?? ""}
                  onChange={(e) =>
                    update({
                      localization_context: (e.target.value ||
                        null) as typeof c.localization_context,
                    })
                  }
                >
                  <option value="">Not declared</option>
                  <option value="cytosolic">cytosolic</option>
                  <option value="er_anchored">er_anchored</option>
                </select>
              </label>
              {!c.parts.length && (
                <label>
                  {c.id} ordered components (comma separated)
                  <input
                    value={c.components.join(", ")}
                    onChange={(e) =>
                      update({
                        components: e.target.value
                          .split(",")
                          .map((v) => v.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </label>
              )}
              {!schema &&
                c.parts.map((part, i) => (
                  <div key={i}>
                    <label>
                      {c.id} part {i + 1} ID
                      <input
                        value={part.id}
                        onChange={(e) =>
                          update({
                            parts: c.parts.map((p, j) =>
                              j === i ? { ...p, id: e.target.value } : p,
                            ),
                          })
                        }
                      />
                    </label>
                    <label>
                      {c.id} part {i + 1} sequence
                      <input
                        value={part.sequence ?? ""}
                        onChange={(e) =>
                          update({
                            parts: c.parts.map((p, j) =>
                              j === i
                                ? { ...p, sequence: e.target.value || null }
                                : p,
                            ),
                          })
                        }
                      />
                    </label>
                    <button
                      disabled={!i}
                      onClick={() => {
                        const parts = [...c.parts];
                        [parts[i - 1], parts[i]] = [parts[i], parts[i - 1]];
                        update({ parts });
                      }}
                    >
                      Move part up
                    </button>
                  </div>
                ))}
              {schema && (
                <ScientificFields
                  schema={{
                    ...schema.$defs!.ConstructDefinition,
                    properties: Object.fromEntries(
                      Object.entries(
                        schema.$defs!.ConstructDefinition.properties!,
                      ).filter(
                        ([key]) =>
                          ![
                            "id",
                            "components",
                            "fusion_orientation",
                            "localization_context",
                            "localization_design_evidence",
                            "coding_dna",
                            "sequence_source_ref",
                            "m1_review",
                          ].includes(key),
                      ),
                    ),
                  }}
                  definitions={schema.$defs!}
                  path={`scientific_project.config.inputs.constructs.${index}`}
                  value={c}
                  onChange={(v) => update(v as Partial<typeof c>)}
                  files={[...project.files, ...scope.evidence_files]}
                />
              )}
            </fieldset>
          );
        })
      ) : (
        <>
          <h3>Typed parameters</h3>
          <p>
            Blank values are not zero. Original source records are retained.
            Create an override to edit a new, unapproved version. Until that
            version is separately approved, it is not used instead of an
            existing approved source record.
          </p>
          <label>Reason for parameter override<input aria-label="Reason for parameter override" value={reason} onChange={event => setReason(event.target.value)}/></label>
          <table aria-label="Parameter source records"><thead><tr><th>Name</th><th>Value</th><th>Unit</th><th>Source</th><th>Condition</th><th>Status</th></tr></thead>
            <tbody>{scope.config.parameters.map(p => <tr key={p.parameter_id}><td>{p.name}</td><td>{p.value === '' ? 'Missing' : p.value}</td><td>{p.unit ?? 'Missing'}</td>
              <td>{p.source_reference ?? 'Missing'} · {p.source_type}</td><td>{p.condition_id ?? 'Not scoped'}</td><td>{p.review_status}</td></tr>)}</tbody></table>
          {scope.config.parameters.map((p, i) => (
            <section key={p.parameter_id}>
            <fieldset
              disabled={!editingIds.has(p.parameter_id)}
              data-parameter-name={p.name}
              data-parameter-id={p.parameter_id}
            >
              <legend>{p.name} · version {p.parameter_version}</legend>
              <p>
                Review {p.review_status} · version {p.parameter_version} ·
                reviewer {p.approved_by ?? "Not approved"}
              </p>
              <ParameterValueInput
                fieldPath={`scientific_project.config.parameters.${i}.value`}
                label={`${p.name} v${p.parameter_version} value`}
                value={p.value}
                onChange={(value) => updateParameter(i, { value })}
              />
              <label>
                {p.name} v{p.parameter_version} name
                <input
                  value={p.name}
                  onChange={(e) => updateParameter(i, { name: e.target.value })}
                />
              </label>
              {schema && (
                <ScientificFields
                  schema={{
                    ...schema.$defs!.ParameterRecord,
                    properties: Object.fromEntries(
                      Object.entries(
                        schema.$defs!.ParameterRecord.properties!,
                      ).filter(
                        ([key]) =>
                          ![
                            "parameter_id",
                            "name",
                            "value",
                            "unit",
                            "source_type",
                            "source_reference",
                            "doi",
                            "evidence_text",
                            "evidence_location",
                            "construct_id",
                            "condition_id",
                            "uncertainty",
                            "review_status",
                            "approved_by",
                            "validation_flags",
                            "parameter_version",
                            "created_at",
                            "updated_at",
                            "supersedes",
                            "derived_from",
                          ].includes(key),
                      ),
                    ),
                  }}
                  definitions={schema.$defs!}
                  path={`scientific_project.config.parameters.${i}`}
                  value={p}
                  onChange={(v) => updateParameter(i, v as Partial<Parameter>)}
                  files={[...project.files, ...scope.evidence_files]}
                />
              )}
              {(
                [
                  "unit",
                  "source_reference",
                  "doi",
                  "evidence_text",
                  "evidence_location",
                  "construct_id",
                  "condition_id",
                ] as const
              ).map((key) => (
                <label key={key}>
                  {p.name} v{p.parameter_version} {key}
                  <input
                    value={p[key] ?? ""}
                    onChange={(e) =>
                      updateParameter(i, { [key]: e.target.value || null })
                    }
                  />
                </label>
              ))}
              <label>
                {p.name} v{p.parameter_version} source type
                <select
                  value={p.source_type}
                  onChange={(e) =>
                    updateParameter(i, {
                      source_type: e.target.value as Parameter["source_type"],
                    })
                  }
                >
                  {["literature", "wetlab", "prediction", "assumption"].map(
                    (t) => (
                      <option key={t}>{t}</option>
                    ),
                  )}
                </select>
              </label>
              {(["value", "lower", "upper"] as const).map((key) => (
                <label key={key}>
                  {p.name} v{p.parameter_version} uncertainty {key}
                  <input
                    type="number"
                    step="any"
                    value={p.uncertainty?.[key] ?? ""}
                    onChange={(e) =>
                      updateParameter(i, {
                        uncertainty: {
                          value: null,
                          lower: null,
                          upper: null,
                          type: null,
                          ...p.uncertainty,
                          [key]:
                            e.target.value === ""
                              ? null
                              : Number(e.target.value),
                        },
                      })
                    }
                  />
                </label>
              ))}
              <label>
                {p.name} v{p.parameter_version} uncertainty type
                <input
                  value={p.uncertainty?.type ?? ""}
                  onChange={(e) =>
                    updateParameter(i, {
                      uncertainty: {
                        value: null,
                        lower: null,
                        upper: null,
                        ...p.uncertainty,
                        type: e.target.value || null,
                      },
                    })
                  }
                />
              </label>
            </fieldset>
            {!editingIds.has(p.parameter_id) && <button disabled={!reason.trim()} onClick={() => overrideParameter(p)}>Create override for {p.name}</button>}
            <p>{p.supersedes ? 'New source-linked override; review required.' : 'Original source record; editing requires a new version.'} {p.notes}</p>
            <button disabled={!reason.trim() || p.review_status === 'rejected'} onClick={() => change({...scope.config,
              parameters: scope.config.parameters.map((record,index) => index === i ? {...record,review_status:'rejected',approved_by:null,
                validation_flags:[],notes:`${record.notes ?? ''}\nRemoved from calculation: ${reason.trim()}`} : record)})}>Remove {p.name} from calculation (retain source)</button>
            </section>
          ))}
        </>
      )}
      <details ref={addPanel}>
        <summary>
          Add {section === "constructs" ? "construct" : "parameter"}
        </summary>
        <fieldset disabled={pending}>
          <label>
            New record ID
            <input value={id} onChange={(e) => setId(e.target.value)} />
          </label>
          {section === "constructs" ? (
            <label>
              Ordered component IDs (comma separated)
              <input
                value={components}
                onChange={(e) => setComponents(e.target.value)}
              />
            </label>
          ) : (
            <>
              <label>
                Parameter name
                <input value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              <label>
                Numeric parameter value
                <input
                  type="number"
                  step="any"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                />
              </label>
              <label>
                Explicit parameter unit
                <input value={unit} onChange={(e) => setUnit(e.target.value)} />
              </label>
              <label>
                Parameter source type
                <select
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                >
                  <option value="">Choose explicitly</option>
                  {["literature", "wetlab", "prediction", "assumption"].map(
                    (t) => (
                      <option key={t}>{t}</option>
                    ),
                  )}
                </select>
              </label>
              <label>
                Parameter source reference
                <input
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                />
              </label>
              <label>
                Parameter DOI
                <input value={doi} onChange={(e) => setDoi(e.target.value)} />
              </label>
              <label>
                New parameter construct scope
                <input
                  value={construct}
                  onChange={(e) => setConstruct(e.target.value)}
                />
              </label>
              <label>
                New parameter condition scope
                <input
                  value={condition}
                  onChange={(e) => setCondition(e.target.value)}
                />
              </label>
            </>
          )}
          <button
            disabled={
              !id.trim() ||
              (section === "constructs"
                ? !components.trim()
                : !name.trim() || !value.trim() || !unit.trim() || !sourceType)
            }
            onClick={() => void add()}
          >
            Validate and add to draft
          </button>
        </fieldset>
      </details>
    </section>
  );
}
