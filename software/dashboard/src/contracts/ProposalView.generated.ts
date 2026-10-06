/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type TaskId = string;
export type ProjectId = string;
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
export type Limitations = string[];
export type Id1 = string;
export type Name = string;
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
export type ProjectId1 = string;
export type ProjectRevision = number;
export type ProjectInputSha256 = string;
export type WorkflowSha256 = string;
export type CreatedAt = string;

export interface ProposalView {
  id: Id;
  task_id: TaskId;
  project_id: ProjectId;
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
  limitations: Limitations;
  workflow: Workflow | null;
  confirmation: PlanBinding | null;
  created_at: CreatedAt;
}
export interface Workflow {
  id: Id1;
  name: Name;
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
export interface PlanBinding {
  project_id: ProjectId1;
  project_revision: ProjectRevision;
  project_input_sha256: ProjectInputSha256;
  workflow_sha256: WorkflowSha256;
}
