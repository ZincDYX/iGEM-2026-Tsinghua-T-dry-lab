/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type Revision = number;
export type Description = string;
export type Id1 = string;
export type Sequence = string;
export type Role = string;
export type Sequences = SequenceRecord[];
export type Id2 = string;
export type Description1 = string;
export type Assemblies = AssemblyRecord[];
export type Pathway = {
  [k: string]: unknown;
} | null;
export type Datasets = {
  [k: string]: unknown;
}[];
export type RuntimeProfileRef = string | null;
export type ParentRunId = string | null;
export type ParentSnapshotSha256 = string | null;
export type Id3 = string;
export type FileId = string;
export type Path = string;
export type Sha256 = string;
export type Name1 = string;
export type Files = AssetIdentity[];
export type Mode = "demo" | "real";
export type RequireProvenance = boolean;
export type AllowAssumptions = boolean;
export type AnalysisGrade = "formal_measured" | "mechanistic_sensitivity";
export type Host = string | null;
export type Strain = string | null;
export type TemperatureC = number | null;
export type Ph = number | null;
export type AssaySystem = string | null;
export type ProteinFasta = string;
export type Id4 = string;
export type Name2 = string;
export type Role1 = string;
export type Sdf = string | null;
export type Ligands = LigandConfig[];
export type Id5 = string;
export type ProteinId = string;
export type ReactionRole = string;
export type StructurePdb = string | null;
export type SequenceSha256 = string | null;
export type Enzymes = EnzymeConfig[];
export type Id6 = string;
export type Description2 = string;
export type OligomericState = number;
export type StructurePdb1 = string | null;
export type Scaffolds = ScaffoldConfig[];
export type Id7 = string;
export type Sequence1 = string;
export type Source = string;
export type SequenceKind = "idr" | "enzyme_ligand_linker" | "scaffold_linker" | "rigid_linker";
export type Linkers = LinkerConfig[];
export type IdrId = string | null;
export type Id8 = string;
export type Components = string[];
export type Id9 = string;
export type Kind = "protein" | "idr" | "enzyme_ligand_linker" | "scaffold_linker" | "rigid_linker" | "tag";
export type Sequence2 = string | null;
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
export type Constructs = ConstructDefinition[];
export type ConstructId = string;
export type ConstructType = string;
export type Proteins = string[];
export type Host1 = string | null;
export type Scaffold = string | null;
export type Idr = string | null;
export type RecruitmentDomains = string[];
export type LigandTags = string[];
export type FusionOrientation1 = string | null;
export type LocalizationContext1 = ("cytosolic" | "er_anchored") | null;
export type LocalizationDesignEvidence1 = string | null;
export type M1Review1 = {
  [k: string]: unknown;
} | null;
export type DomainOrder1 = string[];
export type Promoter = string | null;
export type CopyNumber = string | null;
export type CodingDna1 = string | null;
export type SequenceSourceRef1 = string | null;
export type ForbiddenRestrictionSites1 = {
  [k: string]: string;
} | null;
export type SourceType = string;
export type Doi = string | null;
export type Evidence = string | null;
export type ReviewStatus = string;
export type CreatedAt = string;
export type Supersedes = string | null;
export type Notes = string;
export type ConstructRecords = ConstructRecord[];
export type Id10 = string;
/**
 * @minItems 1
 */
