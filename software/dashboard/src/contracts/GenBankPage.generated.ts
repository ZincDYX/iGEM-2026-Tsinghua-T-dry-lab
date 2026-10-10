/* Generated from public Pydantic contracts. Do not edit. */

export type DesignId = string;
export type FileId = string;
export type RecordIndex = number;
export type RecordId = string;
export type RecordCount = number;
export type Description = string;
export type MoleculeType = string;
export type Dbxrefs = string[];
export type NucleotideCount = number;
export type NucleotideStart1Based = number;
export type NucleotideFragment = string | null;
export type FeatureOffset = number;
export type FeatureTotal = number;
export type FeatureIndex = number;
export type Type = string;
export type Location = string | null;
export type Parts = {
  [k: string]: unknown;
}[];
export type LinkedSequenceId = string | null;
export type TranslationStatus = string;
export type Features = GenBankFeatureView[];
export type ExportScope = "unchanged_original_annotated_genbank";

export interface GenBankPage {
  design_id: DesignId;
  file_id: FileId;
  record_index: RecordIndex;
  record_id: RecordId;
  record_count: RecordCount;
  description: Description;
  molecule_type: MoleculeType;
  annotations: Annotations;
  dbxrefs: Dbxrefs;
  nucleotide_count: NucleotideCount;
  nucleotide_start_1based: NucleotideStart1Based;
  nucleotide_fragment: NucleotideFragment;
  feature_offset: FeatureOffset;
  feature_total: FeatureTotal;
  features: Features;
  export_scope: ExportScope;
}
export interface Annotations {
  [k: string]: unknown;
}
export interface GenBankFeatureView {
  feature_index: FeatureIndex;
  type: Type;
  location: Location;
  parts: Parts;
  qualifiers: Qualifiers;
  linked_sequence_id: LinkedSequenceId;
  translation_status: TranslationStatus;
}
export interface Qualifiers {
  [k: string]: string[];
}
