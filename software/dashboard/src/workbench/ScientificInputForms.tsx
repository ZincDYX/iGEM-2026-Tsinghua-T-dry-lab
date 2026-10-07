import { useEffect, useRef, useState } from "react";
import type { ProjectView } from "../contracts/generated";
import { parsePublic } from "../contracts/validation";
import { requestJson } from "../api";

type Scope = NonNullable<ProjectView["scientific_project"]>;
type Parameter = Scope["config"]["parameters"][number];
function ParameterValueInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | string;
  onChange: (value: number | string) => void;
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
}: {
  project: ProjectView;
  section: "constructs" | "parameters";
  onChange: (value: ProjectView) => void;
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
  const [id, setId] = useState(""),
    [components, setComponents] = useState("");
  const [name, setName] = useState(""),
    [value, setValue] = useState(""),
    [unit, setUnit] = useState("");
  const [sourceType, setSourceType] = useState(""),
    [reference, setReference] = useState(""),
    [doi, setDoi] = useState("");
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
    <section id={section === "parameters" ? "input-parameters" : undefined}>
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
              {c.parts.map((part, i) => (
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
            </fieldset>
          );
        })
      ) : (
        <>
          <h3>Typed parameters</h3>
          <p>
            Blank values are not zero. Editing removes approval and validation
            flags; scientific approval requires a separate review.
          </p>
          {scope.config.parameters.map((p, i) => (
            <fieldset key={p.parameter_id}>
              <legend>Parameter {p.parameter_id}</legend>
              <p>
                Review {p.review_status} · version {p.parameter_version} ·
                reviewer {p.approved_by ?? "Not approved"}
              </p>
              <ParameterValueInput
                label={`${p.parameter_id} value`}
                value={p.value}
                onChange={(value) => updateParameter(i, { value })}
              />
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
                  {p.parameter_id} {key}
                  <input
                    value={p[key] ?? ""}
                    onChange={(e) =>
                      updateParameter(i, { [key]: e.target.value || null })
                    }
                  />
                </label>
              ))}
              <label>
                {p.parameter_id} source type
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
                  {p.parameter_id} uncertainty {key}
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
                {p.parameter_id} uncertainty type
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
          ))}
        </>
      )}
      <details>
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
