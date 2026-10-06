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
export type SchemaVersion = "sequence-metrics-map-view-v1";
export type RunId = string;
export type ProjectId = string;
export type SnapshotHash = string;
export type ParentNodeId = string;
export type TotalCount = number;
export type Offset1 = number;
export type NodeId = string;
export type SequenceId = string | null;
export type SequenceSha256 = string | null;
export type Attempt = number;
export type Status1 = string;
export type ArtifactId = string | null;
export type ArtifactSha256 = string | null;
export type SchemaVersion1 = "sequence-metrics-v1";
export type Id1 = string;
export type Role = string;
export type FormulaVersion = string;
export type FeatureDefinitionsSha256 = string;
export type SequenceSha2561 = string;
export type Length = number;
export type GsFraction = number;
export type ProFraction = number;
export type AromaticFraction = number;
export type HydrophobicFraction = number;
export type ChargedFraction = number;
export type PolarFraction = number;
export type NetChargeProxy = number;
export type ShannonEntropy = number;
export type Top2Fraction = number;
export type MaxHydrophobicRun = number;
export type MeanHydropathy = number;
export type ForbiddenMotifs = string[];
export type ChargeBlockiness = null;
export type MultivalencyDensity = null;
export type ToolName = "Biopython ProtParam";
export type ToolVersion = string;
export type InputSha256 = string;
export type MolecularWeightDa = number;
export type TheoreticalPi = number;
export type Interpretation = string;
export type Issue = string | null;
export type Rows = SequenceMetricRow[];

export interface NodePage {
  node: NodeResultView;
  offset: Offset;
  limit: Limit;
  total_records: TotalRecords;
  artifact: Artifact;
  sequence_map: SequenceMapView | null;
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
export interface SequenceMapView {
  schema_version: SchemaVersion;
  run_id: RunId;
  project_id: ProjectId;
  snapshot_hash: SnapshotHash;
  parent_node_id: ParentNodeId;
  tool_identity: ToolIdentity;
  total_count: TotalCount;
  offset: Offset1;
  rows: Rows;
}
export interface ToolIdentity {
  [k: string]: unknown;
}
export interface SequenceMetricRow {
  node_id: NodeId;
  sequence_id: SequenceId;
  sequence_sha256: SequenceSha256;
  attempt: Attempt;
  status: Status1;
  artifact_id: ArtifactId;
  artifact_sha256: ArtifactSha256;
  metrics: SequenceMetricsView | null;
  issue: Issue;
}
export interface SequenceMetricsView {
  schema_version: SchemaVersion1;
  id: Id1;
  role: Role;
  features: SequenceFeatures;
  protparam: ProtParamEvidence;
  interpretation: Interpretation;
}
export interface SequenceFeatures {
  formula_version: FormulaVersion;
  feature_definitions_sha256: FeatureDefinitionsSha256;
  sequence_sha256: SequenceSha2561;
  length: Length;
  gs_fraction: GsFraction;
  pro_fraction: ProFraction;
  aromatic_fraction: AromaticFraction;
  hydrophobic_fraction: HydrophobicFraction;
  charged_fraction: ChargedFraction;
  polar_fraction: PolarFraction;
  net_charge_proxy: NetChargeProxy;
  shannon_entropy: ShannonEntropy;
  top2_fraction: Top2Fraction;
  max_hydrophobic_run: MaxHydrophobicRun;
  mean_hydropathy: MeanHydropathy;
  forbidden_motifs: ForbiddenMotifs;
  charge_blockiness: ChargeBlockiness;
  multivalency_density: MultivalencyDensity;
}
export interface ProtParamEvidence {
  tool_name: ToolName;
  tool_version: ToolVersion;
  input_sha256: InputSha256;
  molecular_weight_da: MolecularWeightDa;
  theoretical_pi: TheoreticalPi;
  amino_acid_counts: AminoAcidCounts;
}
export interface AminoAcidCounts {
  [k: string]: number;
}
