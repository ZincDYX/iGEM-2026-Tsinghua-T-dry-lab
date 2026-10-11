/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type Status = "not_configured" | "configured_unverified" | "available" | "failed";
export type Version = string | null;
export type LastRealCheck = string | null;
export type LatestFileId = string | null;
export type SourceReference = string;
export type Location = "connected_backend";
export type FailureStep = string | null;
export type Code = string;
export type Message = string;
export type DiagnosticId = string;
export type FieldPaths = string[];
export type LogicalFiles = string[];
export type Actions = string[];

export interface PredictionToolView {
  id: Id;
  name: Name;
  status: Status;
  version: Version;
  last_real_check: LastRealCheck;
  latest_file_id: LatestFileId;
  source_reference: SourceReference;
  location: Location;
  failure_step: FailureStep;
  problem: PublicError | null;
}
export interface PublicError {
  code: Code;
  message: Message;
  diagnostic_id: DiagnosticId;
  field_paths: FieldPaths;
  logical_files: LogicalFiles;
  actions: Actions;
}
