/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type ProjectId = string;
export type ExpectedRevision = number;
export type State = "preview" | "committed" | "discarded";
export type DetectedFormat = string;
export type SemanticType = string;
export type Records = {
  [k: string]: unknown;
}[];
export type Code = string;
export type Message = string;
export type Severity = "error" | "warning" | "confirmation" | "info";
export type Field = string | null;
export type ExpectedFilename = string | null;
export type Issues = ImportIssue[];
export type ProposedLinks = {
  [k: string]: unknown;
}[];
export type SupportedScope = string;
export type InputRoles = string[];
export type Filename = string;
export type DuplicateFileId = string | null;
export type Items = ImportedItem[];
export type Issues1 = ImportIssue[];
export type ProposedLinks1 = {
  [k: string]: unknown;
}[];
export type RequiresConfirmation = boolean;

export interface ImportTransactionPreview {
  id: Id;
  project_id: ProjectId;
  expected_revision: ExpectedRevision;
  state: State;
  items: Items;
  issues: Issues1;
  proposed_links: ProposedLinks1;
  requires_confirmation: RequiresConfirmation;
}
export interface ImportedItem {
  detected_format: DetectedFormat;
  semantic_type: SemanticType;
  records: Records;
  issues: Issues;
  proposed_links: ProposedLinks;
  supported_scope: SupportedScope;
  input_roles: InputRoles;
  patch: Patch;
  filename: Filename;
  file: File;
  duplicate_file_id: DuplicateFileId;
}
export interface ImportIssue {
  code: Code;
  message: Message;
  severity: Severity;
  field: Field;
  expected_filename: ExpectedFilename;
}
export interface Patch {
  [k: string]: unknown;
}
export interface File {
  [k: string]: string;
}