export type ProteinConstructIds = [string, ...string[]];
export type RequiredEnzymeIds = string[];
export type Host2 = string | null;
export type ConditionId = string | null;
export type Designs = DesignConfig[];
export type ParameterId = string;
export type Name3 = string;
export type Value = number | string;
export type Unit = string | null;
export type SpeciesId = string | null;
export type EnzymeId = string | null;
export type SubstrateId = string | null;
export type ProductId = string | null;
export type ConstructId1 = string | null;
export type ConditionId1 = string | null;
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
export type SourceType1 = "literature" | "wetlab" | "prediction" | "assumption";
export type DerivationType = "direct_measurement" | "model_fit" | "literature_extraction" | "other";
export type SourceReference1 = string | null;
export type Doi1 = string | null;
export type EvidenceText = string | null;
export type EvidenceLocation = string | null;
export type Value1 = number | null;
export type Lower = number | null;
export type Upper = number | null;
export type Type = string | null;
export type ReviewStatus1 = "extracted" | "validated" | "approved" | "rejected";
export type ApprovedBy = string | null;
export type ValidationFlags = string[];
export type CreatedAt1 = string;
export type UpdatedAt = string;
export type ModelVersion = string | null;
export type ParameterVersion = number;
export type Supersedes1 = string | null;
export type DerivedFrom = string[];
export type Notes1 = string;
export type Parameters = ParameterRecord[];
export type TopN = number;
export type ForbiddenMotifs = string[];
export type FeatureDefinitionsFile = string;
export type RulesFile = string;
export type PredictorEvidenceFile = string | null;
export type RequireExternalEvidenceInRealMode = boolean;
export type StructureMetricsFile = string | null;
export type PhiSource = "measured" | "lever_rule" | "compare";
export type TargetEnzymeRatioParameter = string | null;
export type DesignDecisionId = string | null;
export type BindingModel = "independent" | "hill";
export type HillCoefficient = number | null;
export type EnzymeId1 = string;
export type EnzymeTotalParameter = string;
export type SiteTotalParameter = string;
export type KdParameter = string;
export type HillCoefficientParameter = string | null;
export type Recruitment = RecruitmentConfig[];
export type RecruitmentMode = "finite_site" | "legacy_independent_partition" | "effective_ratio";
export type SlotRatioSh3ToPdz = number | null;
export type TotalRecruitedFraction = number | null;
export type RecruitmentBiasOcVsDmt = number;
export type PtrPtPhaseHandling = "dilute_only" | "homogeneous_kp_1";
export type PtrScale = number;
export type PtScale = number;
export type OcScale = number;
export type DmtScale = number;
export type Source1 = "published_author_model" | "explicit_sensitivity_input";
export type Interpretation = "relative_enzyme_scale_not_measured_abundance";
export type LocalParameterNames = string[];
export type ParameterName = string;
export type Distribution = "uniform" | "empirical" | "interpolated_empirical";
export type InterpolationReference = string | null;
export type Lower1 = number | null;
export type Upper1 = number | null;
export type EmpiricalValues = number[];
export type SourceReference2 = string;
/**
 * @minItems 1
 */
export type ParameterIds = [string, ...string[]];
export type ReviewedBy = string;
export type Ranges = RangeEvidence[];
export type Samples = number;
export type RandomSeed = number;
export type StandardDeviationDdof = (0 | 1) | null;
export type IndependenceEvidenceReference = string | null;
export type A = number;
export type B = number;
export type C = number;
export type Const = number;
export type ThetaHydro = number;
export type ThetaAro = number;
export type SourceReference3 = string;
export type ApplicableDomainReference = string;
export type ReviewedBy1 = string;
export type AssayMode = ("substrate_feeding_functional" | "full_pathway_production") | null;
export type MeasurementCompartment = ("intracellular" | "extracellular" | "total_extract") | null;
export type ExpressionMode = ("constitutive" | "induced") | null;
export type FeedingTimeH = number | null;
export type NetworkVariant = "full_ten" | "oc_dmt_verified_absence";
export type Artifact = string;
export type Sha2561 = string;
export type ReviewedBy2 = string;
export type SteadyStateObservationReference = string | null;
export type TargetProduct = string;
export type FeedCompoundId = string | null;
export type FeedMode = ("batch_initial_state" | "continuous_feed") | null;
export type TEnd = number;
export type ConcentrationUnit = "uM";
export type X9 = number;
export type X10 = number;
export type X11 = number;
export type X13 = number;
export type X15 = number;
export type ConcentrationUnit1 = "uM" | "author_native";
export type ReactionNetworkFile = string | null;
export type SteadyStateInitialGuessUm = {
  [k: string]: number;
} | null;
export type OnTime = number;
export type OffTime = number | null;
export type Basal = number;
export type Induced = number;
export type Mode1 = "step" | "sigmoid";
export type TransitionWidth = number;
export type TimeUnit = "h" | "author_native_day_axis";
export type ConditionId2 = string | null;
export type MaxSideProductFraction13 = number;
export type Min13Reduction = number;
export type Min15Improvement = number;
export type MinProductivity = number;
export type EnableDegradation = boolean;
export type NetworkMode =
  "markdown_steady_state" | "legacy_reduced" | "galatea_full_competitive" | "published_reference";
