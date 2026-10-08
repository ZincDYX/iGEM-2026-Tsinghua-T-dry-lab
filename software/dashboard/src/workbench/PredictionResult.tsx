import { lazy, Suspense } from "react";
import { object } from "../contracts/validation";
import { show } from "../contracts/resultAdapters";
const Plot = lazy(() =>
  import("./viewers/PlotViewer").then((module) => ({
    default: module.PlotViewer,
  })),
);

export function PredictionResult({
  output,
}: {
  output: Record<string, unknown>;
}) {
  const parsed = object(output.parsed) ? output.parsed : undefined;
  const models = Array.isArray(output.parsed)
    ? output.parsed.filter(object)
    : [];
  const scores =
    parsed && Array.isArray(parsed.scores) ? parsed.scores : undefined;
  const scoreData = scores
    ? [
        {
          type: "scatter" as const,
          mode: "lines" as const,
          x: scores.map((_, index) => index + 1),
          y: scores.map((value) => (typeof value === "number" ? value : null)),
          name: "Recorded IUPred score",
          connectgaps: false,
        },
      ]
    : [];
  return (
    <section>
      <h2>
        {show(output.candidate_id)}: {show(output.tool)}
      </h2>
      <p>
        Tool execution: {show(output.tool_status)}. Output parsing:{" "}
        {show(output.parse_status)}.
      </p>
      {typeof output.blocker === "string" && <p>{output.blocker}</p>}
      <p>
        Diagnostic output, not formal M1/M2 acceptance. Pocket, activity and
        assembly conclusions require their separate evidence-gated analyses.
      </p>
      {scores && parsed && (
        <>
          <p>
            Mean disorder score: {show(parsed.disorder_mean)}. Disordered
            fraction: {show(parsed.disorder_fraction)}. Longest disordered run:{" "}
            {show(parsed.longest_disordered_run)} residues.
          </p>
          <Suspense fallback={<p>Loading recorded disorder plot…</p>}>
            <Plot
              data={scoreData}
              title="Recorded per-residue disorder"
              xLabel="Complete input residue position"
              yLabel="IUPred score (0–1)"
              dataIdentity={String(output.input_sequence_sha256)}
            />
          </Suspense>
        </>
      )}
      {parsed && Array.isArray(parsed.low_complexity_positions) && (
        <p>
          Low-complexity fraction: {show(parsed.low_complexity_fraction)}.
          Masked positions:{" "}
          {parsed.low_complexity_positions.join(", ") || "None recorded"}.
        </p>
      )}
      {!!models.length && (
        <table>
          <thead>
            <tr>
              <th>Model rank</th>
              <th>Model / seed</th>
              <th>Length (aa)</th>
              <th>Mean pLDDT (0–100)</th>
              <th>pTM (0–1)</th>
            </tr>
          </thead>
          <tbody>
            {models.map((model) => (
              <tr key={String(model.model_name)}>
                <td>{show(model.model_rank)}</td>
                <td>{show(model.model_name)}</td>
                <td>{show(model.residue_count)}</td>
                <td>{show(model.mean_plddt)}</td>
                <td>{show(model.ptm)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
