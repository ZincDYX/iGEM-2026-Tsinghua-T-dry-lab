import { lazy, Suspense, useEffect, useState } from "react";
import { downloadResource, requestJson } from "../api";
import { parsePublicAsync } from "../contracts/validation";
import type {
  ImportView,
  ProjectView,
  ResourcePage,
} from "../contracts/generated";
import { StructureAnnotationLinker } from "./StructureAnnotationLinker";
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

export type FileContext = {
  fileId: string;
  name: string;
  runId?: string;
  targetSpecies?: string;
  seriesIds?: string[];
  dataOpen?: boolean;
  origin?: "inputs" | "results" | "tools";
};
/** A selected file, never a directory. Mount only while its document is visible. */
export function FileDocument({
  projectId,
  revision,
  file,
  onRegistered,
  project,
}: {
  projectId: string;
  revision: number;
  file: FileContext;
  onRegistered: (value: ImportView) => void;
  project?: ProjectView;
}) {
  const [resource, setResource] = useState<ResourcePage["items"][number]>(),
    [error, setError] = useState("");
  const [annotation, setAnnotation] = useState<ImportView>();
  useEffect(() => {
    const controller = new AbortController();
    setResource(undefined);
    setError("");
    const query = new URLSearchParams({ project_id: projectId });
    if (file.runId) query.set("run_id", file.runId);
    void requestJson(
      `/files/${encodeURIComponent(file.fileId)}/resource?${query}`,
      undefined,
      controller.signal,
    )
      .then((raw) => parsePublicAsync("ResourcePage", raw))
      .then((page) => {
        if (controller.signal.aborted) return;
        const selected = page.items[0];
        if (
          page.project_id !== projectId ||
          selected?.identity.file_id !== file.fileId
        )
          throw Error("File does not belong to this document.");
        if (file.runId && page.run_id !== file.runId)
          throw Error("File does not belong to this recorded run.");
        if (selected.status !== "available")
          throw Error(
            "File is unavailable. Its original record has been retained.",
          );
        setResource(selected);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) setError(String(reason));
      });
    return () => controller.abort();
  }, [projectId, revision, file.fileId, file.runId]);
  return (
    <section aria-label="Open file">
      <h2>{file.name}</h2>
      {error && <p role="alert">{error}</p>}
      {resource ? (
        <>
          <Suspense fallback={<p>Opening file…</p>}>
            {resource.kind === "structure" ? (
              <Structure
                key={revision}
                projectId={projectId}
                fileId={file.fileId}
              />
            ) : resource.kind === "series" ? (
              <Series
                projectId={projectId}
                fileId={file.fileId}
                targetSpecies={file.targetSpecies}
                initialSeriesIds={file.seriesIds}
                initialDataOpen={file.dataOpen}
              />
            ) : resource.kind === "image" ? (
              <Image projectId={projectId} fileId={file.fileId} />
            ) : resource.kind === "scan" ? (
              <Scan projectId={projectId} fileId={file.fileId} />
            ) : resource.kind === "m5" ? (
              <M5 projectId={projectId} fileId={file.fileId} />
            ) : (
              <Table
                projectId={projectId}
                fileId={file.fileId}
                revision={revision}
                onRegistered={onRegistered}
              />
            )}
          </Suspense>
          {resource.kind === "structure" && !file.runId && project && (
            <StructureAnnotationLinker
              project={project}
              targetFileId={file.fileId}
              disabled={false}
              action={async (job) => {
                try {
                  await job();
                } catch (reason) {
                  setError(String(reason));
                }
              }}
              onPreview={setAnnotation}
            />
          )}
          {annotation && (
            <section>
              <p>
                Use this linked annotation source for {file.name}? Original
                files remain unchanged.
              </p>
              <button
                onClick={() => {
                  onRegistered(annotation);
                  setAnnotation(undefined);
                }}
              >
                Use annotation source
              </button>
              <button onClick={() => setAnnotation(undefined)}>Cancel</button>
            </section>
          )}
          <button
            onClick={() =>
              void downloadResource(
                `/files/${encodeURIComponent(file.fileId)}?project_id=${encodeURIComponent(projectId)}`,
                resource.name,
              ).catch((reason) => setError(String(reason)))
            }
          >
            Export file
          </button>
        </>
      ) : (
        !error && <p>Opening file…</p>
      )}
    </section>
  );
}
