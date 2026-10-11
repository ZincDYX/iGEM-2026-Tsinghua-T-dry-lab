import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  lazy,
  Suspense,
  type CSSProperties,
} from "react";
import type {
  ProposalView,
  RunListView,
  RuntimeInfoView,
  ScientificPrecheckView,
  WorkflowDocument,
} from "../contracts/generated";
import type { ExecutionPolicy } from "../contracts/Workflow.generated";
import type { Goal } from "../types";
import { LazyJson } from "../contracts/LazyJson";
import { show } from "../contracts/resultAdapters";
import * as client from "./client";
import { useProject } from "./useProject";
import { useRun } from "./useRun";
import { dependencies, statusLabel } from "./PlanPanel";
import { ModuleScientificStatus } from './ModuleStatus';
import { WorkflowWorkspace } from './WorkflowWorkspace';
import { WorkflowControls } from './WorkflowControls';
import { AgentPanel } from "./AgentPanel";
import { InputEditor } from "./InputEditor";
import { InputIssues, type InputIssue } from "./PrecheckPanel";
import { SelectedResult } from "./SelectedResult";
import { ComparisonPanel } from "./ComparisonPanel";
import { InputDiffPanel } from "./InputDiffPanel";
import { WorkflowImporter } from "./WorkflowImporter";
import { LocalSettings } from "./LocalSettings";
import { Splitter } from "./Splitter";
import { useWorkbenchLayout } from "./useWorkbenchLayout";
import { useSelectedResult } from "./useSelectedResult";
import { matchesRun, selectRunNode, type Selection } from "./selection";
import "./workbench.css";
import { ResourceBrowser } from "./ResourceBrowser";
import { WorkbenchMenus } from "./WorkbenchMenus";
import { primaryCommand } from "./workbenchCommands";
import { usePlanController } from "./usePlanController";
import { useDocuments } from "./useDocuments";
const MethodPanel = lazy(() => import('./MethodPanel').then(module => ({default: module.MethodPanel})));
const AssistantSettings = lazy(() => import('./AssistantSettings').then(module=>({default:module.AssistantSettings})));
const ExtensionsPanel = lazy(() => import('./ExtensionsPanel').then(module=>({default:module.ExtensionsPanel})));

type Tab =
  | "plan"
  | "inputs"
  | "results"
  | "compare"
  | "settings"
  | "assistant-settings"
  | "tools"
  | "artifacts";
