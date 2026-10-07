/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "display-finite-scan-v1";
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
export type DecisionId = string;
export type DecisionScope = string;
export type Objective = string;
export type MetricDefinition = string | null;
export type MetricUnit = string | null;
export type ComparisonContract = {
  [k: string]: unknown;
} | null;
export type Ordinal = number;
export type CandidateId1 = string;
export type SiteRatio = number | null;
export type DenseOcDmtRatio = number | null;
export type Status = string;
export type Feasible = boolean | null;
export type MetricValue = number | null;
export type ReasonCodes = string[];
export type Points = ScanPoint[];
export type RankingPerformed = false;
export type ClaimScope = "source_reported_scan_not_execution_or_parameter_approval";

export interface ScanPage {
  schema_version: SchemaVersion;
  identity: ResourceIdentity;
  offset: Offset;
  total: Total;
  has_more: HasMore;
  decision_id: DecisionId;
  decision_scope: DecisionScope;
  objective: Objective;
  metric_definition: MetricDefinition;
  metric_unit: MetricUnit;
  comparison_contract: ComparisonContract;
  points: Points;
  ranking_performed: RankingPerformed;
  claim_scope: ClaimScope;
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
export interface ScanPoint {
  ordinal: Ordinal;
  candidate_id: CandidateId1;
  site_ratio: SiteRatio;
  dense_oc_dmt_ratio: DenseOcDmtRatio;
  status: Status;
  feasible: Feasible;
  metric_value: MetricValue;
  reason_codes: ReasonCodes;
}
