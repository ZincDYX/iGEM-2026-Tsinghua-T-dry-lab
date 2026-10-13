import { useEffect, useState } from "react";
import type {
  ProjectView,
  ScientificPrecheckView,
} from "../contracts/generated";
import { requestJson,downloadResource } from "../api";
import { object } from "../contracts/validation";
import { UnifiedImport } from "./UnifiedImport";
import { ConstructObject, NewConstruct } from "./ScientificInputForms";
import { GenBankDesigns } from "./GenBankDesigns";
import type { InputIssue } from "./PrecheckPanel";

const typeLabels: Record<string, string> = {
  SequenceCollection: "Sequences",
  StructureRecord: "Protein structure",
  ProjectConfig: "Analysis plan",
  genbank_design: "Annotated DNA",
  MeasurementTable: "Measurements",
  wetlab: "Measurements",
  synthetic_ps_v3: "Synthetic demonstration",
  EvidenceAttachment: "Evidence",
  UnmappedTable: "Evidence table",
};
type SourceRecord = {
  id: string;
  length: number;
  molecule_type: string | null;
  role: string | null;
  sequence: string | null;
  bound_sequence_id: string | null;
};
function SourceSequences({
  project,
  fileId,
  onChange,
}: {
  project: ProjectView;
  fileId: string;
  onChange: (value: ProjectView) => void;
}) {
  const [rows, setRows] = useState<SourceRecord[]>([]),
    [selected, setSelected] = useState(""),
    [offset, setOffset] = useState(0),
    [total, setTotal] = useState(0),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    const query = new URLSearchParams({
      project_id: project.id,
      offset: String(offset),
    });
    if (selected) query.set("record_id", selected);
    void requestJson(
      `/files/${encodeURIComponent(fileId)}/sequence-records?${query}`,
      undefined,
      controller.signal,
    )
      .then((value) => {
        if (controller.signal.aborted) return;
        if (
          !object(value) ||
          value.file_id !== fileId ||
          !Array.isArray(value.records)
        )
          throw Error("Sequence source unavailable.");
        setRows(value.records as SourceRecord[]);
        setTotal(Number(value.total));
      })
      .catch((reason) => {
        if (!controller.signal.aborted) setError(String(reason));
      });
    return () => controller.abort();
  }, [project.id, project.revision, fileId, offset, selected]);
  const record = rows.find((row) => row.id === selected);
  return (
    <section aria-label="Source sequences">
      {error && <p role="alert">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Sequence</th>
            <th>Type</th>
            <th>Length</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>
                <button onClick={() => setSelected(row.id)}>{row.id}</button>
              </td>
              <td>{row.molecule_type ?? "Unconfirmed"}</td>
              <td>
                {row.length} {row.molecule_type === "protein" ? "aa" : "bases"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {total > 100 && (
        <nav>
          <button
            disabled={!offset}
            onClick={() => {
              setOffset((value) => Math.max(0, value - 100));
              setSelected("");
            }}
          >
            Previous sequences
          </button>
          <button
            disabled={offset + 100 >= total}
            onClick={() => {
              setOffset((value) => value + 100);
              setSelected("");
            }}
          >
            Next sequences
          </button>
        </nav>
      )}
      {record && (
        <section aria-label="Selected sequence">
          <h3>{record.id}</h3>
          <p className="sequence-text">
            {record.sequence ?? "Opening source record…"}
          </p>
          {record.bound_sequence_id && (
            <label>
              Design role
              <select
                aria-label={`M1 role for ${record.id}`}
                value={
                  project.sequences.find(
                    (value) => value.id === record.bound_sequence_id,
                  )?.role ??
                  record.role ??
                  ""
                }
                onChange={(event) =>
                  onChange({
                    ...project,
                    sequences: project.sequences.map((value) =>
                      value.id === record.bound_sequence_id
                        ? { ...value, role: event.target.value }
                        : value,
                    ),
                  })
                }
              >
                <option value={record.role ?? ""}>
                  {record.role?.replaceAll("_", " ") ?? "Not declared"}
                </option>
                {[
                  "idr",
                  "enzyme_ligand_linker",
                  "scaffold_linker",
                  "rigid_linker",
                  "full_fusion",
                ]
                  .filter((role) => role !== record.role)
                  .map((role) => (
                    <option key={role} value={role}>
                      {role.replaceAll("_", " ")}
                    </option>
                  ))}
              </select>
            </label>
          )}
        </section>
      )}
    </section>
  );
}

export function InputEditor({
  project,
  persisted,
  busy,
  dirty,
  onChange,
  action,
  onOpenResource,
  inputTarget,
  onPlanMethod,
  prepareImport,
  onImported,
}: {
  project: ProjectView;
  persisted: boolean;
  busy: boolean;
  dirty: boolean;
  onChange: (value: ProjectView) => void;
  action: (job: () => Promise<unknown>) => Promise<void>;
  inputCheck?: ScientificPrecheckView;
  checkStale: boolean;
  onCheck: () => void;
  onLocate: (issue: InputIssue) => void;
  onOpenResource: (id: string) => void;
  inputTarget?: InputIssue;
  onPlanMethod?: (method: "ps-v3-demo") => void;
  prepareImport: () => Promise<ProjectView | undefined>;
  onImported: (project: ProjectView) => void;
}) {
  const [selected, setSelected] = useState(""),
    [design, setDesign] = useState(""),
    [planOpen, setPlanOpen] = useState(false);
  const [manualSequence, setManualSequence] = useState("");
  const scope = project.scientific_project;
  const files = [
    ...new Map(
      [...project.files, ...(scope?.evidence_files ?? [])].map((file) => [
        file.id,
        file,
      ]),
    ).values(),
  ];
  const dataset = project.datasets.find((row) => row.file_id === selected),
    file = files.find((row) => row.id === selected);
  useEffect(() => {
    if (inputTarget) {
      setPlanOpen(true);
      if (inputTarget.construct_id)
        setDesign("definition:" + inputTarget.construct_id);
    }
  }, [inputTarget]);
  const unfiled =
    !files.some((file) =>
      project.datasets.some(
        (row) => row.file_id === file.id && row.kind === "SequenceCollection",
      ),
    ) && project.sequences.length > 0;
  return (
    <section aria-label="Project inputs and evidence">
      <h2>Inputs</h2>
      <UnifiedImport
        project={project}
        persisted={persisted}
        busy={busy}
        dirty={dirty}
        action={action}
        prepare={prepareImport}
        onCommitted={onImported}
      />
      <table aria-label="Input objects">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => {
            const source = project.datasets.find(
                (row) => row.file_id === file.id,
              ),
              kind = String(source?.kind ?? "EvidenceAttachment");
            const count = Array.isArray(source?.records)
              ? source.records.length
              : undefined;
            const molecule =
              kind === "SequenceCollection" &&
              count &&
              object((source!.records as unknown[])[0])
                ? String(
                    (source!.records as Record<string, unknown>[])[0]
                      .molecule_type,
                  )
                : undefined;
            return (
              <tr key={file.id} aria-selected={selected===file.id}>
                <td>
                  <button
                    onClick={() => {
                      setSelected(file.id);setDesign('');
                      if (
                        kind === "StructureRecord" ||
                        (!source && /\.(pdb|cif|mmcif|bcif)$/i.test(file.name))
                      )
                        onOpenResource(file.id);
                      else {
                        setSelected(file.id);
                        setDesign("");
                        setPlanOpen(kind === "ProjectConfig");
                      }
                    }}
                  >
                    {file.name}
                  </button>
                </td>
                <td>
                  {kind === "SequenceCollection"
                    ? molecule === "protein"
                      ? "Protein FASTA"
                      : molecule === "DNA"
                        ? "DNA FASTA"
                        : molecule === "RNA"
                          ? "RNA FASTA"
                          : "Sequences"
                    : !source && /\.(pdb|cif|mmcif|bcif)$/i.test(file.name)
                      ? "Coordinate file"
                      : (typeLabels[kind] ?? "Data file")}
                  {count && kind === "SequenceCollection"
                    ? ` (${count} records)`
                    : ""}
                </td>
                <td>
                  {source?.has_unresolved_inputs ? "Needs review" : "Imported"}
                </td>
              </tr>
            );
          })}
          {unfiled && (
            <tr>
              <td>
                <button
                  onClick={() => {
                    setSelected("unfiled");
                    setPlanOpen(false);
                  }}
                >
                  Project sequences
                </button>
              </td>
              <td>Protein sequences ({project.sequences.length})</td>
              <td>Design input</td>
            </tr>
          )}
        </tbody>
      </table>
      {file && (
        <section aria-label="Selected input object">
          <h3>{file.name}</h3>
          {dataset?.kind === "SequenceCollection" ||
          (!dataset && /\.(fasta|faa|fa|fna)$/i.test(file.name)) ? (
            <><SourceSequences
              key={file.id}
              project={project}
              fileId={file.id}
              onChange={onChange}
            /><button onClick={()=>void action(()=>downloadResource(`/files/${encodeURIComponent(file.id)}?project_id=${encodeURIComponent(project.id)}`,file.name))}>Export original FASTA</button></>
          ) : dataset?.kind === "genbank_design" ? (
            <GenBankDesigns
              project={project}
              fileId={file.id}
              dirty={dirty}
              action={action}
            />
          ) : (
            dataset?.kind !== "ProjectConfig" && (
              <button onClick={() => onOpenResource(file.id)}>Open file</button>
            )
          )}
        </section>
      )}
      {selected === "unfiled" && (
        <section>
          <h3>Project sequences</h3>
          <table>
            <tbody>
              {project.sequences.map((row) => (
                <tr key={row.id}>
                  <td>
                    <button onClick={() => setManualSequence(row.id)}>
                      {row.id}
                    </button>
                  </td>
                  <td>{row.sequence.length} aa</td>
                  <td>{row.role.replaceAll("_", " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {project.sequences
            .filter((row) => row.id === manualSequence)
            .map((row) => (
              <section key={row.id}>
                <h4>{row.id}</h4>
                <p className="sequence-text">{row.sequence}</p>
                <label>
                  Localization
                  <select aria-label={`Localization for ${row.id}`}
                    value={row.localization_context ?? "cytosolic"}
                    onChange={(event) => onChange({...project, sequences: project.sequences.map(
                      (value) => value.id === row.id ? {...value, localization_context:
                        event.target.value as "cytosolic" | "er_anchored"} : value)})}>
                    <option value="cytosolic">Cytosolic</option>
                    <option value="er_anchored">ER anchored — topology needs evaluation</option>
                  </select>
                </label>
                <label>
                  Design role
                  <input
                    aria-label={`Design role for ${row.id}`}
                    value={row.role}
                    onChange={(event) =>
                      onChange({
                        ...project,
                        sequences: project.sequences.map((value) =>
                          value.id === row.id
                            ? { ...value, role: event.target.value }
                            : value,
                        ),
                      })
                    }
                  />
                </label>
              </section>
            ))}
        </section>
      )}
      {scope && (
        <section aria-label="Analysis plan and configuration">
          <button onClick={() => setPlanOpen((value) => !value)}>
            Analysis plan — {scope.config.inputs.constructs.length} protein
            designs
          </button>
          {planOpen && (
            <>
              <p>
                {scope.config.execution.mode === "demo"
                  ? "Demonstration"
                  : "Real-data plan"}
                ; pathway {scope.config.stages.m4_reaction.network_variant}.
              </p>
              {scope.config.inputs.constructs.map((value) => (
                <button
                  key={value.id}
                  onClick={() => setDesign("definition:" + value.id)}
                >
                  {value.id}
                </button>
              ))}
              {scope.config.inputs.construct_records
                .filter(
                  (record) =>
                    !scope.config.inputs.constructs.some(
                      (value) => value.id === record.construct_id,
                    ),
                )
                .map((value) => (
                  <button
                    key={value.construct_id}
                    onClick={() => setDesign("record:" + value.construct_id)}
                  >
                    {value.construct_id} — evidence declaration
                  </button>
                ))}
              <ConstructObject
                project={project}
                selected={design}
                onChange={onChange}
              />
              <NewConstruct project={project} onChange={onChange} />
              <p>
                Sources retain their original values. Model inputs are edited in
                Workflow; import a corrected source as a new version.
              </p>
            </>
          )}
        </section>
      )}
      {project.datasets.some((row) => row.kind === "synthetic_ps_v3") && (
        <section>
          <p>Synthetic demonstration, not experimental evidence.</p>
          <button disabled={busy} onClick={() => onPlanMethod?.("ps-v3-demo")}>
            Create demonstration plan
          </button>
        </section>
      )}
    </section>
  );
}
