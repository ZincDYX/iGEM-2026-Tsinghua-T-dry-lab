/* Generated from public Pydantic contracts. Do not edit. */

export type ProjectId = string;
export type ProjectRevision = number;
export type InputSha256 = string;
export type Stage = string;
export type Code = string;
export type FieldPath = string;
export type ConstructId = string | null;
export type ConditionId = string | null;
export type ReasonCodes = string[];
export type SourceKind = string;
export type Missing = KnownMissingInput[];
export type Scope = string;
export type FinalStageGatesRequired = boolean;
export type ScientificApprovalGranted = boolean;
export type Limitations = string[];

export interface ScientificPrecheckView {
  project_id: ProjectId;
  project_revision: ProjectRevision;
  input_sha256: InputSha256;
  missing: Missing;
  scope: Scope;
  final_stage_gates_required: FinalStageGatesRequired;
  scientific_approval_granted: ScientificApprovalGranted;
  limitations: Limitations;
}
export interface KnownMissingInput {
  stage: Stage;
  code: Code;
  field_path: FieldPath;
  construct_id: ConstructId;
  condition_id: ConditionId;
  reason_codes: ReasonCodes;
  source_kind: SourceKind;
}
