/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type ProjectId = string;
export type ProjectRevision = number;
export type Version = number;
export type BaseMethodId = string;
export type BaseVersion = string;
export type Title = string;
export type FormulaId = string;
export type OriginalLatex = string;
export type Latex = string;
export type Reason = string;
export type SourceReference = string;
export type PreviousId = string | null;
export type ValidationStatus = "unvalidated";
export type Executable = boolean;
export type Expression = string;
export type Value = number;
export type Unit = string;
export type Source = string;
export type OutputUnit = string;
export type Items = MethodDraftView[];
export type HasMore = boolean;

export interface MethodDraftPage {
  items: Items;
  has_more: HasMore;
}
export interface MethodDraftView {
  id: Id;
  project_id: ProjectId;
  project_revision: ProjectRevision;
  version: Version;
  base_method_id: BaseMethodId;
  base_version: BaseVersion;
  title: Title;
  formula_id: FormulaId;
  original_latex: OriginalLatex;
  latex: Latex;
  reason: Reason;
  source_reference: SourceReference;
  previous_id: PreviousId;
  validation_status: ValidationStatus;
  executable: Executable;
  execution_spec: FormulaSpec | null;
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
