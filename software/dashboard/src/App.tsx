import { useEffect, useState } from "react";

import { getDag, getRun, startRun } from "./api";
import type { DashboardModule, DashboardRun } from "./types";
import "./styles.css";

const terminalStatuses = new Set(["succeeded", "failed", "unavailable"]);

export default function App() {
  const [modules, setModules] = useState<DashboardModule[]>([]);
  const [selected, setSelected] = useState<DashboardModule>();
  const [configPath, setConfigPath] = useState("configs/m1_m4_example.yaml");
  const [attachment, setAttachment] = useState("");
  const [run, setRun] = useState<DashboardRun>();
  const [error, setError] = useState("");

  useEffect(() => {
    getDag()
      .then((items) => {
        setModules(items);
        setSelected(items[0]);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    if (!run || terminalStatuses.has(run.status)) return;
    const timer = window.setInterval(() => {
      getRun(run.run_id).then(setRun).catch((reason: Error) => setError(reason.message));
    }, 800);
    return () => window.clearInterval(timer);
  }, [run]);

  async function execute() {
    if (!selected) return;
    setError("");
    try {
      setRun(await startRun(selected.id, configPath));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Run request failed.");
    }
  }

  return (
    <main>
      <header><strong>Dry-lab Dashboard</strong><span>Local runtime</span></header>
      <section className="layout">
        <aside>
          <h2>Task</h2>
          <label>Project configuration<input aria-label="Project configuration" value={configPath} onChange={(event) => setConfigPath(event.target.value)} /></label>
          <label>Attachment<input aria-label="Attachment" type="file" onChange={(event) => setAttachment(event.target.files?.[0]?.name ?? "")} /></label>
          {attachment && <small>Selected: {attachment} (not uploaded in MVP)</small>}
          <button disabled={!selected} onClick={execute}>Run {selected?.id.toUpperCase()}</button>
          {error && <p className="error">{error}</p>}
        </aside>
        <section className="content">
          <Dag modules={modules} selected={selected} onSelect={setSelected} />
          <Execution run={run} />
        </section>
      </section>
    </main>
  );
}

function Dag({ modules, selected, onSelect }: { modules: DashboardModule[]; selected?: DashboardModule; onSelect: (item: DashboardModule) => void }) {
  return <div className="dag"><h2>M0–M5 workflow</h2><div className="nodes">{modules.map((item) => <button key={item.id} className={selected?.id === item.id ? "node active" : "node"} onClick={() => onSelect(item)}>{item.id.toUpperCase()}</button>)}</div>{selected && <article><h3>{selected.name}</h3><p>{selected.description}</p><p><b>Inputs:</b> {selected.inputs.join(", ")}</p><p><b>Outputs:</b> {selected.outputs.join(", ")}</p><p className={selected.run_available ? "available" : "unavailable"}>{selected.run_available ? "Standalone runtime available" : selected.unavailable_reason}</p></article>}</div>;
}

function Execution({ run }: { run?: DashboardRun }) {
  return <div className="logs"><h2>Execution</h2>{!run ? <p>No run started.</p> : <><p>Status: <b>{run.status}</b></p><ul>{run.logs.map((log, index) => <li key={`${log.timestamp}-${index}`}>{log.status}: {log.message}</li>)}</ul>{run.error && <p className="error">{run.error.code}: {run.error.message}</p>}</>}</div>;
}
