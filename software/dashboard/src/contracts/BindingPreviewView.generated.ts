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
export type PreparedThrough = "m1" | "m2" | "m3" | "m4" | "m5";
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
export type EvidenceId = string;
export type ConstructId = string;
export type ConstructVersion = string;
export type ConditionId = string;
export type InputSequenceSha256 = string;
export type Start = number;
export type End = number;
export type AnchorSourceRecord = string;
export type Tool = "DeepTMHMM";
export type ToolVersion = string;
export type NativeRecordId = string;
export type Path1 = string;
export type Sha2561 = string;
export type BodySide = "cytosolic" | "luminal" | "unknown";
export type OrientationSource = string | null;
export type CleavageState = "not_cleaved" | "cleaved" | "unknown";
export type BodyRemovedByCleavage = boolean | null;
export type CleavageSource = string | null;
export type EvidenceLevel = "predicted" | "experimentally_supported";
/**
 * @minItems 1
 */
export type RawReferences = [ArtifactReference, ...ArtifactReference[]];
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
export type ConstructId1 = string;
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
export type ConditionId1 = string | null;
export type Designs = DesignConfig[];
export type ParameterId = string;
export type Name3 = string;
export type Value = number | string;
export type Unit = string | null;
export type SpeciesId = string | null;
export type EnzymeId = string | null;
export type SubstrateId = string | null;
export type ProductId = string | null;
export type ConstructId2 = string | null;
export type ConditionId2 = string | null;
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
export type PolicyVersion = string;
export type SourceReference2 = string;
export type Reviewer = string;
export type RuleId = string;
export type Feature = string;
export type Transform = "identity" | "absolute";
export type Operator = "lt" | "le" | "gt" | "ge" | "inside" | "outside";
export type Lower1 = number;
export type Upper1 = number | null;
export type Tool1 = "FuzDrop" | "catGRANULE_2016" | "PSPredictor" | "PScore" | "Mpipi_original";
export type NormalizationMinimum = number;
export type NormalizationMaximum = number;
export type HighDirection = "greater_equal" | "less_equal";
export type NormalizedHighCutoff = number;
export type Weight = number;
export type PredictorRules = PredictorRule[];
export type SortKeys = ("risk" | "consensus" | "rank_score")[];
export type RankingFormulaReference = string | null;
export type FormulaVersion = "m2-er-membrane-v1-2026-10-10";
export type ConstructId3 = string;
export type ConditionId3 = string;
export type AssemblyApplicabilitySource = string;
export type AnchorCountBasis = "explicit_subunit_composition";
/**
 * @minItems 1
 */
export type Conformers = [MembraneConformer, ...MembraneConformer[]];
export type ModelId = string;
export type ConformerId = string;
export type Path2 = string;
export type ModelId1 = number | null;
export type Altloc = string | null;
export type SourceKind = "experimental" | "prediction";
export type SourceReference3 = string;
export type ConfidenceFile = string | null;
export type ExpectedSequence = string | null;
export type FrameId = string;
/**
 * @minItems 3
 * @maxItems 3
 */
export type OriginAngstrom = [unknown, unknown, unknown];
/**
 * @minItems 3
 * @maxItems 3
 */
export type UnitNormal = [unknown, unknown, unknown];
export type ThicknessAngstrom = number;
export type PositiveSide = "cytosolic" | "luminal";
export type BodySide1 = "cytosolic" | "luminal" | "unknown";
export type SourceReference4 = string;
/**
 * @minItems 1
 */
export type Tethers = [TetherGeometry, ...TetherGeometry[]];
export type SubunitId = string;
export type Chain = string;
/**
 * @minItems 1
 */
