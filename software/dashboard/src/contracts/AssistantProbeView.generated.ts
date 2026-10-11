/* Generated from public Pydantic contracts. Do not edit. */

export type Models = string[];
export type TestedAt = string;
export type Explanation = string;

export interface AssistantProbeView {
  capabilities: Capabilities;
  models: Models;
  tested_at: TestedAt;
  explanation: Explanation;
}
export interface Capabilities {
  [k: string]: string;
}
