/* Generated from public Pydantic contracts. Do not edit. */

export type ProjectId = string;
export type ProjectRevision = number;
export type Offset = number;
export type Total = number;
export type Kind = "sequence";
export type Source = "project" | "scientific_fasta";
export type FileId = string | null;
export type RecordId = string;
export type SequenceSha256 = string;
export type ConstructVersion = number;
export type Label = string;
export type Length = number;
export type Role = string;
export type Items = SequenceChoice[];

export interface SequencePage {
  project_id: ProjectId;
  project_revision: ProjectRevision;
  offset: Offset;
  total: Total;
  items: Items;
}
export interface SequenceChoice {
  ref: SequenceRef;
  label: Label;
  length: Length;
  role: Role;
}
export interface SequenceRef {
  kind: Kind;
  source: Source;
  file_id: FileId;
  record_id: RecordId;
  sequence_sha256: SequenceSha256;
  construct_version: ConstructVersion;
}
