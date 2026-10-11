/* Generated from public Pydantic contracts. Do not edit. */

export type ProjectId = string;
export type Seq = number;
export type Role = "user" | "assistant";
export type Text = string;
export type ProposalId = string;
export type ProjectRevision = number;
export type Timestamp = string;
export type Messages = AssistantMessage[];
export type HasMore = boolean;

export interface AssistantPage {
  project_id: ProjectId;
  messages: Messages;
  has_more: HasMore;
}
export interface AssistantMessage {
  seq: Seq;
  role: Role;
  text: Text;
  proposal_id: ProposalId;
  project_revision: ProjectRevision;
  timestamp: Timestamp;
}
