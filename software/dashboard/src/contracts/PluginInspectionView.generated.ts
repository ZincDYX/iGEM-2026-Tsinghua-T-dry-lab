/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type Description = string;
export type Version = string;
export type Capability = string;
export type License = string;
export type Runtime = string;
export type Permissions = string[];
export type Hash = string;
export type Sandboxed = boolean;
export type TrustRequired = boolean;
export type Installed = boolean;
export type SourcePath = string | null;
export type CapabilityRequests = string[];

export interface PluginInspectionView {
  manifest: PluginMetadataView;
  hash: Hash;
  sandboxed: Sandboxed;
  trust_required: TrustRequired;
  installed: Installed;
  source_path: SourcePath;
  capability_requests: CapabilityRequests;
}
export interface PluginMetadataView {
  id: Id;
  name: Name;
  description: Description;
  version: Version;
  capability: Capability;
  license: License;
  runtime: Runtime;
  permissions: Permissions;
}
