import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import type {
  ImportView,
  ProjectView,
  ProposalView,
  RunListView,
  RuntimeInfoView,
  ScientificPrecheckView,
  Workflow,
  WorkflowDocument,
} from "../contracts/generated";
import type { ExecutionPolicy } from "../contracts/Workflow.generated";
import type { Goal } from "../types";
import * as client from "./client";
import { useProject } from "./useProject";
import { useRun } from "./useRun";
import { useSelectedResult } from "./useSelectedResult";
import { useWorkbenchLayout } from "./useWorkbenchLayout";
import { useDocuments, type DocumentId } from "./useDocuments";
import { usePlanController } from "./usePlanController";
import { matchesRun, selectRunNode, type Selection } from "./selection";
import { dependencies, statusLabel } from "./PlanPanel";
import { WorkflowWorkspace } from "./WorkflowWorkspace";
import { AgentPanel } from "./AgentPanel";
import { InputEditor } from "./InputEditor";
import { InputIssues, type InputIssue } from "./PrecheckPanel";
import { SelectedResult } from "./SelectedResult";
import type { ResultViewState } from "../ScientificResults";
import { ComparisonPanel } from "./ComparisonPanel";
import { FileDocument, type FileContext } from "./FileDocument";
import { RunPanel } from "./RunPanel";
import { Splitter } from "./Splitter";
import { WorkbenchMenus } from "./WorkbenchMenus";
import "./workbench.css";
const MethodPanel = lazy(() =>
  import("./MethodPanel").then((m) => ({ default: m.MethodPanel })),
);
const Settings = lazy(() =>
  import("./LocalSettings").then((m) => ({ default: m.LocalSettings })),
);
const Extensions = lazy(() =>
  import("./ExtensionsPanel").then((m) => ({ default: m.ExtensionsPanel })),
);

