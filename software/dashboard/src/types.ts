export type RunStatus = "queued" | "running" | "succeeded" | "failed" | "unavailable";
export interface DashboardModule { id: string; name: string; description: string; inputs: string[]; outputs: string[]; run_available: boolean; unavailable_reason?: string | null; }
export interface DashboardLog { step: string; status: RunStatus; message: string; timestamp: string; }
export interface DashboardRun { run_id: string; module_id: string; status: RunStatus; logs: DashboardLog[]; result?: Record<string, unknown> | null; error?: { code: string; message: string } | null; }
