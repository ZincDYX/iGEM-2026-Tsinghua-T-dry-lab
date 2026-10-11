import { object } from "./validation";

export function numbers(value: unknown): value is Record<string, number> {
  return (
    object(value) &&
    Object.keys(value).length > 0 &&
    Object.values(value).every(
      (v) => typeof v === "number" && Number.isFinite(v),
    )
  );
}
export function show(value: unknown): string {
  if (value === undefined) return "Not recorded";
  if (value === null) return "Not computed";
  if (typeof value === 'number') return Number.isFinite(value)
    ? new Intl.NumberFormat('en', {maximumSignificantDigits: 3}).format(value) : 'Invalid number';
  if (Array.isArray(value)) return [...new Set(value.map(show))].join('; ') || 'None';
  if (object(value)) return typeof value.status === 'string'
    ? value.status.replaceAll('_', ' ') : 'Details available';
  return String(value);
}

export interface M1Check {
  schema_version: 'm1-method-check-v1'; candidate_id: string; verdict: string;
  precheck?: Record<string, unknown>; screen?: Record<string, unknown>; missing?: unknown[];
}
export function m1Checks(output: unknown): M1Check[] | null {
  const values = object(output) && Array.isArray(output.items) ? output.items : [output];
  if (!values.length || !values.every(value => object(value) && value.schema_version === 'm1-method-check-v1'
    && typeof value.candidate_id === 'string' && typeof value.verdict === 'string')) return null;
  return values as M1Check[];
}
export function adaptSteadyResult(tool: string | undefined, output: unknown) {
  const m4 = tool === "igem.m4.solve_steady_state";
  const data =
    m4 && object(output) && output.ok === true ? output.result : output;
  if (!object(data)) return null;
  if (
    m4
      ? data.schema_version !== "m4-steady-state-v1" ||
        data.model_kind !== "markdown_steady_state" ||
        ![
          "m4-step0-step8-2026-09-27",
          "m4-step0-step8-phase-activity-v2-2026-10-04",
        ].includes(String(data.formula_version))
      : tool !== "pathway.steady_state" ||
        data.schema_version !== "pathway-steady-state-v1" ||
        data.model_kind !== "generic_two_phase_steady_state" ||
        data.rate_law !== "two_phase_competitive_mm_v1"
  )
    return null;
  if (
    ![
      "valid",
      "blocked",
      "solver_failed",
      "insufficient_data",
      "capacity_conflict",
    ].includes(String(data.status))
  )
    return null;
  if (data.status !== "valid")
    return {
      data,
      title: m4 ? "M4 Original-formula steady state" : "Pathway steady state",
      maps: null,
    };
  const keys = [
    m4 ? "concentrations_cell_average_um" : "concentrations_average_um",
    "concentrations_dense_um",
    "concentrations_dilute_um",
    "secretion_flux_um_per_h",
    m4 ? "steady_state_residual_um_per_h" : "residual_um_per_h",
    "reaction_flux_um_per_h",
  ];
  const maps = keys.map((key) => data[key]);
  if (!maps.every(numbers)) return null;
  const species = Object.keys(maps[0]);
  if (
    !maps
      .slice(1, 5)
      .every(
        (map) =>
          Object.keys(map).length === species.length &&
          species.every((s) => s in map),
      )
  )
    return null;
  return {
    data,
    title: m4 ? "M4 Original-formula steady state" : "Pathway steady state",
    maps,
  };
}
export function sequenceOutput(value: unknown) {
  if (
    !object(value) ||
    typeof value.id !== "string" ||
    !object(value.features) ||
    typeof value.features.sequence_sha256 !== "string" ||
    typeof value.features.length !== "number" ||
    !object(value.protparam)
  )
    return null;
  const properties = value.protparam;
  return ["molecular_weight_da", "theoretical_pi"].every(
    (key) =>
      typeof properties[key] === "number" && Number.isFinite(properties[key]),
  )
    ? {
        ...value,
        id: value.id,
        features: value.features,
        protparam: properties,
      }
    : null;
}
export function stageRecords(
  tool: string | undefined,
  output: unknown,
): Record<string, unknown>[] | null {
  if (
    !tool ||
    !/^project\.m[1-5]$/.test(tool) ||
    !object(output) ||
    !["scientific-stage-v1", "scientific-stage-v2"].includes(
      String(output.schema_version),
    ) ||
    tool !== `project.${output.module}` ||
    !Array.isArray(output.records)
  )
    return null;
  const rows: Record<string, unknown>[] = [];
  for (const row of output.records) {
    if (
      !object(row) ||
      typeof row.status !== "string" ||
      typeof row.evidence_ready !== "boolean" ||
      typeof row.numerically_solved !== "boolean" ||
      !Array.isArray(row.missing_inputs)
    )
      return null;
    rows.push(row);
  }
  return rows;
}
