/* Generated from public Pydantic contracts. Do not edit. */

export type ProposalId = string;
export type PreviousProposalId = string | null;
export type Kind = "node" | "tool" | "binding" | "dependency" | "permission";
export type Target = string;
export type Before = string | null;
export type After = string | null;
export type Changes = ProposalChange[];
export type MissingInputs = string[];
export type Evidence = string[];
export type Limitations = string[];

export interface ProposalDiff {
  proposal_id: ProposalId;
  previous_proposal_id: PreviousProposalId;
  changes: Changes;
  missing_inputs: MissingInputs;
  evidence: Evidence;
  limitations: Limitations;
}
export interface ProposalChange {
  kind: Kind;
  target: Target;
  before: Before;
  after: After;
}
