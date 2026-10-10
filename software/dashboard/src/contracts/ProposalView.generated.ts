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
export type Reason = string;
export type EvidenceRefs = string[];
export type Kind = "inspect_project";
export type Reason1 = string;
export type EvidenceRefs1 = string[];
export type Kind1 = "retrieve_evidence";
export type Query = string;
export type SourceScope = "project_registry" | "registered_artifacts";
export type Reason2 = string;
export type EvidenceRefs2 = string[];
export type Kind2 = "prepare_node";
export type ToolId2 = string;
export type InputRefs = string[];
export type Reason3 = string;
export type EvidenceRefs3 = string[];
export type Kind3 = "submit_job";
export type ReviewedProposalId = string;
export type Reason4 = string;
export type EvidenceRefs4 = string[];
export type Kind4 = "inspect_job";
export type RunId2 = string;
export type Reason5 = string;
export type EvidenceRefs5 = string[];
export type Kind5 = "evaluate_result";
export type ResultRef1 = string;
export type Metric = "recorded_stage_status" | "recorded_mass_balance" | "recorded_applicability";
export type Reason6 = string;
export type EvidenceRefs6 = string[];
export type Kind6 = "propose_experiment";
export type Hypothesis = string;
/**
 * @minItems 1
 */
export type Controls = [string, ...string[]];
export type Observable = string;
export type RefutationCriterion = string;
export type RequiresHumanReview = true;
export type Reason7 = string;
export type EvidenceRefs7 = string[];
export type Kind7 = "wait";
/**
 * @minItems 1
 */
export type PendingRefs = [string, ...string[]];
export type Reason8 = string;
export type EvidenceRefs8 = string[];
export type Kind8 = "finish";
export type Outcome = "available_work_completed" | "human_input_required" | "no_compute_requested";
export type ScientificActions = (
  | InspectProjectAction
  | RetrieveEvidenceAction
  | PrepareNodeAction
  | SubmitJobAction
  | InspectJobAction
  | EvaluateResultAction
  | ProposeExperimentAction
  | WaitAction
  | FinishAction
)[];
export type ReviewedToolLabels = string[];
export type Id = string;
export type TaskId = string;
export type ProjectId1 = string;
export type Source = string;
export type Status = "proposed" | "accepted" | "rejected" | "blocked" | "stale";
export type Objective = string;
export type Rationale = string;
export type ChangeTypes = string[];
export type Evidence = string[];
export type RequestedStages = string[];
export type ExecutionStages = string[];
export type ReusedArtifacts = string[];
export type MissingInputs = string[];
export type Limitations1 = string[];
export type Id1 = string;
export type Name = string;
export type Description = string;
export type Version1 = string;
/**
 * @minItems 1
 */
export type Nodes = [WorkflowNode, ...WorkflowNode[]];
export type Id2 = string;
export type Label = string;
export type ToolId3 = string;
export type Kind9 = "literal";
export type Kind10 = "project";
export type Path = (string | number)[];
export type Kind11 = "node";
export type NodeId2 = string;
export type Path1 = (string | number)[];
export type Kind12 = "sequence";
export type Source1 = "project" | "scientific_fasta";
export type FileId = string | null;
export type RecordId = string;
export type SequenceSha256 = string;
export type ConstructVersion = number;
export type DependsOn = string[];
export type Items = LiteralInput | ProjectInput | NodeInput | SequenceRef;
export type ItemArgument = string;
export type TargetNodeId = string | null;
export type MaxCompletedStages = number | null;
export type CheckpointsBefore = string[];
export type CheckpointsAfter = string[];
export type AllowedTools = string[];
export type MaxToolCalls = number;
export type StopAfterSeconds = number | null;
export type MemoryLimitMb = number | null;
export type ProjectId2 = string;
export type ProjectRevision1 = number;
export type ProjectInputSha256 = string;
export type WorkflowSha256 = string;
export type CreatedAt = string;
export type ReviewIdentity = {
  [k: string]: unknown;
} | null;
export type PreviousReviewIdentity = {
  [k: string]: unknown;
} | null;

