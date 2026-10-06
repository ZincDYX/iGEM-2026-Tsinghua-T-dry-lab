/* Generated from public Pydantic contracts. Do not edit. */

export type Name = string;
export type ProtocolVersion = "2";
export type Authentication = string;
export type WorkspaceId = string;
export type Storage = string;
export type MaxWorkers = number;
export type PluginSandbox = boolean;
export type AgentBackend = string;
export type RemoteDesktopAuthenticatedSession = boolean;
export type SupportedRateLaws = string[];

export interface RuntimeInfoView {
  name: Name;
  protocol_version: ProtocolVersion;
  authentication: Authentication;
  workspace_id: WorkspaceId;
  storage: Storage;
  max_workers: MaxWorkers;
  plugin_sandbox: PluginSandbox;
  agent_backend: AgentBackend;
  capabilities: Capabilities;
  resources: Resources;
  remote_desktop_authenticated_session: RemoteDesktopAuthenticatedSession;
  supported_rate_laws: SupportedRateLaws;
}
export interface Capabilities {
  [k: string]: string;
}
export interface Resources {
  [k: string]: number | boolean;
}
