/* Generated from public Pydantic contracts. Do not edit. */

export type Seq = number;
export type NodeId = string | null;
export type Event = string;
export type Timestamp = string;
export type Items = PublicEvent[];
export type Cursor = number;
export type HasMore = boolean;

export interface EventPage {
  items: Items;
  cursor: Cursor;
  has_more: HasMore;
}
export interface PublicEvent {
  seq: Seq;
  node_id: NodeId;
  event: Event;
  timestamp: Timestamp;
  payload: Payload;
}
export interface Payload {
  [k: string]: unknown;
}
