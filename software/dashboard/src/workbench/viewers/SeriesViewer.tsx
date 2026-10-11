import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { requestJson,downloadResource } from "../../api";
import { parsePublicAsync as parsePublic } from "../../contracts/validation";
import type { SeriesPage } from "../../contracts/generated";
import { displayEnvelope } from "./displayEnvelope";
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
      .then(async (raw) => {
        const value = await parsePublic("SeriesPage", raw);
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
      .then(async (raw) => {
        const value = await parsePublic("SeriesPage", raw);
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
      overview?.series.map((s) => {
        const indices = displayEnvelope(
          overview.values[s.id],
          4000,
          point === undefined ? undefined : point - overview.offset,
        );
        const selectedIndex =
          point === undefined ? -1 : indices.indexOf(point - overview.offset);
        return {
          type: "scatter" as const,
          mode: "lines" as const,
          x: indices.map((i) => overview.time[i]),
          y: indices.map((i) => overview.values[s.id][i]),
          customdata: indices,
          name: s.compartment + " / " + s.species,
          connectgaps: false,
          selectedpoints: selectedIndex < 0 ? undefined : [selectedIndex],
          selected: { marker: { opacity: 1, size: 12 } },
          unselected: { marker: { opacity: 0.5 } },
        };
      }) ?? [],
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
      {page.source_type==='synthetic'&&<p className="scope-warning"><strong>Synthetic demo.</strong> Not a project prediction or experimental validation.</p>}
      {Object.keys(page.pool_volumes).length>0&&<details><summary>Actual pool volumes</summary>
        {Object.entries(page.pool_volumes).map(([id,pool])=><p key={id}>{id}: {String(pool.volume_L)} L ({String(pool.role)}). Amount divided by this pool's volume gives its concentration.</p>)}
      </details>}
      <button onClick={()=>void downloadResource(`/files/${encodeURIComponent(fileId)}/series.csv?project_id=${encodeURIComponent(projectId)}`,'recorded-series.csv').catch(()=>setError('Recorded CSV export unavailable.'))}>Export exact recorded CSV</button>
      <details>
        <summary>Series provenance</summary>
        <p>
          {page.model_kind} · {page.source_reference ?? "Source file"}
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
            {overview.total} points.
          </p>
          {overview.time.length > 4000 && (
            <p>
              Display-only min/max envelope; gap boundaries and original row
              indices are retained. Tables and downloads contain the original
              points.
            </p>
          )}
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
