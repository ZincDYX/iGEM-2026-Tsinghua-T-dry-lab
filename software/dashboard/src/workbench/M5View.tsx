import { lazy, Suspense, useMemo, useState } from "react";
import type { Data } from "plotly.js";
import { object, parsePublic } from "../contracts/validation";
import { show } from "../contracts/resultAdapters";
const Plot = lazy(() =>
  import("./viewers/PlotViewer").then((m) => ({ default: m.PlotViewer })),
);

function Comparison({
  metabolite,
  record,
  comparison,
}: {
  metabolite: string;
  record: Record<string, unknown>;
  comparison: Record<string, unknown>;
}) {
  const [offset, setOffset] = useState(0),
    [selected, setSelected] = useState<number>(),
    [range, setRange] = useState(0);
  const series = useMemo(() => {
    try {
      return parsePublic("M5ComparisonSeries", comparison.display_series);
    } catch {
      return undefined;
    }
  }, [comparison.display_series]);
  if (!series) {
    return (
      <p>
        No registered aligned series for {metabolite}; old summary retained. No
        curve regenerated.
      </p>
    );
  }
  if (
    ["experiment_id", "construct_id", "condition_id", "replicate_id"].some(
      (k) => record[k] !== series[k as "experiment_id"],
    )
  )
    return (
      <p role="alert">
        M5 series identity differs from the selected experiment; overlay
        withheld.
      </p>
    );
  if (
    [
      series.observed,
      series.predicted,
      series.residual_observed_minus_predicted,
      series.censor_mask,
    ].some((v) => v.length !== series.time.length) ||
    (series.uncertainty && series.uncertainty.length !== series.time.length)
  )
    return <p role="alert">M5 series lengths differ; overlay withheld.</p>;
  return (
    <RegisteredComparison
      metabolite={metabolite}
      series={series}
      comparison={comparison}
      offset={offset}
      selected={selected}
      setOffset={setOffset}
      setSelected={setSelected}
      range={range}
      setRange={setRange}
    />
  );
}

