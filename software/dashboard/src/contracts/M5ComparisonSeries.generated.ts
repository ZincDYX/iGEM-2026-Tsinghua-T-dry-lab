/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "m5-comparison-series-v1";
export type ExperimentId = string;
export type ConstructId = string;
export type ConditionId = string;
export type ReplicateId = string;
export type RawDataSha256 = string | null;
export type Compartment = string | null;
export type ConcentrationBasis = string | null;
export type TimeUnit = "h";
export type ConcentrationUnit = "uM";
export type SourceTimeUnit = string;
export type SourceConcentrationUnit = string;
export type ComparisonAdapter = "prediction_contract" | "legacy_trajectory";
export type Time = number[];
export type Observed = number[];
export type Predicted = number[];
export type ResidualObservedMinusPredicted = (number | null)[];
export type CensorMask = string[];
export type Lod = number | null;
export type Loq = number | null;
export type ObservationKind = string;
export type Uncertainty = number[] | null;
export type UncertaintyType = string | null;
export type ParameterApproval = "not_granted_by_display";

/**
 * Persist the values already aligned by the existing comparison, not a replay.
 */
export interface M5ComparisonSeries {
  schema_version: SchemaVersion;
  experiment_id: ExperimentId;
  construct_id: ConstructId;
  condition_id: ConditionId;
  replicate_id: ReplicateId;
  raw_data_sha256: RawDataSha256;
  compartment: Compartment;
  concentration_basis: ConcentrationBasis;
  time_unit: TimeUnit;
  concentration_unit: ConcentrationUnit;
  source_time_unit: SourceTimeUnit;
  source_concentration_unit: SourceConcentrationUnit;
  comparison_adapter: ComparisonAdapter;
  time: Time;
  observed: Observed;
  predicted: Predicted;
  residual_observed_minus_predicted: ResidualObservedMinusPredicted;
  censor_mask: CensorMask;
  lod: Lod;
  loq: Loq;
  observation_kind: ObservationKind;
  uncertainty: Uncertainty;
  uncertainty_type: UncertaintyType;
  parameter_approval: ParameterApproval;
}
