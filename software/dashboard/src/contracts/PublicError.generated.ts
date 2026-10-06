/* Generated from public Pydantic contracts. Do not edit. */

export type Code = string;
export type Message = string;
export type DiagnosticId = string;
export type FieldPaths = string[];
export type LogicalFiles = string[];
export type Actions = string[];

export interface PublicError {
  code: Code;
  message: Message;
  diagnostic_id: DiagnosticId;
  field_paths: FieldPaths;
  logical_files: LogicalFiles;
  actions: Actions;
}
