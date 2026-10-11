/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "custom-formula-v1";
export type MethodId = string;
export type MethodVersion = number;
export type Title = string;
export type BaseMethodId = string;
export type BaseVersion = string;
export type Latex = string;
export type Reason = string;
export type SourceReference = string;
export type Expression = string;
export type Value = number;
export type Unit = string;
export type Source = string;
export type OutputUnit = string;
export type Value1 = number;
export type Unit1 = string;
export type ValidationStatus = "unvalidated";
export type EvidenceReady = false;
export type ClaimScope = "exploratory_scalar_calculation";
export type Interpretation = string;

export interface FormulaResult {
  schema_version: SchemaVersion;
  method: FormulaExecution;
  value: Value1;
  unit: Unit1;
  validation_status: ValidationStatus;
  evidence_ready: EvidenceReady;
  claim_scope: ClaimScope;
  interpretation: Interpretation;
}
export interface FormulaExecution {
  method_id: MethodId;
  method_version: MethodVersion;
  title: Title;
  base_method_id: BaseMethodId;
  base_version: BaseVersion;
  latex: Latex;
  reason: Reason;
  source_reference: SourceReference;
  spec: FormulaSpec;
}
export interface FormulaSpec {
  expression: Expression;
  variables: Variables;
  output_unit: OutputUnit;
}
export interface Variables {
  [k: string]: FormulaVariable;
}
export interface FormulaVariable {
  value: Value;
  unit: Unit;
  source: Source;
}
