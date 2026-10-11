/* Generated from public Pydantic contracts. Do not edit. */

export type SchemaVersion = "display-series-v1";
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
export type ResultSchemaVersion = string;
export type ModelKind = string;
export type FormulaVersion = string;
export type TimeUnit = string;
export type DataSourceSha256 = string | null;
export type SourceReference = string | null;
export type Offset = number;
export type Total = number;
export type HasMore = boolean;
export type DisplayPolicy = "exact_contiguous_page_no_decimation";
export type Time = number[];
export type Id = string;
export type Compartment = string;
export type Species = string;
export type Unit = string;
export type SpeciesId = string | null;
export type Quantity = string | null;
export type Series = SeriesDescriptor[];
export type ClaimScope = string | null;
export type SourceType = string | null;
export type FormalPredictionAllowed = boolean | null;

export interface SeriesPage {
  schema_version: SchemaVersion;
  identity: ResourceIdentity;
  result_schema_version: ResultSchemaVersion;
  model_kind: ModelKind;
  formula_version: FormulaVersion;
  time_unit: TimeUnit;
  data_source_sha256: DataSourceSha256;
  source_reference: SourceReference;
  offset: Offset;
  total: Total;
  has_more: HasMore;
  display_policy: DisplayPolicy;
  time: Time;
  series: Series;
  values: Values;
  claim_scope: ClaimScope;
  source_type: SourceType;
  formal_prediction_allowed: FormalPredictionAllowed;
  pool_volumes: PoolVolumes;
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
export interface SeriesDescriptor {
  id: Id;
  compartment: Compartment;
  species: Species;
  unit: Unit;
  species_id: SpeciesId;
  quantity: Quantity;
}
export interface Values {
  [k: string]: (number | null)[];
}
export interface PoolVolumes {
  [k: string]: {
    [k: string]: unknown;
  };
}
