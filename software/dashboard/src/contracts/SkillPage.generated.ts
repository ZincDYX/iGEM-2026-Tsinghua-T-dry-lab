/* Generated from public Pydantic contracts. Do not edit. */

export type Id = string;
export type Name = string;
export type Description = string;
export type Trigger = string;
export type Version = string;
export type Source = string;
export type License = string;
export type Enabled = boolean;
export type Revision = number;
export type Text = string;
export type UpdatedAt = string;
export type Execution = "instructions_only";
export type Items = SkillView[];
export type HasMore = boolean;

export interface SkillPage {
  items: Items;
  has_more: HasMore;
}
export interface SkillView {
  id: Id;
  name: Name;
  description: Description;
  trigger: Trigger;
  version: Version;
  source: Source;
  license: License;
  enabled: Enabled;
  revision: Revision;
  text: Text;
  updated_at: UpdatedAt;
  execution: Execution;
}
