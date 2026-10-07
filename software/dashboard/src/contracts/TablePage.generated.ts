/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "display-table-v1";
export type ProjectId = string;
export type FileId = string;
export type SourceSha256 = string;
export type RunId = string | null;
export type SnapshotHash = string | null;
export type NodeId = string | null;
export type Attempt = number | null;
export type CandidateId = string | null;
export type ConstructId = string | null;
export type ConditionId = string | null;
export type Offset = number;
export type Total = number;
export type HasMore = boolean;
export type Columns = string[];
export type Rows = (string | null)[][];
export type Text = string | null;

export interface TablePage {
  schema_version: SchemaVersion;
  identity: ResourceIdentity;
  offset: Offset;
  total: Total;
  has_more: HasMore;
  columns: Columns;
  rows: Rows;
  text: Text;
}
export interface ResourceIdentity {
  project_id: ProjectId;
  file_id: FileId;
  source_sha256: SourceSha256;
  run_id: RunId;
  snapshot_hash: SnapshotHash;
  node_id: NodeId;
  attempt: Attempt;
  candidate_id: CandidateId;
  construct_id: ConstructId;
  condition_id: ConditionId;
}
