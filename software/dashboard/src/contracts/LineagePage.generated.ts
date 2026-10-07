/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "run-lineage-v1";
export type ProjectId = string;
export type Offset = number;
export type Total = number;
export type HasMore = boolean;
export type ProjectId1 = string;
export type Name = string;
export type CreatedAt = string;
export type RunId = string;
export type SnapshotHash = string;
export type Revision = number;
export type Status = string;
export type Items = LineageRun[];

export interface LineagePage {
  schema_version: SchemaVersion;
  project_id: ProjectId;
  offset: Offset;
  total: Total;
  has_more: HasMore;
  items: Items;
}
export interface LineageRun {
  project_id: ProjectId1;
  name: Name;
  created_at: CreatedAt;
  run_id: RunId;
  snapshot_hash: SnapshotHash;
  revision: Revision;
  status: Status;
}
