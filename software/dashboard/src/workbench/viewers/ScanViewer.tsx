import { useEffect, useMemo, useState } from "react";
import { requestJson } from "../../api";
import { parsePublic } from "../../contracts/validation";
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
    [selected, setSelected] = useState<number>(),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setPage(undefined);
    setSelected(undefined);
    setError("");
    void requestJson(
      `/files/${encodeURIComponent(fileId)}/scan?project_id=${encodeURIComponent(projectId)}&offset=${offset}`,
      undefined,
      controller.signal,
    )
      .then((raw) => {
        const value = parsePublic("ScanPage", raw);
        if (
          value.identity.project_id !== projectId ||
          value.identity.file_id !== fileId
        )
          throw Error("Wrong scan source.");
        if (!controller.signal.aborted) setPage(value);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Scan source unavailable or incompatible; no ranking performed.",
          );
      });
    return () => controller.abort();
  }, [projectId, fileId, offset]);
  const data = useMemo(
    () => [
      {
        type: "scatter" as const,
        mode: "markers" as const,
        x: page?.points.map((p) => p.site_ratio) ?? [],
        y: page?.points.map((p) => p.metric_value) ?? [],
        text: page?.points.map((p) => p.candidate_id) ?? [],
        name: "Eligible recorded scan points",
      },
    ],
    [page],
  );
  return (
    <section>
      <h3>F3 registered finite scan</h3>
      {error && <p role="alert">{error}</p>}
      {page && (
        <>
          <p>
            Decision {page.decision_id} · source scope {page.decision_scope} ·
            SHA-256 {page.identity.source_sha256}. This source report is not
            execution/parameter approval. Backend source-contract gates apply;
            no scan, selection, interpolation or ranking is performed here.
          </p>
          <PlotViewer
            data={data}
            title="F3 registered finite scan points"
            xLabel="Declared SH3/PDZ site ratio (1)"
            yLabel={`${page.metric_definition ?? page.objective} (${page.metric_unit ?? "unit not registered"})`}
            onPoint={(index) => setSelected(page.points[index].ordinal)}
          />
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
              {page.points.map((p) => (
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
          <button
            disabled={!offset}
            onClick={() => setOffset(Math.max(0, offset - 100))}
          >
            Previous scan points
          </button>
          <button
            disabled={!page.has_more}
            onClick={() => setOffset(offset + 100)}
          >
            Next scan points
          </button>
          <p>
            Only exact points on this page are plotted. Rejected/missing points
            remain rows and null; no synthetic continuous scan or global optimum
            claim.
          </p>
        </>
      )}
    </section>
  );
}
