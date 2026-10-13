import { Component, useState, type ReactNode } from "react";
import { object } from "./contracts/validation";
import {
  adaptSteadyResult,
  numbers,
  sequenceOutput,
  show,
  stageRecords,
  m1Checks,
} from "./contracts/resultAdapters";
import { M1Matrix, M2Metrics } from "./workbench/ScreenResultTables";
import { MissingEvidence } from "./workbench/MissingEvidence";
import { M3View, M4View, SequencePlot } from "./workbench/StageViews";
import { M5View } from "./workbench/M5View";
import { lazy, Suspense } from "react";
import { messages } from "./workbench/messages.en";
import { PredictionResult } from "./workbench/PredictionResult";
import { M1MethodResult } from "./workbench/M1MethodResult";
import {SyntheticPSResult} from './workbench/SyntheticPSResult';
import {CustomFormulaResult} from './workbench/CustomFormulaResult';
import type {FileContext} from './workbench/FileDocument';
export type ResultViewState={scenario?:string;candidate?:number;seriesIds?:string[];trajectoryFileId?:string};
type ResultNavigation={onOpenResource?:(id:string,context?:Partial<FileContext>)=>void;viewState?:ResultViewState;onViewChange?:(value:ResultViewState)=>void};
const Series = lazy(() =>
  import("./workbench/viewers/SeriesViewer").then((m) => ({
    default: m.SeriesViewer,
  })),
);
export { object, adaptSteadyResult, sequenceOutput };

