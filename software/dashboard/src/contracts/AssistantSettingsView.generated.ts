/* Generated from public Pydantic contracts. Do not edit. */

export type ProfileId = string;
export type Provider = "none" | "compatible_api" | "local_endpoint";
export type Model = string;
export type HasSecret = boolean;
export type Configured = boolean;
export type LocalWorkspace = boolean;
export type StyleInstructions = string;
export type SaveScope = "private_workspace";
export type TestedAt = string | null;

export interface AssistantSettingsView {
  profile_id: ProfileId;
  provider: Provider;
  model: Model;
  has_secret: HasSecret;
  configured: Configured;
  local_workspace: LocalWorkspace;
  style_instructions: StyleInstructions;
  save_scope: SaveScope;
  capabilities: Capabilities;
  tested_at: TestedAt;
}
export interface Capabilities {
  [k: string]: string;
}
