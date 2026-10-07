import { useEffect, useState } from "react";
import type {
  ComparePage,
  LineagePage,
  RunListView,
  RunSummaryView,
} from "../contracts/generated";
import { requestJson } from "../api";
import { parsePublic } from "../contracts/validation";
import { LazyJson } from "../contracts/LazyJson";

export function ComparisonPanel({
  current,
  history,
}: {
  history: RunListView[];
  current?: RunSummaryView;
}) {
  const [lineage, setLineage] = useState<LineagePage>();
  const [lineageOffset, setLineageOffset] = useState(0);
  const [other, setOther] = useState("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<ComparePage>();
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setOther("");
    setPage(undefined);
    setLineage(undefined);
    if (current)
      void requestJson(
        `/projects/${encodeURIComponent(current.project_id)}/lineage?offset=${lineageOffset}`,
        undefined,
        controller.signal,
      )
        .then((raw) => {
          if (!controller.signal.aborted)
            setLineage(parsePublic("LineagePage", raw));
        })
        .catch(() => {
          if (!controller.signal.aborted)
            setError("Authorized lineage unavailable.");
        });
    return () => controller.abort();
  }, [current?.project_id, lineageOffset]);
  useEffect(() => {
    const controller = new AbortController();
    setPage(undefined);
    setError("");
    if (current && other)
      void requestJson(
        `/projects/${encodeURIComponent(current.project_id)}/compare?left_run_id=${encodeURIComponent(other)}&right_run_id=${encodeURIComponent(current.id)}&offset=${offset}`,
        undefined,
        controller.signal,
      )
        .then((raw) => {
          if (!controller.signal.aborted) {
            const value = parsePublic("ComparePage", raw);
            if (
              value.left.run_id !== other ||
              value.right.run_id !== current.id ||
              value.right.snapshot_hash !== current.snapshot_hash
            )
              throw new Error("Comparison identity changed.");
            setPage(value);
          }
        })
        .catch(() => {
          if (!controller.signal.aborted)
            setError("Comparison denied or frozen evidence changed.");
        });
    return () => controller.abort();
  }, [current?.id, current?.snapshot_hash, other, offset]);
  return (
    <section>
      <h2>Compare frozen runs</h2>
      <p>
        Authorized parent/child lineage only. Inputs and evidence remain visible
        when numerical comparison is blocked. No automatic ranking.
      </p>
      <label>
        Related run
        <select
          value={other}
          onChange={(e) => {
            setOther(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">Select related run</option>
          {lineage?.items
            .filter((r) => r.run_id !== current?.id)
            .map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.name ||
                  history.find((item) => item.id === r.run_id)?.name ||
                  "Related run"}{" "}
                · Inputs {r.revision} · {r.status}
                {r.created_at &&
                  ` · ${new Date(r.created_at).toLocaleString()}`}
              </option>
            ))}
        </select>
      </label>
      <button
        disabled={!lineageOffset}
        onClick={() => setLineageOffset(Math.max(0, lineageOffset - 50))}
      >
        Previous lineage page
      </button>
      <button
        disabled={!lineage?.has_more}
        onClick={() => setLineageOffset(lineageOffset + 50)}
      >
        Next lineage page
      </button>
      {error && <p role="alert">{error}</p>}
      {page && (
        <>
          <p>
            {page.left.name ||
              history.find((item) => item.id === page.left.run_id)?.name ||
              "Related run"}{" "}
            · Inputs {page.left.revision}
            <br />
            {current?.name ?? "Current run"} · Inputs {page.right.revision}
          </p>
          <h3>Changed input fields</h3>
          <ul>
            {page.input_changed_fields.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          {page.input_diff_truncated && (
            <p>Input differences truncated to 200 fields.</p>
          )}
          <table>
            <thead>
              <tr>
                <th>Stage</th>
                <th>Left identity / evidence</th>
                <th>Right identity / evidence</th>
                <th>F3 gate / values</th>
              </tr>
            </thead>
            <tbody>
              {page.rows.map((r, i) => (
                <tr key={i}>
                  <td>{r.module}</td>
                  <td>
                    {r.left?.record_id ?? "Missing"}
                    <br />
                    {r.left?.sequence_identity_sha256
                      ? "Sequence registered"
                      : "Sequence not registered"}
                    <br />
                    {r.left?.status} / evidence{" "}
                    {String(r.left?.evidence_ready ?? false)}
                  </td>
                  <td>
                    {r.right?.record_id ?? "Missing"}
                    <br />
                    {r.right?.sequence_identity_sha256
                      ? "Sequence registered"
                      : "Sequence not registered"}
                    <br />
                    {r.right?.status} / evidence{" "}
                    {String(r.right?.evidence_ready ?? false)}
                  </td>
                  <td>
                    {r.comparable
                      ? `${r.left?.value} → ${r.right?.value} (${r.metric_unit}); ${r.metric_definition}`
                      : `Not comparable: ${r.reason_codes.join(", ")}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <LazyJson
            value={page.rows}
            label="Data, F3 contracts and artifact identities"
          />
          <button
            disabled={!offset}
            onClick={() => setOffset(Math.max(0, offset - 20))}
          >
            Previous comparison page
          </button>
          <button
            disabled={!page.has_more}
            onClick={() => setOffset(offset + 20)}
          >
            Next comparison page
          </button>
          <p>
            {Math.min(offset + 1, page.total)}–
            {Math.min(offset + 20, page.total)} / {page.total}
          </p>
        </>
      )}
    </section>
  );
}
