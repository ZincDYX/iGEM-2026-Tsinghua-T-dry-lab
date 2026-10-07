import { useEffect, useRef, useState } from "react";
import type {
  ProjectView,
  ImportView,
  ScientificPreviewView,
  ScientificPrecheckView,
} from "../contracts/generated";
import { object, parsePublic } from "../contracts/validation";
import * as client from "./client";
import { downloadResource } from "../api";
import { LazyJson } from "../contracts/LazyJson";
import { PrecheckPanel, type InputIssue } from "./PrecheckPanel";
import { ScientificBundleImporter } from "./ScientificBundleImporter";
import { ScientificInputForms } from "./ScientificInputForms";
import {
  ScientificSetup,
  ScientificSettings,
  useScientificSchema,
} from "./ScientificSetup";

export function InputEditor({
  project,
  busy,
  dirty,
  onChange,
  onEditing,
  action,
  inputCheck,
  checkStale,
  onCheck,
  onLocate,
  onOpenResource,
  inputTarget,
}: {
  project: ProjectView;
  busy: boolean;
  dirty: boolean;
  onChange: (value: ProjectView) => void;
  onEditing: (value: boolean) => void;
  action: (job: () => Promise<unknown>) => Promise<void>;
  inputCheck?: ScientificPrecheckView;
  checkStale: boolean;
  onCheck: () => void;
  onLocate: (issue: InputIssue) => void;
  onOpenResource: (fileId: string) => void;
  inputTarget?: InputIssue;
}) {
  const [kind, setKind] = useState("auto");
  const [preview, setPreview] = useState<ImportView>();
  const [scientific, setScientific] = useState<ScientificPreviewView>();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const { schema, error: schemaError } = useScientificSchema();
  useEffect(() => {
    if (!inputTarget) return;
    const target = Array.from(
      document.querySelectorAll<HTMLElement>("[data-input-path]"),
    ).find((e) => e.dataset.inputPath === inputTarget.field_path);
    if (!target) return;
    for (let p = target.parentElement; p; p = p.parentElement)
      if (p instanceof HTMLDetailsElement) p.open = true;
    target.scrollIntoView({ block: "center" });
    target.focus({ preventScroll: true });
  }, [inputTarget, schema]);
  const mounted = useRef(true);
  const epoch = useRef(0);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      ++epoch.current;
    };
  }, []);
  function change(value: ProjectView) {
    ++epoch.current;
    onChange(value);
  }
  function startEditor() {
    setText(JSON.stringify(project, null, 2));
    setEditing(true);
    onEditing(true);
  }
  const scope = project.scientific_project;
  return (
    <section aria-label="Project inputs and evidence">
      <header className="panel-heading">
        <h2>Inputs and evidence</h2>
        <span>revision {project.revision}</span>
      </header>
      <fieldset className="input-fields" disabled={busy || editing}>
        <label>
          Project name
          <input
            aria-label="Project name"
            value={project.name}
            onChange={(e) => change({ ...project, name: e.target.value })}
          />
        </label>
        <label>
          Project notes (not scientific conditions)
          <textarea
            value={project.description}
            onChange={(e) =>
              change({ ...project, description: e.target.value })
            }
          />
        </label>
        <section className="input-section">
          <h3>Import files</h3>
          <label>
            Data type
            <select
              value={kind}
              onChange={(e) => {
                ++epoch.current;
                setKind(e.target.value);
                setPreview(undefined);
              }}
            >
              <option value="auto">
                Sequence / table / display-only JSON / image / structure
              </option>
              <option value="pathway">pathway JSON</option>
              <option value="wetlab">WetLabResult Measurements JSON</option>
            </select>
          </label>
          <input
            aria-label="Import data file"
            type="file"
            accept=".fasta,.fa,.faa,.gb,.gbk,.genbank,.json,.csv,.tsv,.png,.jpg,.jpeg,.pdb,.cif,.mmcif"
            disabled={busy}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const stamp = epoch.current;
              void action(async () => {
                const value = await client.importFile(file, kind);
                if (mounted.current && stamp === epoch.current)
                  setPreview(value);
              });
            }}
          />
          {preview && (
            <div>
              <p>
                Preview: {preview.kind} · {preview.file.name}
              </p>
              <details>
                <summary>File provenance</summary>
                <p>SHA-256 {preview.file.sha256}</p>
              </details>
              <LazyJson value={preview.patch} />
              <button
                disabled={busy}
                onClick={() => {
                  const patch = preview.patch;
                  const draft = parsePublic("ProjectView", {
                    ...project,
                    ...patch,
                    files: [...project.files, preview.file],
                    datasets: Array.isArray(patch.datasets)
                      ? [...project.datasets, ...patch.datasets]
                      : project.datasets,
                  });
                  change(draft);
                  setPreview(undefined);
                }}
              >
                Confirm import into draft
              </button>
              <button onClick={() => setPreview(undefined)}>
                Discard import
              </button>
            </div>
          )}
        </section>
        <section id="input-conditions" className="input-section">
          {!scope && (
            <ScientificSetup
              project={project}
              dirty={dirty}
              busy={busy || editing}
              onPreview={setScientific}
              schema={schema}
              schemaError={schemaError}
            />
          )}
          <ScientificBundleImporter
            busy={busy || editing}
            action={action}
            onPreview={(value) => {
              ++epoch.current;
              setScientific(value);
            }}
          />
          {scientific && (
            <div>
              <p>
                Validated typed configuration, binding{" "}
                {scientific.scientific_project.evidence_files.length} original
                files; import does not approve evidence.
              </p>
              <LazyJson value={scientific.scientific_project} />
              <button
                disabled={busy}
                onClick={() => {
                  change({
                    ...project,
                    scientific_project: scientific.scientific_project,
                  });
                  setScientific(undefined);
                }}
              >
                Confirm scientific inputs into draft
              </button>
            </div>
          )}
          {scope ? (
            <>
              <p>
                Execution mode: {scope.config.execution.mode} · Authoritative
                conditions are below. Ordinary project notes do not enter
                computation.
              </p>
              <div className="field-grid">
                {(["host", "strain", "assay_system"] as const).map((key) => (
                  <label key={key}>
                    {key}
                    <input
                      value={scope.config.experimental_context[key] ?? ""}
                      onChange={(e) =>
                        change({
                          ...project,
                          scientific_project: {
                            ...scope,
                            config: {
                              ...scope.config,
                              experimental_context: {
                                ...scope.config.experimental_context,
                                [key]: e.target.value || null,
                              },
                            },
                          },
                        })
                      }
                    />
                  </label>
                ))}
                {(["temperature_c", "pH"] as const).map((key) => (
                  <label key={key}>
                    {key}
                    <input
                      aria-label={key}
                      type="number"
                      step="any"
                      value={scope.config.experimental_context[key] ?? ""}
                      onChange={(e) =>
                        change({
                          ...project,
                          scientific_project: {
                            ...scope,
                            config: {
                              ...scope.config,
                              experimental_context: {
                                ...scope.config.experimental_context,
                                [key]:
                                  e.target.value === ""
                                    ? null
                                    : Number(e.target.value),
                              },
                            },
                          },
                        })
                      }
                    />
                  </label>
                ))}
              </div>
              <p>
                Network {scope.config.stages.m4_reaction.network_variant} · Unit{" "}
                {scope.config.stages.m4_reaction.unit_mode} · Missing values
                remain absent.
              </p>
              <ScientificInputForms
                project={project}
                section="parameters"
                onChange={change}
                schema={schema}
                inputTarget={inputTarget}
              />
              <ScientificSettings
                project={project}
                onChange={change}
                schema={schema}
              />
            </>
          ) : (
            <p>
              Full scientific pipeline not attached; standalone sequence
              statistics are not a formal M1–M5 project.
            </p>
          )}
        </section>
        <h3 id="input-evidence">Registered input files</h3>
        <table>
          <thead>
            <tr>
              <th>Logical file</th>
              <th>File identity</th>
              <th>Authorized download</th>
            </tr>
          </thead>
          <tbody>
            {[
              ...new Map(
                [...project.files, ...(scope?.evidence_files ?? [])].map(
                  (file) => [file.id, file],
                ),
              ).values(),
            ].map((file, i) => (
              <tr key={`${file.id}-${i}`}>
                <td>{file.name}</td>
                <td>
                  <button
                    disabled={dirty}
                    onClick={() => onOpenResource(file.id)}
                  >
                    Open resource
                  </button>
                  <details>
                    <summary>Integrity details</summary>
                    <code>{file.sha256}</code>
                  </details>
                </td>
                <td>
                  <button
                    onClick={() =>
                      void action(() =>
                        downloadResource(
                          `/files/${encodeURIComponent(file.id)}?project_id=${encodeURIComponent(project.id)}`,
                          file.name,
                        ),
                      )
                    }
                  >
                    Original file
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <h3>Measurements and M5</h3>
        {dirty && (
          <p>
            Save this draft before previewing the backend M5 binding, to
            preserve unsaved changes.
          </p>
        )}
        {project.datasets
          .filter((row) => row.kind === "wetlab")
          .map((row, i) => (
            <article key={i}>
              <p>
                {String(row.name)} · Import / QC does not imply approval of
                fitted parameters.
              </p>
              <LazyJson value={row} />
              {scope && typeof row.file_id === "string" && (
                <button
                  disabled={busy || dirty}
                  onClick={() => {
                    const fileId = row.file_id;
                    if (typeof fileId !== "string") return;
                    const stamp = epoch.current;
                    void action(async () => {
                      const value = await client.bindMeasurement(
                        project.id,
                        project.revision,
                        fileId,
                      );
                      if (mounted.current && stamp === epoch.current)
                        change(value.project);
                    });
                  }}
                >
                  Preview M5 measurement binding (save and review required)
                </button>
              )}
            </article>
          ))}
        <h3 id="input-sequences">Sequences</h3>
        <p>
          Standalone sequences: {project.sequences.length} · Scientific
          sequences:{" "}
          {scope?.sequence_index.status === "indexed"
            ? scope.sequence_index.count
            : "Not indexed"}{" "}
          · Assembly declarations: {project.assemblies.length}
        </p>
        <LazyJson
          value={scope?.sequence_index}
          label="Read-only scientific FASTA index"
        />
        <LazyJson value={project.sequences} label="Sequences and roles" />
        <h3 id="input-constructs">Constructs and assembly declarations</h3>
        <ScientificInputForms
          project={project}
          section="constructs"
          onChange={change}
          schema={schema}
          inputTarget={inputTarget}
        />
        <LazyJson
          value={project.assemblies}
          label="Assembly declarations (not experimental confirmation)"
        />
      </fieldset>
      <PrecheckPanel
        result={inputCheck}
        stale={checkStale}
        disabled={busy || editing}
        onCheck={onCheck}
        onLocate={onLocate}
      />
      <button disabled={busy || editing} onClick={startEditor}>
        Advanced: Edit public project JSON
      </button>
      {editing && (
        <section>
          <p>
            This edits the scientific draft, not runtime profile; apply edits
            before new plans. Backend verification remains required.
          </p>
          <textarea
            aria-label="Public inputs JSON"
            className="json-editor"
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              ++epoch.current;
            }}
          />
          <button
            disabled={busy}
            onClick={() =>
              void action(async () => {
                const value = parsePublic("ProjectView", JSON.parse(text));
                if (
                  value.id !== project.id ||
                  value.revision !== project.revision
                )
                  throw new Error(
                    "Do not change project  ID/revision; create an iteration instead.",
                  );
                change(value);
                setEditing(false);
                onEditing(false);
              })
            }
          >
            Apply validated draft
          </button>
          <button
            disabled={busy}
            onClick={() => {
              setEditing(false);
              onEditing(false);
            }}
          >
            Discard unapplied edits
          </button>
        </section>
      )}
    </section>
  );
}
