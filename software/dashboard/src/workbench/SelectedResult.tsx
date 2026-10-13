import type { NodePage, RunSummaryView } from "../contracts/generated";
import { ScientificResults,type ResultViewState } from "../ScientificResults";
import { downloadArtifact,downloadResource } from "../api";
import {useState} from 'react';
import { show } from "../contracts/resultAdapters";
import { SequenceMapTable } from "./SequenceMapTable";
import type {FileContext} from './FileDocument';

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
  onAddData,
  viewState,onViewChange,
}: {
  run: RunSummaryView;
  selected: string;
  data?: NodePage;
  error?: string;
  offset: number;
  onOffset: (value: number) => void;
  onSelect: (id: string) => void;
  action: (job: () => Promise<unknown>) => Promise<void>;
  onOpenResource?: (fileId: string,context?:Partial<FileContext>) => void;
  onAddData?:()=>void;
  viewState?:ResultViewState;onViewChange?:(value:ResultViewState)=>void;
}) {
  const [exportOpen,setExportOpen]=useState(false);
  if (error) return <p role="alert">{error}</p>;
  if (!selected) return <p>Select a stage in Workflow or Results.</p>;
  if (!data) return <p>Loading selected stage…</p>;
  return (
    <section>
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
          onAddData={onAddData}
          onOpenResource={onOpenResource}
          viewState={viewState} onViewChange={onViewChange}
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
      {data.total_records > 20 && (
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
        <><button onClick={()=>setExportOpen(value=>!value)}>Export</button>{exportOpen&&<div>
          <button onClick={()=>void action(()=>downloadArtifact(data.artifact!.id,run.project_id))}>Result record</button>
          {viewState?.trajectoryFileId&&<button onClick={()=>void action(()=>downloadResource(`/files/${encodeURIComponent(viewState.trajectoryFileId!)}/series.csv?project_id=${encodeURIComponent(run.project_id)}`,'recorded-series.csv'))}>Recorded time course CSV</button>}
        </div>}</>
      )}
    </section>
  );
}
