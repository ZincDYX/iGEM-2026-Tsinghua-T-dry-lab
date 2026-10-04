import type {
  Goal,
  ImportPreview,
  PluginInspection,
  Project,
  Run,
  RunSummary,
  RuntimeInfo,
  Tool,
  Workflow,
} from "./types";

export let baseUrl =
  import.meta.env.VITE_DASHBOARD_API_URL ?? "http://127.0.0.1:8780";
let sessionToken = "";
declare global {
  interface Window {
    __TAURI__?: { core: { invoke<T>(command: string): Promise<T> } };
  }
}
const connection = window.__TAURI__
  ? window.__TAURI__.core
      .invoke<{ url: string; token: string }>("backend_info")
      .then((info) => {
        baseUrl = info.url;
        sessionToken = info.token;
      })
  : Promise.resolve();
async function request<T>(path: string, body?: unknown): Promise<T> {
  await connection;
  const response = await fetch(`${baseUrl}/api/platform${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      "Content-Type": "application/json",
      ...(sessionToken ? { "X-FusionLab-Token": sessionToken } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(
      typeof error?.detail?.message === "string"
        ? error.detail.message
        : JSON.stringify(error?.detail ?? `请求失败 (${response.status})`),
    );
  }
  return response.json() as Promise<T>;
}
export const getProjects = () => request<Project[]>("/projects");
export const saveProject = (project: Project, expectedRevision?: number) =>
  request<Project>("/projects", {
    project,
    expected_revision: expectedRevision,
  });
export const previewImport = (file: File) =>
  file.text().then((content) =>
    request<ImportPreview>("/imports/preview", {
      filename: file.name,
      content,
    }),
  );
export const createPlan = (projectId: string, goal: Goal, objective: string) =>
  request<{
    workflow: Workflow;
    source: string;
    requires_confirmation: boolean;
  }>("/plans", { project_id: projectId, goal, objective });
export const validateWorkflow = (workflow: unknown) =>
  request<Workflow>("/workflows/validate", workflow);
export const startRun = (projectId: string, workflow: Workflow) =>
  request<Run>("/runs", { project_id: projectId, workflow });
export const getRun = (id: string) =>
  request<Run>(`/runs/${encodeURIComponent(id)}`);
export const getRuns = (projectId?: string) =>
  request<RunSummary[]>(
    `/runs${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""}`,
  );
export const controlRun = (
  id: string,
  action: "pause" | "cancel" | "resume" | "retry",
) => request<Run>(`/runs/${encodeURIComponent(id)}/control`, { action });
export const cloneRun = (id: string) =>
  request<Run>(`/runs/${encodeURIComponent(id)}/clone`, {});
export const getTools = () => request<Tool[]>("/tools");
export const getInfo = () => request<RuntimeInfo>("/info");
export const inspectPlugin = (sourcePath: string) =>
  request<PluginInspection>("/plugins/inspect", { source_path: sourcePath });
export const fetchGithubPlugin = (repositoryUrl: string, commit: string) =>
  request<PluginInspection & { source_path: string }>("/plugins/github", {
    repository_url: repositoryUrl,
    commit,
  });
export const installPlugin = (
  sourcePath: string,
  trusted: boolean,
  expectedHash: string,
) =>
  request<PluginInspection>("/plugins/install", {
    source_path: sourcePath,
    trusted,
    expected_hash: expectedHash,
  });
export const artifactUrl = (id: string) =>
  `${baseUrl}/api/platform/artifacts/${encodeURIComponent(id)}${sessionToken ? `?token=${encodeURIComponent(sessionToken)}` : ""}`;