const tabs: { id: Tab; label: string }[] = [
  { id: "inputs", label: "Inputs" },
  { id: "plan", label: "Workflow" },
  { id: "results", label: "Results" },
  { id: "compare", label: "Compare" },
  { id: "artifacts", label: "Resources" },
  { id: "settings", label: "Settings" },
  { id: "assistant-settings", label: "Assistant Settings" },
  { id: "tools", label: "Tools & extensions" },
];
function Tabs({
  values,
  selected,
  onChange,
  label,
  onClose,
}: {
  values: { id: string; label: string }[];
  selected: string;
  onChange: (id: string) => void;
  label: string;
  onClose?: (id: string) => void;
}) {
  return (
    <div
      role="tablist"
      aria-label={label}
      onKeyDown={(e) => {
        if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
        const index = values.findIndex((tab) => tab.id === selected);
        const next =
          (index + (e.key === "ArrowRight" ? 1 : -1) + values.length) %
          values.length;
        onChange(values[next].id);
        e.preventDefault();
        const nodes =
          e.currentTarget.querySelectorAll<HTMLButtonElement>("[role=tab]");
        nodes[next]?.focus();
      }}
    >
      {values.map((tab) => (
        <span key={tab.id} className={`workbench-tab ${selected===tab.id?'selected':''}`}>
        <button
          role="tab"
          key={tab.id}
          tabIndex={selected === tab.id ? 0 : -1}
          aria-selected={selected === tab.id}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
        {onClose && !['inputs','plan','results'].includes(tab.id) && <button aria-label={`Close ${tab.label}`} onClick={() => onClose(tab.id)}>×</button>}
        </span>
      ))}
    </div>
  );
}
export function WorkspaceShell() {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(0);
  const busy = pending > 0;
  const fail = useCallback(
    (reason: unknown) =>
      setError(
        reason instanceof Error
          ? reason.message
          : "Operation incomplete. Check the safe diagnostic.",
      ),
    [],
  );
  const project = useProject(fail);
  const [runId, setRunId] = useState<string>();
  const [refresh, setRefresh] = useState(0);
  const { run, events } = useRun(runId, project.draft?.id, refresh, fail);
  const [info, setInfo] = useState<RuntimeInfoView>();
  const [history, setHistory] = useState<RunListView[]>([]);
  const [proposal, setProposal] = useState<ProposalView>();
  const [workflowDocument, setWorkflowDocument] = useState<WorkflowDocument>();
  useLayoutEffect(() => setWorkflowDocument(current => current && proposal?.workflow &&
    JSON.stringify(current.workflow) === JSON.stringify(proposal.workflow) ? current : undefined), [proposal?.id]);
  const [goal, setGoal] = useState<Goal>("fusion_screen");
  const [inputTarget, setInputTarget] = useState<InputIssue>();
  const [objective, setObjective] = useState("");
  const [mode, setMode] = useState<"template" | "hybrid">(()=>localStorage.getItem("fusionlab.planner")==="hybrid"?"hybrid":"template");
  const [permission, setPermission] = useState(false);
  const [policy, setPolicy] = useState<ExecutionPolicy>(client.defaultPolicy);
  const { tab, setTab, openDocuments, closeDocument } = useDocuments(info?.workspace_id ?? "initial", project.dirty,
    () => setError("Save or discard input edits before closing Inputs."));
  const [resourceFile, setResourceFile] = useState<string>();
  const [resourceRunScope, setResourceRunScope] = useState(false);
  const [resourcesVisited, setResourcesVisited] = useState(false);
  const resourceReturn = useRef<{ tab: Tab; scroll: number }>({
    tab: "plan",
    scroll: 0,
  });
  const [inspector, setInspector] = useState("agent");
  const [bottom, setBottom] = useState("queue");
  const [selection, setSelection] = useState<Selection>();
  const view = useWorkbenchLayout();
  const { layout, bottomOpen, setBottomOpen, inspectorOpen, setInspectorOpen } =
    view;
  const [infoRefresh, setInfoRefresh] = useState(0);
  const goalChosen = useRef(false);
  const planController = usePlanController();
  const planGeneration = planController.generation;
  const [inputCheck, setInputCheck] = useState<ScientificPrecheckView>();
  const currentProject = project.draft;
  const selected =
    selection && selection.kind !== "resource" ? selection.nodeId : "";
  const runSelected = matchesRun(selection, run, currentProject?.id);
  const result = useSelectedResult(
    runSelected ? run : undefined,
    currentProject?.id,
    runSelected ? selected : "",
  );
  const nodeData = result.data;
  const workflow =
    selection?.kind === "run-node"
      ? run?.workflow
      : (workflowDocument?.workflow ?? proposal?.workflow ?? run?.workflow);
  const workflowChanged = !!workflowDocument && JSON.stringify(workflowDocument.workflow) !== JSON.stringify(proposal?.workflow);
  const visiblePolicy = runSelected && run ? run.workflow.execution_policy : policy;
  const node = workflow?.nodes.find((value) => value.id === selected);
  const m1Dependencies=new Set(run?.workflow.nodes.filter(n=>n.tool_id==='method.m1.decision').flatMap(dependencies));
  const resultNodes = run?.nodes.filter(item => item.parent_id === null && !m1Dependencies.has(item.id)) ?? [];
  useEffect(()=>{
    if(tab==='results'&&run&&(!runSelected||!resultNodes.some(item=>item.id===selected)))
      setSelection(selectRunNode(run,resultNodes[0]?.id??''));
  },[tab,run?.id,run?.state_version,runSelected,selected]);
  const stopped =
    run &&
    ["succeeded", "failed", "paused", "cancelled", "interrupted"].includes(
      run.status,
    );
  const executing = run && ["queued", "running"].includes(run.status);

  useEffect(()=>{if(run?.status==='succeeded')setBottomOpen(false);},[run?.status]);

  async function action(job: () => Promise<unknown>) {
    setPending((value) => value + 1);
    setError("");
    try {
      await job();
    } catch (reason) {
      fail(reason);
    } finally {
      setPending((value) => value - 1);
    }
  }
  function invalidate() {
    planController.invalidate();
    setProposal(undefined);
    setWorkflowDocument(undefined);
    setSelection(undefined);
  }
  function updatePolicy(value: ExecutionPolicy) {
    if (workflowDocument && currentProject && !runSelected) {
      const document = workflowDocument, stamp = project.generation.current;
      void action(async () => {
        const revised = structuredClone(document.workflow);
        revised.execution_policy = value;
        const saved = await client.saveWorkflowDocument(currentProject.id, document.id, {
          workflow: revised, layout: document.layout, selected_node_id: document.selected_node_id, view: document.view,
        }, currentProject.revision, document.revision);
        if (stamp !== project.generation.current) return;
        setWorkflowDocument(saved);
        setPolicy(saved.workflow.execution_policy);
        planController.invalidate();
      });
      return;
    }
    setPolicy(value);
    invalidate();
  }
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const value = await client.info(controller.signal);
        if (controller.signal.aborted) return;
        setInfo(value);
        if (value.capabilities.scientific_mcp === "checking" || executing)
          timer = setTimeout(load, 2500);
      } catch (reason) {
        if (!controller.signal.aborted) fail(reason);
      }
    }
    void load();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [!!executing, infoRefresh, fail]);
  useLayoutEffect(() => {
    // Reset project-scoped commands before the new project's controls are interactive.
    invalidate();
    setSelection(undefined);
    setHistory([]);
    setPolicy(client.defaultPolicy());
    setResourceFile(undefined);
    setResourceRunScope(false);
    setResourcesVisited(false);
    goalChosen.current = false;
    setRunId(
      currentProject
        ? (localStorage.getItem(`fusionlab.run.${currentProject.id}`) ??
            undefined)
        : undefined,
    );
    setGoal(
      currentProject?.scientific_project
        ? "scientific_pipeline"
        : "fusion_screen",
    );
  }, [currentProject?.id]);
  useEffect(() => {
    if (currentProject?.scientific_project && !goalChosen.current)
      setGoal("scientific_pipeline");
  }, [currentProject?.id, !!currentProject?.scientific_project]);
  useEffect(() => {
    if (!currentProject || project.saved?.id !== currentProject.id) return;
    const controller = new AbortController();
    client
      .history(currentProject.id, 0, controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setHistory(value);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) fail(reason);
      });
    return () => controller.abort();
  }, [currentProject?.id, project.saved?.id, run?.status, fail]);
  useEffect(() => {
    if (!run || proposal) return;
    if (
      !selection ||
      (selection.kind === "run-node" &&
        selection.runId === run.id &&
        !runSelected)
    )
      setSelection(
        selectRunNode(
          run,
          selection?.kind === "run-node"
            ? selection.nodeId
            : (resultNodes[0]?.id ?? ""),
        ),
      );
  }, [run?.id, run?.state_version, proposal?.id]);
  function selectRun(id: string) {
    if (run) setSelection(selectRunNode(run, id));
  }
  function selectPlan(id: string) {
    if (selection?.kind !== "run-node" && (workflowDocument || proposal?.workflow))
      setSelection({
        kind: "proposal-node",
        proposalId: proposal?.id ?? workflowDocument!.id,
        nodeId: id,
      });
    else selectRun(id);
  }

  async function propose(scope = policy) {
    await action(() =>
      planController.guarded(
        project.generation,
        project.save,
        (saved) =>
          client.propose(
            (saved as import("../contracts/generated").ProjectView).id,
            goal,
            objective,
            mode,
            scope,
            permission,
          ),
        (value) => {
          setPolicy(scope);
          setProposal(value);
          setTab("plan");
          setInspector("agent");
          setInspectorOpen(true);
          setSelection(
            value.workflow
              ? {
                  kind: "proposal-node",
                  proposalId: value.id,
                  nodeId: value.workflow.nodes[0].id,
                }
              : undefined,
          );
        },
      ),
    );
  }
  async function proposeMethod(method:'ps-v3-demo') {
    await action(()=>planController.guarded(project.generation,project.save,
      saved=>client.planMethod((saved as import('../contracts/generated').ProjectView).id,method),
      value=>{setProposal(value);setTab('plan');setInspector('agent');setInspectorOpen(true);
        setSelection(value.workflow?{kind:'proposal-node',proposalId:value.id,nodeId:value.workflow.nodes[0].id}:undefined);}
    ));
  }
  async function decide(decision: "accept" | "reject") {
    if (!proposal) return;
    const stamp = planGeneration.current;
    await action(async () => {
      const value = await client.decide(proposal.id, decision);
      if (stamp === planGeneration.current) setProposal(value);
    });
  }
  async function reviseProposal(prompt: string) {
    if (!proposal) return;
    const stamp = planGeneration.current;
    await action(async () => {
      const value = await client.revise(proposal.id, prompt, workflowDocument?.workflow);
      if (stamp === planGeneration.current) {
        setProposal(value); setTab('plan');
        if (value.workflow) setSelection({kind:'proposal-node',proposalId:value.id,nodeId:value.workflow.nodes[0].id});
      }
    });
  }
  async function openRecordedProposal(id:string) {
    const stamp=planGeneration.current;
    await action(async()=>{
      const value=await client.proposal(id);
      if(stamp!==planGeneration.current || value.project_id!==currentProject?.id) return;
      setProposal(value);setTab('plan');
      setSelection(value.workflow?.nodes.length?{kind:'proposal-node',proposalId:value.id,nodeId:value.workflow.nodes[0].id}:undefined);
    });
  }
  async function reviewParameter(id: string, stage: 'm3'|'m4', name: string, reviewer: string, reason: string) {
    await action(() => planController.guarded(project.generation,project.save,
      saved => {const value = saved as import('../contracts/generated').ProjectView;
        return client.reviewParameter(value.id,id,stage,name,reviewer,reason,value.revision);},
      value => {project.adopt(value); invalidate();}));
  }
  async function importWorkflow(
    create: () => Promise<import("../contracts/generated").Workflow>,
  ) {
    await action(async () => {
      const stamp = project.generation.current;
      const planStamp = planGeneration.current;
      const saved = await project.save();
      if (!saved) return;
      if (
        stamp !== project.generation.current ||
        planStamp !== planGeneration.current
      )
        return;
      const workflow = await create();
      const value = await client.proposeCustom(saved.id, workflow, objective);
      if (
        stamp !== project.generation.current ||
        planStamp !== planGeneration.current
      )
        return;
      setProposal(value);
      setTab('plan');
      setInspector('agent');
      setInspectorOpen(true);
      setSelection(
        value.workflow
          ? {
              kind: "proposal-node",
              proposalId: value.id,
              nodeId: value.workflow.nodes[0].id,
            }
          : undefined,
      );
    });
  }
  async function start() {
    if (!proposal || workflowChanged) return;
    const stamp = project.generation.current;
    await action(async () => {
      const value = await client.start(proposal);
      if (stamp === project.generation.current) {
        setRunId(value.id);
        setSelection(selectRunNode(value, value.nodes[0]?.id ?? ""));
        setRefresh((value) => value + 1);
        setProposal(undefined);
        setBottom("queue");setBottomOpen(true);
      }
    });
  }
  async function control(kind: "pause" | "cancel" | "resume" | "retry") {
    if (!run || !runSelected) return;
    const id = run.id;
    await action(async () => {
      await client.control(id, kind, kind === "retry" ? selected : undefined);
      if (runId === id) setRefresh((value) => value + 1);
    });
  }
  function discardDraft(message: string) {
    return (
      !(project.dirty) ||
      window.confirm(message + " (including unapplied  JSON edits). Continue?")
    );
  }
  function chooseProject(id: string) {
    if (!discardDraft("Switching projects discards the unsaved draft")) return;
    invalidate();
    setRunId(undefined);
    void project.choose(id);
  }
  function navigateInput(section: string) {
    setTab("inputs");
    requestAnimationFrame(() => {
      const target = document.getElementById(`input-${section}`);
      if (!target) return;
      const details =
        target instanceof HTMLDetailsElement
          ? target
          : target.querySelector("details");
      if (details) details.open = true;
      target.scrollIntoView({ block: "start" });
      target
        .querySelector<HTMLInputElement>(
          "input:not([disabled]),select:not([disabled])",
        )
        ?.focus({ preventScroll: true });
    });
  }
  useEffect(() => {
    if (tab === "artifacts") setResourcesVisited(true);
  }, [tab]);
  function openResource(fileId: string, fromRun = false) {
    resourceReturn.current = {
      tab,
      scroll: document.querySelector(".workspace-content")?.scrollTop ?? 0,
    };
    setResourceFile(fileId);
    setResourceRunScope(fromRun);
    setTab("artifacts");
  }
  function returnFromResource() {
    setTab(resourceReturn.current.tab);
    requestAnimationFrame(() => {
      const content = document.querySelector(".workspace-content");
      if (content) content.scrollTop = resourceReturn.current.scroll;
    });
  }
  function createIteration() {
    if (
      !run ||
      !runSelected ||
      !discardDraft("Creating an iteration discards the unsaved draft")
    )
      return;
    void action(async () => {
      const value = await client.iteration(run.id);
      project.adopt(value.project);
      setRunId(undefined);
      invalidate();
      setTab("inputs");
    });
  }
  const primary = primaryCommand(
    proposal,
    run,
    runSelected,
    inputCheck?.project_id === currentProject?.id &&
      inputCheck?.project_revision === currentProject?.revision &&
      !project.dirty &&
      true,
  );
  async function runPrimary() {
    if (primary === "resume") return control("resume");
    if (primary === "start") return start();
    if (primary === "review") return reviewWorkflow();
    if (primary === "check") return checkInputs();
  }
  async function reviewWorkflow() {
    if (workflowDocument && !runSelected) return importWorkflow(async () => workflowDocument.workflow);
    if (proposal?.workflow && !runSelected) return importWorkflow(async()=>proposal.workflow!);
    setError('Choose a method or open a saved workflow before reviewing a plan.');
  }
  async function checkInputs() {
    await action(async () => {
      const stamp = project.generation.current;
      const saved = await project.save();
      if (saved && stamp === project.generation.current) {
        const result = await client.precheck(saved.id);
        if (stamp !== project.generation.current) return;
        if (
          result.project_id !== saved.id ||
          result.project_revision !== saved.revision
        )
          throw new Error("Input revision changed; save and check again.");
        setInputCheck(result);
        setTab("inputs");
      }
    });
  }
  const projectCheck =
    inputCheck?.project_id === currentProject?.id ? inputCheck : undefined;
  const checkStale =
    project.dirty ||
    projectCheck?.project_revision !== currentProject?.revision;
  function openInput(issue: InputIssue) {
    setInputTarget(issue);
    const field = issue.field_path;
    const section = field.includes("construct")
      ? "constructs"
      : field.includes("fasta")
        ? "sequences"
        : field.includes("parameter")
          ? "evidence"
          : field.includes("condition") ||
              field.includes("experimental_context")
            ? "conditions"
            : field === "scientific_project"
              ? "scientific-setup"
              : field.includes("stages.")
                ? "conditions"
                : "evidence";
    navigateInput(section);
  }
  const style = {
    "--right-width": `${layout.right}px`,
    "--bottom-height": `${layout.bottom}px`,
  } as CSSProperties;
  return (
    <div
      ref={view.root}
      className={`workbench ${layout.theme} ${layout.density} ${view.narrow ? "narrow" : ""} ${inspectorOpen ? "" : "inspector-hidden"} ${bottomOpen ? "" : "bottom-hidden"}`}
      style={style}
    >
      <header className="workbench-top">
        <span className="brand">FusionLab</span>
        <WorkbenchMenus
          file={[
            {
              label: "New project",
              disabled: busy,
              action: () => {
                if (!discardDraft("New project discards the unsaved draft"))
                  return;
                project.new();
                setRunId(undefined);
                invalidate();
                setTab("inputs");
              },
            },
            {
              label: "Import project folder",
              disabled: !currentProject,
              action: () => {navigateInput('import');requestAnimationFrame(()=>document.getElementById('input-import-folder')?.click());},
            },
            {
              label:'Import files',disabled:!currentProject||busy,
              action:()=>{navigateInput('import');requestAnimationFrame(()=>document.getElementById('input-import-file')?.click());},
            },
            {
              label: "Save",
              disabled: busy || !currentProject,
              action: () => void action(() => project.save()),
            },
            {
              label: "Create iteration",
              disabled: busy || !run || !runSelected,
              action: createIteration,
            },
          ]}
          view={[
            {
              label: "Inspector",
              action: () => setInspectorOpen((value) => !value),
            },
            {
              label: "Jobs panel",
              action: () => setBottomOpen((value) => !value),
            },
            {
              label: "Artifacts",
              disabled: !currentProject,
              action: () => setTab("artifacts"),
            },
          ]}
          tools={[
            {
              label: "Tools & extensions",
              disabled: !currentProject,
              action: () => setTab("tools"),
            },
            { label: "Settings", action: () => setTab("settings") },
            { label: "Assistant Settings", action: () => setTab("assistant-settings") },
          ]}
          help={[
            {
              label: "Scientific boundaries",
              action: () => {
                setTab('plan');
                setInspector("evidence");
                setInspectorOpen(true);
              },
            },
          ]}
        />
        <select
          aria-label="Current project"
          disabled={busy}
          value={currentProject?.id ?? ""}
          onChange={(e) => chooseProject(e.target.value)}
        >
          <option value="" disabled>
            Select or create a project
          </option>
          {currentProject &&
            !project.summaries.some((row) => row.id === currentProject.id) && (
              <option value={currentProject.id}>
                {currentProject.name} (draft)
              </option>
            )}
          {project.summaries.map((row) => (
            <option key={row.id} value={row.id}>
              {row.name} · r{row.revision}
            </option>
          ))}
        </select>
        <button aria-expanded={inspectorOpen} onClick={() => {setInspector("agent");setInspectorOpen(value=>!value);}}>Assistant</button>
        <button onClick={() => setBottomOpen(value=>!value)}>Jobs{executing ? " · running" : run?.status === "failed" ? " · failed" : ""}</button>
        <span className="workspace-state">
          {info ? "Connected workspace" : "Connecting to backend"}
        </span>
      </header>
      <main className="workspace-center">
        <Tabs
          values={tabs.filter(item => ["inputs","plan","results"].includes(item.id) || openDocuments.includes(item.id))}
          selected={tab}
          label="Workspace documents"
          onClose={(id) => {if (!["inputs","plan","results"].includes(id)) closeDocument(id as Tab);}}
          onChange={(id) => {
            const value = tabs.find((t) => t.id === id);
            if (value) setTab(value.id);
          }}
        />
        <div className="workspace-content" role="tabpanel">
          <div className="document-status">
            <span>
              {currentProject?.name ?? "No project loaded"} ·{" "}
              {project.dirty ? "Unsaved changes" : "Draft synchronized"}
              {""}
            </span>
            <span>
              {run
                ? `${statusLabel(run.status)} / Inputs r${run.project_revision}`
                : "No run started"}
            </span>
          </div>
          {error && (
            <div className="error-strip" role="alert">
              {error}
              <button onClick={() => setError("")}>Dismiss</button>
            </div>
          )}
          {executing && run?.control && (
            <p className="control-notice">
              Requested {run.control === "pause" ? "Pause" : "Cancel"}; waiting
              for the current step to finish. Scientific solvers are not
              truncated.
            </p>
          )}
          {project.loading ? (
            <p>Loading project…</p>
          ) : currentProject ? (
            <div hidden={tab !== "inputs"}>
              <InputEditor
                key={currentProject.id}
                project={currentProject}
                busy={busy}
                dirty={project.dirty}
                onChange={(value) => {
                  project.edit(value);
                  invalidate();
                }}
                action={action}
                inputCheck={projectCheck}
                checkStale={checkStale}
                onCheck={() => void checkInputs()}
                onLocate={openInput}
                inputTarget={inputTarget}
                onOpenResource={openResource}
                onPlanMethod={method=>void proposeMethod(method)}
                prepareImport={project.save}
                onImported={value=>{project.adopt(value);invalidate();}}
              />
            </div>
          ) : tab === "inputs" ? (
            <p>Create or select a project first.</p>
          ) : null}
          {tab === "plan" && (
            <>
              <WorkflowControls primary={primary} disabled={busy || !currentProject}
                reviewDisabled={!workflowDocument && !proposal?.workflow}
                pausePending={!!run?.control}
                startDisabled={workflowChanged || project.dirty} executing={!!executing && runSelected}
                cancellable={!!run && runSelected && ['queued','running','paused','interrupted'].includes(run.status) && run.control!=='cancel'}
                retryable={runSelected && ['failed','interrupted'].includes(run?.nodes.find(n=>n.id===selected)?.status??'')}
                frozen={runSelected} onPrimary={()=>void runPrimary()} onPause={()=>void control('pause')}
                onCancel={()=>void control('cancel')} onRetry={()=>void control('retry')}
                onReview={()=>void reviewWorkflow()}/>
              <p aria-label="Selection context">
                {selection?.kind === "proposal-node"
                  ? "Draft proposal; no computed result yet."
                  : runSelected
                    ? `${run?.name} · Saved inputs ${run?.project_revision}`
                    : "Select a proposal or a frozen run."}
              </p>
              <WorkflowWorkspace
                key={`workflow:${currentProject?.id}`}
                projectId={currentProject?.id}
                projectRevision={currentProject?.revision}
                seedId={selection?.kind === 'run-node' ? run?.id : proposal?.id}
                seed={selection?.kind === 'run-node' ? run?.workflow : proposal?.workflow ?? undefined}
                document={workflowDocument}
                onDocument={value=>{setWorkflowDocument(value);setPolicy(value.workflow.execution_policy);setSelection({kind:'proposal-node',proposalId:proposal?.id??value.id,nodeId:value.selected_node_id??value.workflow.nodes[0].id});}}
                frozen={selection?.kind === 'run-node'}
                busy={busy || project.dirty}
                inputCheck={checkStale ? undefined : projectCheck}
                run={selection?.kind === "proposal-node" ? undefined : run}
                selected={selected}
                onSelect={selectPlan}
              />
              {workflowChanged && selection?.kind !== 'run-node' && <p role="status">Workflow changes are saved but not authorized. Review and accept a new proposal before running.</p>}
              {tab === 'plan' && node && currentProject && <Suspense fallback={<p>Loading method details…</p>}><MethodPanel
                key={node.id} project={currentProject} toolId={node.tool_id} runId={runSelected ? run?.id : undefined}
                disabled={busy} onChange={value => {project.edit(value); invalidate();}} onReview={reviewParameter}
                onPlan={value=>void importWorkflow(async()=>value)}/></Suspense>}
              <fieldset className="policy-editor" disabled={busy || !!runSelected || (!!proposal?.workflow && !workflowDocument)}>
                <h3>Execution settings</h3>
                {!!proposal?.workflow && !workflowDocument && !runSelected && <p role="status">Saving this workflow before execution settings can be edited.</p>}
                <p>{runSelected ? 'Recorded settings for this frozen run; not the current draft.' : 'Choose the execution scope here, then Review plan. Changing these settings requires a new accepted proposal; it does not approve scientific evidence.'}</p>
                <label>
                  Run through module
                  <select aria-label="Run through module" value={visiblePolicy.target_node_id ?? ''}
                    onChange={event => updatePolicy({...policy, target_node_id: event.target.value || null})}>
                    <option value="">All modules in this workflow</option>
                    {workflow?.nodes.map(value => <option key={value.id} value={value.id}>{value.label}</option>)}
                  </select>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={visiblePolicy.max_completed_stages === 1}
                    onChange={(e) =>
                      updatePolicy({
                        ...policy,
                        max_completed_stages: e.target.checked ? 1 : null,
                      })
                    }
                  />
                  Pause after each completed module
                </label>
                {node && (
                  <>
                    <label>
                      <input type="checkbox" checked={visiblePolicy.checkpoints_before.includes(selected)}
                      onChange={() =>
                        updatePolicy({
                          ...policy,
                          checkpoints_before:
                            policy.checkpoints_before.includes(selected)
                              ? policy.checkpoints_before.filter(
                                  (id) => id !== selected,
                                )
                              : [...policy.checkpoints_before, selected],
                        })
                      }
                      />
                      Pause before {node.label}
                    </label>
                    <label>
                      <input type="checkbox" checked={visiblePolicy.checkpoints_after.includes(selected)}
                      onChange={() =>
                        updatePolicy({
                          ...policy,
                          checkpoints_after: policy.checkpoints_after.includes(
                            selected,
                          )
                            ? policy.checkpoints_after.filter(
                                (id) => id !== selected,
                              )
                            : [...policy.checkpoints_after, selected],
                        })
                      }
                      />
                      Pause after {node.label}
                    </label>
                    <p>
                      Pauses before: {visiblePolicy.checkpoints_before.map(id => workflow?.nodes.find(value => value.id === id)?.label ?? 'Unavailable module').join(', ') || 'None'}.
                      Pauses after: {visiblePolicy.checkpoints_after.map(id => workflow?.nodes.find(value => value.id === id)?.label ?? 'Unavailable module').join(', ') || 'None'}.
                      Frozen run snapshots do not change.
                    </p>
                  </>
                )}
              </fieldset>
              <WorkflowImporter
                key={`workflow-import:${currentProject?.id}`}
                busy={busy}
                enabled={!!currentProject}
                submit={importWorkflow}
                onEdit={invalidate}
              />
            </>
          )}
          {tab === "results" && <>
            <label>Run version<select aria-label="Run version" value={runId ?? ''} onChange={event=>{invalidate();setRunId(event.target.value||undefined);setRefresh(value=>value+1);}}>
              <option value="">Choose recorded run</option>{history.map(value=><option key={value.id} value={value.id}>{value.name} · {statusLabel(value.status)}</option>)}
            </select></label>
            {history.length>=50&&<button onClick={()=>void action(async()=>{const values=await client.history(currentProject!.id,history.length);setHistory(previous=>[...previous,...values.filter(row=>!previous.some(item=>item.id===row.id))]);})}>More runs</button>}
            {run ? <>
              <p>Batch jobs: {statusLabel(run.status)}{run.scientific_assessment.numerical_state==='partial_or_blocked'?' · scientific results partially complete':''}</p>
              <label>Module<select aria-label="Result object" value={runSelected ? selected : ''} onChange={e=>selectRun(e.target.value)}>
                <option value="">Select module</option>{resultNodes.map(value=><option key={value.id} value={value.id}>{value.label}</option>)}
              </select></label>
              {runSelected?<SelectedResult onAddData={()=>navigateInput('evidence')} run={run} selected={selected} data={nodeData} error={result.error} offset={result.offset}
                onOffset={result.setOffset} onOpenResource={id=>openResource(id,true)} onSelect={selectRun} action={action}/>:<p>Select a recorded module result.</p>}
            </>:<p>No run selected; no example results generated.</p>}
          </>}
          {tab === "compare" && (
            <ComparisonPanel history={history} current={run} />
          )}
          {currentProject && (tab === "artifacts" || resourcesVisited) && (
            <div hidden={tab !== "artifacts"}>
              <ResourceBrowser
                key={`${currentProject.id}:${run?.id ?? "inputs"}`}
                projectId={currentProject.id}
                runId={run?.id}
                revision={currentProject.revision}
                active={tab === "artifacts"}
                initialFileId={resourceFile}
                initialRunScope={resourceRunScope}
                onRegistered={(value) => {
                  project.edit({
                    ...currentProject,
                    files: [...currentProject.files, value.file],
                  });
                  invalidate();
                  setResourceFile(value.file.id);
                  setResourceRunScope(false);
                }}
              />
            </div>
          )}
          {tab === "artifacts" && (
            <button onClick={returnFromResource}>Return to source</button>
          )}
          {(tab === "settings" || tab === "artifacts") && (
            <button onClick={() => setTab("plan")}>Back to Workflow</button>
          )}
          {tab === "settings" && (
            <LocalSettings
              goal={goal} mode={mode} onGoal={value=>{goalChosen.current=true;setGoal(value);invalidate();}} onMode={value=>{setMode(value);localStorage.setItem("fusionlab.planner",value);invalidate();}}
              layout={layout}
              onLayout={view.update}
              info={info}
              onRefresh={() => setInfoRefresh((value) => value + 1)}
            />
          )}
          {tab === "assistant-settings" && <Suspense fallback={<p>Loading Assistant settings…</p>}><AssistantSettings onSaved={()=>{setInfoRefresh(value=>value+1);setPermission(false);invalidate();}}/></Suspense>}
          {tab === "tools" && (
            <Suspense fallback={<p>Loading Tools &amp; extensions…</p>}><ExtensionsPanel
              key={`${info?.workspace_id}:${currentProject?.id}`}
              workspace={info?.workspace_id ?? 'initial'}
              project={currentProject}
              busy={busy}
              action={action}
              onPlan={(workflow) => void importWorkflow(async () => workflow).then(() => setTab("plan"))}
              onOpenResource={(id) => openResource(id, false)}
            /></Suspense>
          )}
        </div>
      </main>
      {inspectorOpen && !view.narrow && (
        <Splitter
          dimension="right"
          value={layout.right}
          {...view.bounds.right}
          defaultValue={view.defaults.right}
          onChange={(value, save) => view.resize("right", value, save)}
        />
      )}
      <aside
        id="workspace-inspector"
        className="workspace-inspector"
        aria-label="Inspector"
      >
        <div className="inspector-heading">
          <span>
            {view.narrow
              ? "Inspector drawer; run controls remain above"
              : "Inspector"}
          </span>
          <button onClick={() => setInspectorOpen(false)}>
            Close inspector
          </button>
        </div>
        <Tabs
          label="Inspector tabs"
          values={[
            { id: "agent", label: "Assistant" },
            { id: "evidence", label: "Inputs / Evidence" },
          ]}
          selected={inspector}
          onChange={setInspector}
        />
        <div className="inspector-content">
          {inspector === "agent" && (
            <AgentPanel
              proposal={proposal}
              projectId={project.saved?.id===currentProject?.id?project.saved?.id:undefined}
              projectRevision={project.saved?.revision}
              context={`${tab === 'inputs' ? 'Inputs and missing data' : tab === 'plan' ? 'Workflow' : tab === 'results' ? 'Recorded results' : 'Workspace'}${node ? ' · '+node.label : ''}`}
              info={info}
              goal={goal}
              objective={objective}
              mode={mode}
              permission={permission}
              busy={busy}
              canPlan={!!currentProject}
              onGoal={(value) => {
                goalChosen.current = true;
                setGoal(value);
                invalidate();
              }}
              onObjective={(value) => {
                setObjective(value);
                invalidate();
              }}
              onMode={(value) => {
                setMode(value);
                invalidate();
              }}
              onPermission={(value) => {
                setPermission(value);
                invalidate();
              }}
              onPropose={() => void propose()}
              onDecision={(value) => void decide(value)}
              onRevise={reviseProposal}
              onOpenProposal={openRecordedProposal}
            />
          )}
          {inspector === "evidence" && (
            <section>
              <h2>Selected object / Source</h2>
              <p>
                {selection?.kind === "proposal-node"
                  ? "Draft proposal; planned inputs only."
                  : runSelected
                    ? run?.name
                    : "No selected run result."}
              </p>
              <p>{node?.label ?? "No stage selected"}</p>
              {node && (
                <>
                  <p>
                    Tool: {node.tool_id} · Dependencies:{" "}
                    {dependencies(node).join(", ") || "None"}
                  </p>
                  <p>Job completion, numerical results, evidence readiness and experimental validation are separate. Missing evidence remains blocked; an accepted plan does not approve scientific parameters.</p>
                  <ModuleScientificStatus summary={runSelected ? run?.nodes.find(value => value.id === selected)?.scientific_summary : undefined}
                    experimentalValidation={runSelected ? run?.scientific_assessment.experimental_validation : undefined}/>
                  <LazyJson
                    value={node.inputs}
                    label="Input bindings (not client scientific flags)"
                  />
                  <LazyJson
                    value={
                      selection?.kind === "proposal-node"
                        ? proposal?.review_identity
                        : run?.tools[node.tool_id]
                    }
                    label="Calculation method and version"
                  />
                </>
              )}
              <p>
                Current draft r{currentProject?.revision ?? "Not recorded"} ·
                Selected frozen input r{run?.project_revision ?? "Not recorded"}
                ; editing the draft does not overwrite a frozen run.
              </p>
              {currentProject && (
                <InputDiffPanel
                  project={currentProject}
                  runId={run?.id}
                  dirty={project.dirty}
                />
              )}
              <LazyJson
                value={
                  currentProject?.scientific_project?.config
                    .experimental_context
                }
                label="Authoritative scientific conditions"
              />
              <p aria-label="Loaded result identity">
                {nodeData
                  ? `Loaded: ${node?.label ?? "Stage result"} · attempt ${nodeData.node.attempts} · candidate page ${Math.floor(nodeData.offset / 20) + 1}`
                  : "Selected result not loaded; other stage values are not shown."}
              </p>
              <LazyJson
                value={nodeData?.node.output}
                label="Current result page values / Unit / Source"
              />
              <button onClick={() => setTab("inputs")}>
                Locate inputs and sources
              </button>
              <button
                disabled={!run || !selected}
                onClick={() => setTab("results")}
              >
                Locate stage result
              </button>
            </section>
          )}
        </div>
      </aside>
      {bottomOpen && (
        <Splitter
          dimension="bottom"
          value={layout.bottom}
          {...view.bounds.bottom}
          defaultValue={view.defaults.bottom}
          onChange={(value, save) => view.resize("bottom", value, save)}
        />
      )}
      <section
        id="workspace-bottom"
        className="workspace-bottom"
        aria-label="Jobs and actions"
      >
        <Tabs
          label="Bottom panel tabs"
          values={[
            { id: "queue", label: "Jobs" },
            { id: "events", label: "Output" },
            { id: "problems", label: "Problems" },
          ]}
          selected={bottom}
          onChange={setBottom}
        />
        <div className="bottom-content">
          {bottom === "queue" && (
            <>
              <p>
                Workspace jobs: {show(info?.resources.active_tasks)} Execution /{" "}
                {show(info?.resources.queued_tasks)} Queued · CPU pool{" "}
                {info?.max_workers ?? "Not recorded"} · GPU slots{" "}
                {show(info?.resources.gpu_slots)} · Hard memory limits
                unsupported
              </p>
              <table>
                <thead>
                  <tr>
                    <th>Job / Frozen input</th>
                    <th>Actual status</th>
                    <th>Control request</th>
                    <th>Scope</th>
                  </tr>
                </thead>
                <tbody>
                  {run && (
                    <tr>
                      <td>
                        {run.name} · Inputs {run.project_revision}
                      </td>
                      <td>{statusLabel(run.status)}</td>
                      <td>{run.control ?? "None"}</td>
                      <td>
                        {run.workflow.execution_policy.target_node_id ??
                          "Authorized plan"}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </>
          )}
          {bottom === "events" && (
            <table>
              <thead>
                <tr>
                  <th>Sequence number</th>
                  <th>Node</th>
                  <th>Actual event</th>
                  <th>Public status / Reason</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.seq}>
                    <td>{event.seq}</td>
                    <td>{event.node_id ?? "Run"}</td>
                    <td>{event.event}</td>
                    <td>{show(event.payload)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {bottom==="queue"&&run&&<table aria-label="Execution jobs"><thead><tr><th>Step</th><th>Status</th><th>Output / log</th></tr></thead><tbody>{run.nodes.map(job=><tr key={job.id}><td>{job.label}</td><td>{statusLabel(job.status)}</td><td><button onClick={()=>{selectRun(job.id);setBottom('problems');}}>View diagnostic</button></td></tr>)}</tbody></table>}
          {bottom === "problems" && (
            <>
              {nodeData?.node.error && <section aria-label="Selected module problem">
                <h3>{node?.label ?? 'Selected module'} — job problem</h3>
                <p>{typeof nodeData.node.error.message === 'string' ? nodeData.node.error.message : 'The job failed; its private backend diagnostic is retained.'}</p>
                {Array.isArray(nodeData.node.error.actions) && <ul>{nodeData.node.error.actions.filter((value): value is string => typeof value === 'string').map((value, index) => <li key={index}>{value}</li>)}</ul>}
                <p>Non-idempotent interruptions require reconciliation of the original job. Tool or input changes require a new reviewed iteration.</p>
              </section>}
              <InputIssues
                result={projectCheck}
                stale={checkStale}
                onLocate={openInput}
              />
              <p>
                {error ||
                  "No current public  API error; not proof of evidence completeness."}
              </p>
              <p>
                Proposal: {proposal?.status ?? "Not generated"} · Scientific
                parameters/measurement approvals: only explicit existing records
                apply; accepting a proposal does not approve parameters.
              </p>
              {proposal?.missing_inputs.map((item) => (
                <p key={item}>{item}</p>
              ))}
              <button
                disabled={!proposal || proposal.status !== "proposed"}
                onClick={() => void decide("reject")}
              >
                Stop / Reject current Agent Proposal
              </button>
              <p>
                Use Cancel run for numerical jobs; proposals and runs are
                different objects.
              </p>
            </>
          )}
        </div>
      </section>
      <footer className="workbench-footer">
        <span>
          {busy
            ? "Working"
            : stopped
              ? "Run "+run.status.replaceAll("_", " ")
              : executing
                ? "Backend executing"
                : "Ready"}
        </span>
      </footer>
    </div>
  );
}
