/* Generated from public Pydantic contracts. Do not edit. */

export type ProjectId = string;
export type ProjectRevision = number;
export type Id = string;
export type Version = string;
export type Title = string;
export type Scope = string;
export type SourceReference = string;
export type SourceVersion = string;
export type Id1 = string;
export type Title1 = string;
export type Description = string;
export type Steps = MethodStep[];
export type Id2 = string;
export type Title2 = string;
export type Latex = string;
export type Assumptions = string[];
export type Implementation = string[];
export type Status = "implemented" | "conditional" | "undefined_in_source" | "source_discrepancy";
export type Formulas = MethodFormula[];
export type Tools = string[];
export type Discrepancies = string[];
export type FormalFormulaEditable = false;
export type Methods = MethodDefinition[];
export type Id3 = string;
export type Name = string;
export type Version1 = string;
export type Description1 = string;
export type Runtime = string;
export type Status1 = "registered_not_tested";
export type License = string;
export type InputNames = string[];
export type OutputScope = string;
export type ConfiguredMode = string | null;
export type Limitations = string[];
export type ParameterRecords = {
  [k: string]: unknown;
}[];

export interface ModuleMethodView {
  project_id: ProjectId;
  project_revision: ProjectRevision;
  methods: Methods;
  tool: ModuleTool;
  configured_mode: ConfiguredMode;
  limitations: Limitations;
  parameter_records: ParameterRecords;
}
export interface MethodDefinition {
  id: Id;
  version: Version;
  title: Title;
  scope: Scope;
  source_reference: SourceReference;
  source_version: SourceVersion;
  steps: Steps;
  formulas: Formulas;
  symbols: Symbols;
  tools: Tools;
  discrepancies: Discrepancies;
  formal_formula_editable: FormalFormulaEditable;
}
export interface MethodStep {
  id: Id1;
  title: Title1;
  description: Description;
}
export interface MethodFormula {
  id: Id2;
  title: Title2;
  latex: Latex;
  assumptions: Assumptions;
  implementation: Implementation;
  status: Status;
}
export interface Symbols {
  [k: string]: string;
}
export interface ModuleTool {
  id: Id3;
  name: Name;
  version: Version1;
  description: Description1;
  runtime: Runtime;
  status: Status1;
  license: License;
  input_names: InputNames;
  output_scope: OutputScope;
}
