import type { DashboardModule, DashboardRun } from "./types";

const baseUrl = import.meta.env.VITE_DASHBOARD_API_URL ?? "http://127.0.0.1:8780";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, init);
  if (!response.ok) { const body = await response.json().catch(() => null); throw new Error(body?.detail?.message ?? `Request failed (${response.status})`); }
  return response.json() as Promise<T>;
}
export const getDag = () => request<DashboardModule[]>("/api/dashboard/dag");
export const startRun = (moduleId: string, configPath: string) => request<DashboardRun>("/api/dashboard/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ module_id: moduleId, config_path: configPath }) });
export const getRun = (runId: string) => request<DashboardRun>(`/api/dashboard/runs/${runId}`);