export interface ProposalView {
  observation: ScientificObservation | null;
  scientific_actions: ScientificActions;
  reviewed_tool_labels: ReviewedToolLabels;
  id: Id;
  task_id: TaskId;
  project_id: ProjectId1;
  source: Source;
  status: Status;
  objective: Objective;
  rationale: Rationale;
  change_types: ChangeTypes;
  evidence: Evidence;
  requested_stages: RequestedStages;
  execution_stages: ExecutionStages;
  reused_artifacts: ReusedArtifacts;
  missing_inputs: MissingInputs;
  limitations: Limitations1;
  workflow: Workflow | null;
  confirmation: PlanBinding | null;
  created_at: CreatedAt;
  review_identity: ReviewIdentity;
  previous_review_identity: PreviousReviewIdentity;
}
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
export interface InspectProjectAction {
  reason: Reason;
  evidence_refs: EvidenceRefs;
  kind: Kind;
}
export interface RetrieveEvidenceAction {
  reason: Reason1;
  evidence_refs: EvidenceRefs1;
  kind: Kind1;
  query: Query;
  source_scope: SourceScope;
}
export interface PrepareNodeAction {
  reason: Reason2;
  evidence_refs: EvidenceRefs2;
  kind: Kind2;
  tool_id: ToolId2;
  input_refs: InputRefs;
}
export interface SubmitJobAction {
  reason: Reason3;
  evidence_refs: EvidenceRefs3;
  kind: Kind3;
  reviewed_proposal_id: ReviewedProposalId;
}
export interface InspectJobAction {
  reason: Reason4;
  evidence_refs: EvidenceRefs4;
  kind: Kind4;
  run_id: RunId2;
}
export interface EvaluateResultAction {
  reason: Reason5;
  evidence_refs: EvidenceRefs5;
  kind: Kind5;
  result_ref: ResultRef1;
  metric: Metric;
}
export interface ProposeExperimentAction {
  reason: Reason6;
  evidence_refs: EvidenceRefs6;
  kind: Kind6;
  hypothesis: Hypothesis;
  controls: Controls;
  observable: Observable;
  refutation_criterion: RefutationCriterion;
  requires_human_review: RequiresHumanReview;
}
export interface WaitAction {
  reason: Reason7;
  evidence_refs: EvidenceRefs7;
  kind: Kind7;
  pending_refs: PendingRefs;
}
export interface FinishAction {
  reason: Reason8;
  evidence_refs: EvidenceRefs8;
  kind: Kind8;
  outcome: Outcome;
}
export interface Workflow {
  id: Id1;
  name: Name;
  description: Description;
  version: Version1;
  nodes: Nodes;
  execution_policy: ExecutionPolicy;
}
export interface WorkflowNode {
  id: Id2;
  label: Label;
  tool_id: ToolId3;
  inputs: Inputs;
  depends_on: DependsOn;
  map: MapSpec | null;
}
export interface Inputs {
  [k: string]: LiteralInput | ProjectInput | NodeInput | SequenceRef;
}
export interface LiteralInput {
  kind: Kind9;
  value: Value1;
}
export interface Value1 {
  [k: string]: unknown;
}
export interface ProjectInput {
  kind: Kind10;
  path: Path;
}
export interface NodeInput {
  kind: Kind11;
  node_id: NodeId2;
  path: Path1;
}
export interface SequenceRef {
  kind: Kind12;
  source: Source1;
  file_id: FileId;
  record_id: RecordId;
  sequence_sha256: SequenceSha256;
  construct_version: ConstructVersion;
}
export interface MapSpec {
  items: Items;
  item_argument: ItemArgument;
}
export interface ExecutionPolicy {
  target_node_id: TargetNodeId;
  max_completed_stages: MaxCompletedStages;
  checkpoints_before: CheckpointsBefore;
  checkpoints_after: CheckpointsAfter;
  allowed_tools: AllowedTools;
  max_tool_calls: MaxToolCalls;
  stop_after_seconds: StopAfterSeconds;
  memory_limit_mb: MemoryLimitMb;
}
export interface PlanBinding {
  project_id: ProjectId2;
  project_revision: ProjectRevision1;
  project_input_sha256: ProjectInputSha256;
  workflow_sha256: WorkflowSha256;
}
