import { useEffect, useRef, useState } from "react";
import * as api from "./api";
import type {
  Goal,
  ImportPreview,
  PluginInspection,
  Project,
  Run,
  RunSummary,
  RuntimeInfo,
  Tool,
  Workflow,
  PlanBinding,
} from "./types";
import "./styles.css";
import { ScientificResults, ResultComparison, nodeTool, sequenceOutput } from "./ScientificResults";
import { ScientificProjectPanel } from "./ScientificProjectPanel";
import { DesktopConnectionPanel } from "./DesktopConnectionPanel";

type Page =
  | "Dashboard"
  | "Project"
  | "Analysis"
  | "Results"
  | "History"
  | "Tools"
  | "Settings"
  | "Developer";
const pages: { id: Page; label: string; icon: string }[] = [
  { id: "Dashboard", label: "工作台", icon: "◈" },
  { id: "Project", label: "项目数据", icon: "▦" },
  { id: "Analysis", label: "分析流程", icon: "↗" },
  { id: "Results", label: "分析结果", icon: "◴" },
  { id: "History", label: "分析历史", icon: "◷" },
  { id: "Tools", label: "工具库", icon: "◇" },
  { id: "Settings", label: "设置", icon: "⚙" },
];
const labels: Record<string, string> = {
  queued: "准备中",
  running: "运行中",
  succeeded: "作业完成",
  failed: "需要处理",
  paused: "已暂停",
  interrupted: "已中断",
  cancelled: "已取消",
  pending: "等待上游",
  blocked: "需要处理",
};
const goalLabels: Record<Goal, string> = {
  fusion_screen: "分析融合蛋白序列",
  assembly_review: "核验自组装组成",
  pathway_simulation: "模拟上传的反应通路",
  scientific_pipeline: "M1–M5 原式科学项目管线",
};
const terminal = new Set(["succeeded", "failed", "paused", "cancelled"]);
const newProject = (): Project => ({
  id: crypto.randomUUID(),
  name: "新的融合蛋白项目",
  revision: 1,
  description: "",
  sequences: [],
  assemblies: [],
  conditions: {},
  pathway: null,
  files: [],
  datasets: [],
});

