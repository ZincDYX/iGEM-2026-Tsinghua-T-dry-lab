import { useState } from "react";
import type {
  EventPage,
  NodePage,
  RunSummaryView,
} from "../contracts/generated";
import { statusLabel } from "./PlanPanel";

const eventLabels: Record<string, string> = {
  run_created: "Run queued",
  run_started: "Run started",
  run_claimed: "Worker started",
  run_succeeded: "Run completed",
  run_failed: "Run failed",
  run_cancelled: "Run stopped",
  run_paused: "Run paused",
  node_started: "Task started",
  node_succeeded: "Task completed",
  node_failed: "Task failed",
  node_skipped: "Task skipped",
  remote_job_submitted: "Remote task submitted",
  remote_job_polled: "Remote status updated",
  checkpoint: "Paused at checkpoint",
  control_requested: "Control requested",
};
export function RunPanel({
  run,
  events,
  data,
  error,
  selected,
  onSelect,
  onControl,
}: {
  run?: RunSummaryView;
  events: EventPage["items"];
  data?: NodePage;
  error: string;
  selected: string;
  onSelect: (id: string) => void;
  onControl: (action: "pause" | "cancel" | "resume" | "retry") => void;
}) {
  const [tab, setTab] = useState<"jobs" | "output" | "problems">("jobs"),
    [offset, setOffset] = useState(0);
  const problem = data?.node.id === selected ? data.node.error : undefined;
  const messages = events
    .filter(
      (event) => !selected || !event.node_id || event.node_id === selected,
    )
    .map((event) => ({
      seq: event.seq,
      time: new Date(event.timestamp).toLocaleTimeString(),
      module:
        run?.nodes.find((node) => node.id === event.node_id)?.label ?? "Run",
      level: event.event.includes("fail")
        ? "Error"
        : event.event.includes("warn")
          ? "Warning"
          : event.event.includes("suggest")
            ? "Suggestion"
            : event.event.includes("succeed")
              ? "Success"
              : "Info",
      text:
        typeof event.payload.message === "string"
          ? event.payload.message
          : typeof event.payload.reason === "string"
            ? event.payload.reason
            : (eventLabels[event.event] ?? "Task status updated"),
    }));
  return (
    <section className="workspace-bottom" aria-label="Jobs and actions">
      {run&&<h3>{run.name}</h3>}
      <div role="tablist" aria-label="Bottom panel tabs">
        {(["jobs", "output", "problems"] as const).map((value) => (
          <button
            key={value}
            role="tab"
            aria-selected={tab === value}
            onClick={() => setTab(value)}
          >
            {value === "jobs"
              ? "Jobs"
              : value === "output"
                ? "Output"
                : "Problems"}
          </button>
        ))}
      </div>
      <div className="bottom-content">
        {tab === "jobs" &&
          (run ? (
            <>
              <table aria-label="Execution jobs">
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {run.nodes.slice(offset, offset + 50).map((task) => (
                    <tr key={task.id}>
                      <td>{task.label}</td>
                      <td>{statusLabel(task.status)}</td>
                      <td>
                        <button
                          onClick={() => {
                            onSelect(task.id);
                            setTab("output");
                          }}
                        >
                          Log
                        </button>
                        {["failed", "interrupted"].includes(task.status) && (
                          <button
                            onClick={() => {
                              onSelect(task.id);
                              setTab("problems");
                            }}
                          >
                            Fix problem
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {run.nodes.length > 50 && (
                <nav>
                  <button
                    disabled={!offset}
                    onClick={() =>
                      setOffset((value) => Math.max(0, value - 50))
                    }
                  >
                    Previous tasks
                  </button>
                  <button
                    disabled={offset + 50 >= run.nodes.length}
                    onClick={() => setOffset((value) => value + 50)}
                  >
                    Next tasks
                  </button>
                </nav>
              )}
            </>
          ) : (
            <p>No tasks started.</p>
          ))}
        {tab === "output" && (
          <section aria-label="Task log">
            {messages.length ? (
              <>
                <button
                  onClick={() => {
                    const url = URL.createObjectURL(
                      new Blob(
                        [
                          messages
                            .map(
                              (message) =>
                                `${message.time} [${message.level}] ${message.module}: ${message.text}`,
                            )
                            .join("\n"),
                        ],
                        { type: "text/plain" },
                      ),
                    );
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = "FusionLab-task-log.txt";
                    link.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  Export public log
                </button>
                {messages.map((message) => (
                  <p
                    className={`log-${message.level.toLowerCase()}`}
                    key={message.seq}
                  >
                    <time>{message.time}</time> <strong>{message.level}</strong>{" "}
                    {message.module}: {message.text}
                  </p>
                ))}
              </>
            ) : (
              <p>No recorded log messages.</p>
            )}
          </section>
        )}
        {tab === "problems" && (
          <>
            {error && <p role="alert">{error}</p>}
            {problem && (
              <section>
                <h3>
                  {run?.nodes.find((node) => node.id === selected)?.label ??
                    "Task"}
                </h3>
                <p role="alert">
                  {typeof problem.message === "string"
                    ? problem.message
                    : "This task failed. Open its log for the recorded cause."}
                </p>
                {Array.isArray(problem.actions) && (
                  <ul>
                    {problem.actions
                      .filter(
                        (value): value is string => typeof value === "string",
                      )
                      .map((value) => (
                        <li key={value}>{value}</li>
                      ))}
                  </ul>
                )}
                {["failed", "interrupted"].includes(data!.node.status) && (
                  <button onClick={() => onControl("retry")}>Retry task</button>
                )}
              </section>
            )}
            {!error && !problem && <p>No current errors.</p>}
          </>
        )}
      </div>
    </section>
  );
}
