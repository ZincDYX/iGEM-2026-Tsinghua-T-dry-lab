/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type Status = "not_configured" | "configured_unverified" | "available" | "failed";
export type Version = string | null;
export type LastRealCheck = string | null;
export type LatestFileId = string | null;
export type SourceReference = string;
export type Location = "connected_backend";

export interface PredictionToolView {
  id: Id;
  name: Name;
  status: Status;
  version: Version;
  last_real_check: LastRealCheck;
  latest_file_id: LatestFileId;
  source_reference: SourceReference;
  location: Location;
}
