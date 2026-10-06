/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type ParentId = string | null;
export type Status = string;
export type Attempts = number;
export type Output = {
  [k: string]: unknown;
} | null;
export type Error = {
  [k: string]: unknown;
} | null;
export type Inputs = null;
export type Offset = number;
export type Limit = number;
export type TotalRecords = number;
export type Artifact = {
  [k: string]: string;
} | null;

export interface NodePage {
  node: NodeResultView;
  offset: Offset;
  limit: Limit;
  total_records: TotalRecords;
  artifact: Artifact;
}
export interface NodeResultView {
  id: Id;
  parent_id: ParentId;
  status: Status;
  attempts: Attempts;
  output: Output;
  error: Error;
  inputs: Inputs;
}
