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
export type ParameterRequirements = {
  [k: string]: unknown;
}[];
export type Id4 = string;
export type ProjectId1 = string;
export type ProjectRevision1 = number;
export type Version2 = number;
export type BaseMethodId = string;
export type BaseVersion = string;
export type Title3 = string;
export type FormulaId = string;
export type OriginalLatex = string;
export type Latex1 = string;
export type Reason = string;
export type SourceReference1 = string;
export type PreviousId = string | null;
export type ValidationStatus = "unvalidated";
export type Executable = boolean;
export type Expression = string;
export type Value = number;
export type Unit = string;
export type Source = string;
export type OutputUnit = string;

export interface ModuleMethodView {
  project_id: ProjectId;
  project_revision: ProjectRevision;
  methods: Methods;
  tool: ModuleTool;
  configured_mode: ConfiguredMode;
  limitations: Limitations;
  parameter_records: ParameterRecords;
  parameter_requirements: ParameterRequirements;
  parameter_source_options: ParameterSourceOptions;
  scalar_method: MethodDraftView | null;
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
export interface ParameterSourceOptions {
  [k: string]: string[];
}
export interface MethodDraftView {
  id: Id4;
  project_id: ProjectId1;
  project_revision: ProjectRevision1;
  version: Version2;
  base_method_id: BaseMethodId;
  base_version: BaseVersion;
  title: Title3;
  formula_id: FormulaId;
  original_latex: OriginalLatex;
  latex: Latex1;
  reason: Reason;
  source_reference: SourceReference1;
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
