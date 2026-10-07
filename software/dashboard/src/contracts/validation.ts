import * as validators from "./public.validators.generated.js";
import type {
  ProjectView,
  ProjectSummaryView,
  RunSummaryView,
  RuntimeInfoView,
  EventPage,
  NodePage,
  PlanView,
  ProposalView,
  ScientificPreviewView,
  BindingPreviewView,
  IterationView,
  ImportView,
  ActionView,
  Workflow,
} from "./generated";
import type { RunListView } from "./generated";
import type {
  InputDiffView,
  PluginInspectionView,
  ScientificPrecheckView,
} from "./generated";

import type {
  ResourcePage,
  SeriesPage,
  StructurePage,
  LineagePage,
  ComparePage,
} from "./generated";
export type Protocol = {
  ResourcePage: ResourcePage;
  SeriesPage: SeriesPage;
  StructurePage: StructurePage;
  LineagePage: LineagePage;
  ComparePage: ComparePage;
  ProjectView: ProjectView;
  ProjectSummaryView: ProjectSummaryView;
  RunSummaryView: RunSummaryView;
  RuntimeInfoView: RuntimeInfoView;
  EventPage: EventPage;
  NodePage: NodePage;
  PlanView: PlanView;
  ProposalView: ProposalView;
  ScientificPreviewView: ScientificPreviewView;
  ScientificPrecheckView: ScientificPrecheckView;
  BindingPreviewView: BindingPreviewView;
  IterationView: IterationView;
  ImportView: ImportView;
  ActionView: ActionView;
  Workflow: Workflow;
  RunListView: RunListView;
  InputDiffView: InputDiffView;
  PluginInspectionView: PluginInspectionView;
};
export function parsePublic<K extends keyof Protocol>(
  name: K,
  value: unknown,
): Protocol[K] {
  const validate = validators[name];
  if (!validate(value))
    throw new Error(
      `Public protocol ${name}  is incompatible; no defaults or predictions were generated.`,
    );
  // Ajv runtime validated against the schema generated from this exact type.
  return value as Protocol[K];
}
export function parseList<K extends keyof Protocol>(
  name: K,
  value: unknown,
): Protocol[K][] {
  if (!Array.isArray(value))
    throw new Error("Incompatible public list protocol.");
  return value.map((item) => parsePublic(name, item));
}
export function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