export interface ResultRun {
  id: string;
  nodes: {
    id: string;
    parent_id: string | null;
    status: string;
    output: unknown;
  }[];
  snapshot: {
    workflow: { nodes: { id: string; tool_id: string }[] };
    project?: { revision: number };
  };
}
export function nodeTool(run: ResultRun, node: ResultRun["nodes"][number]) {
  return run.snapshot.workflow.nodes.find(
    (item) => item.id === (node.parent_id ?? node.id),
  )?.tool_id;
}
class ResultBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <p role="alert">
        Result display failed. Authorized originals are retained; the workbench
        remains usable.
      </p>
    ) : (
      this.props.children
    );
  }
}
function TrajectoryReference({
  reference,
  projectId,
}: {
  reference: unknown;
  projectId?: string;
  onAddData?:()=>void;
}) {
  const path = object(reference) ? reference.path : reference;
  if (typeof path !== "string" || !path.startsWith("asset:") || !projectId)
    return (
      <p>No authorized registered series reference; no curve generated.</p>
    );
  return (
    <section aria-label="Recorded time course">
        <Suspense fallback={<p>Loading local series viewer…</p>}>
          <Series fileId={path.slice(6)} projectId={projectId} targetSpecies="15" />
        </Suspense>
    </section>
  );
}
function StageResult({
  output,
  records,
  projectId,
  onAddData,
}: {
  output: Record<string, unknown>;
  records: Record<string, unknown>[];
  projectId?: string;
  onAddData?:()=>void;
}) {
  const [selected, setSelected] = useState(0);
  const record = records[selected] ?? records[0];
  const module = String(output.module).toUpperCase();
  if (!record)
    return (
      <section>
        <h2>{module} · Scientific project results</h2>
        <p>No candidate records; not a valid prediction.</p>
      </section>
    );
  const id = String(record.candidate_id ?? record.experiment_id ?? selected);
  return (
    <section>
      <h2>{module} · Scientific project results</h2>
      {records.length>1&&<label>
        Current candidate
        <select
          aria-label="Current candidate"
          value={selected}
          onChange={(e) => setSelected(Number(e.target.value))}
        >
          {records.map((row, i) => (
            <option key={i} value={i}>
              {show(row.candidate_id ?? row.experiment_id ?? i)}
            </option>
          ))}
        </select>
      </label>}
      <p className="result-status">{record.numerically_solved === true ? 'Numerically solved' : record.status === 'insufficient_data' ? 'Blocked · missing data' : show(record.status)}{record.data_quality==='demo_fixture'?' · synthetic':''}</p>
      {module !== 'M2' && <MissingEvidence module={module} missing={record.missing_inputs} status={record.status}/>}
      {module === "M1" && (
        <>
          <M1Matrix records={records} />
        </>
      )}
      {module === "M2" && (
        <>
          <M2Metrics record={record} onAddData={onAddData} />
        </>
      )}
      {module === "M3" && <M3View record={record} />}
      {module === "M4" && (
        <>
          <M4View record={record} />
          <TrajectoryReference
            projectId={projectId}
            reference={
              object(output.trajectory_refs)
                ? output.trajectory_refs[id]
                : record.trajectory_artifact
            }
          />
        </>
      )}
      {module === "M5" && (
        <>
          <M5View record={record} />
          <p>
            QC：{show(record.qc_flags)} · Fit candidate:{" "}
            {record.fitted_parameter_candidate
              ? "Recorded; review required"
              : "None"}{" "}
            · Fit warnings: {show(record.fit_warnings)}
          </p>
        </>
      )}
    </section>
  );
}
function NodeResult({
  run,
  node,
  projectId,
  onAddData,
  onOpenResource,viewState,onViewChange,
}: {
  run: ResultRun;
  node: ResultRun["nodes"][number];
  projectId?: string;
  onAddData?:()=>void;
} & ResultNavigation) {
  const tool = nodeTool(run, node);
  const output = node.output;
  if (tool==='synthetic.ps_v3'&&object(output)&&output.schema_version==='synthetic-ps-v3-run-v1')
    return <SyntheticPSResult output={output} projectId={projectId} onOpenResource={onOpenResource} viewState={viewState} onViewChange={onViewChange}/>;
  if (tool==='workflow.custom_formula'&&object(output)&&output.schema_version==='custom-formula-v1')
    return <CustomFormulaResult output={output}/>;
  if (object(output) && m1Checks(output))
    return <M1MethodResult output={output} />;
  if (object(output) && output.schema_version === "sequence-prediction-v1")
    return <PredictionResult output={output} />;
  const records = stageRecords(tool, output);
  if (records && object(output))
    return (
      <StageResult output={output} records={records} projectId={projectId} onAddData={onAddData}/>
    );
  const sequence = sequenceOutput(output);
  if (tool === "fusion.sequence_metrics" && sequence)
    return (
      <section>
        <h2>Sequence statistics · {String(sequence.id)}</h2>
        <SequencePlot features={sequence.features} />
        <p>
          Length {show(sequence.features.length)} · Molecular weight{" "}
          {show(sequence.protparam.molecular_weight_da)} Da · Theoretical pI{" "}
          {show(sequence.protparam.theoretical_pi)}
        </p>
        <p>
          Sequence statistics; activity and assembly are not experimentally
          assessed.
        </p>
      </section>
    );
  if (
    tool === "assembly.inventory" &&
    object(output) &&
    numbers(output.subunits) &&
    typeof output.assembly_id === "string" &&
    typeof output.total_subunits === "number" &&
    typeof output.molecular_weight_da === "number" &&
    Number.isFinite(output.molecular_weight_da)
  )
    return (
      <section>
        <h2>Assembly inventory check · {output.assembly_id}</h2>
        <p>
          {Object.entries(output.subunits)
            .map(([id, count]) => `${id} × ${count}`)
            .join(" + ")}
        </p>
        <p>
          Total subunits {output.total_subunits} · Assembly molecular weight{" "}
          {output.molecular_weight_da} Da
        </p>
        <p>
          Declared inventory calculation, not a prediction of assembly success
          or interface stability.
        </p>
      </section>
    );
  const adapted = adaptSteadyResult(tool, output);
  if (!adapted)
    return (
      <section>
        <h2>
          Recorded result
        </h2>
        <p>
          This result format is not supported for display. Export the authorized result record.
        </p>
      </section>
    );
  const { data, title, maps } = adapted;
  return (
    <section>
      <h2>{title}</h2>
      <p>
        Job status：{node.status} · Scientific status: {String(data.status)}
      </p>
      <p>
        Numerical result:{" "}
        {maps ? "Solver contract satisfied" : "No valid prediction"} · Evidence
        status:{" "}
        {data.evidence_ready === true
          ? "Declared evidence available"
          : "Not formally reviewed as project evidence"}
      </p>
      <p>
        Model / Formula: {String(data.model_kind)} /{" "}
        {String(data.formula_version ?? data.rate_law)}
      </p>
      {maps && (
        <>
          <table>
            <thead>
              <tr>
                <th>Species</th>
                <th>Whole-cell average μM</th>
                <th>Dense phase μM</th>
                <th>Dilute phase μM</th>
                <th>Secretion μM/h</th>
                <th>Residual μM/h</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(maps[0]).map((s) => (
                <tr key={s}>
                  <td>{s}</td>
                  {maps.slice(0, 5).map((map, i) => (
                    <td key={i}>{map[s]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <h3>Reaction flux μM/h</h3>
          <table>
            <tbody>
              {Object.entries(maps[5]).map(([r, v]) => (
                <tr key={r}>
                  <td>{r}</td>
                  <td>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      {Array.isArray(data.warnings) && (
        <p>{data.warnings.map(String).join("；")}</p>
      )}
      {object(data.local_stability) && (
        <p>
          Local stability:{" "}
          {show(
            data.local_stability.classification ?? data.local_stability.status,
          )}
          ; not proof of global stability or uniqueness.
        </p>
      )}
    </section>
  );
}
export function ScientificResults({
  run,
  projectId,
  onAddData,
  onOpenResource,viewState,onViewChange,
}: {
  run: ResultRun;
  projectId?: string;
  onAddData?:()=>void;
} & ResultNavigation) {
  return (
    <>
      {run.nodes
        .filter((node) => node.status === "succeeded")
        .map((node) => (
          <ResultBoundary key={`${run.id}:${node.id}`}>
            <NodeResult run={run} node={node} projectId={projectId} onAddData={onAddData} onOpenResource={onOpenResource} viewState={viewState} onViewChange={onViewChange}/>
          </ResultBoundary>
        ))}
    </>
  );
}
export function ResultComparison({ runs }: { runs: ResultRun[] }) {
  if (runs.length !== 2) return null;
  const metrics = runs.map(
    (run) =>
      new Map(
        run.nodes
          .filter(
            (node) =>
              nodeTool(run, node) === "fusion.sequence_metrics" &&
              node.status === "succeeded",
          )
          .flatMap((node) => {
            const output = sequenceOutput(node.output);
            return output ? [[String(output.id), output] as const] : [];
          }),
      ),
  );
  const shared = [...metrics[0].keys()].filter((id) => metrics[1].has(id));
  return (
    <section>
      <h3>Inputs/Result identity comparison (not formal F3 ranking)</h3>
      <p>
        revision {show(runs[0].snapshot.project?.revision)} →{" "}
        {show(runs[1].snapshot.project?.revision)}; same ID does not establish
        the same construct/conditions.
      </p>
      {!shared.length ? (
        <p>
          No shared identifiable sequence results; no comparison or zero
          substitution.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Record</th>
              <th>Difference</th>
              <th>Molecular weight Da</th>
            </tr>
          </thead>
          <tbody>
            {shared.map((id) => {
              const a = metrics[0].get(id)!;
              const b = metrics[1].get(id)!;
              const ah = String(a.features.sequence_sha256);
              const bh = String(b.features.sequence_sha256);
              return (
                <tr key={id}>
                  <td>{id}</td>
                  <td>
                    {ah === bh
                      ? "Same sequence; conditions still require checking"
                      : "Sequence changed; not the same construct"}
                  </td>
                  <td>
                    {show(a.protparam.molecular_weight_da)} →{" "}
                    {show(b.protparam.molecular_weight_da)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      <p>
        Scientific numeric comparison requires backend comparability gates; this
        view never upgrades evidence by numerical magnitude.
      </p>
    </section>
  );
}
