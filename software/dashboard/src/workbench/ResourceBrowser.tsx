import { lazy, Suspense, useEffect, useState } from "react";
import type { ResourcePage } from "../contracts/generated";
import { requestJson, downloadResource } from "../api";
import { parsePublic } from "../contracts/validation";
const Image = lazy(() =>
  import("./viewers/ImageViewer").then((m) => ({ default: m.ImageViewer })),
);
const Series = lazy(() =>
  import("./viewers/SeriesViewer").then((m) => ({ default: m.SeriesViewer })),
);
const Structure = lazy(() =>
  import("./viewers/StructureViewer").then((m) => ({
    default: m.StructureViewer,
  })),
);
const Scan = lazy(() =>
  import("./viewers/ScanViewer").then((m) => ({ default: m.ScanViewer })),
);

export function ResourceBrowser({
  projectId,
  runId,
}: {
  projectId: string;
  runId?: string;
}) {
  const [scope, setScope] = useState("project");
  const activeRun = scope === "run" ? runId : undefined;
  const [page, setPage] = useState<ResourcePage>();
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState("");
  const [kind, setKind] = useState("all");
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setPage(undefined);
    setError("");
    setSelected("");
    const path = activeRun
      ? `/runs/${encodeURIComponent(activeRun!)}/resources?project_id=${encodeURIComponent(projectId)}&offset=${offset}`
      : `/projects/${encodeURIComponent(projectId)}/resources?offset=${offset}`;
    void requestJson(path, undefined, controller.signal)
      .then((raw) => {
        if (!controller.signal.aborted) {
          const value = parsePublic("ResourcePage", raw);
          if (
            value.project_id !== projectId ||
            value.run_id !== (activeRun ?? null)
          )
            throw new Error("Wrong resource scope.");
          setPage(value);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Resource catalogue unavailable. Check identity and authorization.",
          );
      });
    return () => controller.abort();
  }, [projectId, activeRun, offset]);
  const resource = page?.items.find((r) => r.identity.file_id === selected);
  return (
    <section>
      <h2>Registered artifacts</h2>
      <p>
        Only registered, authorized resources. No example plots or structures.
        Filters apply to this page.
      </p>
      {error && <p role="alert">{error}</p>}
      <label>
        Scope
        <select
          value={scope}
          onChange={(e) => {
            setOffset(0);
            setScope(e.target.value);
          }}
        >
          <option value="project">Project inputs and registered files</option>
          <option value="run" disabled={!runId}>
            Selected frozen run
          </option>
        </select>
      </label>
      <label>
        Resource type
        <select value={kind} onChange={(e) => setKind(e.target.value)}>
          {["all", "image", "series", "scan", "structure", "table"].map((k) => (
            <option key={k}>{k}</option>
          ))}
        </select>
      </label>
      <ul>
        {page?.items
          .filter((r) => kind === "all" || kind === r.kind)
          .map((r) => (
            <li key={r.identity.file_id}>
              <button onClick={() => setSelected(r.identity.file_id)}>
                {r.name} · {r.kind}
              </button>
            </li>
          ))}
      </ul>
      {page && (
        <>
          <button
            disabled={!offset}
            onClick={() => setOffset(Math.max(0, offset - 50))}
          >
            Previous resources
          </button>
          <button
            disabled={!page.has_more}
            onClick={() => setOffset(offset + 50)}
          >
            Next resources
          </button>
          <span>
            {" "}
            {Math.min(offset + 1, page.total)}–
            {Math.min(offset + 50, page.total)} / {page.total}
          </span>
        </>
      )}
      {resource && (
        <section
          key={`${projectId}:${selected}:${resource.identity.source_sha256}`}
        >
          <h3>{resource.name}</h3>
          <p>
            {resource.identity.file_id} · SHA-256{" "}
            {resource.identity.source_sha256} · {resource.byte_count} bytes
          </p>
          <Suspense fallback={<p>Loading local viewer…</p>}>
            {resource.kind === "image" ? (
              <Image projectId={projectId} fileId={selected} />
            ) : resource.kind === "series" ? (
              <Series projectId={projectId} fileId={selected} />
            ) : resource.kind === "structure" ? (
              <Structure projectId={projectId} fileId={selected} />
            ) : resource.kind === "scan" ? (
              <Scan projectId={projectId} fileId={selected} />
            ) : (
              <p>
                No active-content viewer. Use authorized original download or
                the stage table.
              </p>
            )}
          </Suspense>
          <button
            onClick={() =>
              void downloadResource(
                `/files/${encodeURIComponent(selected)}?project_id=${encodeURIComponent(projectId)}`,
                resource.name,
              ).catch(() =>
                setError(
                  "Original download denied by the disclosure boundary.",
                ),
              )
            }
          >
            Download authorized original
          </button>
        </section>
      )}
    </section>
  );
}
