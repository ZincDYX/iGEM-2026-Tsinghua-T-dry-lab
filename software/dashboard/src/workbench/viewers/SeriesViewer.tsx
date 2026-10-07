import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { requestJson } from "../../api";
import { parsePublic } from "../../contracts/validation";
import type { SeriesPage } from "../../contracts/generated";
const Plot = lazy(() =>
  import("./PlotViewer").then((m) => ({ default: m.PlotViewer })),
);

export function SeriesViewer({
  fileId,
  projectId,
}: {
  fileId: string;
  projectId: string;
}) {
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<SeriesPage>();
  const [selected, setSelected] = useState("");
  const [point, setPoint] = useState<number>();
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setPage(undefined);
    setError("");
    setPoint(undefined);
    void requestJson(
      `/files/${encodeURIComponent(fileId)}/series?project_id=${encodeURIComponent(projectId)}&offset=${offset}&limit=500`,
      undefined,
      controller.signal,
    )
      .then((raw) => {
        if (controller.signal.aborted) return;
        const value = parsePublic("SeriesPage", raw);
        if (
          value.identity.file_id !== fileId ||
          value.identity.project_id !== projectId
        )
          throw new Error("Resource identity changed.");
        setPage(value);
        setSelected((previous) =>
          value.series.some((s) => s.id === previous)
            ? previous
            : (value.series[0]?.id ?? ""),
        );
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("No authorized time-course data available.");
      });
    return () => controller.abort();
  }, [fileId, projectId, offset]);
  const descriptor = page?.series.find((s) => s.id === selected);
  const data = useMemo(
    () =>
      page && descriptor
        ? [
            {
              type: "scatter" as const,
              mode: "lines+markers" as const,
              x: page.time,
              y: page.values[descriptor.id],
              name: `${descriptor.compartment} / ${descriptor.species}`,
              connectgaps: false,
              selectedpoints: point === undefined ? undefined : [point],
              selected: { marker: { opacity: 1, size: 12 } },
              unselected: { marker: { opacity: 0.5 } },
            },
          ]
        : [],
    [page, descriptor, point],
  );
  if (error) return <p role="alert">{error}</p>;
  if (!page) return <p>Loading registered series…</p>;
  if (!page.total)
    return (
      <p>
        No time-course data available. A steady state is not a time trajectory.
      </p>
    );
  return (
    <section>
      <p>
        {page.model_kind} · {page.formula_version} · SHA-256{" "}
        {page.identity.source_sha256}
        {page.data_source_sha256 && (
          <>
            {" "}
            · original data SHA-256 {page.data_source_sha256} · declared source{" "}
            {page.source_reference}. This is a source display, not a prediction
            or evidence approval.
          </>
        )}
      </p>
      <label>
        Registered series
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          {page.series.map((s) => (
            <option key={s.id} value={s.id}>
              {s.compartment} / {s.species} ({s.unit})
            </option>
          ))}
        </select>
      </label>
      <p>
        Exact contiguous page, {offset + 1}–{offset + page.time.length} /{" "}
        {page.total} points. No interpolation, decimation, unit conversion,
        error bands or null-to-zero substitution.
      </p>
      <Suspense fallback={<p>Loading local plot renderer…</p>}>
        <Plot
          dataIdentity={`${projectId}:${fileId}:${page.identity.source_sha256}:${selected}:${offset}`}
          data={data}
          title="Recorded time course"
          xLabel={`Time (${page.time_unit})`}
          yLabel={`${descriptor?.compartment ?? ""} / ${descriptor?.species ?? ""} (${descriptor?.unit ?? "not recorded"})`}
          onPoint={setPoint}
        />
      </Suspense>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Time ({page.time_unit})</th>
              <th>
                {descriptor?.species} ({descriptor?.unit})
              </th>
            </tr>
          </thead>
          <tbody>
            {page.time.map((time, i) => (
              <tr
                key={i}
                aria-selected={point === i}
                onClick={() => setPoint(i)}
              >
                <td>{time}</td>
                <td>{page.values[selected]?.[i] ?? "Not recorded"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button
        disabled={!offset}
        onClick={() => setOffset(Math.max(0, offset - 500))}
      >
        Previous series page
      </button>
      <button disabled={!page.has_more} onClick={() => setOffset(offset + 500)}>
        Next series page
      </button>
    </section>
  );
}
