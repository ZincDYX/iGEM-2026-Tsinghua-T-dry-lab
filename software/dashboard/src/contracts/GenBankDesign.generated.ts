/* Generated from public Pydantic contracts. Do not edit. */

export type Kind = "genbank_design";
export type Id = string;
export type Name = string;
export type FileId = string;
export type RecordIndex = number;
export type RecordId = string;
export type NucleotideCount = number;
export type FeatureCount = number;
export type UntranslatedCdsCount = number;
export type Records = GenBankRecordRef[];
export type RecordIndex1 = number;
export type FeatureIndex = number;
export type SequenceId = string | null;
export type SourceProteinId = string | null;
export type CdsProteins = CDSProteinBinding[];

export interface GenBankDesign {
  kind: Kind;
  id: Id;
  name: Name;
  file_id: FileId;
  records: Records;
  cds_proteins: CdsProteins;
}
export interface GenBankRecordRef {
  record_index: RecordIndex;
  record_id: RecordId;
  nucleotide_count: NucleotideCount;
  feature_count: FeatureCount;
  untranslated_cds_count: UntranslatedCdsCount;
}
export interface CDSProteinBinding {
  record_index: RecordIndex1;
  feature_index: FeatureIndex;
  sequence_id: SequenceId;
  source_protein_id: SourceProteinId;
}
