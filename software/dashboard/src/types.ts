export type Json =
  null | boolean | number | string | Json[] | { [key: string]: Json };
export interface Sequence {
  id: string;
  sequence: string;
  role: string;
}
export interface Assembly {
  id: string;
  subunits: Record<string, number>;
  description: string;
}
export interface ImportedFile {
  id: string;
  sha256: string;
  path: string;
  name: string;
}
export interface Project {
  id: string;
  name: string;
  revision: number;
  description: string;
  sequences: Sequence[];
  assemblies: Assembly[];
  conditions: Record<string, Json>;
  pathway: Record<string, Json> | null;
  files: ImportedFile[];
  datasets: Record<string, Json>[];
  scientific_project?: ScientificProject | null;
}
export interface ScientificProject {
  config: Record<string, Json>;
  evidence_files: { path: string; sha256: string }[];
  dependency_scope: string;
}
export type Input =
  | { kind: "literal"; value: Json }
  | { kind: "project"; path: (string | number)[] }
  | { kind: "node"; node_id: string; path: (string | number)[] };
export interface WorkflowNode {
  id: string;
  label: string;
  tool_id: string;
  inputs: Record<string, Input>;
  depends_on: string[];
  map: { items: Input; item_argument: string } | null;
}
export interface Workflow {
  id: string;
  name: string;
  description: string;
  version: string;
  nodes: WorkflowNode[];
}
export interface PlanBinding {
  project_id: string;
  project_revision: number;
  project_input_sha256: string;
  workflow_sha256: string;
}
export interface ReviewedPlan {
  workflow: Workflow;
  confirmation: PlanBinding;
  source: string;
  requires_confirmation: boolean;
}
export type RunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "paused"
  | "interrupted"
  | "cancelled";
export interface RunSummary {
  name?: string;
  project_revision?: number;
  id: string;
  project_id: string;
  status: RunStatus;
  snapshot_hash: string;
  created_at: string;
  updated_at: string;
}
export interface NodeRecord {
  id: string;
  parent_id: string | null;
  status: string;
  attempts: number;
  inputs: Record<string, Json> | null;
  output: Record<string, Json> | null;
  error: { code: string; message: string } | null;
}
export interface Artifact {
  id: string;
  run_id: string;
  node_id: string;
  hash: string;
  path: string;
  upstream: string[];
  metadata: Record<string, Json>;
}
export interface Run extends RunSummary {
  heartbeat: string | null;
  owner: string | null;
  control: string | null;
  snapshot: {
    project: Project;
    workflow: Workflow;
    tools: Record<string, Json>;
    environment: Record<string, Json>;
  };
  nodes: NodeRecord[];
  events: {
    seq: number;
    node_id: string | null;
    event: string;
    timestamp: string;
    payload: Record<string, Json>;
  }[];
  artifacts: Artifact[];
}
export interface Tool {
  id: string;
  name: string;
  description: string;
  capability: string;
  version: string;
  runtime: string;
  plugin_hash: string | null;
  input_schema: Record<string, Json>;
  output_schema: Record<string, Json>;
  idempotent: boolean;
  resource: string;
}
export interface ImportPreview {
  kind: string;
  patch: Partial<Project>;
  file: ImportedFile;
}
export interface PluginInspection {
  manifest: {
    id: string;
    name: string;
    version: string;
    description: string;
    permissions: string[];
    license: string;
    runtime: string;
  };
  hash: string;
  sandboxed: boolean;
  trust_required: boolean;
  installed?: boolean;
}
export interface RuntimeInfo {
  name: string;
  workspace_id: string;
  protocol_version: string;
  authentication: string;
  capabilities: Record<string, string>;
  storage: string;
  max_workers: number;
  plugin_sandbox: boolean;
  agent_backend: string;
  supported_rate_laws: string[];
}
export type Goal = "fusion_screen" | "assembly_review" | "pathway_simulation" | "scientific_pipeline";
