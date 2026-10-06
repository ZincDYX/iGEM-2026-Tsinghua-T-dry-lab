/* Generated from public Pydantic contracts. Do not edit. */

export type Kind = string;
export type Id = string;
export type FileId = string;
export type Path = string;
export type Sha256 = string;
export type Name = string;

export interface ImportView {
  kind: Kind;
  patch: Patch;
  file: AssetIdentity;
}
export interface Patch {
  [k: string]: unknown;
}
export interface AssetIdentity {
  id: Id;
  file_id: FileId;
  path: Path;
  sha256: Sha256;
  name: Name;
}
