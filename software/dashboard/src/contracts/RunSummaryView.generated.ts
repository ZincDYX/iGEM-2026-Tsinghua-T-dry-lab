/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type ProjectId = string;
export type Status = string;
export type SnapshotHash = string;
export type CreatedAt = string;
export type UpdatedAt = string;
export type Control = string | null;
export type Heartbeat = string | null;
export type StateVersion = number;
export type EventCursor = number;
export type ProjectRevision = number;
export type Id1 = string;
export type Name1 = string;
export type Description = string;
export type Version = string;
/**
 * @minItems 1
 */
export type Nodes = [WorkflowNode, ...WorkflowNode[]];
export type Id2 = string;
export type Label = string;
export type ToolId = string;
export type Kind = "literal";
export type Kind1 = "project";
export type Path = (string | number)[];
export type Kind2 = "node";
export type NodeId = string;
export type Path1 = (string | number)[];
export type DependsOn = string[];
export type Items = LiteralInput | ProjectInput | NodeInput;
export type ItemArgument = string;
export type TargetNodeId = string | null;
export type MaxCompletedStages = number | null;
export type CheckpointsBefore = string[];
export type CheckpointsAfter = string[];
export type AllowedTools = string[];
export type MaxToolCalls = number;
export type StopAfterSeconds = number | null;
export type MemoryLimitMb = number | null;
export type Id3 = string;
export type ParentId = string | null;
export type Status1 = string;
export type Attempts = number;
export type ToolId1 = string | null;
export type Label1 = string;
export type Module = string;
export type RecordCount = number;
export type NumericallySolvedCount = number;
export type EvidenceReadyCount = number;
export type MissingInputCount = number;
export type ClaimScope = string | null;
export type Nodes1 = NodeStateView[];
export type Id4 = string;
export type RunId = string;
export type NodeId1 = string;
export type Hash = string;
export type Name2 = string;
export type Upstream = string[];
export type Artifacts = ArtifactView[];

export interface RunSummaryView {
  id: Id;
  name: Name;
  project_id: ProjectId;
  status: Status;
  snapshot_hash: SnapshotHash;
  created_at: CreatedAt;
  updated_at: UpdatedAt;
  control: Control;
  heartbeat: Heartbeat;
  state_version: StateVersion;
  event_cursor: EventCursor;
  project_revision: ProjectRevision;
  workflow: Workflow;
  tools: Tools;
  nodes: Nodes1;
  artifacts: Artifacts;
}
export interface Workflow {
  id: Id1;
  name: Name1;
  description: Description;
  version: Version;
  nodes: Nodes;
  execution_policy: ExecutionPolicy;
}
export interface WorkflowNode {
  id: Id2;
  label: Label;
  tool_id: ToolId;
  inputs: Inputs;
  depends_on: DependsOn;
  map: MapSpec | null;
}
export interface Inputs {
  [k: string]: LiteralInput | ProjectInput | NodeInput;
}
export interface LiteralInput {
  kind: Kind;
  value: Value;
}
export interface Value {
  [k: string]: unknown;
}
export interface ProjectInput {
  kind: Kind1;
  path: Path;
}
export interface NodeInput {
  kind: Kind2;
  node_id: NodeId;
  path: Path1;
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
export interface Tools {
  [k: string]: unknown;
}
export interface NodeStateView {
  id: Id3;
  parent_id: ParentId;
  status: Status1;
  attempts: Attempts;
  tool_id: ToolId1;
  label: Label1;
  scientific_summary: ScientificStageSummary | null;
}
export interface ScientificStageSummary {
  module: Module;
  record_count: RecordCount;
  status_counts: StatusCounts;
  numerically_solved_count: NumericallySolvedCount;
  evidence_ready_count: EvidenceReadyCount;
  missing_input_count: MissingInputCount;
  claim_scope: ClaimScope;
}
export interface StatusCounts {
  [k: string]: number;
}
export interface ArtifactView {
  id: Id4;
  run_id: RunId;
  node_id: NodeId1;
  hash: Hash;
  name: Name2;
  upstream: Upstream;
  metadata: Metadata;
}
export interface Metadata {
  [k: string]: unknown;
}
