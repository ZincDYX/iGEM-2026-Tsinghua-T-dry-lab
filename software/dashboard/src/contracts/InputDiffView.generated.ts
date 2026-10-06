/* Generated from public Pydantic contracts. Do not edit. */

export type BaselineRunId = string;
export type BaselineSnapshotSha256 = string;
export type ProjectId = string;
export type ProjectRevision = number;
export type ChangedFields = string[];
export type TotalChangedFields = number;
export type AffectedNodes = string[];
export type ReuseSupported = boolean;
export type Explanation = string;

export interface InputDiffView {
  baseline_run_id: BaselineRunId;
  baseline_snapshot_sha256: BaselineSnapshotSha256;
  project_id: ProjectId;
  project_revision: ProjectRevision;
  changed_fields: ChangedFields;
  total_changed_fields: TotalChangedFields;
  affected_nodes: AffectedNodes;
  reuse_supported: ReuseSupported;
  explanation: Explanation;
}
