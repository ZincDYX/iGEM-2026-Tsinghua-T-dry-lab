/* Generated from public Pydantic contracts. Do not edit. */

export type ProjectId = string;
export type ProjectRevision = number;
export type ObservationIdentity = string;
export type ScientificInputIdentity = string | null;
export type PreparedThrough = string | null;
export type AvailableInputRefs = string[];
export type Stage = string;
export type Code = string;
export type ConstructId = string | null;
export type ConditionId = string | null;
export type Reasons = string[];
export type Gaps = ScientificGap[];
export type OmittedGapCount = number;
export type ParameterId = string;
export type ParameterType = string;
export type ConstructId1 = string | null;
export type ConditionId1 = string | null;
export type ReviewStatus = string;
export type SourceType = string;
export type Unit = string | null;
export type EntityBasis = string | null;
export type ModelVersion = string | null;
export type Value = number | string;
export type ParameterVersion = number;
export type ParameterSummaries = ReviewedParameterSummary[];
export type OmittedParameterCount = number;
export type ToolId = string;
export type Version = string;
export type Resource = string;
export type RouteState = "local_method" | "configured_not_verified" | "unconfigured";
export type ExecutionAllowedByPolicy = boolean;
export type Capabilities = DomainCapability[];
export type RunId = string;
export type NodeId = string;
export type Stage1 = string;
export type NodeStatus = string;
export type Attempt = number;
export type ResultRef = string | null;
export type CurrentProjectRevision = boolean;
export type NumericallySolvedCount = number | null;
export type EvidenceReadyCount = number | null;
export type ClaimScopes = string[];
export type RecordedResults = RecordedStageResult[];
export type RunId1 = string;
export type NodeId1 = string;
export type ToolId1 = string;
export type NodeStatus1 = string;
export type Attempt1 = number;
export type ToolStatus = string | null;
export type ParseStatus = string | null;
export type RemoteStatus = string | null;
export type RemotePollCount = number | null;
export type RemoteCancellationConfirmed = false;
export type RecordedJobs = RecordedJob[];
export type AcceptedProposalRefs = string[];
export type Limitations = string[];

export interface ScientificObservation {
  project_id: ProjectId;
  project_revision: ProjectRevision;
  observation_identity: ObservationIdentity;
  scientific_input_identity: ScientificInputIdentity;
  prepared_through: PreparedThrough;
  scenarios: Scenarios;
  available_input_refs: AvailableInputRefs;
  gaps: Gaps;
  omitted_gap_count: OmittedGapCount;
  parameter_summaries: ParameterSummaries;
  omitted_parameter_count: OmittedParameterCount;
  capabilities: Capabilities;
  recorded_results: RecordedResults;
  recorded_jobs: RecordedJobs;
  accepted_proposal_refs: AcceptedProposalRefs;
  budget: Budget;
  limitations: Limitations;
}
export interface Scenarios {
  [k: string]: string;
}
export interface ScientificGap {
  stage: Stage;
  code: Code;
  construct_id: ConstructId;
  condition_id: ConditionId;
  reasons: Reasons;
}
export interface ReviewedParameterSummary {
  parameter_id: ParameterId;
  parameter_type: ParameterType;
  construct_id: ConstructId1;
  condition_id: ConditionId1;
  review_status: ReviewStatus;
  source_type: SourceType;
  unit: Unit;
  entity_basis: EntityBasis;
  model_version: ModelVersion;
  value: Value;
  parameter_version: ParameterVersion;
  conditions: Conditions;
}
export interface Conditions {
  [k: string]: string | number;
}
export interface DomainCapability {
  tool_id: ToolId;
  version: Version;
  resource: Resource;
  route_state: RouteState;
  execution_allowed_by_policy: ExecutionAllowedByPolicy;
}
export interface RecordedStageResult {
  run_id: RunId;
  node_id: NodeId;
  stage: Stage1;
  node_status: NodeStatus;
  attempt: Attempt;
  result_ref: ResultRef;
  current_project_revision: CurrentProjectRevision;
  scientific_status_counts: ScientificStatusCounts;
  numerically_solved_count: NumericallySolvedCount;
  evidence_ready_count: EvidenceReadyCount;
  claim_scopes: ClaimScopes;
}
export interface ScientificStatusCounts {
  [k: string]: number;
}
export interface RecordedJob {
  run_id: RunId1;
  node_id: NodeId1;
  tool_id: ToolId1;
  node_status: NodeStatus1;
  attempt: Attempt1;
  tool_status: ToolStatus;
  parse_status: ParseStatus;
  remote_status: RemoteStatus;
  remote_poll_count: RemotePollCount;
  remote_cancellation_confirmed: RemoteCancellationConfirmed;
}
export interface Budget {
  [k: string]: number | null;
}
