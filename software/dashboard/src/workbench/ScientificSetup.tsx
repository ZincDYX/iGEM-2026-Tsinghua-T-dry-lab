import { useEffect, useRef, useState } from "react";
import { requestJson } from "../api";
import { object, parsePublic } from "../contracts/validation";
import type {
  ProjectView,
  ScientificPreviewView,
} from "../contracts/generated";
import { ScientificFields, type FieldSchema } from "./ScientificFields";

export function useScientificSchema() {
  const [schema, setSchema] = useState<FieldSchema>(),
    [error, setError] = useState("");
  useEffect(() => {
    const c = new AbortController();
    void requestJson("/scientific-projects/form-schema", undefined, c.signal)
      .then((v) => {
        if (!object(v) || !object(v.$defs) || !object(v.properties))
          throw Error("Scientific form schema unavailable");
        if (!c.signal.aborted) setSchema(v as FieldSchema);
      })
      .catch((e) => {
        if (!c.signal.aborted) setError(String(e));
      });
    return () => c.abort();
  }, []);
  return { schema, error };
}
export function ScientificSetup({
  project,
  dirty,
  busy,
  onPreview,
  schema,
  schemaError,
}: {
  project: ProjectView;
  dirty: boolean;
  busy: boolean;
  onPreview: (v: ScientificPreviewView) => void;
  schema?: FieldSchema;
  schemaError: string;
}) {
  const [value, setValue] = useState<Record<string, unknown>>({
    execution: {},
    experimental_context: {},
    inputs: { enzymes: [], scaffolds: [], linkers: [], constructs: [] },
    stages: { m3_concentration: {}, m4_reaction: {} },
  });
  const [error, setError] = useState(""),
    [pending, setPending] = useState(false);
  const latest = useRef(project);
  latest.current = project;
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  return (
    <details id="input-scientific-setup">
      <summary>Create scientific configuration without YAML</summary>
      <p>
        Use saved registered files and explicitly declared model controls. No
        biological values or approvals are generated; missing experimental data
        still block the original scientific stages. Creation does not save or
        run.
      </p>
      {(error || schemaError) && <p role="alert">{error || schemaError}</p>}
      {dirty && (
        <p>Save registered files before creating the bound scientific draft.</p>
      )}
      <fieldset disabled={dirty || busy || pending}>
        {schema && (
          <ScientificFields
            schema={schema}
            definitions={schema.$defs!}
            value={value}
            onChange={(v) => setValue(v as Record<string, unknown>)}
            path="scientific_project.config"
            files={project.files}
          />
        )}
        <button
          disabled={!schema || !project.files.length}
          onClick={async () => {
            setPending(true);
            setError("");
            try {
              const v = parsePublic(
                "ScientificPreviewView",
                await requestJson("/scientific-projects/create-preview", {
                  project_id: project.id,
                  expected_revision: project.revision,
                  config: value,
                }),
              );
              if (mounted.current && latest.current === project) onPreview(v);
              else if (mounted.current)
                setError(
                  "Project changed; retry against current saved inputs.",
                );
            } catch (e) {
              if (mounted.current) setError(String(e));
            } finally {
              if (mounted.current) setPending(false);
            }
          }}
        >
          Validate scientific configuration
        </button>
      </fieldset>
    </details>
  );
}

export function ScientificSettings({
  project,
  onChange,
  schema,
}: {
  project: ProjectView;
  onChange: (v: ProjectView) => void;
  schema?: FieldSchema;
}) {
  const scope = project.scientific_project;
  if (!scope) return null;
  const files = [
    ...new Map(
      [...project.files, ...scope.evidence_files].map((f) => [f.id, f]),
    ).values(),
  ];
  function change(config: unknown) {
    const next = config as NonNullable<
      ProjectView["scientific_project"]
    >["config"];
    const refs = new Set<string>();
    function walk(v: unknown) {
      if (typeof v === "string" && v.startsWith("asset:")) refs.add(v);
      else if (Array.isArray(v)) v.forEach(walk);
      else if (object(v)) Object.values(v).forEach(walk);
    }
    walk(next);
    onChange({
      ...project,
      scientific_project: {
        ...scope!,
        config: next,
        evidence_files: [
          ...new Map(
            [
              ...scope!.evidence_files,
              ...files.filter((f) => refs.has(f.path)),
            ].map((f) => [f.id, f]),
          ).values(),
        ],
      },
    });
  }
  return (
    <details id="input-model-settings">
      <summary>Model controls and additional input declarations</summary>
      <p>
        Fields use the backend's original scientific contract. Editing does not
        run or approve anything; incompatible combinations are rejected when
        saved.
      </p>
      {schema && (
        <>
          <ScientificFields
            schema={schema.properties!.stages}
            definitions={schema.$defs!}
            value={scope.config.stages}
            onChange={(v) => change({ ...scope.config, stages: v })}
            path="scientific_project.config.stages"
            files={files}
          />
          <ScientificFields
            schema={{
              ...schema.$defs!.InputsConfig,
              properties: Object.fromEntries(
                Object.entries(schema.$defs!.InputsConfig.properties!).filter(
                  ([k]) => k !== "constructs",
                ),
              ),
            }}
            definitions={schema.$defs!}
            value={scope.config.inputs}
            onChange={(v) => change({ ...scope.config, inputs: v })}
            path="scientific_project.config.inputs"
            files={files}
          />
        </>
      )}
    </details>
  );
}
