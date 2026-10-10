import type { NodePage, RunSummaryView } from "../contracts/generated";
import { ScientificResults } from "../ScientificResults";
import { downloadArtifact } from "../api";
import { show } from "../contracts/resultAdapters";
import { SequenceMapTable } from "./SequenceMapTable";
import {RunAssessment} from './RunAssessment';

export function SelectedResult({
  run,
  selected,
  data,
  error,
  offset,
  onOffset,
  onSelect,
  action,
  onOpenResource,
}: {
  run: RunSummaryView;
  selected: string;
  data?: NodePage;
  error?: string;
  offset: number;
  onOffset: (value: number) => void;
  onSelect: (id: string) => void;
  action: (job: () => Promise<unknown>) => Promise<void>;
  onOpenResource?: (fileId: string) => void;
}) {
  if (error) return <p role="alert">{error}</p>;
  if (!selected) return <p>Select a stage in Workflow or Results.</p>;
  if (!data) return <p>Loading selected stage…</p>;
  const files = new Set<string>();
  function visit(value: unknown) {
    if (typeof value === "string" && value.startsWith("asset:"))
      files.add(value.slice(6));
    else if (Array.isArray(value)) value.forEach(visit);
    else if (value && typeof value === "object")
      Object.values(value).forEach(visit);
  }
  visit(data.node.output);
  return (
    <section>
      <RunAssessment run={run}/>
      <p>
        {run.name} · Saved inputs {run.project_revision}
      </p>
      {data.node.error && <p role="alert">{show(data.node.error.message)}</p>}
      {data.sequence_map ? (
        <SequenceMapTable
          key={`${run.id}:${selected}:${offset}`}
          value={data.sequence_map}
          onSelect={onSelect}
        />
      ) : data.node.status !== "succeeded" ? (
        <p>Node not fully completed; not published as a valid prediction.</p>
      ) : (
        <ScientificResults
          key={`${run.id}:${selected}:${data.node.attempts}:${data.artifact?.hash}:${offset}`}
          projectId={run.project_id}
          run={{
            id: run.id,
            snapshot: {
              workflow: run.workflow,
              project: { revision: run.project_revision },
            },
            nodes: [data.node],
          }}
        />
      )}
      {data.total_records > 0 && (
        <p>
          <button
            disabled={!offset}
            onClick={() => onOffset(Math.max(0, offset - 20))}
          >
            Previous candidate page
          </button>
          <button
            disabled={offset + 20 >= data.total_records}
            onClick={() => onOffset(offset + 20)}
          >
            Next candidate page
          </button>{" "}
          {offset + 1}–{Math.min(offset + 20, data.total_records)} /{" "}
          {data.total_records}
        </p>
      )}
      {data.artifact && (
        <button
          onClick={() =>
            void action(() =>
              downloadArtifact(data.artifact!.id, run.project_id),
            )
          }
        >
          Authorized scientific export (not original artifact bytes)
        </button>
      )}
      {onOpenResource &&
        [...files].map((id, index) => (
          <button key={id} onClick={() => onOpenResource(id)}>
            Open stage resource {index + 1}
          </button>
        ))}
    </section>
  );
}
