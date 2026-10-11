import { useEffect, useMemo, useState } from "react";
import type { Data } from "plotly.js";
import { requestJson } from "../../api";
import { parsePublicAsync as parsePublic } from "../../contracts/validation";
import type { ScanPage } from "../../contracts/generated";
import { show } from "../../contracts/resultAdapters";
import { PlotViewer } from "./PlotViewer";

export function ScanViewer({
  projectId,
  fileId,
}: {
  projectId: string;
  fileId: string;
}) {
  const [page, setPage] = useState<ScanPage>(),
    [offset, setOffset] = useState(0),
    [range, setRange] = useState(0);
  const [selected, setSelected] = useState<number>(),
    [error, setError] = useState(""),
    [mode, setMode] = useState("scatter");
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setPage(undefined);
    void requestJson(
      "/files/" +
        encodeURIComponent(fileId) +
        "/scan?project_id=" +
        encodeURIComponent(projectId) +
        "&offset=" +
        range +
        "&limit=10000",
      undefined,
      controller.signal,
    )
      .then(async (raw) => {
        const value = await parsePublic("ScanPage", raw);
        if (
          value.identity.project_id !== projectId ||
          value.identity.file_id !== fileId
        )
          throw Error("Wrong scan source.");
        if (!controller.signal.aborted) {
          setPage(value);
          setOffset(0);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Scan source unavailable or incompatible; no ranking performed.",
          );
      });
    return () => controller.abort();
  }, [projectId, fileId, range]);
  const axes = useMemo(() => {
    const points =
      page?.points.filter(
        (p) => p.site_ratio !== null && p.dense_oc_dmt_ratio !== null,
      ) ?? [];
    const x = [...new Set(points.map((p) => p.site_ratio!))].sort(
      (a, b) => a - b,
    );
    const y = [...new Set(points.map((p) => p.dense_oc_dmt_ratio!))].sort(
      (a, b) => a - b,
    );
    const cells = new Map(
      points.map((p) => [
        JSON.stringify([p.site_ratio, p.dense_oc_dmt_ratio]),
        p,
      ]),
    );
    return {
      points,
      x,
      y,
      cells,
      heatmap:
        points.length > 0 &&
        cells.size === points.length &&
        x.length * y.length <= 10000,
    };
  }, [page]);
  const data = useMemo<Data[]>(() => {
    if (!page) return [];
    if (mode === "heatmap" && axes.heatmap)
      return [
        {
          type: "heatmap",
          x: axes.x,
          y: axes.y,
          z: axes.y.map((y) =>
            axes.x.map(
              (x) =>
                axes.cells.get(JSON.stringify([x, y]))?.metric_value ?? null,
            ),
          ),
          customdata: axes.y.map((y) =>
            axes.x.map(
              (x) => axes.cells.get(JSON.stringify([x, y]))?.ordinal ?? null,
            ),
          ),
          connectgaps: false,
          zsmooth: false,
          hoverongaps: false,
          colorbar: {
            title: { text: page.metric_unit ?? "unit not registered" },
          },
        },
      ];
    if (mode === "3d")
      return [
        {
          type: "scatter3d",
          mode: "markers",
          x: axes.points.map((p) => p.site_ratio),
          y: axes.points.map((p) => p.dense_oc_dmt_ratio),
          z: axes.points.map((p) => p.metric_value),
          text: axes.points.map((p) => p.candidate_id),
          customdata: axes.points.map((p) => p.ordinal),
          name: "Eligible recorded scan points",
        },
      ];
    return [
      {
        type: "scatter",
        mode: "markers",
        x: page.points.map((p) => p.site_ratio),
        y: page.points.map((p) => p.metric_value),
        text: page.points.map((p) => p.candidate_id),
        customdata: page.points.map((p) => p.ordinal),
        name: "Eligible recorded scan points",
      },
    ];
  }, [page, mode, axes]);
  const metric =
    (page?.metric_definition ?? page?.objective) +
    " (" +
    (page?.metric_unit ?? "unit not registered") +
    ")";
  return (
    <section>
      <h3>F3 registered finite scan</h3>
      {error && <p role="alert">{error}</p>}
      {page && (
        <>
          <details>
            <summary>Scan provenance</summary>
            <p>{page.decision_scope}</p>
          </details>
          <label>
            Recorded scan display
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="scatter">Recorded 2D points</option>
              <option value="3d" disabled={!axes.points.length}>
                Recorded 3D points
              </option>
              <option value="heatmap" disabled={!axes.heatmap}>
                Original grid heatmap
              </option>
            </select>
          </label>
          {!axes.heatmap && (
            <p>
              No unambiguous bounded source grid: repeated coordinates are not
              averaged and missing axes are not inferred.
            </p>
          )}
          <p>
            {range === 0 && !page.has_more ? "Complete" : "Partial"} original
            scan range: {range + 1}–{range + page.points.length} / {page.total}.
            Missing cells remain gaps; no synthetic continuous scan or global
            optimum claim.
          </p>
          <PlotViewer
            dataIdentity={[
              projectId,
              fileId,
              page.identity.source_sha256,
              range,
              mode,
            ].join(":")}
            data={data}
            title="F3 registered finite scan points"
            xLabel="Declared SH3/PDZ site ratio (1)"
            yLabel={
              mode === "scatter" ? metric : "Recorded dense OC:DMT ratio (1)"
            }
            zLabel={mode === "3d" ? metric : undefined}
            onPoint={(ordinal) => {
              setSelected(ordinal);
              setOffset(Math.floor((ordinal - range) / 100) * 100);
            }}
          />
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Source ordinal</th>
                  <th>Candidate</th>
                  <th>Declared site ratio</th>
                  <th>Dense OC:DMT ratio</th>
                  <th>Status / feasible</th>
                  <th>Comparable recorded metric</th>
                  <th>Blocked reasons</th>
                </tr>
              </thead>
              <tbody>
                {page.points.slice(offset, offset + 100).map((p) => (
                  <tr
                    key={p.ordinal}
                    aria-selected={selected === p.ordinal}
                    onClick={() => setSelected(p.ordinal)}
                  >
                    <td>{p.ordinal}</td>
                    <td>{p.candidate_id}</td>
                    <td>{show(p.site_ratio)}</td>
                    <td>{show(p.dense_oc_dmt_ratio)}</td>
                    <td>
                      {p.status} / {show(p.feasible)}
                    </td>
                    <td>{show(p.metric_value)}</td>
                    <td>
                      {p.reason_codes.join(", ") ||
                        "source contract matches; not revalidated execution"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            disabled={!offset}
            onClick={() => setOffset(Math.max(0, offset - 100))}
          >
            Previous scan points
          </button>
          <button
            disabled={offset + 100 >= page.points.length}
            onClick={() => setOffset(offset + 100)}
          >
            Next scan points
          </button>
          {(range > 0 || page.has_more) && (
            <>
              <p>
                Display budget: 10,000 exact scan points per range; table
                pagination does not alter plot coverage.
              </p>
              <button
                disabled={!range}
                onClick={() => setRange(Math.max(0, range - 10000))}
              >
                Previous scan range
              </button>
              <button
                disabled={!page.has_more}
                onClick={() => setRange(range + page.points.length)}
              >
                Next scan range
              </button>
            </>
          )}
        </>
      )}
    </section>
  );
}
