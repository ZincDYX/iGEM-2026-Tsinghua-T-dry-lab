/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type Description = string;
export type Version = string;
/**
 * @minItems 1
 */
export type Nodes = [WorkflowNode, ...WorkflowNode[]];
export type Id1 = string;
export type Label = string;
export type ToolId = string;
export type Kind = "literal";
export type Kind1 = "project";
export type Path = (string | number)[];
export type Kind2 = "node";
export type NodeId = string;
export type Path1 = (string | number)[];
export type Kind3 = "sequence";
export type Source = "project" | "scientific_fasta";
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
export type ProjectId = string;
export type ProjectRevision = number;
export type ProjectInputSha256 = string;
export type WorkflowSha256 = string;
export type Source1 = string;
export type RequiresConfirmation = boolean;
export type ReviewId = string;

export interface PlanView {
  workflow: Workflow;
  confirmation: PlanBinding;
  source: Source1;
  requires_confirmation: RequiresConfirmation;
  review_id: ReviewId;
}
export interface Workflow {
  id: Id;
  name: Name;
  description: Description;
  version: Version;
  nodes: Nodes;
  execution_policy: ExecutionPolicy;
}
export interface WorkflowNode {
  id: Id1;
  label: Label;
  tool_id: ToolId;
  inputs: Inputs;
  depends_on: DependsOn;
  map: MapSpec | null;
}
export interface Inputs {
  [k: string]: LiteralInput | ProjectInput | NodeInput | SequenceRef;
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
export interface SequenceRef {
  kind: Kind3;
  source: Source;
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
  project_id: ProjectId;
  project_revision: ProjectRevision;
  project_input_sha256: ProjectInputSha256;
  workflow_sha256: WorkflowSha256;
}
