/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type ProjectId = string;
export type Status = string;
export type SnapshotHash = string;
export type CreatedAt = string;
export type UpdatedAt = string;
export type Name = string;
export type ProjectRevision = number;

export interface RunListView {
  id: Id;
  project_id: ProjectId;
  status: Status;
  snapshot_hash: SnapshotHash;
  created_at: CreatedAt;
  updated_at: UpdatedAt;
  name: Name;
  project_revision: ProjectRevision;
}
