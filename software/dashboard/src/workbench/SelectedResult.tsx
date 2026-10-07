import type { NodePage, RunSummaryView } from "../contracts/generated";
import { ScientificResults } from "../ScientificResults";
import { downloadArtifact } from "../api";
import { show } from "../contracts/resultAdapters";
import { SequenceMapTable } from "./SequenceMapTable";

export function SelectedResult({
  run,
  selected,
  data,
  error,
  offset,
  onOffset,
  onSelect,
  action,
}: {
  run: RunSummaryView;
  selected: string;
  data?: NodePage;
  error?: string;
  offset: number;
  onOffset: (value: number) => void;
  onSelect: (id: string) => void;
  action: (job: () => Promise<unknown>) => Promise<void>;
}) {
  if (error) return <p role="alert">{error}</p>;
  if (!selected) return <p>Select a stage in Workflow or Results.</p>;
  if (!data) return <p>Loading selected stage…</p>;
  return (
    <section>
      <p>
        Run {run.id} · Frozen input revision {run.project_revision} · artifact
        SHA-256 {show(data.artifact?.hash)}
      </p>
      {data.node.error && (
        <p role="alert">
          {show(data.node.error.code)} · {show(data.node.error.message)} ·
          Diagnostic {show(data.node.error.diagnostic_id)}
        </p>
      )}
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
    </section>
  );
}
