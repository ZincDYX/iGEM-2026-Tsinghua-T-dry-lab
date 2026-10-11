import { lazy, Suspense, useEffect, useState } from "react";
import type { ResourcePage, ImportView } from "../contracts/generated";
import { requestJson, downloadResource } from "../api";
import { parsePublicAsync as parsePublic } from "../contracts/validation";
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
const M5 = lazy(() =>
  import("./viewers/M5Viewer").then((m) => ({ default: m.M5Viewer })),
);
const Table = lazy(() =>
  import("./viewers/TableViewer").then((m) => ({ default: m.TableViewer })),
);

export function ResourceBrowser({
  projectId,
  runId,
  revision,
  initialFileId,
  initialRunScope,
  onRegistered,
  active = true,
}: {
  projectId: string;
  runId?: string;
  revision: number;
  initialFileId?: string;
  initialRunScope?: boolean;
  onRegistered: (value: ImportView) => void;
  active?: boolean;
}) {
  const [scope, setScope] = useState("project");
  const activeRun = scope === "run" ? runId : undefined;
  const [page, setPage] = useState<ResourcePage>();
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState("");
  const [kind, setKind] = useState("all");
  const [error, setError] = useState("");
  const [requestedResource, setRequestedResource] =
    useState<ResourcePage["items"][number]>();
  useEffect(() => {
    setScope(initialRunScope ? "run" : "project");
    setOffset(0);
  }, [initialFileId, initialRunScope]);
  useEffect(() => {
    if (!initialFileId) return;
    const controller = new AbortController();
    setRequestedResource(undefined);
    void requestJson(
      `/files/${encodeURIComponent(initialFileId)}/resource?project_id=${encodeURIComponent(projectId)}${initialRunScope && runId ? `&run_id=${encodeURIComponent(runId)}` : ""}`,
      undefined,
      controller.signal,
    )
      .then(async (raw) => {
        const value = await parsePublic("ResourcePage", raw);
        if (!controller.signal.aborted) {
          setRequestedResource(value.items[0]);
          setSelected(initialFileId);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("Requested resource unavailable in this project/run.");
      });
    return () => controller.abort();
  }, [initialFileId, initialRunScope, projectId, runId]);
  useEffect(() => {
    const controller = new AbortController();
    setPage(undefined);
    setError("");
    const path = activeRun
      ? `/runs/${encodeURIComponent(activeRun!)}/resources?project_id=${encodeURIComponent(projectId)}&offset=${offset}`
      : `/projects/${encodeURIComponent(projectId)}/resources?offset=${offset}`;
    void requestJson(
      path + (kind === "all" ? "" : `&kind=${encodeURIComponent(kind)}`),
      undefined,
      controller.signal,
    )
      .then(async (raw) => {
        if (!controller.signal.aborted) {
          const value = await parsePublic("ResourcePage", raw);
          if(controller.signal.aborted)return;
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
  }, [projectId, activeRun, offset, revision, kind]);
  const resource =
    page?.items.find((r) => r.identity.file_id === selected) ??
    (requestedResource?.identity.file_id === selected
      ? requestedResource
      : undefined);
  return (
    <section>
      <h2>Registered artifacts</h2>
      <p>
        Only registered, authorized resources. No example plots or structures.
        Type filters apply to the complete authorized catalogue.
      </p>
      {error && <p role="alert">{error}</p>}
      <label>
        Scope
        <select
          value={scope}
          onChange={(e) => {
            setOffset(0);
            setSelected("");
            setRequestedResource(undefined);
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
        <select
          value={kind}
          onChange={(e) => {
            setKind(e.target.value);
            setOffset(0);
          }}
        >
          {["all", "image", "series", "scan", "m5", "structure", "table"].map(
            (k) => (
              <option key={k}>{k}</option>
            ),
          )}
        </select>
      </label>
      <ul>
        {page?.items.map((r) => (
          <li key={r.identity.file_id}>
            <button
              disabled={r.status !== "available"}
              onClick={() => setSelected(r.identity.file_id)}
            >
              {r.name} · {r.kind}
            </button>
            {r.status !== "available" && (
              <span>
                {" "}
                {r.status} · {r.error_code}
              </span>
            )}
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
      {active && resource && (
        <section
          key={`${projectId}:${selected}:${resource.identity.source_sha256}`}
        >
          <h3>{resource.name}</h3>
          <p>
            {resource.logical_relative_path ?? resource.name} ·{" "}
            {resource.byte_count} bytes · Verified
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
            ) : resource.kind === "m5" ? (
              <M5 projectId={projectId} fileId={selected} />
            ) : (
              <Table
                projectId={projectId}
                fileId={selected}
                revision={revision}
                onRegistered={onRegistered}
              />
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
