import { useEffect, useState } from "react";
import type { InputDiffView, ProjectView } from "../contracts/generated";
import { diff } from "./client";

export function InputDiffPanel({
  project,
  runId,
  dirty,
}: {
  project: ProjectView;
  runId?: string;
  dirty: boolean;
}) {
  const [value, setValue] = useState<InputDiffView>();
  const [error, setError] = useState("");
  const baseline = project.parent_run_id ?? runId;
  useEffect(() => {
    setValue(undefined);
    setError("");
    if (!baseline) return;
    const controller = new AbortController();
    diff(project.id, baseline, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setValue(result);
      })
      .catch((reason) => {
        if (!controller.signal.aborted)
          setError(
            reason instanceof Error ? reason.message : "Difference read failed",
          );
      });
    return () => controller.abort();
  }, [project.id, project.revision, baseline]);
  if (!baseline) return null;
  return (
    <section aria-label="Frozen input differences">
      <h3>Saved inputs versus frozen run</h3>
      {dirty && (
        <p>
          Unsaved edits exist; this comparison uses the latest saved revision
          only.
        </p>
      )}
      {error ? (
        <p role="alert">{error}</p>
      ) : value ? (
        <>
          <p>
            Baseline {value.baseline_run_id} · Saved revision r
            {value.project_revision} · {value.total_changed_fields} changed
            fields
          </p>
          <ul>
            {value.changed_fields.map((field) => (
              <li key={field}>
                <code>{field}</code>
              </li>
            ))}
          </ul>
          <p>
            Affected nodes:{" "}
            {value.affected_nodes.join(" → ") ||
              "No bound scientific input changes"}
          </p>
          <p className="subtle">
            {value.explanation} Old scientific results were not reused.
          </p>
        </>
      ) : (
        <p>Checking saved inputs…</p>
      )}
    </section>
  );
}
