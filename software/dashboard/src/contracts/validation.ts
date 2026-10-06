import * as validators from "./public.validators.generated.js";
import type {ProjectView,ProjectSummaryView,RunSummaryView,RuntimeInfoView,EventPage,NodePage,PlanView,ProposalView,ScientificPreviewView,BindingPreviewView,IterationView,ImportView,ActionView,Workflow} from "./generated";
import type {RunListView} from "./generated";
import type {InputDiffView,PluginInspectionView} from "./generated";

export type Protocol = {ProjectView:ProjectView;ProjectSummaryView:ProjectSummaryView;RunSummaryView:RunSummaryView;RuntimeInfoView:RuntimeInfoView;EventPage:EventPage;NodePage:NodePage;PlanView:PlanView;ProposalView:ProposalView;ScientificPreviewView:ScientificPreviewView;BindingPreviewView:BindingPreviewView;IterationView:IterationView;ImportView:ImportView;ActionView:ActionView;Workflow:Workflow;RunListView:RunListView;InputDiffView:InputDiffView;PluginInspectionView:PluginInspectionView};
export function parsePublic<K extends keyof Protocol>(name:K,value:unknown):Protocol[K] {
  const validate = validators[name];
  if (!validate(value)) throw new Error(`公开协议 ${name} 不兼容；没有补默认值或生成预测。`);
  // Ajv runtime validated against the schema generated from this exact type.
  return value as Protocol[K];
}
export function parseList<K extends keyof Protocol>(name:K,value:unknown):Protocol[K][] {
  if (!Array.isArray(value)) throw new Error("公开列表协议不兼容。");
  return value.map(item=>parsePublic(name,item));
}
export function object(value:unknown):value is Record<string,unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
