import type {RunSummaryView} from "../contracts/generated";

export type Selection =
  | {kind: "proposal-node"; proposalId: string; nodeId: string}
  | {kind: "run-node"; projectId: string; runId: string; snapshotHash: string; nodeId: string; attempt: number}
  | {kind: "resource"; projectId: string; fileId: string; sha256: string};

export function selectRunNode(run: RunSummaryView, nodeId: string): Selection | undefined {
  const node = run.nodes.find(value => value.id === nodeId);
  return node ? {kind: "run-node", projectId: run.project_id, runId: run.id,
    snapshotHash: run.snapshot_hash, nodeId, attempt: node.attempts} : undefined;
}

export function matchesRun(selection: Selection | undefined, run: RunSummaryView | undefined, projectId: string | undefined) {
  return selection?.kind === "run-node" && run?.id === selection.runId &&
    run.project_id === selection.projectId && projectId === selection.projectId &&
    run.snapshot_hash === selection.snapshotHash &&
    run.nodes.find(node => node.id === selection.nodeId)?.attempts === selection.attempt;
}
