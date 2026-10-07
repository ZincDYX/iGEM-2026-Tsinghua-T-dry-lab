/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "display-structure-v1";
export type ProjectId = string;
export type FileId = string;
export type SourceSha256 = string;
export type RunId = string | null;
export type SnapshotHash = string | null;
export type NodeId = string | null;
export type Attempt = number | null;
export type CandidateId = string | null;
export type ConstructId = string | null;
export type ConditionId = string | null;
export type Format = string;
export type Offset = number;
export type Total = number;
export type Chains = string[];
export type Models = string[];
export type Model = string;
export type Chain = string;
export type ResidueNumber = string;
export type InsertionCode = string;
export type ResidueName = string;
export type Residues = ResidueIdentity[];
export type ConfidenceStatus = "not_registered" | "source_registered_not_scientific_approval";
export type MappingStatus = "not_registered" | "source_registered_not_scientific_approval";
export type PocketStatus = "not_registered" | "source_registered_not_scientific_approval";
export type AnnotationFileId = string | null;
export type AnnotationSha256 = string | null;
export type AnnotationSourceReference = string | null;
export type AnnotationSourceTool = string | null;
export type AnnotationSourceToolVersion = string | null;
export type FusionSequenceFileId = string | null;
export type FusionSequenceFileSha256 = string | null;
export type FusionSequenceId = string | null;
export type FullFusionPosition = number | null;
export type Region = ("enzyme" | "scaffold" | "idr" | "linker" | "ligand_tail" | "tag") | null;
export type ReferenceSha256 = string | null;
export type Pocket = boolean;
export type Clash = boolean;
export type Plddt = number | null;
export type ReferenceFileId = string | null;
export type Annotations = DisplayResidueAnnotation[];
export type AnnotationScope = "residue_page" | "full_model";
export type ReferenceSha2561 = string;
export type SourceReference = string;
export type SourceTool = string;
export type SourceToolVersion = string;
export type Direction = "reference_to_target";
export type CoordinateUnit = "angstrom";
export type Convention = "row_major_column_vector_xyz1";
export type Matrix = number[][];
export type ReferenceFileId1 = string;
export type TargetSha256 = string;
export type Overlays = DisplayOverlay[];
export type PreviewPolicy = "atom_coordinates_only_original_sealed";

export interface StructurePage {
  schema_version: SchemaVersion;
  identity: ResourceIdentity;
  format: Format;
  offset: Offset;
  total: Total;
  chains: Chains;
  models: Models;
  residues: Residues;
  confidence_status: ConfidenceStatus;
  mapping_status: MappingStatus;
  pocket_status: PocketStatus;
  annotation_file_id: AnnotationFileId;
  annotation_sha256: AnnotationSha256;
  annotation_source_reference: AnnotationSourceReference;
  annotation_source_tool: AnnotationSourceTool;
  annotation_source_tool_version: AnnotationSourceToolVersion;
  fusion_sequence_file_id: FusionSequenceFileId;
  fusion_sequence_file_sha256: FusionSequenceFileSha256;
  fusion_sequence_id: FusionSequenceId;
  annotations: Annotations;
  annotation_scope: AnnotationScope;
  overlays: Overlays;
  preview_policy: PreviewPolicy;
}
export interface ResourceIdentity {
  project_id: ProjectId;
  file_id: FileId;
  source_sha256: SourceSha256;
  run_id: RunId;
  snapshot_hash: SnapshotHash;
  node_id: NodeId;
  attempt: Attempt;
  candidate_id: CandidateId;
  construct_id: ConstructId;
  condition_id: ConditionId;
}
export interface ResidueIdentity {
  model: Model;
  chain: Chain;
  residue_number: ResidueNumber;
  insertion_code: InsertionCode;
  residue_name: ResidueName;
}
export interface DisplayResidueAnnotation {
  residue: ResidueIdentity;
  full_fusion_position: FullFusionPosition;
  region: Region;
  reference_residue: ResidueIdentity | null;
  reference_sha256: ReferenceSha256;
  pocket: Pocket;
  clash: Clash;
  plddt: Plddt;
  reference_file_id: ReferenceFileId;
}
export interface DisplayOverlay {
  reference_sha256: ReferenceSha2561;
  source_reference: SourceReference;
  source_tool: SourceTool;
  source_tool_version: SourceToolVersion;
  direction: Direction;
  coordinate_unit: CoordinateUnit;
  convention: Convention;
  matrix: Matrix;
  reference_file_id: ReferenceFileId1;
  target_sha256: TargetSha256;
}
