/* Generated from public Pydantic contracts. Do not edit. */

export type Seq = number;
export type ProposalId = string | null;
export type RunId = string | null;
export type Action = string;
export type Actor = string;
export type Timestamp = string;

export interface ActionView {
  seq: Seq;
  proposal_id: ProposalId;
  run_id: RunId;
  action: Action;
  actor: Actor;
  timestamp: Timestamp;
}