export type ScenarioMode =
  | "published_reference"
  | "homogeneous_constitutive"
  | "homogeneous_published_like_temporal"
  | "galatea_spatial"
  | "galatea_spatiotemporal_ablation";
export type UnitMode = "physical" | "author_native_sensitivity";
export type AuthorNativeTimeLabel = "author_native_day_axis";
export type ActivityMode = "unity_assumption" | "sensitivity_parameters";
export type TransportAccess = "dilute_phase" | "cell_average";
export type TransportEnabled = boolean;
export type TransportRateParameter = string | null;
export type IntracellularVolumeL = number | null;
export type ExtracellularVolumeL = number | null;
export type VolumeSourceReference = string | null;
export type TransportRatioSourceReference = string | null;
export type FormulaVersion = string;
export type RateParameterId = string;
export type IntracellularVolumeParameterId = string;
export type ExtracellularVolumeParameterId = string;
export type SolverPoints = number;
export type WetlabResultsFile = string | null;
export type AbsoluteResidualTolerance = number;
export type RelativeResidualTolerance = number;
export type DiscrepancyThresholdConfigured = boolean;
export type ParameterName1 = string;
export type FixedParameterNames = string[];
/**
 * @minItems 2
 * @maxItems 2
 */
export type Bounds = [unknown, unknown];
/**
 * @minItems 1
 */
export type Observables = ["13" | "15", ...("13" | "15")[]];
export type Id11 = string;
export type EvidenceFiles = AssetIdentity[];
export type DependencyScope = string;
export type Status = "indexed" | "not_indexed";
export type FileId1 = string;
export type SourceSha256 = string;
export type Count = number | null;
export type ReasonCode = string | null;
export type RequiresConfirmation = boolean;
export type Status1 = string;

export interface BindingPreviewView {
  project: ProjectView;
  requires_confirmation: RequiresConfirmation;
  status: Status1;
}
export interface ProjectView {
  id: Id;
  name: Name;
  revision: Revision;
  description: Description;
  sequences: Sequences;
  assemblies: Assemblies;
  conditions: Conditions;
  pathway: Pathway;
  datasets: Datasets;
  runtime_profile_ref: RuntimeProfileRef;
  parent_run_id: ParentRunId;
  parent_snapshot_sha256: ParentSnapshotSha256;
  files: Files;
  scientific_project: ScientificInputsView | null;
}
export interface SequenceRecord {
  id: Id1;
  sequence: Sequence;
  role: Role;
}
export interface AssemblyRecord {
  id: Id2;
  subunits: Subunits;
  description: Description1;
}
export interface Subunits {
  [k: string]: number;
}
export interface Conditions {
  [k: string]: unknown;
}
export interface AssetIdentity {
  id: Id3;
  file_id: FileId;
  path: Path;
  sha256: Sha256;
  name: Name1;
}
export interface ScientificInputsView {
  config: ScientificConfig;
  evidence_files: EvidenceFiles;
  dependency_scope: DependencyScope;
  sequence_index: SequenceIndexView;
}
export interface ScientificConfig {
  execution: ExecutionConfig;
  experimental_context: ExperimentalContext;
  inputs: InputsConfig;
  parameters: Parameters;
  stages: StagesConfig;
  run: PublicRunInput;
}
export interface ExecutionConfig {
  mode: Mode;
  require_provenance: RequireProvenance;
  allow_assumptions: AllowAssumptions;
  analysis_grade: AnalysisGrade;
}
export interface ExperimentalContext {
  host: Host;
  strain: Strain;
  temperature_c: TemperatureC;
  pH: Ph;
  assay_system: AssaySystem;
}
export interface InputsConfig {
  protein_fasta: ProteinFasta;
  ligands: Ligands;
  enzymes: Enzymes;
  scaffolds: Scaffolds;
  linkers: Linkers;
  idr_id: IdrId;
  constructs: Constructs;
  construct_records: ConstructRecords;
  designs: Designs;
}
export interface LigandConfig {
  id: Id4;
  name: Name2;
  role: Role1;
  sdf: Sdf;
}
export interface EnzymeConfig {
  id: Id5;
  protein_id: ProteinId;
  reaction_role: ReactionRole;
  structure_pdb: StructurePdb;
  sequence_sha256: SequenceSha256;
}
export interface ScaffoldConfig {
  id: Id6;
  description: Description2;
  oligomeric_state: OligomericState;
  structure_pdb: StructurePdb1;
}
export interface LinkerConfig {
  id: Id7;
  sequence: Sequence1;
  source: Source;
  sequence_kind: SequenceKind;
}
/**
 * A wet-lab construct description; no fusion topology is inferred by code.
 */
