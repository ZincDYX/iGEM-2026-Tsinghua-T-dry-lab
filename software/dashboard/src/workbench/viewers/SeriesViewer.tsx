import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { requestJson,downloadResource } from "../../api";
import { parsePublicAsync as parsePublic } from "../../contracts/validation";
import type { SeriesPage } from "../../contracts/generated";
import {show} from "../../contracts/resultAdapters";
import { displayEnvelope } from "./displayEnvelope";
const Plot = lazy(() =>
  import("./PlotViewer").then((m) => ({ default: m.PlotViewer })),
);

export function SeriesViewer({
  fileId,
  projectId,
  targetSpecies,
  scopeMarked = false,
  initialSeriesIds,
  initialDataOpen = false,
  onSelectionChange,
  onData,
}: {
  fileId: string;
  projectId: string;
  targetSpecies?: string;
  scopeMarked?: boolean;
  initialSeriesIds?: string[];
  initialDataOpen?: boolean;
  onSelectionChange?:(ids:string[])=>void;
  onData?:(ids:string[])=>void;
}) {
  const [dataOpen,setDataOpen] = useState(initialDataOpen);
  const [adding,setAdding]=useState(false);
  const [offset, setOffset] = useState(0),
    [rangeOffset, setRangeOffset] = useState(0);
  const [page, setPage] = useState<SeriesPage>(),
    [overview, setOverview] = useState<SeriesPage>();
  const [selected, setSelected] = useState<string[]>(initialSeriesIds??[]),
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
              : (()=>{const match=value.series.find(s=>s.species_id===targetSpecies && s.quantity==='concentration' && s.compartment==='dilute')
                ?? value.series.find(s=>s.species_id===targetSpecies && s.quantity==='concentration')
                ?? value.series.find(s=>s.species_id===targetSpecies);return match?[match.id]:[];})(),
          );
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("No authorized time-course data available.");
      });
    return () => controller.abort();
  }, [fileId, projectId, offset, targetSpecies]);
  const seriesKey = selected.join(",");
  useEffect(()=>{if(selected.length)onSelectionChange?.(selected);},[seriesKey]);
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
      {page.source_type==='synthetic'&&!scopeMarked&&<p className="scope-warning"><strong>Synthetic demo.</strong> Not a project prediction or experimental validation.</p>}
      {Object.keys(page.pool_volumes).length>0&&<details><summary>Actual pool volumes</summary>
        {Object.entries(page.pool_volumes).map(([id,pool])=><p key={id}>{id}: {String(pool.volume_L)} L ({String(pool.role)}). Amount divided by this pool's volume gives its concentration.</p>)}
      </details>}
      <details>
        <summary>Series provenance</summary>
        <p>
          {page.model_kind} · {page.source_reference ?? "Source file"}
        </p>
      </details>
      {initialDataOpen&&initialSeriesIds?.length?<p>{selected.map(id=>{const series=page.series.find(series=>series.id===id);return series?`${series.species} — ${series.compartment} — ${series.quantity??'Recorded value'} (${series.unit})`:'Selected series unavailable';}).join('; ')}</p>:<div className="result-controls">
        {(['species','phase','quantity'] as const).map(kind=>{
          const current=page.series.find(s=>s.id===selected[0]);
          const valueOf=(s:SeriesPage['series'][number])=>kind==='species'?(s.species_id??s.species):kind==='phase'?s.compartment:(s.quantity??'Recorded value');
          const relevant=page.series.filter(s=>kind==='species'||!current||(s.species_id??s.species)===(current.species_id??current.species));
          return <label key={kind}>{kind==='species'?'Species':kind==='phase'?'Phase':'Quantity'}<select aria-label={kind==='species'?'Species':kind==='phase'?'Phase':'Quantity'} value={current?valueOf(current):''}
            onChange={e=>{const next=relevant.find(s=>valueOf(s)===e.target.value&&(!current || (kind==='species' ? s.compartment===current.compartment && s.quantity===current.quantity : kind==='phase' ? s.quantity===current.quantity : s.compartment===current.compartment)))??relevant.find(s=>valueOf(s)===e.target.value);
              setSelected(next?[next.id]:[]);setRangeOffset(0);setUnitError('');}}>
            <option value="">Choose {kind}</option>{[...new Set(relevant.map(valueOf))].map(value=><option key={value}>{value}</option>)}
          </select></label>;})}
      </div>}
      {!selected.length&&<p>Select the target species, phase and quantity; no target is inferred from column order.</p>}
      {!!selected.length&&!initialDataOpen&&<button onClick={()=>setAdding(value=>!value)}>Add series</button>}
      {adding&&<label>Comparable series<select aria-label="Additional series" value="" onChange={event=>{if(!event.target.value)return;setSelected(values=>[...values,event.target.value]);setAdding(false);setRangeOffset(0);}}>
        <option value="">Choose a series</option>{page.series.filter(series=>{const current=page.series.find(value=>value.id===selected[0]);return current&&!selected.includes(series.id)&&series.unit===current.unit&&series.quantity===current.quantity&&series.compartment===current.compartment;})
          .map(series=><option key={series.id} value={series.id}>{series.species} — {series.compartment} ({series.unit})</option>)}
      </select></label>}
      {selected.slice(1).map(id=><button key={id} onClick={()=>setSelected(values=>values.filter(value=>value!==id))}>Remove {page.series.find(series=>series.id===id)?.species}</button>)}
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
      {overview?.time.length ? <p className="result-status">{overview.series[0]?.species}: {show(overview.values[overview.series[0]?.id]?.at(-1))} {overview.series[0]?.unit} at {show(overview.time.at(-1))} {overview.time_unit}, {overview.series[0]?.compartment}. Transient endpoint, not steady state.</p> : null}
      <button aria-expanded={dataOpen} onClick={()=>onData?onData(selected):setDataOpen(value=>!value)}>Data</button>
      {dataOpen&&<section aria-label="Recorded numerical data">
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
                    <td key={s.id}>{show(page.values[s.id][i])}</td>
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
      </section>}
    </section>
  );
}
