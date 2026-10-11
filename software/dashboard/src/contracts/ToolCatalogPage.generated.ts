/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type Version = string;
export type Description = string;
export type Runtime = string;
export type Status = "registered_not_tested";
export type License = string;
export type InputNames = string[];
export type OutputScope = string;
export type Items = ModuleTool[];
export type HasMore = boolean;

export interface ToolCatalogPage {
  items: Items;
  has_more: HasMore;
}
export interface ModuleTool {
  id: Id;
  name: Name;
  version: Version;
  description: Description;
  runtime: Runtime;
  status: Status;
  license: License;
  input_names: InputNames;
  output_scope: OutputScope;
}
