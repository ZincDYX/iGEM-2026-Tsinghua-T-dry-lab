import { lazy, Suspense, useMemo } from "react";
import { object } from "../contracts/validation";
import { show } from "../contracts/resultAdapters";
const Plot = lazy(() =>
  import("./viewers/PlotViewer").then((m) => ({ default: m.PlotViewer })),
);

export function M3View({record}:{record:Record<string,unknown>}) {
  const concentrations=object(record.concentrations)?record.concentrations:{};
  const fractions=object(record.fraction_in_dense)?record.fraction_in_dense:{};
  const dilute=object(record.free_dilute_concentration)?record.free_dilute_concentration:{};
  return <section><h3>Enzyme recruitment</h3><table><thead><tr><th>Enzyme</th><th>Total dense (µM)</th><th>Free dilute (µM)</th><th>Dense fraction (1)</th></tr></thead><tbody>
    {Object.entries(concentrations).filter(([,value])=>object(value)).map(([enzyme,value])=>{const c=value as Record<string,unknown>;return <tr key={enzyme}><td>{enzyme}</td><td>{show(c.dense_concentration??c.dense)}</td><td>{show(dilute[enzyme]??c.dilute_concentration??c.dilute)}</td><td>{show(fractions[enzyme])}</td></tr>;})}
  </tbody></table><p>OC:DMT dense ratio: {show(record.dense_oc_dmt_ratio)}</p>
  </section>;
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
      {(typeof record.final_15==='number' || typeof record.final_13==='number') && <p>
        Endpoint compound 15 {show(record.final_15)} · compound 13{" "}
        {show(record.final_13)}. Endpoint titers, dimensionless yield and
        secretion flux are not interchangeable.
      </p>}
      {["yield_abs", "productivity", "secretion_loss"].some(field=>typeof record[field]==='number') && <table>
        <thead>
          <tr>
            <th>Original field</th>
            <th>Recorded value</th>
          </tr>
        </thead>
        <tbody>
          {["yield_abs", "productivity", "secretion_loss"].filter(field=>typeof record[field]==='number').map((field) => (
            <tr key={field}>
              <td>{field}</td>
              <td>{show(record[field])}</td>
            </tr>
          ))}
        </tbody>
      </table>}
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
      {Object.keys(robustness).length>0&&<><h3>Recorded robustness</h3>
      <p>
        Robustness {show(robustness.value)} · sigma {show(robustness.sigma)} ·
        ddof {show(robustness.ddof)} · scope {show(robustness.scope)}. No
        uncertainty interval is invented.
      </p>
      </>}
      {Object.keys(ranks).length > 0 && (
        <Suspense fallback={<p>Loading local plot renderer…</p>}>
          <Plot
            data={data}
            title="Recorded global sensitivity"
            dataIdentity={JSON.stringify([
              record.candidate_id,
              record.condition_id,
              data,
            ])}
            xLabel="Parameter identity"
            yLabel="Spearman coefficient (1)"
          />
        </Suspense>
      )}
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
          dataIdentity={JSON.stringify([features.sequence_sha256, data])}
          xLabel="Feature group"
          yLabel="Fraction (1)"
        />
      </Suspense>
    </section>
  ) : (
    <p>No sequence fractions recorded; no values reconstructed.</p>
  );
}
