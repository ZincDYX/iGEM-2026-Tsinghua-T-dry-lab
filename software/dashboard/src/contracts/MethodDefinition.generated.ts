/* Generated from public Pydantic contracts. Do not edit. */

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
