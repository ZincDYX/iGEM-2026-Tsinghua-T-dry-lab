/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type Revision = number;
export type Scientific = boolean;
export type SequenceCount = number;
export type ScientificSequenceCount = number | null;
export type ScientificSequenceIndexStatus = string;

export interface ProjectSummaryView {
  id: Id;
  name: Name;
  revision: Revision;
  scientific: Scientific;
  sequence_count: SequenceCount;
  scientific_sequence_count: ScientificSequenceCount;
  scientific_sequence_index_status: ScientificSequenceIndexStatus;
}
