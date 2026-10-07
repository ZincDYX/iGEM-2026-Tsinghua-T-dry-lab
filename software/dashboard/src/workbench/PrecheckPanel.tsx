import { useEffect, useState } from "react";
import type { ScientificPrecheckView } from "../contracts/generated";
import * as client from "./client";

export function PrecheckPanel({
  projectId,
  revision,
  disabled,
}: {
  projectId: string;
  revision: number;
  disabled: boolean;
}) {
  const [request, setRequest] = useState(0);
  const [result, setResult] = useState<ScientificPrecheckView>();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  useEffect(() => {
    setResult(undefined);
    setError("");
    if (!request) return;
    const controller = new AbortController();
    setPending(true);
    client
      .precheck(projectId, controller.signal)
      .then((value) => {
        if (controller.signal.aborted) return;
        if (
          value.project_id !== projectId ||
          value.project_revision !== revision
        )
          throw new Error("Input revision changed; save and check again.");
        setResult(value);
      })
      .catch((reason) => {
        if (!controller.signal.aborted)
          setError(
            reason instanceof Error
              ? reason.message
              : "Input check incomplete.",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setPending(false);
      });
    return () => controller.abort();
  }, [projectId, revision, request]);
  const current =
    !disabled &&
    result?.project_id === projectId &&
    result.project_revision === revision
      ? result
      : undefined;
  return (
    <section aria-label="Saved scientific input check">
      <h3>Partial input check</h3>
      <p>
        Checks saved inputs and existing parameter contracts only; no solvers or
        approval. Final stage gates still apply.
      </p>
      <button
        disabled={disabled || pending}
        onClick={() => setRequest((value) => value + 1)}
      >
        Check inputs
      </button>
      {disabled && <p>Apply edits and save the draft first.</p>}
      {pending && <p>Reading contract omissions…</p>}
      {error && <p role="alert">{error}</p>}
      {current && (
        <>
          <p>
            revision {current.project_revision} · Inputs SHA-256{" "}
            {current.input_sha256}
          </p>
          <table>
            <thead>
              <tr>
                <th>Stage / Missing evidence</th>
                <th>Field</th>
                <th>Construct / Conditions</th>
                <th>Required source / Reason</th>
              </tr>
            </thead>
            <tbody>
              {current.missing.map((item, index) => (
                <tr key={index}>
                  <td>
                    {item.stage} / {item.code}
                  </td>
                  <td>
                    {item.field_path}{" "}
                    <button
                      onClick={() => {
                        const section = item.field_path.includes("construct")
                          ? "constructs"
                          : item.field_path.includes("fasta")
                            ? "sequences"
                            : item.field_path.includes("condition")
                              ? "conditions"
                              : "evidence";
                        document
                          .getElementById(`input-${section}`)
                          ?.scrollIntoView({ block: "start" });
                      }}
                    >
                      Locate input section
                    </button>
                  </td>
                  <td>
                    {item.construct_id ?? "Not declared"} /{" "}
                    {item.condition_id ?? "Not declared"}
                  </td>
                  <td>
                    {item.source_kind} / {item.reason_codes.join(", ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!current.missing.length && (
            <p>
              No known contract omissions found; this is not evidence approval
              or prediction permission.
            </p>
          )}
          {current.limitations.map((text) => (
            <p key={text}>{text}</p>
          ))}
        </>
      )}
    </section>
  );
}
