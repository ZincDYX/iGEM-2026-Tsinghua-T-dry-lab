import { requestJson, requestBinary } from "../api";
import { parsePublicAsync as parsePublic, parseList, object } from "../contracts/validation";
import type { Protocol } from "../contracts/validation";
import type {
  ProjectView,
  Workflow,
  ProposalView,
} from "../contracts/generated";
import type { ExecutionPolicy } from "../contracts/Workflow.generated";
import type { Goal } from "../types";

const read = async <K extends keyof Protocol>(
  name: K,
  path: string,
  body?: unknown,
  signal?: AbortSignal,
) => parsePublic(name, await requestJson(path, body, signal));
const list = async <K extends keyof Protocol>(
  name: K,
  path: string,
  signal?: AbortSignal,
) => parseList(name, await requestJson(path, undefined, signal));
export const projectSummaries = (signal?: AbortSignal) =>
  list("ProjectSummaryView", "/project-summaries", signal);
export const history = (id: string, offset = 0, signal?: AbortSignal) =>
  list(
    "RunListView",
    `/runs?project_id=${encodeURIComponent(id)}&offset=${offset}&limit=50`,
    signal,
  );
export const project = (id: string, signal?: AbortSignal) =>
  read("ProjectView", `/projects/${encodeURIComponent(id)}`, undefined, signal);
export const genbankDesign = (projectId: string, designId: string, recordIndex = 0, featureOffset = 0, nucleotideOffset = 0) =>
  read('GenBankPage', `/projects/${encodeURIComponent(projectId)}/designs/${encodeURIComponent(designId)}?record_index=${recordIndex}&feature_offset=${featureOffset}&nucleotide_offset=${nucleotideOffset}`);
export const precheck = (id: string, signal?: AbortSignal) =>
  read(
    "ScientificPrecheckView",
    `/projects/${encodeURIComponent(id)}/precheck`,
    undefined,
    signal,
  );
export const save = (value: ProjectView, revision?: number) =>
  read("ProjectView", "/projects", {
    project: value,
    expected_revision: revision,
  });
export const info = (signal?: AbortSignal) =>
  read("RuntimeInfoView", "/info", undefined, signal);
export const summary = (id: string, signal?: AbortSignal) =>
  read(
    "RunSummaryView",
    `/runs/${encodeURIComponent(id)}/summary`,
    undefined,
    signal,
  );
export const events = (id: string, cursor: number, signal?: AbortSignal) =>
  read(
    "EventPage",
    `/runs/${encodeURIComponent(id)}/events?after_seq=${cursor}&limit=200`,
    undefined,
    signal,
  );
export const node = (
  id: string,
  nodeId: string,
  offset = 0,
  signal?: AbortSignal,
) =>
  read(
    "NodePage",
    `/runs/${encodeURIComponent(id)}/nodes/${encodeURIComponent(nodeId)}/result?offset=${offset}&limit=20`,
    undefined,
    signal,
  );
export const propose = (
  id: string,
  goal: Goal,
  objective: string,
  mode: "template" | "hybrid",
  policy: ExecutionPolicy,
  permission: boolean,
) =>
  read("ProposalView", "/proposals", {
    project_id: id,
    goal,
    objective,
    mode,
    policy,
    external_planning_approved: permission,
  });
export const decide = (id: string, action: "accept" | "reject") =>
  read("ProposalView", `/proposals/${encodeURIComponent(id)}/decision`, {
    action,
  });
export const assistantHistory = (projectId: string, signal?: AbortSignal, before?: number) =>
  read('AssistantPage', `/projects/${encodeURIComponent(projectId)}/assistant${before === undefined ? '' : `?before=${before}`}`, undefined, signal);