export type Residues = [number | string, ...(number | string)[]];
export type ContourLengthAngstrom = number;
export type ContourLengthSource = string;
export type SamplingMethod = string;
export type SamplingScope = string;
export type CoordinateTransformReference = string;
export type HeavyAtomClashCutoffAngstrom = number;
export type ClashRuleSource = string;
export type StructureMetricsFile = string | null;
export type RegionAssessmentsFile = string | null;
export type CalculationRequestsFile = string | null;
export type FormulaVersion1 = "m3-er-amount-independent-set-v1-2026-10-10";
export type ConstructId4 = string;
export type ConditionId4 = string;
export type TopologyEvidenceRef = string;
export type BodySide2 = "cytosolic" | "luminal" | "unknown";
export type GeometryRef = string;
export type Value2 = number;
export type Unit1 = "uM" | "umol" | "L" | "um2" | "copies/um2" | "1" | "L/h" | "1/h" | "umol/h";
export type EntityBasis = string;
export type ParameterId1 = string;
export type SourceReference5 = string;
export type DensityEntityBasis = "scaffold_monomer" | "complete_assembly" | "effective_anchor";
export type SubunitsPerAssembly = number;
export type AnchorsPerAssembly = number;
export type CompositionSource = string;
export type UnanchoredScaffoldBinding = "included_in_droplet" | "excluded_with_evidence";
export type UnanchoredScaffoldApplicabilitySource = string;
export type SiteId = string;
export type Species = "OC" | "DMT";
export type GeometryRef1 = string;
export type BindingPairRef = string;
export type Sites = BindingSite[];
export type ConflictEdges = [unknown, unknown][];
export type EntityBasis1 = "complete_assembly";
export type GeometryRef2 = string;
export type MethodAssumption = "hard_exclusion_no_additional_cooperativity";
export type ApplicabilityReference = string;
export type MaxPartitionStates = number;
export type SolverMaxEvaluations = number;
export type RelativeMassTolerance = number;
export type Method = "statistical_factor" | "alpha" | "free_energy";
export type ParameterName = string;
/**
 * @minItems 1
 */
export type Ranges = [RangeEvidence, ...RangeEvidence[]];
export type ParameterName1 = string;
export type Distribution = "uniform" | "empirical" | "interpolated_empirical";
export type InterpolationReference = string | null;
export type Lower2 = number | null;
export type Upper2 = number | null;
export type EmpiricalValues = number[];
export type SourceReference6 = string;
/**
 * @minItems 1
 */
export type ParameterIds = [string, ...string[]];
export type ReviewedBy = string;
export type Samples = number;
export type Seed = number;
export type IndependenceReference = string;
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
export type FormulaVersion2 = "m4-compartment-amount-v1-2026-10-10";
export type ConstructId5 = string;
export type ConditionId5 = string;
export type Scenario = "no_LLPS" | "cytosolic_LLPS" | "ER_anchored_LLPS";
export type TopologyEvidenceRef1 = string | null;
export type ReactionLocationReference = string;
/**
 * @minItems 1
 */
export type Pools = [ReactionPool, ...ReactionPool[]];
export type PoolId = string;
export type Role2 = "cytosol" | "anchored_droplet" | "er_lumen" | "extracellular";
export type GeometryRef3 = string;
export type InterfaceId = string;
export type FirstPool = string;
export type SecondPool = string;
export type Mode1 = "finite_exchange" | "rapid_equilibrium";
export type Conductance = {
  [k: string]: ScientificQuantity;
} | null;
export type ApplicabilityReference1 = string;
export type TimescaleEvidenceReference = string | null;
export type Interfaces = ExchangeInterface[];
export type ReactionId = string;
export type Enzyme = "PTR" | "PT" | "OC" | "DMT";
export type Substrate = string;
export type Product = string;
export type KcatPerH = number;
export type KmUm = number;
/**
 * @minItems 2
 */
export type ParameterIds1 = [string, string, ...string[]];
export type Reactions = M4ReactionInput[];
export type BoundaryId = string;
export type PoolId1 = string;
export type Compound = "8" | "9" | "10" | "11" | "12" | "13" | "14" | "15";
export type Kind1 = "constant_feed" | "first_order_loss";
export type Normalization = "physical_amount";
export type Boundaries = AmountBoundary[];
/**
 * @minItems 2
 */
