/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "display-resource-v1";
export type ProjectId = string;
export type RunId = string | null;
export type SnapshotHash = string | null;
export type Offset = number;
export type Total = number;
export type HasMore = boolean;
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
export type ByteCount = number;
export type LogicalRelativePath = string | null;
export type Status = "available" | "unavailable" | "quarantined";
export type ErrorCode = string | null;
export type Kind = "image";
export type MediaType = "image/png" | "image/jpeg";
export type Role = "registered_source";
export type ClaimScope = "display_only_not_experimental_validation";
export type Name1 = string;
export type ByteCount1 = number;
export type LogicalRelativePath1 = string | null;
export type Status1 = "available" | "unavailable" | "quarantined";
export type ErrorCode1 = string | null;
export type Kind1 = "structure";
export type Format = "pdb" | "mmcif";
export type Role1 = "registered_source";
export type ClaimScope1 = "geometry_only_no_inferred_activity_or_confidence";
export type Name2 = string;
export type ByteCount2 = number;
export type LogicalRelativePath2 = string | null;
export type Status2 = "available" | "unavailable" | "quarantined";
export type ErrorCode2 = string | null;
export type Kind2 = "series";
export type ResultSchemaVersion = "m4-prediction-v2" | "display-series-source-v1" | "m4-compartment-amount-v1";
export type Role2 = "prediction_contract" | "declared_source_series";
export type Name3 = string;
export type ByteCount3 = number;
export type LogicalRelativePath3 = string | null;
export type Status3 = "available" | "unavailable" | "quarantined";
export type ErrorCode3 = string | null;
export type Kind3 = "scan";
export type ResultSchemaVersion1 = "finite-scaffold-scan-v2";
export type Name4 = string;
export type ByteCount4 = number;
export type LogicalRelativePath4 = string | null;
export type Status4 = "available" | "unavailable" | "quarantined";
export type ErrorCode4 = string | null;
export type Kind4 = "m5";
export type ResultSchemaVersion2 = "m5-comparison-series-v1";
export type ClaimScope2 = "recorded_alignment_not_parameter_or_experimental_approval";
export type Name5 = string;
export type ByteCount5 = number;
export type LogicalRelativePath5 = string | null;
export type Status5 = "available" | "unavailable" | "quarantined";
export type ErrorCode5 = string | null;
export type Kind5 = "table";
export type MediaType1 = string;
export type Role3 = "registered_source";
export type Items = (ImageResource | StructureResource | SeriesResource | ScanResource | M5Resource | TableResource)[];

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
  identity: ResourceIdentity;
  name: Name;
  byte_count: ByteCount;
  logical_relative_path: LogicalRelativePath;
  status: Status;
  error_code: ErrorCode;
  kind: Kind;
  media_type: MediaType;
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
  identity: ResourceIdentity;
  name: Name1;
  byte_count: ByteCount1;
  logical_relative_path: LogicalRelativePath1;
  status: Status1;
  error_code: ErrorCode1;
  kind: Kind1;
  format: Format;
  role: Role1;
  claim_scope: ClaimScope1;
}
export interface SeriesResource {
  identity: ResourceIdentity;
  name: Name2;
  byte_count: ByteCount2;
  logical_relative_path: LogicalRelativePath2;
  status: Status2;
  error_code: ErrorCode2;
  kind: Kind2;
  result_schema_version: ResultSchemaVersion;
  role: Role2;
}
export interface ScanResource {
  identity: ResourceIdentity;
  name: Name3;
  byte_count: ByteCount3;
  logical_relative_path: LogicalRelativePath3;
  status: Status3;
  error_code: ErrorCode3;
  kind: Kind3;
  result_schema_version: ResultSchemaVersion1;
}
export interface M5Resource {
  identity: ResourceIdentity;
  name: Name4;
  byte_count: ByteCount4;
  logical_relative_path: LogicalRelativePath4;
  status: Status4;
  error_code: ErrorCode4;
  kind: Kind4;
  result_schema_version: ResultSchemaVersion2;
  claim_scope: ClaimScope2;
}
export interface TableResource {
  identity: ResourceIdentity;
  name: Name5;
  byte_count: ByteCount5;
  logical_relative_path: LogicalRelativePath5;
  status: Status5;
  error_code: ErrorCode5;
  kind: Kind5;
  media_type: MediaType1;
  role: Role3;
}
