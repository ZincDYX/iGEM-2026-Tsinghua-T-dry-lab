import { PublicError as isPublicError } from "./contracts/public.validators.generated.js";
import type { PublicError } from "./contracts/generated";
export let baseUrl =
  import.meta.env.VITE_DASHBOARD_API_URL ?? "http://127.0.0.1:8780";
let sessionToken = "";
export let backendMode: "local" | "https" = "local";
declare global {
  interface Window {
    __TAURI__?: {
      core: {
        invoke<T>(command: string, args?: Record<string, unknown>): Promise<T>;
      };
    };
  }
}
const connection = window.__TAURI__
  ? window.__TAURI__.core
      .invoke<{ url: string; token: string; mode: "local" | "https" }>(
        "backend_info",
      )
      .then((info) => {
        baseUrl = info.url;
        sessionToken = info.token;
        backendMode = info.mode;
      })
      .catch(() => {
        throw new Error(
          "Desktop backend connection failed. Check private maintenance diagnostics.",
        );
      })
  : Promise.resolve();
export interface DesktopSettings {
  mode: "local" | "https";
  api_url: string;
  ca_file: string;
  has_access_token: boolean;
}
export const isDesktop = () => Boolean(window.__TAURI__);
export const getDesktopSettings = () =>
  window.__TAURI__!.core.invoke<DesktopSettings>("desktop_settings");
export const saveDesktopSettings = (
  settings: Omit<DesktopSettings, "has_access_token"> & {
    access_token?: string;
  },
) => window.__TAURI__!.core.invoke<void>("save_desktop_settings", { settings });
export class PublicApiError extends Error {
  constructor(public readonly detail: PublicError) {
    super(
      [
        detail.message,
        ...detail.field_paths.map((value) => `Field: ${value}`),
        ...detail.logical_files.map((value) => `File: ${value}`),
        ...detail.actions,
      ].join("\n"),
    );
  }
}
export async function requestJson(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<unknown> {
  await connection;
  const response = await fetch(`${baseUrl}/api/platform${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      "Content-Type": "application/json",
      ...(sessionToken ? { "X-FusionLab-Token": sessionToken } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
    cache: "no-store",
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null),
      detail = error?.detail;
    if (isPublicError(detail)) throw new PublicApiError(detail);
    throw new Error(
      `Request failed (${response.status}); check the safe diagnostic.`,
    );
  }
  return response.json();
}
export async function requestBinary(
  path: string,
  body?: Blob,
  signal?: AbortSignal,
): Promise<Response> {
  await connection;
  const response = await fetch(`${baseUrl}/api/platform${path}`, {
    method: body ? "POST" : "GET",
    headers: {
      ...(body ? { "Content-Type": "application/octet-stream" } : {}),
      ...(sessionToken ? { "X-FusionLab-Token": sessionToken } : {}),
    },
    body,
    signal,
    cache: "no-store",
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    if (isPublicError(error?.detail)) throw new PublicApiError(error.detail);
    throw new Error(
      `Resource request denied (${response.status}). Check the safe diagnostic.`,
    );
  }
  return response;
}
export const downloadArtifact = (id: string, projectId: string) =>
  downloadResource(
    `/artifacts/${encodeURIComponent(id)}/science-export?project_id=${encodeURIComponent(projectId)}`,
    "scientific-public-export.json",
  );
export async function downloadResource(path: string, filename: string) {
  await connection;
  const response = await fetch(`${baseUrl}/api/platform${path}`, {
    headers: sessionToken ? { "X-FusionLab-Token": sessionToken } : {},
  });
  if (!response.ok)
    throw new Error(
      `Download denied (${response.status}); check authorization and the safe diagnostic.`,
    );
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