export default function App() {
  const [page, setPage] = useState<Page>("Dashboard");
  const [developer, setDeveloper] = useState(
    localStorage.getItem("fusionlab.mode") === "developer",
  );
  const [projects, setProjects] = useState<Project[]>([]);
  const [project, setProjectState] = useState<Project>();
  const projectRef = useRef<Project | undefined>(undefined);
  const editGeneration = useRef(0);
  const [tools, setTools] = useState<Tool[]>([]);
  const [history, setHistory] = useState<RunSummary[]>([]);
  const [run, setRun] = useState<Run>();
  const [info, setInfo] = useState<RuntimeInfo>();
  const [workflow, setWorkflow] = useState<Workflow>();
  const [confirmation, setConfirmation] = useState<PlanBinding>();
  const [objective, setObjective] = useState("");
  const [goal, setGoal] = useState<Goal>("fusion_screen");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<ImportPreview>();
  const [inputKind, setInputKind] = useState("auto");
  const [compare, setCompare] = useState<Run[]>([]);
  const savedProject = projects.find((item) => item.id === project?.id);
  const dirty = !!project && JSON.stringify(project) !== JSON.stringify(savedProject);

  function setProject(value: Project | undefined) {
    editGeneration.current += 1;
    projectRef.current = value;
    setProjectState(value);
    setWorkflow(undefined);
    setConfirmation(undefined);
  }

  async function action(job: () => Promise<unknown>) {
    setError("");
    setBusy(true);
    try {
      await job();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    let alive = true;
    const generation = editGeneration.current;
    Promise.all([api.getProjects(), api.getTools(), api.getInfo()])
      .then(([items, installed, runtime]) => {
        if (!alive) return;
        setTools(installed);
        setInfo(runtime);
        if (generation === editGeneration.current) {
          setProjects(items);
          setProject(items.find((item) => item.id === localStorage.getItem("fusionlab.project")) ?? items[0]);
        } else {
          setProjects((current) => [...current, ...items.filter((item) => !current.some((known) => known.id === item.id))]);
        }
        const savedRun = localStorage.getItem("fusionlab.run");
        if (savedRun)
          api
            .getRun(savedRun)
            .then((value) => {
              if (alive && projectRef.current?.id === value.project_id) setRun(value);
            })
            .catch(() => localStorage.removeItem("fusionlab.run"));
      })
      .catch((reason) => {
        if (alive) setError(reason.message);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (!project) return;
    localStorage.setItem("fusionlab.project", project.id);
    let alive = true;
    api
      .getRuns(project.id)
      .then((value) => {
        if (alive) setHistory(value);
      })
      .catch((reason) => {
        if (alive) setError(reason.message);
      });
    return () => {
      alive = false;
    };
  }, [project?.id, run?.status]);

  useEffect(() => {
    if (!run) return;
    localStorage.setItem("fusionlab.run", run.id);
    if (terminal.has(run.status)) return;
    let alive = true;
    const timer = window.setInterval(
      () =>
        api
          .getRun(run.id)
          .then((value) => {
            if (alive) setRun(value);
          })
          .catch((reason) => {
            if (alive) setError(reason.message);
          }),
      1200,
    );
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [run?.id, run?.status]);

  async function persist(updated: Project) {
    const generation = editGeneration.current;
    const known = projects.find((item) => item.id === updated.id);
    const saved = await api.saveProject(updated, known?.revision);
    setProjects((items) => [
      saved,
      ...items.filter((item) => item.id !== saved.id),
    ]);
    if (editGeneration.current !== generation) return;
    setProject(saved);
    return saved;
  }

  async function plan() {
    if (!project) return;
    await action(async () => {
      const saved = await persist(project);
      if (!saved) return;
      const generation = editGeneration.current;
      const result = await api.createPlan(saved.id, goal, objective);
      if (generation !== editGeneration.current || projectRef.current?.id !== result.confirmation.project_id ||
          projectRef.current?.revision !== result.confirmation.project_revision) return;
      setWorkflow(result.workflow);
      setConfirmation(result.confirmation);
      setPage("Analysis");
    });
  }

  function selectProject(id: string) {
    setProject(projects.find((item) => item.id === id));
    setWorkflow(undefined);
    setPreview(undefined);
    setRun(undefined);
    setCompare([]);
    localStorage.removeItem("fusionlab.run");
  }

  const activeRun = run?.project_id === project?.id ? run : undefined;
  const isStale =
    activeRun?.status === "running" &&
    !!activeRun.heartbeat &&
    Date.now() - Date.parse(activeRun.heartbeat) > 22000;
  const sequenceCount = project?.sequences.length ?? 0;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={() => setPage("Dashboard")}>
          <span className="brand-mark">F</span>
          <span>
            FusionLab<small>融合蛋白研究工作台</small>
          </span>
        </a>
        <div className="project-switch">
          <span className="eyebrow">CURRENT PROJECT</span>
          <select
            aria-label="当前项目"
            value={project?.id ?? ""}
            onChange={(event) => selectProject(event.target.value)}
          >
            <option value="" disabled>
              选择或创建项目
            </option>
            {projects.map((item) => (
              <option value={item.id} key={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <button
            className="text-button"
            disabled={busy}
            onClick={() =>
              action(async () => {
                await persist(newProject());
                setRun(undefined);
                setPage("Project");
              })
            }
          >
            ＋ 创建项目
          </button>
        </div>
        <nav aria-label="主导航">
          {pages.map((item) => (
            <button
              className={page === item.id ? "nav-item selected" : "nav-item"}
              key={item.id}
              onClick={() => setPage(item.id)}
            >
              <span>{item.icon}</span>
              {item.label}
            </button>
          ))}
          {developer && (
            <button
              className={
                page === "Developer" ? "nav-item selected" : "nav-item"
              }
              onClick={() => setPage("Developer")}
            >
              <span>⌘</span>开发者面板
            </button>
          )}
        </nav>
        <div className="sidebar-bottom">
          <span className="local-indicator" /> {api.backendMode === "ssh" ? "远程服务器 · SQLite" : "Local-first · SQLite"}
          <button
            className="mode-button"
            onClick={() => {
              const value = !developer;
              setDeveloper(value);
              localStorage.setItem(
                "fusionlab.mode",
                value ? "developer" : "scientist",
              );
              if (!value && page === "Developer") setPage("Dashboard");
            }}
          >
            {developer ? "Developer Mode" : "Scientist Mode"} ⇄
          </button>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>
            工作空间 <span className="slash">/</span>{" "}
            {project?.name ?? "尚未创建项目"}
          </span>
          <span className="pill">
            {developer ? "开发者视图" : "实验研究视图"}
          </span>
        </header>
        {error && (
          <div className="error-banner" role="alert">
            {error}
            <button onClick={() => setError("")} aria-label="关闭错误">
              ×
            </button>
          </div>
        )}
        <div className="page-heading">
          <div>
            <span className="eyebrow">FUSION PROTEINS & SELF-ASSEMBLY</span>
            <h1>
              {pages.find((item) => item.id === page)?.label ?? "开发者面板"}
            </h1>
            <p>
              {page === "Dashboard"
                ? "从真实构建出发，把分析、结果和下一轮实验连接起来。"
                : (project?.name ?? "先创建一个项目，然后导入构建序列。")}
            </p>
          </div>
          {project && (
            <span className="revision">项目版本 {project.revision}</span>
          )}
        </div>

        {page === "Dashboard" && (
          <>
            <section className="metrics-grid">
              <Metric
                label="融合蛋白序列"
                value={sequenceCount}
                detail="已确认的项目输入"
              />
              <Metric
                label="自组装方案"
                value={project?.assemblies.length ?? 0}
                detail="用户声明的亚基组成"
              />
              <Metric
                label="分析记录"
                value={history.length}
                detail="保存在本地数据库"
              />
              <Metric
                label="可用工具"
                value={tools.length}
                detail="注册能力与独立插件"
              />
            </section>
            <section className="two-columns">
              <article className="card composer">
                <div className="card-title">
                  <h2>准备下一次分析</h2>
                  <span className="tag">无需 LLM 也能运行</span>
                </div>
                <p>选择研究目标，查看并确认具体步骤后运行。</p>
                <textarea
                  aria-label="任务说明"
                  placeholder="记录你希望比较的构建、条件或实验问题…"
                  value={objective}
                  onChange={(event) => setObjective(event.target.value)}
                />
                <label>
                  分析目标
                  <select
                    aria-label="分析目标"
                    value={goal}
                    onChange={(event) => setGoal(event.target.value as Goal)}
                  >
                    {Object.entries(goalLabels).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="button-row">
                  <button
                    className="primary"
                    disabled={!project || busy}
                    onClick={plan}
                  >
                    生成可审阅流程 ↗
                  </button>
                  <button
                    disabled={!project || busy}
                    onClick={() => setPage("Project")}
                  >
                    导入项目数据
                  </button>
                </div>
              </article>
              <article className="card">
                <h2>项目准备情况</h2>
                <Readiness
                  done={sequenceCount > 0}
                  title="构建序列"
                  detail={
                    sequenceCount
                      ? `${sequenceCount} 条蛋白序列`
                      : "导入 FASTA 或带 CDS 翻译的 GenBank"
                  }
                />
                <Readiness
                  done={!!project?.assemblies.length}
                  title="自组装组成"
                  detail="填写参与组装的蛋白与亚基数"
                />
                <Readiness
                  done={!!project?.pathway}
                  title="反应通路（可选）"
                  detail="上传含单位、参数来源和速率律的 JSON"
                />
                <p className="muted note">
                  序列统计、自组装组成与反应通路有各自的证据范围；计算结果页会说明适用条件。
                </p>
              </article>
            </section>
            <RunProgress
              run={activeRun}
              stale={!!isStale}
              busy={busy}
              onControl={(control) =>
                action(async () =>
                  setRun(await api.controlRun(activeRun!.id, control)),
                )
              }
              onResults={() => setPage("Results")}
            />
          </>
        )}

        {page === "Project" &&
          (project ? (
            <>
              <section className="card">
                <div className="card-title">
                  <h2>构建信息</h2>
                  <button
                    className="primary"
                    disabled={busy}
                    onClick={() => action(() => persist(project))}
                  >
                    保存项目
                  </button>
                </div>
                <div className="form-grid">
                  <label>
                    项目名称
                    <input
                      aria-label="项目名称"
                      value={project.name}
                      onChange={(event) =>
                        setProject({ ...project, name: event.target.value })
                      }
                    />
                  </label>
                  <label>
                    项目说明
                    <input
                      value={project.description}
                      onChange={(event) =>
                        setProject({
                          ...project,
                          description: event.target.value,
                        })
                      }
                    />
                  </label>
                </div>
              </section>
              <section className="card">
                <div className="card-title">
                  <h2>序列与实验数据</h2>
                  <label>导入类型<select aria-label="导入类型" value={inputKind} onChange={(event) => setInputKind(event.target.value)}>
                    <option value="auto">序列 / 普通表格 / 通路 JSON</option>
                    <option value="wetlab">WetLabResult 科学测量 JSON</option>
                  </select></label>
                  <label className="upload-button">
                    ＋ 导入文件
                    <input
                      aria-label="导入文件"
                      type="file"
                      accept=".fasta,.fa,.faa,.gb,.gbk,.genbank,.json,.csv,.tsv"
                      disabled={busy}
                      onChange={(event) => {
                        const file = event.target.files?.[0];
                        if (file)
                          action(async () =>
                            setPreview(await api.previewImport(file, inputKind)),
                          );
                        event.target.value = "";
                      }}
                    />
                  </label>
                </div>
                <p className="muted">
                  FASTA · GenBank 蛋白 CDS · 通路 JSON · CSV /
                  TSV。导入后先预览，再确认写入项目。
                </p>
                {preview && (
                  <div className="import-preview">
                    <h3>导入预览 · {preview.file.name}</h3>
                    {preview.patch.sequences && (
                      <ul>
                        {preview.patch.sequences.map((sequence) => (
                          <li key={sequence.id}>
                            {sequence.id} · {sequence.sequence.length} aa
                          </li>
                        ))}
                      </ul>
                    )}
                    {preview.patch.pathway && (
                      <p>
                        通路 {String(preview.patch.pathway.id)} ·{" "}
                        {(preview.patch.pathway.species as string[]).length}{" "}
                        个物种 ·{" "}
                        {(preview.patch.pathway.reactions as unknown[]).length}{" "}
                        个反应 · 两相竞争 MM
                      </p>
                    )}
                    {preview.patch.datasets && (
                      <p>
                        {preview.kind === "wetlab" ? "已校验 WetLabResult；条件/QC/删失及来源保留，不自动批准参数。" :
                          `普通数据表 ${(preview.patch.datasets[0].rows as unknown[]).length} 行；不是科学测量注册。`}
                      </p>
                    )}
                    {developer && (
                      <details>
                        <summary>结构化导入内容</summary>
                        <pre>{JSON.stringify(preview.patch, null, 2)}</pre>
                      </details>
                    )}
                    <div className="button-row">
                      <button
                        className="primary"
                        disabled={busy}
                        onClick={() =>
                          action(async () => {
                            const patch = preview.patch;
                            const updated = {
                              ...project,
                              ...patch,
                              sequences: patch.sequences
                                ? [...project.sequences, ...patch.sequences]
                                : project.sequences,
                              datasets: patch.datasets
                                ? [...project.datasets, ...patch.datasets]
                                : project.datasets,
                              files: [
                                ...project.files.filter(
                                  (file) => file.id !== preview.file.id,
                                ),
                                preview.file,
                              ],
                            };
                            await persist(updated);
                            setPreview(undefined);
                          })
                        }
                      >
                        确认导入
                      </button>
                      <button onClick={() => setPreview(undefined)}>
                        取消
                      </button>
                    </div>
                  </div>
                )}
                {project.sequences.length ? (
                  <div className="sequence-grid">
                    {project.sequences.map((sequence) => (
                      <article className="sequence-card" key={sequence.id}>
                        <span className="tag">{sequence.role}</span>
                        <h3>{sequence.id}</h3>
                        <p>{sequence.sequence.length} aa</p>
                        <code>
                          {sequence.sequence.slice(0, 72)}
                          {sequence.sequence.length > 72 ? "…" : ""}
                        </code>
                      </article>
                    ))}
                  </div>
                ) : (
                  <Empty
                    title="还没有构建序列"
                    description="上传实际融合蛋白序列，或先准备独立蛋白部件。"
                  />
                )}
                <div className="file-list">
                  {project.files.map((file) => (
                    <p key={file.id}>
                      {file.name}
                      <small>SHA-256 {file.sha256.slice(0, 16)}…</small>
                    </p>
                  ))}
                </div>
              </section>
              <AssemblyEditor project={project} onChange={setProject} />
              <ScientificProjectPanel key={project.id} project={project} busy={busy} action={action}
                onChange={(value) => { if (projectRef.current?.id === project.id) setProject(value); }} />
              <section className="card">
                <h2>反应通路与实验条件</h2>
                <p>
                  {project.pathway
                    ? `已上传通路：${String(project.pathway.id)} · 两相竞争 MM`
                    : "可选：上传自定义通路 JSON 后再运行代谢分析。"}
                </p>
                <p>{project.datasets.length} 份实验数据表已导入。</p>
                <div className="form-grid">
                  {[
                    { key: "temperature_c", label: "温度（°C）" },
                    { key: "ph", label: "pH" },
                    { key: "ionic_strength_mm", label: "离子强度（mM）" },
                  ].map((field) => (
                    <label key={field.key}>
                      {field.label}
                      <input
                        type="number"
                        step="any"
                        value={
                          typeof project.conditions[field.key] === "number"
                            ? (project.conditions[field.key] as number)
                            : ""
                        }
                        onChange={(event) => {
                          const conditions = { ...project.conditions };
                          if (event.target.value === "")
                            delete conditions[field.key];
                          else
                            conditions[field.key] = Number(event.target.value);
                          setProject({ ...project, conditions });
                        }}
                      />
                    </label>
                  ))}
                </div>
                <p className="muted">
                  {dirty ? "有未保存修改；旧方案已失效，保存后重新生成并审阅。" : `已保存 revision ${project.revision}。`}
                  条件用于记录实验背景；只有工作流显式绑定的参数才参与计算。
                </p>
                {developer && (
                  <label>
                    条件与参数记录（JSON）
                    <textarea
                      aria-label="实验条件"
                      defaultValue={JSON.stringify(project.conditions, null, 2)}
                      key={`${project.id}-${project.revision}`}
                      onBlur={(event) => {
                        try {
                          const value = JSON.parse(event.target.value);
                          if (
                            value === null ||
                            typeof value !== "object" ||
                            Array.isArray(value)
                          )
                            throw new Error("条件必须是 JSON 对象");
                          setProject({ ...project, conditions: value });
                        } catch (reason) {
                          setError(String(reason));
                        }
                      }}
                    />
                  </label>
                )}
              </section>
            </>
          ) : (
            <Empty
              title="创建你的第一个项目"
              description="点击侧栏“创建项目”以保存序列、组装方案和实验数据。"
            />
          ))}

        {page === "Analysis" && (
          <>
            <section className="card">
              <div className="card-title">
                <h2>分析目标</h2>
                <span className="tag">已校验模板</span>
              </div>
              <label>
                选择目标
                <select
                  value={goal}
                  onChange={(event) => {
                    setGoal(event.target.value as Goal);
                    setWorkflow(undefined);
                  }}
                >
                  {Object.entries(goalLabels).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <button disabled={!project || busy} onClick={plan}>
                生成流程
              </button>
            </section>
            {workflow && (
              <section className="card">
                <div className="card-title">
                  <div>
                    <h2>{workflow.name}</h2>
                    <p>{workflow.description}</p>
                  </div>
                  <button
                    className="primary"
                    disabled={busy || dirty || !confirmation || confirmation.project_revision !== project?.revision}
                    onClick={() =>
                      action(async () => {
                        if (dirty || !confirmation) throw new Error("请保存当前输入并重新审阅方案");
                        const generation = editGeneration.current;
                        const result = await api.startRun(project!.id, workflow, confirmation);
                        if (generation === editGeneration.current) setRun(result);
                      })
                    }
                  >
                    确认并运行
                  </button>
                </div>
                <div className="step-list">
                  {workflow.nodes.map((node, index) => (
                    <div className="plan-step" key={node.id}>
                      <span className="step-number">{index + 1}</span>
                      <div>
                        <h3>{node.label}</h3>
                        <p>
                          {node.map
                            ? "对输入集合逐项运行，汇合后进入下一步"
                            : "使用已声明的输入执行计算"}
                        </p>
                        {developer && <code>{node.tool_id}</code>}
                      </div>
                      <span className="tag">
                        {node.map ? "批处理" : "分析"}
                      </span>
                    </div>
                  ))}
                </div>
                {developer && (
                  <WorkflowEditor
                    workflow={workflow}
                    onChange={(value) => action(async () => {
                      if (dirty || !project) throw new Error("自定义工作流也需绑定已保存的项目版本");
                      const generation = editGeneration.current;
                      const reviewed = await api.reviewCustomPlan(project.id, value);
                      if (generation !== editGeneration.current || reviewed.confirmation.project_revision !== projectRef.current?.revision) return;
                      setWorkflow(reviewed.workflow);
                      setConfirmation(reviewed.confirmation);
                    })}
                    onError={setError}
                  />
                )}
              </section>
            )}
            <RunProgress
              run={activeRun}
              stale={!!isStale}
              busy={busy}
              onControl={(control) =>
                action(async () =>
                  setRun(await api.controlRun(activeRun!.id, control)),
                )
              }
              onResults={() => setPage("Results")}
            />
          </>
        )}

        {page === "Results" && (
          <>
            {activeRun?.status !== "succeeded" && (
              <RunProgress
                run={activeRun}
                stale={!!isStale}
                busy={busy}
                onControl={(control) =>
                  action(async () =>
                    setRun(await api.controlRun(activeRun!.id, control)),
                  )
                }
                onResults={() => setPage("Results")}
              />
            )}
            <Results run={activeRun} developer={developer} />
          </>
        )}
        {page === "History" && (
          <section className="card">
            <div className="card-title">
              <h2>分析历史</h2>
              <span className="tag">本地持久化</span>
            </div>
            {!history.length && (
              <Empty
                title="尚未运行分析"
                description="确认分析流程后，记录会保存在这里。"
              />
            )}
            <div className="history-list">
              {history.map((item) => (
                <div className="history-row" key={item.id}>
                  <div>
                    <b>{item.name ?? "分析记录"}</b>
                    <small>
                      {new Date(item.created_at).toLocaleString("zh-CN")} ·
                      项目版本 {item.project_revision}
                    </small>
                    <small>
                      {item.id.slice(0, 8)} · {item.snapshot_hash.slice(0, 12)}
                    </small>
                  </div>
                  <Status status={item.status} />
                  <div className="button-row">
                    <button
                      disabled={busy}
                      onClick={() =>
                        action(async () => {
                          setRun(await api.getRun(item.id));
                          setPage("Results");
                        })
                      }
                    >
                      查看
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        action(async () => {
                          setRun(await api.cloneRun(item.id));
                          setPage("Analysis");
                        })
                      }
                    >
                      克隆运行
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        action(async () => {
                          const value = await api.getRun(item.id);
                          setCompare((previous) =>
                            [
                              ...previous.filter((run) => run.id !== item.id),
                              value,
                            ].slice(-2),
                          );
                        })
                      }
                    >
                      加入对比
                    </button>
                  </div>
                </div>
              ))}
            </div>
            {compare.length > 0 && (
              <div className="comparison">
                <h3>运行对比</h3>
                <ResultComparison runs={compare} />
                <table>
                  <thead>
                    <tr>
                      <th>记录</th>
                      <th>项目版本</th>
                      <th>序列数</th>
                      <th>完成步骤</th>
                      <th>状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compare.map((item) => (
                      <tr key={item.id}>
                        <td>{item.id.slice(0, 8)}</td>
                        <td>{item.snapshot.project.revision}</td>
                        <td>{item.snapshot.project.sequences.length}</td>
                        <td>
                          {
                            item.nodes.filter(
                              (node) => node.status === "succeeded",
                            ).length
                          }
                        </td>
                        <td>{labels[item.status]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="muted">
                  比较使用各次运行的输入快照；不同构建或条件的结果需要结合实验设计解释。
                </p>
              </div>
            )}
          </section>
        )}
        {page === "Tools" && (
          <>
            <section className="tools-grid">
              {tools.map((tool) => (
                <article className="card tool-card" key={tool.id}>
                  <span className="tool-icon">◇</span>
                  <span className="tag">
                    {tool.runtime === "builtin" ? "内置工具" : "独立环境"}
                  </span>
                  <h2>{tool.name}</h2>
                  <p>{tool.description}</p>
                  <small>
                    {tool.capability} · v{tool.version}
                  </small>
                  {developer && (
                    <details>
                      <summary>输入输出协议</summary>
                      <pre>{JSON.stringify(tool, null, 2)}</pre>
                    </details>
                  )}
                </article>
              ))}
            </section>
            <PluginInstaller
              busy={busy}
              action={action}
              onInstalled={async () => setTools(await api.getTools())}
            />
          </>
        )}
        {page === "Settings" && (
          <section className="card">
            <h2>工作空间设置</h2>
            <DesktopConnectionPanel />
            <label className="checkbox">
              <input
                type="checkbox"
                checked={developer}
                onChange={(event) => {
                  setDeveloper(event.target.checked);
                  localStorage.setItem(
                    "fusionlab.mode",
                    event.target.checked ? "developer" : "scientist",
                  );
                }}
              />
              显示 Developer Mode
            </label>
            <dl>
              <dt>项目与运行数据库</dt>
              <dd>{info?.data_dir ?? "连接后显示"}</dd>
              <dt>计算位置</dt>
              <dd>{api.backendMode === "ssh" ? "用户配置的远程服务器；本机仅显示桌面前端和建立 SSH 隧道" : "当前连接的本地 Python 后台"}</dd>
              <dt>执行状态保存</dt>
              <dd>每个节点执行前后写入 SQLite，历史运行保留输入快照</dd>
              <dt>任务恢复</dt>
              <dd>恢复完成节点；中断的非幂等工具需要核对原始外部任务</dd>
              <dt>Agent 状态</dt>
              <dd>
                当前使用可审阅的工作流模板。自然语言说明会保存；尚未配置 LLM
                自动规划。
              </dd>
              <dt>插件环境</dt>
              <dd>独立 Python venv 与进程；当前仅支持用户明确信任的插件</dd>
            </dl>
          </section>
        )}
        {page === "Developer" && developer && (
          <section className="card">
            <h2>工作流与运行详情</h2>
            {activeRun ? (
              <>
                <Dag workflow={activeRun.snapshot.workflow} run={activeRun} />
                <details open>
                  <summary>节点状态、输入输出、错误</summary>
                  <pre>{JSON.stringify(activeRun.nodes, null, 2)}</pre>
                </details>
                <details>
                  <summary>执行事件</summary>
                  <pre>{JSON.stringify(activeRun.events, null, 2)}</pre>
                </details>
                <details>
                  <summary>不可变快照与环境</summary>
                  <pre>{JSON.stringify(activeRun.snapshot, null, 2)}</pre>
                </details>
                <details>
                  <summary>Artifact provenance</summary>
                  <pre>{JSON.stringify(activeRun.artifacts, null, 2)}</pre>
                </details>
              </>
            ) : workflow ? (
              <Dag workflow={workflow} />
            ) : (
              <Empty
                title="还没有工作流"
                description="先在分析页面生成流程。"
              />
            )}
          </section>
        )}
        <footer>
          FusionLab · 本地项目与可审计计算{" "}
          <span>研究结果需结合适用条件与实验验证</span>
        </footer>
      </main>
    </div>
  );
}

function Status({ status }: { status: string }) {
  return (
    <span className={`status status-${status}`}>
      {labels[status] ?? status}
    </span>
  );
}
function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: number;
  detail: string;
}) {
  return (
    <article className="metric">
      <span>{label}</span>
      <strong>{value.toString().padStart(2, "0")}</strong>
      <small>{detail}</small>
    </article>
  );
}
function Empty({ title, description }: { title: string; description: string }) {
  return (
    <div className="empty">
      <span>◇</span>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}
function Readiness({
  done,
  title,
  detail,
}: {
  done: boolean;
  title: string;
  detail: string;
}) {
  return (
    <div className="readiness">
      <span className={done ? "check done" : "check"}>{done ? "✓" : "·"}</span>
      <div>
        <b>{title}</b>
        <small>{detail}</small>
      </div>
    </div>
  );
}

function RunProgress({
  run,
  stale,
  busy,
  onControl,
  onResults,
}: {
  run?: Run;
  stale: boolean;
  busy: boolean;
  onControl: (action: "pause" | "cancel" | "resume" | "retry") => void;
  onResults: () => void;
}) {
  if (!run) return null;
  const nodes = run.nodes.filter((node) => !node.parent_id);
  const complete = nodes.filter((node) => node.status === "succeeded").length;
  return (
    <section className="card">
      <div className="card-title">
        <div>
          <h2>{run.snapshot.workflow.name}</h2>
          <p>
            {complete} / {nodes.length} 步骤完成{" "}
            {run.control === "pause" ? "· 当前任务结束后暂停" : ""}
          </p>
        </div>
        <Status status={stale ? "interrupted" : run.status} />
      </div>
      <div className="progress">
        <span style={{ width: `${(complete / nodes.length) * 100}%` }} />
      </div>
      <div className="run-steps">
        {nodes.map((node) => (
          <div key={node.id}>
            <span>
              {
                run.snapshot.workflow.nodes.find((item) => item.id === node.id)
                  ?.label
              }
            </span>
            <Status status={node.status} />
          </div>
        ))}
      </div>
      <div className="button-row">
        {run.status === "running" && !stale && (
          <>
            <button disabled={busy} onClick={() => onControl("pause")}>
              暂停
            </button>
            <button disabled={busy} onClick={() => onControl("cancel")}>
              停止后续步骤
            </button>
          </>
        )}
        {(run.status === "paused" || stale || run.status === "interrupted") && (
          <button disabled={busy} onClick={() => onControl("resume")}>
            恢复分析
          </button>
        )}
        {run.status === "failed" && (
          <button disabled={busy} onClick={() => onControl("retry")}>
            重试可恢复步骤
          </button>
        )}
        <button onClick={onResults}>查看结果与错误 →</button>
      </div>
    </section>
  );
}

function AssemblyEditor({
  project,
  onChange,
}: {
  project: Project;
  onChange: (project: Project) => void;
}) {
  const [name, setName] = useState("");
  const [counts, setCounts] = useState<Record<string, number>>({});
  return (
    <section className="card">
      <h2>自组装方案</h2>
      <p className="muted">
        先记录实际组装单元及亚基数，结构可行性需要后续结构与界面证据。
      </p>
      {project.assemblies.map((assembly) => (
        <div className="assembly-row" key={assembly.id}>
          <b>{assembly.id}</b>
          <span>
            {Object.entries(assembly.subunits)
              .map(([id, count]) => `${id} × ${count}`)
              .join(" + ")}
          </span>
        </div>
      ))}
      <div className="form-grid">
        <label>
          组装方案名称
          <input
            aria-label="组装名称"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        {project.sequences.map((sequence) => (
          <label key={sequence.id}>
            {sequence.id} 的亚基数
            <input
              type="number"
              min="0"
              step="1"
              value={counts[sequence.id] ?? 0}
              onChange={(event) =>
                setCounts({
                  ...counts,
                  [sequence.id]: Number(event.target.value),
                })
              }
            />
          </label>
        ))}
      </div>
      <button
        disabled={
          !name ||
          !Object.values(counts).some((count) => count > 0) ||
          project.assemblies.some((item) => item.id === name)
        }
        onClick={() => {
          onChange({
            ...project,
            assemblies: [
              ...project.assemblies,
              {
                id: name,
                subunits: Object.fromEntries(
                  Object.entries(counts).filter(([, count]) => count > 0),
                ),
                description: "用户声明的亚基组成",
              },
            ],
          });
          setName("");
          setCounts({});
        }}
      >
        添加方案（保存项目后生效）
      </button>
    </section>
  );
}

function Results({ run, developer }: { run?: Run; developer: boolean }) {
  if (!run)
    return (
      <Empty
        title="选择一次分析查看结果"
        description="运行分析后结果会保存在本地，也可以从分析历史打开。"
      />
    );
  const sequenceResults = run.nodes.filter(
    (node) => nodeTool(run, node) === "fusion.sequence_metrics" && node.status === "succeeded" && sequenceOutput(node.output),
  );
  return (
    <>
      <section className="card">
        <div className="card-title">
          <div>
            <h2>{run.snapshot.workflow.name}</h2>
            <p>
              基于项目版本 {run.snapshot.project.revision} ·{" "}
              {new Date(run.created_at).toLocaleString("zh-CN")}
            </p>
          </div>
          <Status status={run.status} />
        </div>
        <p>
          已生成 {run.artifacts.length}{" "}
          个可溯源结果文件。序列计算描述组成与理化性质；自组装组成核验描述用户声明的亚基组成。
        </p>
        {run.nodes
          .filter((node) => node.error)
          .map((node) => (
            <div className="error-banner" key={node.id}>
              {node.id}: {node.error?.code} · {node.error?.message}
            </div>
          ))}
      </section>
      {sequenceResults.length > 0 && (
        <section className="card">
          <h2>构建序列比较</h2>
          <table>
            <thead>
              <tr>
                <th>构建</th>
                <th>长度</th>
                <th>分子量 Da</th>
                <th>理论 pI</th>
                <th>组成长度</th>
              </tr>
            </thead>
            <tbody>
              {sequenceResults.map((node) => {
                const result = node.output!;
                const features = result.features as Record<string, number>;
                const properties = result.protparam as Record<string, number>;
                const maximum = Math.max(
                  ...run.snapshot.project.sequences.map(
                    (sequence) => sequence.sequence.length,
                  ),
                );
                return (
                  <tr key={node.id}>
                    <td>{String(result.id)}</td>
                    <td>{features.length}</td>
                    <td>{properties.molecular_weight_da.toFixed(1)}</td>
                    <td>{properties.theoretical_pi.toFixed(2)}</td>
                    <td>
                      <div className="mini-bar">
                        <span
                          style={{
                            width: `${(features.length / maximum) * 100}%`,
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="muted">
            这些数值不能证明形成液滴、保持酶活性或成功自组装；后续步骤需对应预测器与实验输入。
          </p>
        </section>
      )}
      <ScientificResults run={run} />
      <section className="card">
        <h2>结果文件与计算来源</h2>
        <div className="artifact-list">
          {run.artifacts.map((artifact) => (
            <article key={artifact.id}>
              <div>
                <b>
                  {developer
                    ? artifact.node_id
                    : artifactLabel(run, artifact.node_id)}
                </b>
                <small>
                  输入来源：
                  {developer
                    ? artifact.upstream.join(", ") || "项目快照"
                    : artifact.upstream
                        .map((id) => artifactLabel(run, id))
                        .join("，") || "项目快照"}
                </small>
              </div>
              <a
                className="button-link"
                href={api.artifactUrl(artifact.id)}
                target="_blank"
                rel="noreferrer"
              >
                打开结果 JSON ↗
              </a>
              {developer && <small className="hash">{artifact.hash}</small>}
            </article>
          ))}
        </div>
        <details>
          <summary>复现信息</summary>
          <pre>
            {JSON.stringify(
              {
                snapshot_hash: run.snapshot_hash,
                project_revision: run.snapshot.project.revision,
                environment: run.snapshot.environment,
                tools: run.snapshot.tools,
              },
              null,
              2,
            )}
          </pre>
        </details>
      </section>
    </>
  );
}

function artifactLabel(run: Run, nodeId: string) {
  const record = run.nodes.find((node) => node.id === nodeId);
  const definition = run.snapshot.workflow.nodes.find(
    (node) => node.id === (record?.parent_id ?? nodeId),
  );
  const item = record?.inputs?.item as { id?: string } | undefined;
  return item?.id
    ? `${definition?.label ?? "分析结果"} · ${item.id}`
    : (definition?.label ?? "分析结果");
}

function WorkflowEditor({
  workflow,
  onChange,
  onError,
}: {
  workflow: Workflow;
  onChange: (workflow: Workflow) => void;
  onError: (error: string) => void;
}) {
  const [text, setText] = useState(JSON.stringify(workflow, null, 2));
  return (
    <details>
      <summary>编辑工作流协议（Developer）</summary>
      <textarea
        className="code-editor"
        aria-label="工作流 JSON"
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
      <button
        onClick={async () => {
          try {
            onChange(await api.validateWorkflow(JSON.parse(text)));
          } catch (error) {
            onError(String(error));
          }
        }}
      >
        校验并应用修改
      </button>
      <Dag workflow={workflow} />
    </details>
  );
}

function Dag({ workflow, run }: { workflow: Workflow; run?: Run }) {
  return (
    <div className="dag-graph">
      {workflow.nodes.map((node) => {
        const references = Object.values(node.inputs)
          .filter((input) => input.kind === "node")
          .map((input) => (input.kind === "node" ? input.node_id : ""));
        if (node.map?.items.kind === "node")
          references.push(node.map.items.node_id);
        const dependencies = [...new Set([...node.depends_on, ...references])];
        return (
          <div className="graph-node" key={node.id}>
            <small>
              {dependencies.length
                ? `← ${dependencies.join(", ")}`
                : "项目输入"}
            </small>
            <b>{node.label}</b>
            <code>{node.tool_id}</code>
            {node.map && <span className="tag">map → shards → gather</span>}
            {run && (
              <Status
                status={
                  run.nodes.find((item) => item.id === node.id)?.status ??
                  "pending"
                }
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function PluginInstaller({
  busy,
  action,
  onInstalled,
}: {
  busy: boolean;
  action: (job: () => Promise<void>) => Promise<void>;
  onInstalled: () => Promise<void>;
}) {
  const [source, setSource] = useState("");
  const [repository, setRepository] = useState("");
  const [commit, setCommit] = useState("");
  const [inspection, setInspection] = useState<PluginInspection>();
  const [trust, setTrust] = useState(false);
  return (
    <section className="card">
      <h2>导入扩展工具</h2>
      <details>
        <summary>从 GitHub 获取固定版本</summary>
        <div className="form-grid">
          <label>
            仓库 URL
            <input
              aria-label="GitHub 仓库"
              value={repository}
              onChange={(event) => setRepository(event.target.value)}
              placeholder="https://github.com/owner/repo"
            />
          </label>
          <label>
            完整 commit SHA
            <input
              aria-label="插件 commit"
              value={commit}
              onChange={(event) => setCommit(event.target.value)}
              placeholder="40 位 commit SHA"
            />
          </label>
        </div>
        <button
          disabled={busy || !repository || !/^[0-9a-fA-F]{40}$/.test(commit)}
          onClick={() =>
            action(async () => {
              const fetched = await api.fetchGithubPlugin(repository, commit);
              setSource(fetched.source_path);
              setInspection(fetched);
              setTrust(false);
            })
          }
        >
          下载源码并预览（尚不运行）
        </button>
      </details>
      <p>
        选择已下载的插件目录，先查看
        manifest、来源、版本和权限。每个版本使用独立 Python 环境。
      </p>
      <label>
        本地插件目录
        <input
          aria-label="插件目录"
          value={source}
          onChange={(event) => {
            setSource(event.target.value);
            setInspection(undefined);
            setTrust(false);
          }}
        />
      </label>
      <button
        disabled={!source || busy}
        onClick={() =>
          action(async () => setInspection(await api.inspectPlugin(source)))
        }
      >
        读取插件说明
      </button>
      {inspection && (
        <div className="import-preview">
          <h3>
            {inspection.manifest.name} · {inspection.manifest.version}
          </h3>
          <p>{inspection.manifest.description}</p>
          <p>
            许可证：{inspection.manifest.license} · 声明权限：
            {inspection.manifest.permissions.join(", ") || "无额外声明"}
          </p>
          <p className="muted">
            独立环境隔离依赖版本，当前不提供操作系统安全沙箱；请仅安装可信代码。
          </p>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={trust}
              onChange={(event) => setTrust(event.target.checked)}
            />
            我信任该插件，并确认安装
          </label>
          <button
            className="primary"
            disabled={!trust || busy}
            onClick={() =>
              action(async () => {
                setInspection(
                  await api.installPlugin(source, trust, inspection.hash),
                );
                await onInstalled();
              })
            }
          >
            {inspection.installed ? "已安装" : "安装到独立环境"}
          </button>
        </div>
      )}
    </section>
  );
}