export const proposalDiff = (id: string, signal?: AbortSignal) => read('ProposalDiff', `/proposals/${encodeURIComponent(id)}/diff`, undefined, signal);
export const proposal = (id: string, signal?: AbortSignal) => read('ProposalView', `/proposals/${encodeURIComponent(id)}`, undefined, signal);
export const assistantSettings = () => read('AssistantSettingsView','/assistant/settings');
export const saveAssistantSettings = (value: {provider:'none'|'compatible_api'|'local_endpoint'; model:string; endpoint?:string; secret?:string; clear_secret:boolean; style_instructions:string}) => read('AssistantSettingsView','/assistant/settings',value);
export const testAssistantSettings = () => read('AssistantProbeView','/assistant/settings/test',{});
export const skills = (offset=0) => read('SkillPage',`/skills?offset=${offset}`);
export const saveSkill = (text:string,enabled:boolean,id?:string,revision?:number) => read('SkillView',id?`/skills/${encodeURIComponent(id)}`:'/skills',{text,enabled,expected_revision:revision??null});
export const methodDrafts = (projectId:string,offset=0) => read('MethodDraftPage',`/projects/${encodeURIComponent(projectId)}/method-drafts?offset=${offset}`);
export const saveMethodDraft = (projectId:string,value:{base_method_id:string;base_version:string;title:string;formula_id:string;latex:string;reason:string;source_reference:string;previous_id:string|null;expected_project_revision:number;execution_spec?:import('../contracts/generated').MethodDraftView['execution_spec']}) =>
  read('MethodDraftView',`/projects/${encodeURIComponent(projectId)}/method-drafts`,value);
export const revise = (id: string, prompt: string, workflow?: Workflow) =>
  read('ProposalView', `/proposals/${encodeURIComponent(id)}/revise`, {prompt, workflow});
export const reviewParameter = (projectId: string, parameterId: string, stage: 'm3'|'m4', requirement_name: string, reviewer: string, reason: string, expected_revision: number) =>
  read('ProjectView', `/projects/${encodeURIComponent(projectId)}/parameters/${encodeURIComponent(parameterId)}/review`,
    {stage, requirement_name, reviewer, reason, expected_revision});
export async function start(proposal: ProposalView) {
  if (
    !proposal.workflow ||
    !proposal.confirmation ||
    proposal.status !== "accepted"
  )
    throw new Error("Accept the current reviewed proposal before starting.");
  const result = await requestJson("/runs", {
    project_id: proposal.project_id,
    workflow: proposal.workflow,
    confirmation: proposal.confirmation,
    proposal_id: proposal.id,
    request_id: proposal.id,
  });
  if (
    !result ||
    typeof result !== "object" ||
    !("id" in result) ||
    typeof result.id !== "string"
  )
    throw new Error("Incompatible run identity protocol.");
  return summary(result.id);
}
export async function control(
  id: string,
  action: "pause" | "cancel" | "resume" | "retry",
  nodeId?: string,
) {
  await requestJson(`/runs/${encodeURIComponent(id)}/control`, {
    action,
    node_id: nodeId,
  });
  return summary(id);
}
export const actions = (id: string, after = 0, signal?: AbortSignal) =>
  list(
    "ActionView",
    `/plan-actions?project_id=${encodeURIComponent(id)}&after_seq=${after}`,
    signal,
  );
export const diff = (id: string, runId: string, signal?: AbortSignal) =>
  read(
    "InputDiffView",
    `/projects/${encodeURIComponent(id)}/input-diff?run_id=${encodeURIComponent(runId)}`,
    undefined,
    signal,
  );
export async function importTransaction(projectId:string,files:File[],transactionId?:string,relativeName?:string){
  if(files.length>256||files.reduce((total,file)=>total+file.size,0)>20_000_000)
    throw Error('Import budget: 256 files / 20 MB.');
  const form=new FormData();
  for(const file of files) form.append('files',file,files.length===1&&relativeName?relativeName:file.webkitRelativePath||file.name);
  const suffix=transactionId?`/${encodeURIComponent(transactionId)}/files`:'';
  return parsePublic('ImportTransactionPreview',await (await requestBinary(`/projects/${encodeURIComponent(projectId)}/imports${suffix}`,form)).json());
}
export const inspectImport=(projectId:string,id:string)=>read('ImportTransactionPreview',`/projects/${encodeURIComponent(projectId)}/imports/${encodeURIComponent(id)}`);
export async function pendingImports(projectId:string):Promise<string[]>{
  const result=await requestJson(`/projects/${encodeURIComponent(projectId)}/imports`);
  if(!object(result)||!Array.isArray(result.transaction_ids)||!result.transaction_ids.every(id=>typeof id==='string')) throw Error('Invalid import list response');
  return result.transaction_ids;
}
export const reviseImport=async(projectId:string,id:string,options:Record<string,Record<string,unknown>>,revision?:number)=>
  parsePublic('ImportTransactionPreview',await requestJson(`/projects/${encodeURIComponent(projectId)}/imports/${encodeURIComponent(id)}`,{options,expected_revision:revision},undefined,'PATCH'));