export interface ConstructDefinition {
  id: Id8;
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
  sequences: Sequences1;
  provenance: Provenance;
  oc_truncation_mapping: TruncationMapping | null;
}
export interface OrderedPartConfig {
  id: Id9;
  kind: Kind;
  sequence: Sequence2;
}
export interface Sequences1 {
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
export interface ConstructRecord {
  construct_id: ConstructId;
  construct_type: ConstructType;
  proteins: Proteins;
  sequences: Sequences2;
  host: Host1;
  scaffold: Scaffold;
  idr: Idr;
  recruitment_domains: RecruitmentDomains;
  ligand_tags: LigandTags;
  fusion_orientation: FusionOrientation1;
  localization_context: LocalizationContext1;
  localization_design_evidence: LocalizationDesignEvidence1;
  m1_review: M1Review1;
  domain_order: DomainOrder1;
  linker_sequences: LinkerSequences;
  promoter: Promoter;
  copy_number: CopyNumber;
  coding_dna: CodingDna1;
  sequence_source_ref: SequenceSourceRef1;
  forbidden_restriction_sites: ForbiddenRestrictionSites1;
  experimental_conditions: ExperimentalConditions;
  measured_outputs: MeasuredOutputs;
  source_type: SourceType;
  doi: Doi;
  evidence: Evidence;
  review_status: ReviewStatus;
  created_at: CreatedAt;
  supersedes: Supersedes;
  notes: Notes;
}
export interface Sequences2 {
  [k: string]: string;
}
export interface LinkerSequences {
  [k: string]: string;
}
export interface ExperimentalConditions {
  [k: string]: string | number;
}
export interface MeasuredOutputs {
  [k: string]: number | string;
}
export interface DesignConfig {
  id: Id10;
  protein_construct_ids: ProteinConstructIds;
  required_enzyme_ids: RequiredEnzymeIds;
  host: Host2;
  promoters: Promoters;
  integration_sites: IntegrationSites;
  condition_id: ConditionId;
}
export interface Promoters {
  [k: string]: string;
}
export interface IntegrationSites {
  [k: string]: string;
}
export interface ParameterRecord {
  parameter_id: ParameterId;
  name: Name3;
  value: Value;
  unit: Unit;
  species_id: SpeciesId;
  enzyme_id: EnzymeId;
  substrate_id: SubstrateId;
  product_id: ProductId;
  construct_id: ConstructId1;
  condition_id: ConditionId1;
  parameter_type: ParameterType;
  source_type: SourceType1;
  derivation_type: DerivationType;
  source_reference: SourceReference1;
  doi: Doi1;
  evidence_text: EvidenceText;
  evidence_location: EvidenceLocation;
  conditions: Conditions1;
  uncertainty: ParameterUncertainty | null;
  review_status: ReviewStatus1;
  approved_by: ApprovedBy;
  validation_flags: ValidationFlags;
  created_at: CreatedAt1;
  updated_at: UpdatedAt;
  model_version: ModelVersion;
  parameter_version: ParameterVersion;
  supersedes: Supersedes1;
  derived_from: DerivedFrom;
  notes: Notes1;
}
export interface Conditions1 {
  [k: string]: string | number;
}
export interface ParameterUncertainty {
  value: Value1;
  lower: Lower;
  upper: Upper;
  type: Type;
}
export interface StagesConfig {
  m1_llps: M1Config;
  m2_fusion: M2Config;
  m3_concentration: M3Config;
  m4_reaction: M4Config;
  m5_feedback: M5Config;
}
export interface M1Config {
  top_n: TopN;
  forbidden_motifs: ForbiddenMotifs;
  feature_definitions_file: FeatureDefinitionsFile;
  rules_file: RulesFile;
  predictor_evidence_file: PredictorEvidenceFile;
  require_external_evidence_in_real_mode: RequireExternalEvidenceInRealMode;
}
export interface M2Config {
  structure_metrics_file: StructureMetricsFile;
}
export interface M3Config {
  phi_source: PhiSource;
  target_enzyme_ratio_parameter: TargetEnzymeRatioParameter;
  design_decision_id: DesignDecisionId;
  binding_model: BindingModel;
  hill_coefficient: HillCoefficient;
  recruitment: Recruitment;
  recruitment_mode: RecruitmentMode;
  slot_ratio_sh3_to_pdz: SlotRatioSh3ToPdz;
  total_recruited_fraction: TotalRecruitedFraction;
  recruitment_bias_oc_vs_dmt: RecruitmentBiasOcVsDmt;
  ptr_pt_phase_handling: PtrPtPhaseHandling;
  author_native_inputs: AuthorNativeEnzymeScales | null;
}
export interface RecruitmentConfig {
  enzyme_id: EnzymeId1;
  enzyme_total_parameter: EnzymeTotalParameter;
  site_total_parameter: SiteTotalParameter;
  kd_parameter: KdParameter;
  hill_coefficient_parameter: HillCoefficientParameter;
}
/**
 * Explicit nonphysical author-model enzyme scales for sensitivity runs.
 */
export interface AuthorNativeEnzymeScales {
  ptr_scale: PtrScale;
  pt_scale: PtScale;
  oc_scale: OcScale;
  dmt_scale: DmtScale;
  source: Source1;
  interpretation: Interpretation;
}
export interface M4Config {
  analysis: M4AnalysisConfig | null;
  assay_mode: AssayMode;
  measurement_compartment: MeasurementCompartment;
  expression_mode: ExpressionMode;
  feeding_time_h: FeedingTimeH;
  confirmed_absent_enzymes: ConfirmedAbsentEnzymes;
  network_variant: NetworkVariant;
  absence_evidence: AbsenceEvidenceBinding | null;
  steady_state_observation_reference: SteadyStateObservationReference;
  target_product: TargetProduct;
  feed_compound_id: FeedCompoundId;
  feed_mode: FeedMode;
  t_end: TEnd;
  initial_state: InitialStateConfig | null;
  full_network_initial_state: FullNetworkInitialStateConfig | null;
  reaction_network_file: ReactionNetworkFile;
  steady_state_initial_guess_um: SteadyStateInitialGuessUm;
  pt_gate: InductionGateConfig | null;
  oc_gate: InductionGateConfig | null;
  dmt_gate: InductionGateConfig | null;
  condition_id: ConditionId2;
  max_side_product_fraction_13: MaxSideProductFraction13;
  min_13_reduction: Min13Reduction;
  min_15_improvement: Min15Improvement;
  min_productivity: MinProductivity;
  enable_degradation: EnableDegradation;
  network_mode: NetworkMode;
  scenario_mode: ScenarioMode;
  unit_mode: UnitMode;
  author_native_time_label: AuthorNativeTimeLabel;
  activity_mode: ActivityMode;
  transport_access: TransportAccess;
  transport_enabled: TransportEnabled;
  transport_rate_parameter: TransportRateParameter;
  intracellular_volume_l: IntracellularVolumeL;
  extracellular_volume_l: ExtracellularVolumeL;
  volume_source_reference: VolumeSourceReference;
  transport_ratio_source_reference: TransportRatioSourceReference;
  transport_evidence: TransportEvidenceBinding | null;
  solver_points: SolverPoints;
  transport_outside_over_inside: TransportOutsideOverInside;
}
export interface M4AnalysisConfig {
  local_parameter_names: LocalParameterNames;
  ranges: Ranges;
  samples: Samples;
  random_seed: RandomSeed;
  standard_deviation_ddof: StandardDeviationDdof;
  independence_evidence_reference: IndependenceEvidenceReference;
  idr_mapping: IDRMappingEvidence | null;
}
export interface RangeEvidence {
  parameter_name: ParameterName;
  distribution: Distribution;
  interpolation_reference: InterpolationReference;
  lower: Lower1;
  upper: Upper1;
  empirical_values: EmpiricalValues;
  source_reference: SourceReference2;
  parameter_ids: ParameterIds;
  reviewed_by: ReviewedBy;
}
export interface IDRMappingEvidence {
  a: A;
  b: B;
  c: C;
  const: Const;
  logp: Logp;
  aromatic_counts: AromaticCounts;
  theta_hydro: ThetaHydro;
  theta_aro: ThetaAro;
  source_reference: SourceReference3;
  applicable_domain_reference: ApplicableDomainReference;
  reviewed_by: ReviewedBy1;
}
export interface Logp {
  [k: string]: number;
}
export interface AromaticCounts {
  [k: string]: number;
}
export interface ConfirmedAbsentEnzymes {
  [k: string]: string;
}
export interface AbsenceEvidenceBinding {
  artifact: Artifact;
  sha256: Sha2561;
  reviewed_by: ReviewedBy2;
}
export interface InitialStateConfig {
  concentration_unit: ConcentrationUnit;
  x9: X9;
  x10: X10;
  x11: X11;
  x13: X13;
  x15: X15;
}
/**
 * Explicit 8--15 state for the audited full Galatea network.
 */
export interface FullNetworkInitialStateConfig {
  concentration_unit: ConcentrationUnit1;
  intracellular: Intracellular;
  parameter_ids: ParameterIds1;
  extracellular: Extracellular;
}
export interface Intracellular {
  [k: string]: number;
}
export interface ParameterIds1 {
  [k: string]: string;
}
export interface Extracellular {
  [k: string]: number;
}
export interface InductionGateConfig {
  on_time: OnTime;
  off_time: OffTime;
  basal: Basal;
  induced: Induced;
  mode: Mode1;
  transition_width: TransitionWidth;
  time_unit: TimeUnit;
}
export interface TransportEvidenceBinding {
  formula_version: FormulaVersion;
  rate_parameter_id: RateParameterId;
  intracellular_volume_parameter_id: IntracellularVolumeParameterId;
  extracellular_volume_parameter_id: ExtracellularVolumeParameterId;
  outside_over_inside_parameter_ids: OutsideOverInsideParameterIds;
}
export interface OutsideOverInsideParameterIds {
  [k: string]: string;
}
export interface TransportOutsideOverInside {
  [k: string]: number;
}
export interface M5Config {
  wetlab_results_file: WetlabResultsFile;
  absolute_residual_tolerance: AbsoluteResidualTolerance;
  relative_residual_tolerance: RelativeResidualTolerance;
  discrepancy_threshold_configured: DiscrepancyThresholdConfigured;
  fit_plan: FitPlanConfig | null;
}
export interface FitPlanConfig {
  parameter_name: ParameterName1;
  fixed_parameter_names: FixedParameterNames;
  bounds: Bounds;
  observables: Observables;
}
export interface PublicRunInput {
  id: Id11;
}
export interface SequenceIndexView {
  status: Status;
  file_id: FileId1;
  source_sha256: SourceSha256;
  count: Count;
  reason_code: ReasonCode;
}
