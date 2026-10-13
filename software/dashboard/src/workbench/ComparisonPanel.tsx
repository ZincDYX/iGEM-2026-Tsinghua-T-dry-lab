import { useEffect, useState } from "react";
import type {
  ComparePage,
  LineagePage,
  RunListView,
  RunSummaryView,
} from "../contracts/generated";
import { requestJson } from "../api";
import { parsePublicAsync } from "../contracts/validation";
import { show } from "../contracts/resultAdapters";

export function ComparisonPanel({
  current,
  history,
}: {
  current?: RunSummaryView;
  history: RunListView[];
}) {
  const [lineage, setLineage] = useState<LineagePage>(),
    [other, setOther] = useState(""),
    [page, setPage] = useState<ComparePage>();
  const [lineageOffset, setLineageOffset] = useState(0),
    [offset, setOffset] = useState(0),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setOther("");
    setPage(undefined);
    setError("");
    if (current)
      void requestJson(
        `/projects/${encodeURIComponent(current.project_id)}/lineage?offset=${lineageOffset}`,
        undefined,
        controller.signal,
      )
        .then((raw) => parsePublicAsync("LineagePage", raw))
        .then((value) => {
          if (!controller.signal.aborted) setLineage(value);
        })
        .catch(() => {
          if (!controller.signal.aborted)
            setError("Related runs could not be loaded.");
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
        .then((raw) => parsePublicAsync("ComparePage", raw))
        .then((value) => {
          if (
            value.left.run_id !== other ||
            value.right.run_id !== current.id ||
            value.right.snapshot_hash !== current.snapshot_hash
          )
            throw Error("Comparison identity changed.");
          if (!controller.signal.aborted) setPage(value);
        })
        .catch(() => {
          if (!controller.signal.aborted)
            setError(
              "These runs cannot be compared, or their recorded evidence changed.",
            );
        });
    return () => controller.abort();
  }, [current?.id, current?.snapshot_hash, other, offset]);
  const name = (id: string) =>
    lineage?.items.find((item) => item.run_id === id)?.name ||
    history.find((item) => item.id === id)?.name ||
    "Related run";
  return (
    <section>
      <h2>Compare runs</h2>
      {!current ? (
        <p>Select a recorded run in Results first.</p>
      ) : (
        <>
          <p>
            Current run: {current.name}. Only compatible recorded metrics are
            compared; missing evidence is not ranked.
          </p>
          <label>
            Related run
            <select
              aria-label="Related run"
              value={other}
              onChange={(event) => {
                setOther(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">Select a related run</option>
              {lineage?.items
                .filter((item) => item.run_id !== current.id)
                .map((item) => (
                  <option key={item.run_id} value={item.run_id}>
                    {name(item.run_id)} — {item.status.replaceAll("_", " ")}
                    {item.created_at
                      ? ` — ${new Date(item.created_at).toLocaleString()}`
                      : ""}
                  </option>
                ))}
            </select>
          </label>
          {(lineageOffset > 0 || lineage?.has_more) && (
            <nav>
              <button
                disabled={!lineageOffset}
                onClick={() =>
                  setLineageOffset((value) => Math.max(0, value - 50))
                }
              >
                Previous runs
              </button>
              <button
                disabled={!lineage?.has_more}
                onClick={() => setLineageOffset((value) => value + 50)}
              >
                Next runs
              </button>
            </nav>
          )}
          {error && <p role="alert">{error}</p>}
          {page && (
            <>
              <h3>
                {name(page.left.run_id)} compared with {current.name}
              </h3>
              {!!page.input_changed_fields.length && (
                <section>
                  <h4>Changed inputs</h4>
                  <ul>
                    {[
                      ...new Set(
                        page.input_changed_fields.map(
                          (field) =>
                            field
                              .split(".")
                              .filter(
                                (part) =>
                                  !/^\d+$/.test(part) && !part.includes("-"),
                              )
                              .map((part) => part.replaceAll("_", " "))
                              .join(" / ") || "Model input",
                        ),
                      ),
                    ].map((field) => (
                      <li key={field}>{field}</li>
                    ))}
                  </ul>
                  {page.input_diff_truncated && (
                    <p>Additional changes are not shown on this page.</p>
                  )}
                </section>
              )}
              <table>
                <thead>
                  <tr>
                    <th>Module</th>
                    <th>Earlier run</th>
                    <th>Current run</th>
                    <th>Metric</th>
                  </tr>
                </thead>
                <tbody>
                  {page.rows.map((row, index) => (
                    <tr key={index}>
                      <td>{row.module.toUpperCase()}</td>
                      {[row.left, row.right].map((record, i) => (
                        <td key={i}>
                          {record
                            ? `${record.status.replaceAll("_", " ")}; ${record.evidence_ready ? "evidence ready" : "missing evidence"}`
                            : "No matching record"}
                        </td>
                      ))}
                      <td>
                        {row.comparable
                          ? `${show(row.left?.value)} → ${show(row.right?.value)} ${row.metric_unit ?? ""} — ${row.metric_definition ?? ""}`
                          : `Not comparable: ${row.reason_codes.map((reason) => reason.replaceAll("_", " ")).join("; ")}`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(offset > 0 || page.has_more) && (
                <nav>
                  <button
                    disabled={!offset}
                    onClick={() =>
                      setOffset((value) => Math.max(0, value - 20))
                    }
                  >
                    Previous comparison page
                  </button>
                  <button
                    disabled={!page.has_more}
                    onClick={() => setOffset((value) => value + 20)}
                  >
                    Next comparison page
                  </button>
                </nav>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