export const commitImport=(projectId:string,id:string,choices:Record<string,string>)=>
  read('ProjectView',`/projects/${encodeURIComponent(projectId)}/imports/${encodeURIComponent(id)}/commit`,{choices});
export const discardImport=(projectId:string,id:string)=>
  read('ImportTransactionPreview',`/projects/${encodeURIComponent(projectId)}/imports/${encodeURIComponent(id)}/discard`,{});
export const bindMeasurement = (id: string, revision: number, fileId: string) =>
  read("BindingPreviewView", "/scientific-projects/bind-measurement", {
    project_id: id,
    expected_revision: revision,
    file_id: fileId,
  });
export const planMethod=(projectId:string,method:'sequence-properties'|'galatea-m1-m2'|'ps-v3-demo')=>
  read('ProposalView','/method-plans',{project_id:projectId,method});
export const methodWorkflow=(projectId:string,draftId:string)=>
  read('Workflow',`/projects/${encodeURIComponent(projectId)}/method-drafts/${encodeURIComponent(draftId)}/workflow`,{});
export const linkStructureAnnotations = (value: {
  project_id: string;
  expected_revision: number;
  source_file_id: string;
  target_file_id: string;
  reference_file_id: string | null;
  sequence_file_id: string | null;
  sequence_id: string | null;
}) => read("ImportView", "/imports/structure-annotations", value);
export const iteration = (id: string) =>
  read("IterationView", `/runs/${encodeURIComponent(id)}/iteration`, {});
export const review = (id: string, workflow: Workflow) =>
  read("PlanView", "/plans/custom", { project_id: id, workflow });
export const validate = (workflow: unknown) =>
  read("Workflow", "/workflows/validate", workflow);
export const proposeCustom = (
  id: string,
  workflow: Workflow,
  objective: string,
) =>
  read("ProposalView", "/custom-proposals", {
    project_id: id,
    workflow,
    objective,
  });
export const fetchPlugin = (repositoryUrl: string, commit: string) =>
  read("PluginInspectionView", "/plugins/repository", {
    repository_url: repositoryUrl,
    revision: commit.trim()||'HEAD',
  });
export const installedPlugins = () => list('PluginInspectionView','/plugins');
export const pluginEnabled = (hash:string,enabled:boolean) => read('PluginInspectionView',`/plugins/${encodeURIComponent(hash)}/state`,{enabled});
export async function uploadPluginSource(file:File) {
  if(file.size>16*1024*1024)throw Error('Source ZIP is limited to 16 MiB.');
  return parsePublic('PluginInspectionView',await (await requestBinary('/plugins/source',file)).json());
}
export const installPlugin = (source: string, hash: string) =>
  read("PluginInspectionView", "/plugins/install", {
    source_path: source,
    expected_hash: hash,
    trusted: true,
  });
export const defaultPolicy = (): ExecutionPolicy => ({
  target_node_id: null,
  max_completed_stages: null,
  checkpoints_before: [],
  checkpoints_after: [],
  allowed_tools: [],
  max_tool_calls: 1000,
  stop_after_seconds: null,
  memory_limit_mb: null,
});
const documentPath = (projectId: string, documentId?: string) =>
  `/projects/${encodeURIComponent(projectId)}/workflow-documents${documentId ? `/${encodeURIComponent(documentId)}` : ''}`;
export const workflowDocuments = (projectId: string, signal?: AbortSignal) =>
  list('WorkflowDocument', documentPath(projectId), signal);
export const workflowDocument = (projectId: string, documentId: string) =>
  read('WorkflowDocument', documentPath(projectId, documentId));
export const saveWorkflowDocument = (
  projectId: string, documentId: string,
  value: Pick<import('../contracts/generated').WorkflowDocument, 'layout' | 'selected_node_id' | 'view'> & {workflow?: Workflow},
  projectRevision: number, revision?: number,
) => read('WorkflowDocument', documentPath(projectId, documentId), {
  ...value, expected_project_revision: projectRevision, expected_revision: revision ?? null,
});
