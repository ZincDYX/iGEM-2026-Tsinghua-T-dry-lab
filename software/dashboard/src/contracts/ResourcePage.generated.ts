/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "display-resource-v1";
export type ProjectId = string;
export type RunId = string | null;
export type SnapshotHash = string | null;
export type Offset = number;
export type Total = number;
export type HasMore = boolean;
export type Kind = "image";
export type ProjectId1 = string;
export type FileId = string;
export type SourceSha256 = string;
export type RunId1 = string | null;
export type SnapshotHash1 = string | null;
export type NodeId = string | null;
export type Attempt = number | null;
export type CandidateId = string | null;
export type ConstructId = string | null;
export type ConditionId = string | null;
export type Name = string;
export type MediaType = "image/png" | "image/jpeg";
export type ByteCount = number;
export type Role = "registered_source";
export type ClaimScope = "display_only_not_experimental_validation";
export type Kind1 = "structure";
export type Name1 = string;
export type Format = "pdb" | "mmcif";
export type ByteCount1 = number;
export type Role1 = "registered_source";
export type ClaimScope1 = "geometry_only_no_inferred_activity_or_confidence";
export type Kind2 = "series";
export type Name2 = string;
export type ByteCount2 = number;
export type ResultSchemaVersion = "m4-prediction-v2";
export type Role2 = "prediction_contract";
export type Kind3 = "scan";
export type Name3 = string;
export type ByteCount3 = number;
export type ResultSchemaVersion1 = "finite-scaffold-scan-v2";
export type Kind4 = "table";
export type Name4 = string;
export type MediaType1 = string;
export type ByteCount4 = number;
export type Role3 = "registered_source";
export type Items = (ImageResource | StructureResource | SeriesResource | ScanResource | TableResource)[];

export interface ResourcePage {
  schema_version: SchemaVersion;
  project_id: ProjectId;
  run_id: RunId;
  snapshot_hash: SnapshotHash;
  offset: Offset;
  total: Total;
  has_more: HasMore;
  items: Items;
}
export interface ImageResource {
  kind: Kind;
  identity: ResourceIdentity;
  name: Name;
  media_type: MediaType;
  byte_count: ByteCount;
  role: Role;
  claim_scope: ClaimScope;
}
export interface ResourceIdentity {
  project_id: ProjectId1;
  file_id: FileId;
  source_sha256: SourceSha256;
  run_id: RunId1;
  snapshot_hash: SnapshotHash1;
  node_id: NodeId;
  attempt: Attempt;
  candidate_id: CandidateId;
  construct_id: ConstructId;
  condition_id: ConditionId;
}
export interface StructureResource {
  kind: Kind1;
  identity: ResourceIdentity;
  name: Name1;
  format: Format;
  byte_count: ByteCount1;
  role: Role1;
  claim_scope: ClaimScope1;
}
export interface SeriesResource {
  kind: Kind2;
  identity: ResourceIdentity;
  name: Name2;
  byte_count: ByteCount2;
  result_schema_version: ResultSchemaVersion;
  role: Role2;
}
export interface ScanResource {
  kind: Kind3;
  identity: ResourceIdentity;
  name: Name3;
  byte_count: ByteCount3;
  result_schema_version: ResultSchemaVersion1;
}
export interface TableResource {
  kind: Kind4;
  identity: ResourceIdentity;
  name: Name4;
  media_type: MediaType1;
  byte_count: ByteCount4;
  role: Role3;
}
