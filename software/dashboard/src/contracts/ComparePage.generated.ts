/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "scientific-comparison-v1";
export type ProjectId = string;
export type Name = string;
export type CreatedAt = string;
export type RunId = string;
export type SnapshotHash = string;
export type Revision = number;
export type Status = string;
export type Offset = number;
export type Total = number;
export type HasMore = boolean;
export type InputChangedFields = string[];
export type InputDiffTruncated = boolean;
export type Module = string;
export type RecordId = string;
export type ConstructId = string | null;
export type ConditionId = string | null;
export type SequenceIdentitySha256 = string | null;
export type Status1 = string;
export type ClaimScope = string | null;
export type NumericallySolved = boolean;
export type EvidenceReady = boolean;
export type ArtifactId = string;
export type ArtifactSha256 = string;
export type NodeId = string;
export type Attempt = number;
export type Value = number | null;
export type Comparable = boolean;
export type ReasonCodes = string[];
export type MetricDefinition = string | null;
export type MetricUnit = string | null;
export type ComparisonContractLeft = {
  [k: string]: unknown;
} | null;
export type ComparisonContractRight = {
  [k: string]: unknown;
} | null;
export type Rows = CompareRow[];
export type RankingPerformed = false;
export type ClaimScope1 = "record_comparison_not_new_prediction_or_validation";

export interface ComparePage {
  schema_version: SchemaVersion;
  left: LineageRun;
  right: LineageRun;
  offset: Offset;
  total: Total;
  has_more: HasMore;
  input_changed_fields: InputChangedFields;
  input_diff_truncated: InputDiffTruncated;
  rows: Rows;
  ranking_performed: RankingPerformed;
  claim_scope: ClaimScope1;
}
export interface LineageRun {
  project_id: ProjectId;
  name: Name;
  created_at: CreatedAt;
  run_id: RunId;
  snapshot_hash: SnapshotHash;
  revision: Revision;
  status: Status;
}
export interface CompareRow {
  module: Module;
  left: ComparedValue | null;
  right: ComparedValue | null;
  comparable: Comparable;
  reason_codes: ReasonCodes;
  metric_definition: MetricDefinition;
  metric_unit: MetricUnit;
  comparison_contract_left: ComparisonContractLeft;
  comparison_contract_right: ComparisonContractRight;
}
export interface ComparedValue {
  record_id: RecordId;
  construct_id: ConstructId;
  condition_id: ConditionId;
  sequence_identity_sha256: SequenceIdentitySha256;
  status: Status1;
  claim_scope: ClaimScope;
  numerically_solved: NumericallySolved;
  evidence_ready: EvidenceReady;
  artifact_id: ArtifactId;
  artifact_sha256: ArtifactSha256;
  node_id: NodeId;
  attempt: Attempt;
  value: Value;
}
