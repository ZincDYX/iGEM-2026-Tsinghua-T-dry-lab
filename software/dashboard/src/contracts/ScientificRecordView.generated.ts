/* Generated from public Pydantic contracts. Do not edit. */

export type Kind = "construct" | "parameter";
export type Id = string;
export type Components = string[];
export type Id1 = string;
export type Kind1 = "protein" | "idr" | "enzyme_ligand_linker" | "scaffold_linker" | "rigid_linker" | "tag";
export type Sequence = string | null;
export type Parts = OrderedPartConfig[];
export type DomainOrder = string[];
export type FusionOrientation = string | null;
export type LocalizationContext = ("cytosolic" | "er_anchored") | null;
export type LocalizationDesignEvidence = string | null;
export type M1Review = {
  [k: string]: unknown;
} | null;
export type LinkerIds = string[];
export type ScaffoldId = string | null;
export type RecruitmentTags = string[];
export type EnzymeIds = string[];
export type OcNTerminalTruncation = boolean | null;
export type ExperimentalBaseline = boolean;
export type CodingDna = string | null;
export type SequenceSourceRef = string | null;
export type ForbiddenRestrictionSites = {
  [k: string]: string;
} | null;
export type IdrIds = string[];
export type ReferenceAccession = string;
/**
 * @minItems 1
 */
export type DeletedReferenceResidues = [number, ...number[]];
export type SourceReference = string;
export type ParameterId = string;
export type Name = string;
export type Value = number | string;
export type Unit = string | null;
export type SpeciesId = string | null;
export type EnzymeId = string | null;
export type SubstrateId = string | null;
export type ProductId = string | null;
export type ConstructId = string | null;
export type ConditionId = string | null;
export type ParameterType =
  | "kcat"
  | "km"
  | "kd"
  | "kp"
  | "phi"
  | "abundance"
  | "activity_ratio"
  | "degradation_rate"
  | "export_rate"
  | "input_flux"
  | "hill_coefficient"
  | "other";
export type SourceType = "literature" | "wetlab" | "prediction" | "assumption";
export type DerivationType = "direct_measurement" | "model_fit" | "literature_extraction" | "other";
export type SourceReference1 = string | null;
export type Doi = string | null;
export type EvidenceText = string | null;
export type EvidenceLocation = string | null;
export type Value1 = number | null;
export type Lower = number | null;
export type Upper = number | null;
export type Type = string | null;
export type ReviewStatus = "extracted" | "validated" | "approved" | "rejected";
export type ApprovedBy = string | null;
export type ValidationFlags = string[];
export type CreatedAt = string;
export type UpdatedAt = string;
export type ModelVersion = string | null;
export type ParameterVersion = number;
export type Supersedes = string | null;
export type DerivedFrom = string[];
export type Notes = string;

export interface ScientificRecordView {
  kind: Kind;
  construct_record: ConstructDefinition | null;
  parameter: ParameterRecord | null;
}
/**
 * A wet-lab construct description; no fusion topology is inferred by code.
 */
export interface ConstructDefinition {
  id: Id;
  components: Components;
  parts: Parts;
  domain_order: DomainOrder;
  fusion_orientation: FusionOrientation;
  localization_context: LocalizationContext;
  localization_design_evidence: LocalizationDesignEvidence;
  m1_review: M1Review;
  linker_ids: LinkerIds;
  scaffold_id: ScaffoldId;
  recruitment_tags: RecruitmentTags;
  enzyme_ids: EnzymeIds;
  oc_n_terminal_truncation: OcNTerminalTruncation;
  experimental_baseline: ExperimentalBaseline;
  coding_dna: CodingDna;
  sequence_source_ref: SequenceSourceRef;
  forbidden_restriction_sites: ForbiddenRestrictionSites;
  idr_ids: IdrIds;
  sequences: Sequences;
  provenance: Provenance;
  oc_truncation_mapping: TruncationMapping | null;
}
export interface OrderedPartConfig {
  id: Id1;
  kind: Kind1;
  sequence: Sequence;
}
export interface Sequences {
  [k: string]: string;
}
export interface Provenance {
  [k: string]: unknown;
}
export interface TruncationMapping {
  reference_accession: ReferenceAccession;
  deleted_reference_residues: DeletedReferenceResidues;
  reference_to_fusion: ReferenceToFusion;
  source_reference: SourceReference;
}
export interface ReferenceToFusion {
  [k: string]: number;
}
export interface ParameterRecord {
  parameter_id: ParameterId;
  name: Name;
  value: Value;
  unit: Unit;
  species_id: SpeciesId;
  enzyme_id: EnzymeId;
  substrate_id: SubstrateId;
  product_id: ProductId;
  construct_id: ConstructId;
  condition_id: ConditionId;
  parameter_type: ParameterType;
  source_type: SourceType;
  derivation_type: DerivationType;
  source_reference: SourceReference1;
  doi: Doi;
  evidence_text: EvidenceText;
  evidence_location: EvidenceLocation;
  conditions: Conditions;
  uncertainty: ParameterUncertainty | null;
  review_status: ReviewStatus;
  approved_by: ApprovedBy;
  validation_flags: ValidationFlags;
  created_at: CreatedAt;
  updated_at: UpdatedAt;
  model_version: ModelVersion;
  parameter_version: ParameterVersion;
  supersedes: Supersedes;
  derived_from: DerivedFrom;
  notes: Notes;
}
export interface Conditions {
  [k: string]: string | number;
}
export interface ParameterUncertainty {
  value: Value1;
  lower: Lower;
  upper: Upper;
  type: Type;
}