const homeTabs = [
  { id: "inputs", label: "Inputs" },
  { id: "plan", label: "Workflow" },
  { id: "results", label: "Results" },
] as const;
const extraLabels: Record<string, string> = {
  tools: "Tools",
  settings: "Settings",
  compare: "Compare",
  help: "Help",
};
export function WorkspaceShell() {
  const [error, setError] = useState(""),
    [pending, setPending] = useState(0);
  const fail = useCallback(
    (reason: unknown) =>
      setError(
        reason instanceof Error ? reason.message : "Operation incomplete.",
      ),
    [],
  );
  const project = useProject(fail),
    current = project.draft,
    busy = pending > 0;
  const [runId, setRunId] = useState<string>(),
    [refresh, setRefresh] = useState(0);
  const { run, events } = useRun(runId, current?.id, refresh, fail);
  const [info, setInfo] = useState<RuntimeInfoView>(),
    [infoRefresh, setInfoRefresh] = useState(0),
    [history, setHistory] = useState<RunListView[]>([]);
  const [proposal, setProposal] = useState<ProposalView>(),
    [document, setDocument] = useState<WorkflowDocument>(),
    [selection, setSelection] = useState<Selection>();
  const [goal, setGoal] = useState<Goal>("fusion_screen"),
    [mode, setMode] = useState<"template" | "hybrid">(() =>
      localStorage.getItem("fusionlab.planner") === "hybrid"
        ? "hybrid"
        : "template",
    );
  const [permission, setPermission] = useState(false),
    [policy, setPolicy] = useState<ExecutionPolicy>(client.defaultPolicy);
  const [chatDrafts, setChatDrafts] = useState<Record<string, string>>({});
  const [chatIntents, setChatIntents] = useState<
    Record<string, "new" | "modify">
  >({});
  const objective = chatDrafts[current?.id ?? "new"] ?? "";
  const chatIntent = chatIntents[current?.id ?? "new"] ?? "new";
  const setChatIntent = (value: "new" | "modify") =>
    setChatIntents((values) => ({ ...values, [current?.id ?? "new"]: value }));
  const chatDraftKey =
    info && current
      ? `fusionlab.chat-draft.${info.workspace_id}.${current.id}`
      : undefined;
  const setObjective = (value: string) => {
    setChatDrafts((drafts) => ({ ...drafts, [current?.id ?? "new"]: value }));
    if (chatDraftKey) sessionStorage.setItem(chatDraftKey, value);
  };
  useEffect(() => {
    if (!chatDraftKey || !current) return;
    const text = sessionStorage.getItem(chatDraftKey) ?? "";
    setChatDrafts((values) =>
      Object.hasOwn(values, current.id)
        ? values
        : { ...values, [current.id]: text },
    );
  }, [chatDraftKey]);
  const [inputCheck, setInputCheck] = useState<ScientificPrecheckView>(),
    [inputTarget, setInputTarget] = useState<InputIssue>();
  const [files, setFiles] = useState<Record<string, FileContext>>({}),
    [settingsSection, setSettingsSection] = useState<
      "appearance" | "assistant" | "connection"
    >("appearance");
  const [resultViews, setResultViews] = useState<
    Record<string, ResultViewState>
  >({});
  const [rename, setRename] = useState(false),
    [renameValue, setRenameValue] = useState("");
  const view = useWorkbenchLayout(),
    { layout, bottomOpen, setBottomOpen, inspectorOpen, setInspectorOpen } =
      view;
  const { tab, setTab, openDocuments, closeDocument } = useDocuments(
    info?.workspace_id ?? "initial",
    project.dirty,
    () => setError("Save or discard the input draft first."),
  );
  const plans = usePlanController();
  const iterationSeed = useRef<
    { projectId: string; document: WorkflowDocument } | undefined
  >(undefined);
  const selected =
    selection && selection.kind !== "resource" ? selection.nodeId : "";
  const resultKey = `${runId}:${selected}`;
  const frozen = matchesRun(selection, run, current?.id);
  const workflow = frozen
    ? run?.workflow
    : (document?.workflow ?? proposal?.workflow);
  const node = workflow?.nodes.find((value) => value.id === selected);
  const changed =
    !!document &&
    JSON.stringify(document.workflow) !== JSON.stringify(proposal?.workflow);
  const approved =
    proposal?.status === "accepted" &&
    !changed &&
    !project.dirty &&
    proposal.confirmation?.project_revision === current?.revision;
  const result = useSelectedResult(
    frozen ? run : undefined,
    current?.id,
    frozen ? selected : "",
  );
  const executing = !!run && ["queued", "running"].includes(run.status);
  const m1Dependencies = new Set(
    run?.workflow.nodes
      .filter((n) => n.tool_id === "method.m1.decision")
      .flatMap(dependencies),
  );
  const resultNodes =
    run?.nodes.filter(
      (n) => n.parent_id === null && !m1Dependencies.has(n.id),
    ) ?? [];
  const check =
    current && inputCheck?.project_id === current.id ? inputCheck : undefined;
  const checkStale =
    project.dirty || check?.project_revision !== current?.revision;

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
    plans.invalidate();
    setProposal(undefined);
  }
  useLayoutEffect(() => {
    invalidate();
    setHistory([]);
    setFiles({});
    setInputCheck(undefined);
    setInputTarget(undefined);
    setPermission(false);
    const pendingSeed = iterationSeed.current;
    const seed =
      pendingSeed && pendingSeed.projectId === current?.id
        ? pendingSeed.document
        : undefined;
    iterationSeed.current = undefined;
    setDocument(seed);
    setPolicy(seed?.workflow.execution_policy ?? client.defaultPolicy());
    setSelection(
      seed
        ? {
            kind: "proposal-node",
            proposalId: seed.id,
            nodeId: seed.selected_node_id ?? seed.workflow.nodes[0].id,
          }
        : undefined,
    );
    setGoal(
      current?.scientific_project ? "scientific_pipeline" : "fusion_screen",
    );
    setRunId(
      current
        ? (localStorage.getItem(`fusionlab.run.${current.id}`) ?? undefined)
        : undefined,
    );
  }, [current?.id]);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const value = await client.info(controller.signal);
        if (controller.signal.aborted) return;
        setInfo(value);
        if (executing || value.capabilities.scientific_mcp === "checking")
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
  }, [executing, infoRefresh, fail]);
  useEffect(() => {
    if (!current || project.saved?.id !== current.id) return;
    const controller = new AbortController();
    void client
      .history(current.id, 0, controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setHistory(value);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) fail(reason);
      });
    return () => controller.abort();
  }, [current?.id, project.saved?.id, run?.status, fail]);
  useEffect(() => {
    if (
      tab === "results" &&
      run &&
      (!frozen || !resultNodes.some((n) => n.id === selected))
    )
      setSelection(selectRunNode(run, resultNodes[0]?.id ?? ""));
  }, [tab, run?.id, run?.state_version, frozen, selected]);
  useEffect(() => {
    if (run?.status === "succeeded") setBottomOpen(false);
    else if (run?.status === "failed") setBottomOpen(true);
  }, [run?.status]);
  function selectRun(id: string) {
    if (run) setSelection(selectRunNode(run, id));
  }
  function selectPlan(id: string) {
    if (frozen) selectRun(id);
    else
      setSelection({
        kind: "proposal-node",
        proposalId: proposal?.id ?? document?.id ?? "",
        nodeId: id,
      });
  }
  function openSettings(section: "appearance" | "assistant" | "connection") {
    setSettingsSection(section);
    setTab("settings");
  }
  function showProposal(value: ProposalView) {
    setProposal(value);
    setInspectorOpen(true);
    if (!document && !frozen && value.workflow)
      setSelection({
        kind: "proposal-node",
        proposalId: value.id,
        nodeId: value.workflow.nodes[0].id,
      });
  }
  async function requestPlan(
    request: (saved: ProjectView) => Promise<ProposalView>,
    publish: (value: ProposalView) => void = showProposal,
  ) {
    await action(() =>
      plans.guarded(project.generation, project.save, request, publish),
    );
  }
  async function propose() {
    await requestPlan(
      (saved) =>
        client.propose(saved.id, goal, objective, mode, policy, permission),
      (value) => {
        showProposal(value);
        setObjective("");
      },
    );
  }
  async function proposeMethod(
    method: Parameters<typeof client.planMethod>[1],
  ) {
    await requestPlan((saved) => client.planMethod(saved.id, method));
  }
  async function proposeWorkflow(value: Workflow) {
    await requestPlan((saved) =>
      client.proposeCustom(saved.id, value, objective),
    );
  }
  async function reviewWorkflow() {
    if (proposal?.status === "proposed") {
      setInspectorOpen(true);
      return;
    }
    if (workflow && !frozen) return proposeWorkflow(workflow);
    return propose();
  }
  async function decide(decision: "accept" | "reject") {
    if (!proposal || !current) return;
    const stamp = plans.generation.current;
    await action(async () => {
      const value = await client.decide(proposal.id, decision);
      if (stamp !== plans.generation.current) return;
      if (decision === "accept" && value.workflow) {
        const nextSelected = value.workflow.nodes.some((n) => n.id === selected)
          ? selected
          : value.workflow.nodes[0].id;
        const existing =
          document?.workflow.id === value.workflow.id ? document : undefined;
        const positions = Object.fromEntries(
          Object.entries(existing?.layout ?? {}).filter(([id]) =>
            value.workflow!.nodes.some((n) => n.id === id),
          ),
        );
        const saved = await client.saveWorkflowDocument(
          current.id,
          existing?.id ?? value.id,
          {
            workflow: value.workflow,
            layout: positions,
            selected_node_id: nextSelected,
            view: existing?.view ?? "graph",
          },
          current.revision,
          existing?.revision,
        );
        if (stamp !== plans.generation.current) return;
        setDocument(saved);
        setPolicy(saved.workflow.execution_policy);
        setSelection({
          kind: "proposal-node",
          proposalId: value.id,
          nodeId: nextSelected,
        });
      }
      setProposal(value);
    });
  }
  async function revise(prompt: string) {
    if (!proposal) return;
    const stamp = plans.generation.current;
    await action(async () => {
      const value = await client.revise(
        proposal.id,
        prompt,
        document?.workflow,
      );
      if (stamp !== plans.generation.current) return;
      showProposal(value);
      setObjective("");
    });
  }
  async function openProposal(id: string) {
    const stamp = plans.generation.current;
    await action(async () => {
      const value = await client.proposal(id);
      if (
        stamp === plans.generation.current &&
        value.project_id === current?.id
      )
        showProposal(value);
    });
  }
  async function start() {
    if (!proposal || !approved) return;
    const stamp = project.generation.current;
    await action(async () => {
      const value = await client.start(proposal);
      if (stamp !== project.generation.current) return;
      setRunId(value.id);
      setSelection(selectRunNode(value, value.nodes[0]?.id ?? ""));
      setProposal(undefined);
      setRefresh((value) => value + 1);
      setBottomOpen(true);
      setTab("plan");
    });
  }
  async function control(kind: "pause" | "cancel" | "resume" | "retry") {
    if (!run) return;
    const id = run.id;
    await action(async () => {
      await client.control(id, kind, kind === "retry" ? selected : undefined);
      if (runId === id) setRefresh((value) => value + 1);
    });
  }
  async function checkInputs() {
    await action(async () => {
      const stamp = project.generation.current,
        saved = await project.save();
      if (!saved || stamp !== project.generation.current) return;
      const value = await client.precheck(saved.id);
      if (stamp !== project.generation.current) return;
      if (value.project_revision !== saved.revision)
        throw Error("Inputs changed. Check the saved version again.");
      setInputCheck(value);
      setInspectorOpen(true);
    });
  }
  async function saveParameter(value: ProjectView) {
    const stamp = project.generation.current;
    const saved = await client.save(value, project.saved?.revision);
    if (stamp !== project.generation.current) return;
    project.adopt(saved);
    invalidate();
  }
  async function reviewParameter(
    id: string,
    stage: "m3" | "m4",
    name: string,
    reviewer: string,
    reason: string,
  ) {
    setPending((value) => value + 1);
    setError("");
    try {
      await plans.guarded(
        project.generation,
        project.save,
        (saved) => {
          const value = saved as ProjectView;
          return client.reviewParameter(
            value.id,
            id,
            stage,
            name,
            reviewer,
            reason,
            value.revision,
          );
        },
        (value) => {
          project.adopt(value);
          invalidate();
        },
      );
    } catch (reason) {
      fail(reason);
      throw reason;
    } finally {
      setPending((value) => value - 1);
    }
  }
  async function replaceScalar(prepared: Workflow) {
    if (!current || !document || frozen)
      throw Error("Open an editable workflow first.");
    const stamp = project.generation.current,
      revised = structuredClone(document.workflow),
      target = revised.nodes.find((n) => n.id === selected)!;
    if (target.tool_id !== prepared.nodes[0].tool_id)
      throw Error(
        "Create and review a separate plan to change the calculation tool.",
      );
    target.inputs = prepared.nodes[0].inputs;
    target.label = prepared.nodes[0].label;
    const value = await client.saveWorkflowDocument(
      current.id,
      document.id,
      {
        workflow: revised,
        layout: document.layout,
        selected_node_id: selected,
        view: document.view,
      },
      current.revision,
      document.revision,
    );
    if (stamp !== project.generation.current) return;
    setDocument(value);
    invalidate();
  }
  async function editAsNewRun() {
    if (!run || !frozen) return;
    const source = run;
    await action(async () => {
      if (project.dirty)
        throw Error("Save or discard input edits before creating a new run.");
      const value = await client.iteration(source.id);
      const doc = await client.saveWorkflowDocument(
        value.project.id,
        "next-run-" + source.id,
        {
          workflow: value.workflow ?? source.workflow,
          layout: {},
          selected_node_id: selected,
          view: "graph",
        },
        value.project.revision,
      );
      iterationSeed.current = { projectId: value.project.id, document: doc };
      project.adopt(value.project);
      setTab("plan");
    });
  }
  async function updatePolicy(value: ExecutionPolicy) {
    if (frozen) return;
    setPolicy(value);
    if (!current || !document) {
      invalidate();
      return;
    }
    await action(async () => {
      const saved = await client.saveWorkflowDocument(
        current.id,
        document.id,
        {
          workflow: { ...document.workflow, execution_policy: value },
          layout: document.layout,
          selected_node_id: document.selected_node_id,
          view: document.view,
        },
        current.revision,
        document.revision,
      );
      setDocument(saved);
      invalidate();
    });
  }
  function openInput(issue: InputIssue) {
    setInputTarget(issue);
    setTab("inputs");
  }
  function openFile(fileId: string, context: Partial<FileContext> = {}) {
    const id = `file:${context.runId ?? "input"}:${fileId}` as DocumentId;
    const name =
      context.name ??
      current?.files.find((file) => file.id === fileId)?.name ??
      current?.scientific_project?.evidence_files.find(
        (file) => file.id === fileId,
      )?.name ??
      "Result file";
    setFiles((values) => ({
      ...values,
      [id]: {
        fileId,
        name,
        origin:
          tab === "results" ? "results" : tab === "tools" ? "tools" : "inputs",
        ...context,
      },
    }));
    setTab(id);
  }
  function registered(value: ImportView) {
    if (current)
      void action(async () => {
        const stamp = project.generation.current;
        const saved = await client.save(
          { ...current, files: [...current.files, value.file] },
          project.saved?.revision,
        );
        if (stamp === project.generation.current) {
          project.adopt(saved);
          invalidate();
        }
      });
  }
  const [switchTo, setSwitchTo] = useState<string>();
  function chooseProject(id: string) {
    if (project.dirty) {
      setSwitchTo(id);
      return;
    }
    setTab("inputs");
    if (id === "new") project.new();
    else void project.choose(id);
  }
  async function switchProject(save: boolean) {
    const id = switchTo;
    if (!id) return;
    if (save) await project.save();
    setSwitchTo(undefined);
    setTab("inputs");
    if (id === "new") project.new();
    else await project.choose(id);
  }
  const runLabel =
    executing && frozen
      ? "Stop"
      : approved
        ? "Run"
        : workflow && !frozen
          ? "Review changes"
          : "Create plan";
  function primary() {
    if (executing && frozen) void control("cancel");
    else if (runLabel === "Run") void start();
    else void reviewWorkflow();
  }
  const file = files[tab];
  const labels = [
    ...homeTabs,
    ...openDocuments
      .filter(
        (id) =>
          !homeTabs.some((home) => home.id === id) &&
          (!id.startsWith("file:") || files[id]),
      )
      .map((id) => ({ id, label: files[id]?.name ?? extraLabels[id] ?? id })),
  ];
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
              action: () => chooseProject("new"),
            },
            {
              label: "Import",
              disabled: busy || !current,
              action: () => {
                setTab("inputs");
                requestAnimationFrame(() =>
                  window.document.getElementById("input-import-file")?.click(),
                );
              },
            },
            {
              label: "Rename project",
              disabled: !current,
              action: () => {
                setRenameValue(current?.name ?? "");
                setRename(true);
              },
            },
            {
              label: "Save",
              disabled: busy || !current,
              action: () => void action(project.save),
            },
          ]}
          view={[
            {
              label: "Assistant",
              action: () => setInspectorOpen((value) => !value),
            },
            {
              label: "Jobs panel",
              action: () => setBottomOpen((value) => !value),
            },
          ]}
          tools={[
            { label: "Tools & extensions", action: () => setTab("tools") },
            { label: "Settings", action: () => openSettings("appearance") },
          ]}
          help={[
            { label: "Scientific boundaries", action: () => setTab("help") },
          ]}
        />
        <select
          aria-label="Current project"
          value={current?.id ?? ""}
          disabled={project.loading}
          onChange={(event) => chooseProject(event.target.value)}
        >
          <option value="" disabled>
            Select or create a project
          </option>
          {current &&
            !project.summaries.some((row) => row.id === current.id) && (
              <option value={current.id}>{current.name}</option>
            )}
          {project.summaries.map((row) => (
            <option key={row.id} value={row.id}>
              {row.name}
            </option>
          ))}
        </select>
        <span className="workspace-state">
          {info ? "Connected" : "Connecting"}
        </span>
      </header>
      <main className="workspace-center">
        <div
          role="tablist"
          aria-label="Workspace documents"
          className="document-tabs"
          onKeyDown={(event) => {
            if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key))
              return;
            event.preventDefault();
            const index = labels.findIndex((item) => item.id === tab);
            const next =
              event.key === "Home"
                ? 0
                : event.key === "End"
                  ? labels.length - 1
                  : (index +
                      (event.key === "ArrowRight" ? 1 : -1) +
                      labels.length) %
                    labels.length;
            setTab(labels[next].id as DocumentId);
            event.currentTarget
              .querySelectorAll<HTMLButtonElement>("[role=tab]")
              [next]?.focus();
          }}
        >
          {labels.map((item) => (
            <span
              className={`workbench-tab ${tab === item.id ? "selected" : ""}`}
              key={item.id}
            >
              <button
                role="tab"
                tabIndex={tab === item.id ? 0 : -1}
                aria-selected={tab === item.id}
                onClick={() => setTab(item.id as DocumentId)}
              >
                {item.label}
              </button>
              {!homeTabs.some((home) => home.id === item.id) && (
                <button
                  aria-label={`Close ${item.label}`}
                  onClick={() => {
                    closeDocument(item.id as DocumentId);
                    if (tab === item.id && files[item.id]?.origin)
                      setTab(files[item.id].origin!);
                  }}
                >
                  ×
                </button>
              )}
            </span>
          ))}
        </div>
        <div className="workspace-content" role="tabpanel">
          {error && (
            <div className="error-strip" role="alert">
              {error}
              <button onClick={() => setError("")}>Dismiss</button>
            </div>
          )}
          {rename && (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                if (current) {
                  project.edit({ ...current, name: renameValue });
                  invalidate();
                  setRename(false);
                }
              }}
            >
              <label>
                Project name
                <input
                  aria-label="Project name"
                  value={renameValue}
                  onChange={(event) => setRenameValue(event.target.value)}
                />
              </label>
              <button>Rename</button>
              <button type="button" onClick={() => setRename(false)}>
                Cancel
              </button>
            </form>
          )}
          {switchTo && (
            <section role="dialog" aria-label="Unsaved input changes">
              <p>The input draft has unsaved changes.</p>
              <button onClick={() => void action(() => switchProject(true))}>
                Save and continue
              </button>
              <button onClick={() => void switchProject(false)}>
                Discard and continue
              </button>
              <button onClick={() => setSwitchTo(undefined)}>Cancel</button>
            </section>
          )}
          {project.loading ? (
            <p>Loading project…</p>
          ) : (
            current && (
              <div hidden={tab !== "inputs"}>
                <InputEditor
                  key={current.id}
                  project={current}
                  persisted={project.saved?.id === current.id}
                  busy={busy}
                  dirty={project.dirty}
                  onChange={(value) => {
                    project.edit(value);
                    invalidate();
                  }}
                  action={action}
                  inputCheck={check}
                  checkStale={checkStale}
                  onCheck={() => void checkInputs()}
                  onLocate={openInput}
                  inputTarget={inputTarget}
                  onOpenResource={(id) => openFile(id)}
                  onPlanMethod={(method) => void proposeMethod(method)}
                  prepareImport={project.save}
                  onImported={(value) => {
                    project.adopt(value);
                    if (value.scientific_project && !current.scientific_project)
                      setGoal("scientific_pipeline");
                    invalidate();
                  }}
                />
              </div>
            )
          )}
          {tab === "plan" && (
            <>
              <section
                className="workflow-run-controls"
                aria-label="Workflow run controls"
              >
                <button
                  disabled={busy || !current || (frozen && !executing)}
                  onClick={primary}
                >
                  {runLabel}
                </button>
                {executing && frozen && (
                  <button
                    disabled={busy || !!run?.control}
                    onClick={() => void control("pause")}
                  >
                    Pause
                  </button>
                )}
                {frozen &&
                  run &&
                  ["paused", "interrupted"].includes(run.status) && (
                    <button
                      disabled={busy}
                      onClick={() => void control("resume")}
                    >
                      Resume
                    </button>
                  )}
                {frozen && !executing && (
                  <button disabled={busy} onClick={() => void editAsNewRun()}>
                    Edit as new run
                  </button>
                )}
                {!workflow && (
                  <label>
                    Task
                    <select
                      aria-label="Analysis task"
                      value={goal}
                      onChange={(event) => {
                        setGoal(event.target.value as Goal);
                        invalidate();
                      }}
                    >
                      <option value="fusion_screen">Sequence statistics</option>
                      <option value="m1_sequence_checks">M1 checks</option>
                      <option value="scientific_pipeline">M1–M4</option>
                      <option value="assembly_review">Assembly</option>
                      <option value="pathway_simulation">Pathway</option>
                    </select>
                  </label>
                )}
                {workflow && !frozen && (
                  <label>
                    Run through
                    <select
                      aria-label="Run through module"
                      disabled={busy || !document}
                      value={policy.target_node_id ?? ""}
                      onChange={(event) =>
                        void updatePolicy({
                          ...policy,
                          target_node_id: event.target.value || null,
                        })
                      }
                    >
                      <option value="">All modules</option>
                      {workflow.nodes.map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.label}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                {workflow && frozen && (
                  <span>
                    Recorded scope:{" "}
                    {workflow.nodes.find(
                      (node) =>
                        node.id === workflow.execution_policy.target_node_id,
                    )?.label ?? "All modules"}
                    ; task budget {workflow.execution_policy.max_tool_calls}.
                  </span>
                )}
              </section>
              <WorkflowWorkspace
                key={current?.id}
                projectId={current?.id}
                projectRevision={current?.revision}
                seedId={frozen ? run?.id : !document ? proposal?.id : undefined}
                seed={
                  frozen
                    ? run?.workflow
                    : !document
                      ? (proposal?.workflow ?? undefined)
                      : undefined
                }
                document={document}
                frozen={frozen}
                busy={busy || project.dirty}
                inputCheck={checkStale ? undefined : check}
                run={frozen ? run : undefined}
                selected={selected}
                onSelect={selectPlan}
                onDocument={(value) => {
                  if (
                    document &&
                    value.semantic_revision !== document.semantic_revision
                  )
                    invalidate();
                  setDocument(value);
                  setPolicy(value.workflow.execution_policy);
                  setSelection({
                    kind: "proposal-node",
                    proposalId: proposal?.id ?? value.id,
                    nodeId:
                      value.selected_node_id ?? value.workflow.nodes[0].id,
                  });
                }}
              />
              {node && current && (
                <Suspense fallback={<p>Opening method…</p>}>
                  <MethodPanel
                    key={node.id}
                    project={current}
                    toolId={node.tool_id}
                    runId={frozen ? run?.id : undefined}
                    workflowId={document?.id}
                    nodeId={node.id}
                    workflow={workflow ?? undefined}
                    disabled={busy || project.dirty}
                    onChange={saveParameter}
                    onReview={reviewParameter}
                    onWorkflowChange={replaceScalar}
                    onEditDraft={() => void editAsNewRun()}
                    onPlan={(value) => void proposeWorkflow(value)}
                  />
                </Suspense>
              )}
            </>
          )}
          {tab === "results" && (
            <section>
              <header className="panel-heading">
                <h2>Results</h2>
                <button disabled={!run} onClick={() => setTab("compare")}>
                  Compare
                </button>
              </header>
              <label>
                Run version
                <select
                  aria-label="Run version"
                  value={runId ?? ""}
                  onChange={(event) => {
                    setRunId(event.target.value || undefined);
                    setSelection(undefined);
                  }}
                >
                  <option value="">Choose a run</option>
                  {history.map((value) => (
                    <option key={value.id} value={value.id}>
                      {value.name} — {statusLabel(value.status)}
                    </option>
                  ))}
                </select>
              </label>
              {history.length >= 50 && (
                <button
                  onClick={() =>
                    void action(async () => {
                      const values = await client.history(
                        current!.id,
                        history.length,
                      );
                      setHistory((previous) => previous.concat(values));
                    })
                  }
                >
                  Earlier runs
                </button>
              )}
              {run && resultNodes.length > 1 && (
                <label>
                  Module
                  <select
                    aria-label="Result object"
                    value={frozen ? selected : ""}
                    onChange={(event) => selectRun(event.target.value)}
                  >
                    {resultNodes.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.label}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {run && frozen ? (
                <SelectedResult
                  run={run}
                  selected={selected}
                  data={result.data}
                  error={result.error}
                  offset={result.offset}
                  onOffset={result.setOffset}
                  onSelect={selectRun}
                  action={action}
                  viewState={resultViews[resultKey]}
                  onViewChange={(value) =>
                    setResultViews((previous) => ({
                      ...previous,
                      [resultKey]: { ...previous[resultKey], ...value },
                    }))
                  }
                  onAddData={() => setTab("inputs")}
                  onOpenResource={(id, context) =>
                    openFile(id, { runId: run.id, ...context })
                  }
                />
              ) : (
                <p>No recorded result selected.</p>
              )}
            </section>
          )}
          {tab === "compare" && (
            <ComparisonPanel history={history} current={run} />
          )}
          {file && current && (
            <FileDocument
              projectId={current.id}
              revision={current.revision}
              file={file}
              project={current}
              onRegistered={registered}
            />
          )}
          {tab === "settings" && (
            <Suspense fallback={<p>Opening Settings…</p>}>
              <Settings
                layout={layout}
                onLayout={view.update}
                info={info}
                onRefresh={() => setInfoRefresh((value) => value + 1)}
                mode={mode}
                onMode={(value) => {
                  setMode(value);
                  localStorage.setItem("fusionlab.planner", value);
                }}
                section={settingsSection}
                onSection={setSettingsSection}
              />
            </Suspense>
          )}
          {tab === "tools" && (
            <Suspense fallback={<p>Opening tools…</p>}>
              <Extensions
                key={`${info?.workspace_id}:${current?.id}`}
                workspace={info?.workspace_id ?? "initial"}
                project={current}
                persisted={project.saved?.id === current?.id}
                busy={busy}
                action={action}
                onMethod={(method) => void proposeMethod(method)}
                onPlan={(value) => void proposeWorkflow(value)}
                onOpenResource={(id, context) => openFile(id, context)}
              />
            </Suspense>
          )}
          {tab === "help" && (
            <section>
              <h2>Scientific boundaries</h2>
              <p>
                Job completion, numerical results, evidence readiness and
                experimental validation are separate. Missing evidence remains
                blocked; an accepted plan does not approve scientific
                parameters.
              </p>
              <p>
                Import data in Inputs. Edit model inputs and methods in
                Workflow. Review the proposed change once, then Run. Results
                retain the model and input version actually used.
              </p>
              <p>
                Synthetic examples and exploratory formulas are not experimental
                validation. Restricted predictors require legal access; missing
                inputs are never filled with invented values.
              </p>
              <a
                href="https://gitlab.igem.org/2026/software/tsinghua-t/galatea/-/blob/develop/README.md"
                target="_blank"
                rel="noreferrer"
              >
                Installation, CLI and method documentation
              </a>
            </section>
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
      {inspectorOpen && (
        <aside
          id="workspace-inspector"
          className="workspace-inspector"
          aria-label="Assistant"
        >
          <header className="inspector-heading">
            <strong>Assistant</strong>
            <button onClick={() => setInspectorOpen(false)}>
              Close Assistant
            </button>
          </header>
          <div className="inspector-content">
            <AgentPanel
              proposal={proposal}
              projectId={
                project.saved?.id === current?.id
                  ? project.saved?.id
                  : undefined
              }
              projectRevision={project.saved?.revision}
              info={info}
              context={
                tab === "plan"
                  ? `Workflow${node ? " — " + node.label : ""}`
                  : tab === "results"
                    ? "Recorded results"
                    : file
                      ? file.name
                      : tab === "inputs"
                        ? "Input data"
                        : "Workspace"
              }
              objective={objective}
              mode={mode}
              permission={permission}
              busy={busy}
              canPlan={!!current}
              intent={chatIntent}
              onIntent={setChatIntent}
              onObjective={setObjective}
              onPermission={setPermission}
              onPropose={() => void propose()}
              onDecision={(value) => void decide(value)}
              onRevise={revise}
              onOpenProposal={openProposal}
              onSettings={() => openSettings("assistant")}
              inputCheck={
                <>
                  <button
                    disabled={busy || !current}
                    onClick={() => void checkInputs()}
                  >
                    Check inputs
                  </button>
                  {check && !checkStale && (
                    <InputIssues
                      result={check}
                      stale={false}
                      onLocate={openInput}
                    />
                  )}
                </>
              }
            />
            {approved && (
              <button disabled={busy} onClick={() => void start()}>
                Run approved task
              </button>
            )}
          </div>
        </aside>
      )}
      {bottomOpen && (
        <>
          <Splitter
            dimension="bottom"
            value={layout.bottom}
            {...view.bounds.bottom}
            defaultValue={view.defaults.bottom}
            onChange={(value, save) => view.resize("bottom", value, save)}
          />
          <RunPanel
            run={run}
            events={events}
            data={result.data}
            error={result.error ?? ""}
            selected={selected}
            onSelect={selectRun}
            onControl={(kind) => void control(kind)}
          />
        </>
      )}
      <footer className="workbench-footer">
        <span>
          {busy
            ? "Working"
            : run && executing
              ? `${statusLabel(run.status)} — ${run.nodes.filter((n) => n.status === "succeeded").length}/${run.nodes.length} tasks`
              : run
                ? `Last run: ${statusLabel(run.status)}`
                : "Ready"}
          {project.dirty ? " — Unsaved input edits" : ""}
        </span>
      </footer>
    </div>
  );
}