export type TimeGridH = [number, number, ...number[]];
export type SteadyInitialGuessesUmol = {
  [k: string]: {
    [k: string]: number;
  };
}[];
export type Method1 = "BDF" | "Radau" | "LSODA";
export type RelativeTolerance = number;
export type AmountAbsoluteToleranceUmol = number;
export type SteadyRelativeTolerance = number;
export type SteadyAbsoluteToleranceUmolPerH = number;
export type EigenvalueTolerancePerH = number;
export type SteadyMaxEvaluations = number;
export type EvidenceMode = "conditional_model" | "reviewed_project_binding";
export type ConstructId6 = string;
export type ConditionId6 = string;
export type SourceReference7 = string;
export type ReviewedBy1 = string;
/**
 * @minItems 1
 */
export type Columns = [JointSampleColumn, ...JointSampleColumn[]];
export type Column = string;
export type Stage = "m3" | "m4";
export type ParameterName2 = string;
export type ParameterId2 = string;
export type Unit2 = "1" | "uM" | "1/h";
export type SampleBasis = "paired_observations" | "supplied_joint_model_draws";
export type SamplingMethodReference = string;
export type LocalParameterNames = string[];
export type Ranges1 = RangeEvidence[];
export type Samples1 = number;
export type RandomSeed = number;
export type StandardDeviationDdof = (0 | 1) | null;
export type IndependenceEvidenceReference = string | null;
export type A = number;
export type B = number;
export type C = number;
export type Const = number;
export type ThetaHydro = number;
export type ThetaAro = number;
export type SourceReference8 = string;
export type ApplicableDomainReference = string;
export type ReviewedBy2 = string;
export type AssayMode = ("substrate_feeding_functional" | "full_pathway_production") | null;
export type MeasurementCompartment = ("intracellular" | "extracellular" | "total_extract") | null;
export type ExpressionMode = ("constitutive" | "induced") | null;
export type FeedingTimeH = number | null;
export type NetworkVariant = "full_ten" | "oc_dmt_verified_absence";
export type Artifact = string;
export type Sha2562 = string;
export type ReviewedBy3 = string;
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
export type Mode2 = "step" | "sigmoid";
export type TransitionWidth = number;
export type TimeUnit = "h" | "author_native_day_axis";
export type ConditionId7 = string | null;
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
export type FormulaVersion3 = string;
export type RateParameterId = string;
export type IntracellularVolumeParameterId = string;
export type ExtracellularVolumeParameterId = string;
export type SolverPoints = number;
export type WetlabResultsFile = string | null;
export type AbsoluteResidualTolerance = number;
export type RelativeResidualTolerance = number;
export type DiscrepancyThresholdConfigured = boolean;
export type ParameterName3 = string;
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
  prepared_through: PreparedThrough;
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
  sequence_roles: SequenceRoles;
  ligands: Ligands;
  enzymes: Enzymes;
  scaffolds: Scaffolds;
  linkers: Linkers;
  idr_id: IdrId;
  constructs: Constructs;
  construct_records: ConstructRecords;
  designs: Designs;
}
export interface SequenceRoles {
  [k: string]:
    "full_fusion" | "idr" | "enzyme" | "enzyme_ligand_linker" | "scaffold_linker" | "rigid_linker" | "protein";
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
  membrane_topology: MembraneTopologyEvidence | null;
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
export interface MembraneTopologyEvidence {
  evidence_id: EvidenceId;
  construct_id: ConstructId;
  construct_version: ConstructVersion;
  condition_id: ConditionId;
  input_sequence_sha256: InputSequenceSha256;
  anchor: ResidueRange;
  anchor_source_record: AnchorSourceRecord;
  tool: Tool;
  tool_version: ToolVersion;
  native_record_id: NativeRecordId;
  native_output: ArtifactReference;
  body_side: BodySide;
  orientation_source: OrientationSource;
  cleavage_state: CleavageState;
  body_removed_by_cleavage: BodyRemovedByCleavage;
  cleavage_source: CleavageSource;
  evidence_level: EvidenceLevel;
  raw_references: RawReferences;
  review_parameter_ids: ReviewParameterIds;
}
export interface ResidueRange {
  start: Start;
  end: End;
}
export interface ArtifactReference {
  path: Path1;
  sha256: Sha2561;
}
export interface ReviewParameterIds {
  [k: string]: string;
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
  construct_id: ConstructId1;
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
  condition_id: ConditionId1;
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
  construct_id: ConstructId2;
  condition_id: ConditionId2;
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
  prioritization_policy: PrioritizationPolicy | null;
}
export interface PrioritizationPolicy {
  policy_version: PolicyVersion;
  source_reference: SourceReference2;
  reviewer: Reviewer;
  risk_rules: RiskRules;
  predictor_rules: PredictorRules;
  sort_keys: SortKeys;
  ranking_formula_reference: RankingFormulaReference;
}
export interface RiskRules {
  [k: string]: RiskPredicate[];
}
export interface RiskPredicate {
  rule_id: RuleId;
  feature: Feature;
  transform: Transform;
  operator: Operator;
  lower: Lower1;
  upper: Upper1;
}
export interface PredictorRule {
  tool: Tool1;
  normalization_minimum: NormalizationMinimum;
  normalization_maximum: NormalizationMaximum;
  high_direction: HighDirection;
  normalized_high_cutoff: NormalizedHighCutoff;
  weight: Weight;
}
export interface M2Config {
  membrane_requests: MembraneRequests;
  structure_metrics_file: StructureMetricsFile;
  region_assessments_file: RegionAssessmentsFile;
  calculation_requests_file: CalculationRequestsFile;
}
export interface MembraneRequests {
  [k: string]: MembraneGeometryInput;
}
/**
 * ER M2 membrane ensemble with explicit geometry and subunit composition.
 */
export interface MembraneGeometryInput {
  formula_version: FormulaVersion;
  construct_id: ConstructId3;
  condition_id: ConditionId3;
  topology: MembraneTopologyEvidence;
  subunit_composition: SubunitComposition;
  assembly_applicability_source: AssemblyApplicabilitySource;
  anchor_count_basis: AnchorCountBasis;
  conformers: Conformers;
  heavy_atom_clash_cutoff_angstrom: HeavyAtomClashCutoffAngstrom;
  clash_rule_source: ClashRuleSource;
}
export interface SubunitComposition {
  [k: string]: boolean;
}
export interface MembraneConformer {
  model_id: ModelId;
  conformer_id: ConformerId;
  structure: StructureInput;
  frame: MembraneFrame;
  tethers: Tethers;
  scaffold: ResidueSelection;
  domains: Domains;
  pockets: Pockets;
  recruited_enzymes: RecruitedEnzymes;
  sampling_method: SamplingMethod;
  sampling_scope: SamplingScope;
  coordinate_transform_reference: CoordinateTransformReference;
}
export interface StructureInput {
  path: Path2;
  model_id: ModelId1;
  altloc: Altloc;
  source_kind: SourceKind;
  source_reference: SourceReference3;
  confidence_file: ConfidenceFile;
  expected_sequence: ExpectedSequence;
}
export interface MembraneFrame {
  frame_id: FrameId;
  origin_angstrom: OriginAngstrom;
  unit_normal: UnitNormal;
  thickness_angstrom: ThicknessAngstrom;
  positive_side: PositiveSide;
  body_side: BodySide1;
  source_reference: SourceReference4;
  raw_reference: ArtifactReference;
  atom_radii_angstrom: AtomRadiiAngstrom;
}
export interface AtomRadiiAngstrom {
  [k: string]: number;
}
export interface TetherGeometry {
  subunit_id: SubunitId;
  anchor: ResidueSelection;
  linker: ResidueSelection;
  attached_body: ResidueSelection;
  contour_length_angstrom: ContourLengthAngstrom;
  contour_length_source: ContourLengthSource;
}
export interface ResidueSelection {
  chain: Chain;
  residues: Residues;
}
export interface Domains {
  [k: string]: ResidueSelection;
}
export interface Pockets {
  [k: string]: ResidueSelection;
}
export interface RecruitedEnzymes {
  [k: string]: ResidueSelection;
}
export interface M3Config {
  er_requests: ErRequests;
  avidity_sh3: AvidityBinding | null;
  avidity_pdz: AvidityBinding | null;
  uncertainty: M3UncertaintySettings | null;
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
export interface ErRequests {
  [k: string]: ERRecruitmentInput;
}
/**
 * Proposed ER M3 method with explicit physical amounts and geometry.
 */
export interface ERRecruitmentInput {
  formula_version: FormulaVersion1;
  construct_id: ConstructId4;
  condition_id: ConditionId4;
  topology_evidence_ref: TopologyEvidenceRef;
  body_side: BodySide2;
  geometry_ref: GeometryRef;
  cytosol_volume: ScientificQuantity;
  droplet_volume: ScientificQuantity;
  er_area: ScientificQuantity;
  scaffold_surface_density: ScientificQuantity;
  density_entity_basis: DensityEntityBasis;
  subunits_per_assembly: SubunitsPerAssembly;
  anchors_per_assembly: AnchorsPerAssembly;
  composition_source: CompositionSource;
  total_scaffold_monomer_amount: ScientificQuantity;
  unanchored_scaffold_binding: UnanchoredScaffoldBinding;
  unanchored_scaffold_applicability_source: UnanchoredScaffoldApplicabilitySource;
  enzyme_total_amounts: EnzymeTotalAmounts;
  free_enzyme_partition: FreeEnzymePartition;
  binding_graph: BindingGraph;
  max_partition_states: MaxPartitionStates;
  solver_max_evaluations: SolverMaxEvaluations;
  relative_mass_tolerance: RelativeMassTolerance;
}
/**
 * Canonical value with a registry binding; numerical controls are separate.
 */
export interface ScientificQuantity {
  value: Value2;
  unit: Unit1;
  entity_basis: EntityBasis;
  parameter_id: ParameterId1;
  source_reference: SourceReference5;
}
export interface EnzymeTotalAmounts {
  [k: string]: ScientificQuantity;
}
export interface FreeEnzymePartition {
  [k: string]: ScientificQuantity;
}
export interface BindingGraph {
  sites: Sites;
  conflict_edges: ConflictEdges;
  entity_basis: EntityBasis1;
  geometry_ref: GeometryRef2;
  method_assumption: MethodAssumption;
  applicability_reference: ApplicabilityReference;
}
export interface BindingSite {
  site_id: SiteId;
  species: Species;
  kd: ScientificQuantity;
  geometry_ref: GeometryRef1;
  binding_pair_ref: BindingPairRef;
}
export interface AvidityBinding {
  method: Method;
  parameter_name: ParameterName;
}
export interface M3UncertaintySettings {
  ranges: Ranges;
  samples: Samples;
  seed: Seed;
  independence_reference: IndependenceReference;
}
export interface RangeEvidence {
  parameter_name: ParameterName1;
  distribution: Distribution;
  interpolation_reference: InterpolationReference;
  lower: Lower2;
  upper: Upper2;
  empirical_values: EmpiricalValues;
  source_reference: SourceReference6;
  parameter_ids: ParameterIds;
  reviewed_by: ReviewedBy;
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
  compartment_requests: CompartmentRequests;
  joint_samples: JointSamples;
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
  condition_id: ConditionId7;
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
export interface CompartmentRequests {
  [k: string]: CompartmentNetworkInput;
}
/**
 * ER M4 amount-state network; original cytosolic secretion is unchanged.
 */
export interface CompartmentNetworkInput {
  formula_version: FormulaVersion2;
  construct_id: ConstructId5;
  condition_id: ConditionId5;
  scenario: Scenario;
  topology_evidence_ref: TopologyEvidenceRef1;
  reaction_location_reference: ReactionLocationReference;
  pools: Pools;
  interfaces: Interfaces;
  reactions: Reactions;
  reaction_locations: ReactionLocations;
  boundaries: Boundaries;
  initial_amounts_umol: InitialAmountsUmol;
  time_grid_h: TimeGridH;
  steady_initial_guesses_umol: SteadyInitialGuessesUmol;
  numerics: CompartmentNumerics;
  evidence_mode: EvidenceMode;
}
export interface ReactionPool {
  pool_id: PoolId;
  role: Role2;
  volume: ScientificQuantity;
  geometry_ref: GeometryRef3;
  enzyme_amounts: EnzymeAmounts;
  enzyme_activity_ratios: EnzymeActivityRatios;
}
export interface EnzymeAmounts {
  [k: string]: ScientificQuantity;
}
export interface EnzymeActivityRatios {
  [k: string]: ScientificQuantity;
}
export interface ExchangeInterface {
  interface_id: InterfaceId;
  first_pool: FirstPool;
  second_pool: SecondPool;
  mode: Mode1;
  second_over_first_partition: SecondOverFirstPartition;
  conductance: Conductance;
  applicability_reference: ApplicabilityReference1;
  timescale_evidence_reference: TimescaleEvidenceReference;
}
export interface SecondOverFirstPartition {
  [k: string]: ScientificQuantity;
}
export interface M4ReactionInput {
  reaction_id: ReactionId;
  enzyme: Enzyme;
  substrate: Substrate;
  product: Product;
  kcat_per_h: KcatPerH;
  km_um: KmUm;
  parameter_ids: ParameterIds1;
}
export interface ReactionLocations {
  [k: string]: string[];
}
export interface AmountBoundary {
  boundary_id: BoundaryId;
  pool_id: PoolId1;
  compound: Compound;
  kind: Kind1;
  quantity: ScientificQuantity;
  normalization: Normalization;
}
export interface InitialAmountsUmol {
  [k: string]: {
    [k: string]: ScientificQuantity;
  };
}
export interface CompartmentNumerics {
  method: Method1;
  relative_tolerance: RelativeTolerance;
  amount_absolute_tolerance_umol: AmountAbsoluteToleranceUmol;
  steady_relative_tolerance: SteadyRelativeTolerance;
  steady_absolute_tolerance_umol_per_h: SteadyAbsoluteToleranceUmolPerH;
  eigenvalue_tolerance_per_h: EigenvalueTolerancePerH;
  steady_max_evaluations: SteadyMaxEvaluations;
}
export interface JointSamples {
  [k: string]: M3M4JointSamples;
}
export interface M3M4JointSamples {
  construct_id: ConstructId6;
  condition_id: ConditionId6;
  source: ArtifactReference;
  source_reference: SourceReference7;
  reviewed_by: ReviewedBy1;
  columns: Columns;
  sample_basis: SampleBasis;
  sampling_method_reference: SamplingMethodReference;
}
export interface JointSampleColumn {
  column: Column;
  stage: Stage;
  parameter_name: ParameterName2;
  parameter_id: ParameterId2;
  unit: Unit2;
}
export interface M4AnalysisConfig {
  local_parameter_names: LocalParameterNames;
  ranges: Ranges1;
  samples: Samples1;
  random_seed: RandomSeed;
  standard_deviation_ddof: StandardDeviationDdof;
  independence_evidence_reference: IndependenceEvidenceReference;
  idr_mapping: IDRMappingEvidence | null;
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
  source_reference: SourceReference8;
  applicable_domain_reference: ApplicableDomainReference;
  reviewed_by: ReviewedBy2;
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
  sha256: Sha2562;
  reviewed_by: ReviewedBy3;
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
  parameter_ids: ParameterIds2;
  extracellular: Extracellular;
}
export interface Intracellular {
  [k: string]: number;
}
export interface ParameterIds2 {
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
  mode: Mode2;
  transition_width: TransitionWidth;
  time_unit: TimeUnit;
}
export interface TransportEvidenceBinding {
  formula_version: FormulaVersion3;
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
  parameter_name: ParameterName3;
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
