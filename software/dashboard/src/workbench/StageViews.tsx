import { lazy, Suspense, useMemo } from "react";
import { object } from "../contracts/validation";
import { show } from "../contracts/resultAdapters";
const Plot = lazy(() =>
  import("./viewers/PlotViewer").then((m) => ({ default: m.PlotViewer })),
);

export function M3View({ record }: { record: Record<string, unknown> }) {
  const fields = [
    ["free_dense_concentration", "Free dense", "uM"],
    ["bound_dense_concentration", "Bound dense", "uM"],
    ["free_dilute_concentration", "Free dilute", "uM"],
    ["bound_fraction_of_whole_cell_total", "Bound / whole-cell total", "1"],
    ["fraction_in_dense", "Dense / whole-cell total", "1"],
    ["site_occupancy", "Site occupancy", "1"],
    ["mass_balance_residual_um", "Mass-balance residual", "uM"],
  ];
  const enzymes = [
    ...new Set(
      fields.flatMap(([field]) =>
        object(record[field]) ? Object.keys(record[field]) : [],
      ),
    ),
  ];
  const data = useMemo(
    () =>
      fields.slice(0, 3).map(([field, label]) => ({
        type: "bar" as const,
        name: label,
        x: enzymes,
        y: enzymes.map((enzyme) =>
          object(record[field]) && typeof record[field][enzyme] === "number"
            ? (record[field][enzyme] as number)
            : null,
        ),
      })),
    [record],
  );
  return (
    <section>
      <h3>Recorded phase distribution</h3>
      <p>
        OC:DMT dense ratio {show(record.dense_oc_dmt_ratio)} · Whole-cell ratio{" "}
        {show(record.whole_cell_oc_dmt_ratio)}
      </p>
      <table>
        <thead>
          <tr>
            <th>Enzyme</th>
            {fields.map(([key, label, unit]) => (
              <th key={key}>
                {label} ({unit})
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {enzymes.map((enzyme) => (
            <tr key={enzyme}>
              <td>{enzyme}</td>
              {fields.map(([field]) => (
                <td key={field}>
                  {object(record[field])
                    ? show(record[field][enzyme])
                    : "Not recorded"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {enzymes.length > 0 ? (
        <Suspense fallback={<p>Loading local plot renderer…</p>}>
          <Plot
            data={data}
            title="M3 recorded enzyme concentrations"
            xLabel="Enzyme identity"
            yLabel="Concentration (uM)"
          />
        </Suspense>
      ) : (
        <p>No phase distribution recorded.</p>
      )}
      <p>
        Site occupancy is distinct from fraction of the whole-cell enzyme pool.
        Capacity {show(record.capacity_status)} · Excess{" "}
        {show(record.capacity_excess_um)} uM.
      </p>
    </section>
  );
}

export function M4View({ record }: { record: Record<string, unknown> }) {
  const residuals = object(record.steady_state_residuals)
    ? record.steady_state_residuals
    : {};
  const fluxes = object(record.steady_state_fluxes)
    ? record.steady_state_fluxes
    : {};
  const analysis = object(record.analysis_result) ? record.analysis_result : {};
  const robustness = object(record.robustness)
    ? record.robustness
    : object(analysis.robustness)
      ? analysis.robustness
      : {};
  const sensitivity = object(record.sensitivity)
    ? record.sensitivity
    : object(analysis.sensitivity)
      ? analysis.sensitivity
      : {};
  const global = object(sensitivity.global) ? sensitivity.global : {};
  const ranks = object(global.spearman) ? global.spearman : {};
  const data = useMemo(
    () => [
      {
        type: "bar" as const,
        x: Object.keys(ranks),
        y: Object.values(ranks).map((v) => (typeof v === "number" ? v : null)),
        name: "Recorded Spearman",
      },
    ],
    [ranks],
  );
  return (
    <section>
      <h3>M4 recorded quantities</h3>
      <p>
        Endpoint compound 15 {show(record.final_15)} · compound 13{" "}
        {show(record.final_13)}. Endpoint titers, dimensionless yield and
        secretion flux are not interchangeable.
      </p>
      <table>
        <thead>
          <tr>
            <th>Original field</th>
            <th>Recorded value</th>
          </tr>
        </thead>
        <tbody>
          {["yield_abs", "productivity", "secretion_loss"].map((field) => (
            <tr key={field}>
              <td>{field}</td>
              <td>{show(record[field])}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {Object.keys(residuals).length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Species</th>
              <th>Steady residual (uM/h)</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(residuals).map(([key, v]) => (
              <tr key={key}>
                <td>{key}</td>
                <td>{show(v)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {Object.keys(fluxes).length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Reaction</th>
              <th>Recorded flux (uM/h)</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(fluxes).map(([key, v]) => (
              <tr key={key}>
                <td>{key}</td>
                <td>{show(v)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <h3>F2 recorded analysis</h3>
      <p>
        Robustness {show(robustness.value)} · sigma {show(robustness.sigma)} ·
        ddof {show(robustness.ddof)} · scope {show(robustness.scope)}. No
        uncertainty interval is invented.
      </p>
      {Object.keys(ranks).length > 0 ? (
        <Suspense fallback={<p>Loading local plot renderer…</p>}>
          <Plot
            data={data}
            title="Recorded global sensitivity"
            xLabel="Parameter identity"
            yLabel="Spearman coefficient (1)"
          />
        </Suspense>
      ) : (
        <p>No global sensitivity analysis recorded.</p>
      )}
      <p>
        Local stability must be read from the recorded analysis; it does not
        establish global uniqueness. F3 comparisons require the backend
        comparison contract.
      </p>
    </section>
  );
}

export function SequencePlot({
  features,
}: {
  features: Record<string, unknown>;
}) {
  const labels: Record<string, string> = {
    gs_fraction: "Glycine / serine",
    pro_fraction: "Proline",
    aromatic_fraction: "Aromatic",
    hydrophobic_fraction: "Hydrophobic",
    charged_fraction: "Charged",
    polar_fraction: "Polar",
    top2_fraction: "Top two residues",
  };
  const entries = Object.entries(labels).filter(
    ([field]) => typeof features[field] === "number",
  );
  const data = useMemo(
    () => [
      {
        type: "bar" as const,
        x: entries.map(([, label]) => label),
        y: entries.map(([field]) => features[field] as number),
      },
    ],
    [features],
  );
  return entries.length ? (
    <section>
      <p>
        Recorded feature fractions (unit 1). Categories can overlap; this is not
        a partition or an assembly prediction.
      </p>
      <Suspense fallback={<p>Loading local plot renderer…</p>}>
        <Plot
          data={data}
          title="Recorded sequence feature fractions"
          xLabel="Feature group"
          yLabel="Fraction (1)"
        />
      </Suspense>
    </section>
  ) : (
    <p>No sequence fractions recorded; no values reconstructed.</p>
  );
}