function RegisteredComparison({
  metabolite,
  series,
  comparison,
  offset,
  selected,
  setOffset,
  setSelected,
  range,
  setRange,
}: {
  metabolite: string;
  series: import("../contracts/generated").M5ComparisonSeries;
  comparison: Record<string, unknown>;
  offset: number;
  selected?: number;
  setOffset: (n: number) => void;
  setSelected: (n: number) => void;
  range: number;
  setRange: (n: number) => void;
}) {
  const indices = Array.from(
    { length: Math.min(100, series.time.length - offset) },
    (_, i) => offset + i,
  );
  const plotIndices = useMemo(
    () =>
      Array.from(
        { length: Math.min(100000, series.time.length - range) },
        (_, i) => range + i,
      ),
    [series, range],
  );
  const data = useMemo<Data[]>(
    () => [
      {
        type: "scatter",
        mode: "markers",
        name: "Recorded aligned prediction",
        x: plotIndices.map((i) => series.time[i]),
        y: plotIndices.map((i) => series.predicted[i]),
        customdata: plotIndices,
      },
      {
        type: "scatter",
        mode: "markers",
        name: "Quantified observation",
        customdata: plotIndices,
        x: plotIndices.map((i) => series.time[i]),
        y: plotIndices.map((i) =>
          series.censor_mask[i] === "quantified" ? series.observed[i] : null,
        ),
        ...(series.uncertainty && series.uncertainty_type
          ? {
              error_y: {
                type: "data" as const,
                array: plotIndices.map((i) =>
                  series.censor_mask[i] === "quantified"
                    ? series.uncertainty![i]
                    : 0,
                ),
                visible: true,
              },
            }
          : {}),
      },
      {
        type: "scatter",
        mode: "markers",
        name: "Censored bound (not quantified)",
        marker: { symbol: "triangle-down-open" },
        customdata: plotIndices,
        x: plotIndices.map((i) => series.time[i]),
        y: plotIndices.map((i) =>
          series.censor_mask[i] === "below_lod"
            ? series.lod
            : series.censor_mask[i] === "below_loq"
              ? series.loq
              : null,
        ),
      },
    ],
    [series, plotIndices],
  );
  const residuals = useMemo<Data[]>(
    () => [
      {
        type: "scatter",
        mode: "markers",
        name: "Observed minus predicted (quantified only)",
        customdata: plotIndices,
        x: plotIndices.map((i) => series.time[i]),
        y: plotIndices.map((i) => series.residual_observed_minus_predicted[i]),
      },
    ],
    [series, plotIndices],
  );
  const onPoint = useMemo(
    () => (index: number) => {
      setSelected(index);
      setOffset(Math.floor(index / 100) * 100);
    },
    [setOffset, setSelected],
  );
  // Source values identify the comparison, not table pagination or selection.
  const dataIdentity = useMemo(
    () =>
      JSON.stringify([
        series.experiment_id,
        series.construct_id,
        series.condition_id,
        series.replicate_id,
        series.raw_data_sha256,
        metabolite,
        plotIndices.map((i) => [
          series.time[i],
          series.observed[i],
          series.predicted[i],
          series.residual_observed_minus_predicted[i],
        ]),
      ]),
    [series, metabolite, plotIndices],
  );
  return (
    <section aria-label={`M5 recorded comparison ${metabolite}`}>
      <h3>M5 {metabolite}: registered comparison</h3>
      <p>
        {series.experiment_id} · construct {series.construct_id} · condition{" "}
        {series.condition_id} · replicate {series.replicate_id} ·{" "}
        {show(series.compartment)} / {show(series.concentration_basis)} · raw
        SHA-256 {show(series.raw_data_sha256)}.{" "}
        {show(comparison.comparison_status)}
      </p>
      <p>
        Exact recorded aligned points, {offset + 1}–{offset + indices.length}/
        {series.time.length}. No interpolation, normalization or fit executed in
        this view. Adapter {series.comparison_adapter}; legacy adapters are not
        formal condition verification. Original units {series.source_time_unit}/
        {series.source_concentration_unit}; registered canonical units h/uM.
        Uncertainty: {show(series.uncertainty_type)} (source magnitude; CI
        coverage is not inferred). Censored bounds are not exact observations.
      </p>
      <Suspense fallback={<p>Loading local comparison plot…</p>}>
        <p>
          {plotIndices.length === series.time.length ? "Complete" : "Partial"}{" "}
          recorded comparison plot: {range + 1}–{range + plotIndices.length}/
          {series.time.length} original points (100,000 point budget). Table
          pagination does not change plot coverage.
        </p>
        <Plot
          dataIdentity={dataIdentity}
          data={data}
          title={`M5 ${metabolite} recorded observations and predictions`}
          xLabel="Recorded time (h)"
          yLabel={`Concentration (uM) · ${show(series.compartment)}`}
          onPoint={onPoint}
        />
        <Plot
          dataIdentity={dataIdentity}
          data={residuals}
          title={`M5 ${metabolite} recorded residuals`}
          xLabel="Recorded time (h)"
          yLabel="Observed minus predicted (uM)"
          onPoint={onPoint}
        />
      </Suspense>
      {series.time.length > 100000 && (
        <div>
          <button
            disabled={range === 0}
            onClick={() => {
              const next = Math.max(0, range - 100000);
              setRange(next);
              setOffset(next);
            }}
          >
            Previous comparison plot range
          </button>
          <button
            disabled={range + 100000 >= series.time.length}
            onClick={() => {
              const next = range + 100000;
              setRange(next);
              setOffset(next);
            }}
          >
            Next comparison plot range
          </button>
        </div>
      )}
      <table>
        <thead>
          <tr>
            <th>Time h</th>
            <th>Reported canonical signal uM</th>
            <th>Censor status</th>
            <th>Prediction uM</th>
            <th>Residual uM</th>
          </tr>
        </thead>
        <tbody>
          {indices.map((i) => (
            <tr
              key={i}
              aria-selected={selected === i}
              onClick={() => setSelected(i)}
            >
              <td>{series.time[i]}</td>
              <td>{show(series.observed[i])}</td>
              <td>{series.censor_mask[i]}</td>
              <td>{series.predicted[i]}</td>
              <td>{show(series.residual_observed_minus_predicted[i])}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button
        disabled={!offset}
        onClick={() => setOffset(Math.max(0, offset - 100))}
      >
        Previous comparison points
      </button>
      <button
        disabled={offset + 100 >= series.time.length}
        onClick={() => setOffset(offset + 100)}
      >
        Next comparison points
      </button>
      <p>
        Descriptive scale-fit parameter interval:{" "}
        {object(comparison.fit)
          ? show(comparison.fit.confidence_interval)
          : "Not recorded"}
        . This is not a prediction confidence band and does not approve a
        parameter.
      </p>
    </section>
  );
}

export function M5View({ record }: { record: Record<string, unknown> }) {
  const comparisons = object(record.metabolite_comparisons)
    ? record.metabolite_comparisons
    : {};
  return (
    <section>
      <p>
        QC{" "}
        {record.qc_passed === true
          ? "passed (not parameter approval)"
          : "not passed/not recorded"}
        ; flags {show(record.qc_flags)}. Fit candidate requires separate
        approval. Missing/legacy series are not reconstructed.
      </p>
      {Object.entries(comparisons).map(([name, c]) =>
        object(c) ? (
          <Comparison
            key={`${String(record.experiment_id)}:${String(record.condition_id)}:${name}`}
            metabolite={name}
            record={record}
            comparison={c}
          />
        ) : null,
      )}
      {!Object.keys(comparisons).length && (
        <p>No registered matched observations.</p>
      )}
      <p>
        Recorded parameter candidate CI:{" "}
        {object(record.fit)
          ? show(record.fit.confidence_interval)
          : "Not recorded"}{" "}
        · warnings {show(record.fit_warnings)}. No new confidence or holdout
        evidence inferred.
      </p>
    </section>
  );
}
