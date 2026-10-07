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
  const [offset, setOffset] = useState(0),
    [rangeOffset, setRangeOffset] = useState(0);
  const [page, setPage] = useState<SeriesPage>(),
    [overview, setOverview] = useState<SeriesPage>();
  const [selected, setSelected] = useState<string[]>([]),
    [point, setPoint] = useState<number>();
  const [error, setError] = useState(""),
    [unitError, setUnitError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    void requestJson(
      "/files/" +
        encodeURIComponent(fileId) +
        "/series?project_id=" +
        encodeURIComponent(projectId) +
        "&offset=" +
        offset +
        "&limit=500",
      undefined,
      controller.signal,
    )
      .then((raw) => {
        const value = parsePublic("SeriesPage", raw);
        if (
          value.identity.file_id !== fileId ||
          value.identity.project_id !== projectId
        )
          throw Error("Resource identity changed.");
        if (!controller.signal.aborted) {
          setPage(value);
          setSelected((previous) =>
            previous.length
              ? previous
              : value.series.slice(0, 1).map((s) => s.id),
          );
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("No authorized time-course data available.");
      });
    return () => controller.abort();
  }, [fileId, projectId, offset]);
  const seriesKey = selected.join(",");
  useEffect(() => {
    if (!selected.length) {
      setOverview(undefined);
      return;
    }
    const controller = new AbortController();
    setOverview(undefined);
    const query = new URLSearchParams({
      project_id: projectId,
      offset: String(rangeOffset),
      limit: "100000",
    });
    for (const id of selected) query.append("series_id", id);
    void requestJson(
      "/files/" + encodeURIComponent(fileId) + "/series?" + query,
      undefined,
      controller.signal,
    )
      .then((raw) => {
        const value = parsePublic("SeriesPage", raw);
        if (
          value.identity.file_id !== fileId ||
          value.identity.project_id !== projectId
        )
          throw Error("Wrong overview identity.");
        if (!controller.signal.aborted) setOverview(value);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("Overview unavailable; original table remains available.");
      });
    return () => controller.abort();
  }, [fileId, projectId, seriesKey, rangeOffset]);
  const data = useMemo(
    () =>
      overview?.series.map((s) => ({
        type: "scatter" as const,
        mode: "lines+markers" as const,
        x: overview.time,
        y: overview.values[s.id],
        name: s.compartment + " / " + s.species,
        connectgaps: false,
        selectedpoints:
          point === undefined ? undefined : [point - overview.offset],
        selected: { marker: { opacity: 1, size: 12 } },
        unselected: { marker: { opacity: 0.5 } },
      })) ?? [],
    [overview, point],
  );
  if (!page)
    return (
      <p role={error ? "alert" : undefined}>
        {error || "Loading registered series…"}
      </p>
    );
  if (!page.total)
    return (
      <p>
        No time-course data available. A steady state is not a time trajectory.
      </p>
    );
  return (
    <section>
      {error && <p role="alert">{error}</p>}
      <details>
        <summary>Series provenance</summary>
        <p>
          {page.model_kind} · {page.formula_version} · SHA-256{" "}
          {page.identity.source_sha256} · {page.data_source_sha256} ·{" "}
          {page.source_reference}. Source display, not evidence approval.
        </p>
      </details>
      <label>
        Registered series
        <select
          value={selected[0] ?? ""}
          onChange={(e) => {
            setSelected([e.target.value]);
            setRangeOffset(0);
            setUnitError("");
          }}
        >
          {page.series.map((s) => (
            <option key={s.id} value={s.id}>
              {s.compartment} / {s.species} ({s.unit})
            </option>
          ))}
        </select>
      </label>
      <details>
        <summary>Overlay recorded series</summary>
        {page.series.map((s) => (
          <label key={s.id}>
            <input
              type="checkbox"
              checked={selected.includes(s.id)}
              onChange={(e) => {
                const next = e.target.checked
                  ? [...selected, s.id]
                  : selected.filter((id) => id !== s.id);
                if (
                  new Set(
                    page.series
                      .filter((c) => next.includes(c.id))
                      .map((c) => c.unit),
                  ).size > 1
                ) {
                  setUnitError(
                    "Incompatible declared units. Select matching units; no automatic conversion.",
                  );
                  return;
                }
                setSelected(next);
                setRangeOffset(0);
                setUnitError("");
              }}
            />
            {s.compartment} / {s.species} ({s.unit})
          </label>
        ))}
      </details>
      {unitError && <p role="alert">{unitError}</p>}
      {overview && (
        <>
          <p>
            {overview.offset === 0 && !overview.has_more
              ? "Complete recorded range"
              : "Partial recorded range"}
            : {overview.offset + 1}–{overview.offset + overview.time.length} /{" "}
            {overview.total} points. No interpolation, decimation, unit
            conversion, error bands or null-to-zero substitution.
          </p>
          <Suspense fallback={<p>Loading local plot renderer…</p>}>
            <Plot
              dataIdentity={[
                projectId,
                fileId,
                overview.identity.source_sha256,
                seriesKey,
                rangeOffset,
              ].join(":")}
              data={data}
              title="Recorded time course"
              xLabel={"Time (" + overview.time_unit + ")"}
              yLabel={
                "Recorded value (" +
                (overview.series[0]?.unit ?? "not recorded") +
                ")"
              }
              onPoint={(i) => {
                const original = overview.offset + i;
                setPoint(original);
                setOffset(Math.floor(original / 500) * 500);
              }}
            />
          </Suspense>
          {(rangeOffset > 0 || overview.has_more) && (
            <>
              <p>
                Overview budget: 100,000 original points / 300,000 numeric cells
                per range. Table pagination never changes the plot range.
              </p>
              <button
                disabled={!rangeOffset}
                onClick={() =>
                  setRangeOffset(
                    Math.max(0, rangeOffset - overview.time.length),
                  )
                }
              >
                Previous plot range
              </button>
              <button
                disabled={!overview.has_more}
                onClick={() =>
                  setRangeOffset(rangeOffset + overview.time.length)
                }
              >
                Next plot range
              </button>
            </>
          )}
        </>
      )}
      <p>
        Exact contiguous page, {offset + 1}–{offset + page.time.length} /{" "}
        {page.total} points.
      </p>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Source index</th>
              <th>Time ({page.time_unit})</th>
              {page.series
                .filter((s) => selected.includes(s.id))
                .map((s) => (
                  <th key={s.id}>
                    {s.species} ({s.unit})
                  </th>
                ))}
            </tr>
          </thead>
          <tbody>
            {page.time.map((time, i) => (
              <tr
                key={offset + i}
                aria-selected={point === offset + i}
                onClick={() => setPoint(offset + i)}
              >
                <td>{offset + i}</td>
                <td>{time}</td>
                {page.series
                  .filter((s) => selected.includes(s.id))
                  .map((s) => (
                    <td key={s.id}>{page.values[s.id][i] ?? "Not recorded"}</td>
                  ))}
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
