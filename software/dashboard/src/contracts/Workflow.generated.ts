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
