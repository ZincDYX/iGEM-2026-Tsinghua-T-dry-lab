import { useEffect, useRef, useState } from "react";
import type { Workflow } from "../contracts/generated";
import * as client from "./client";

export function WorkflowImporter({
  busy,
  enabled,
  submit,
  onEdit,
}: {
  busy: boolean;
  enabled: boolean;
  submit: (create: () => Promise<Workflow>) => Promise<void>;
  onEdit: () => void;
}) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const readEpoch = useRef(0);
  useEffect(
    () => () => {
      ++readEpoch.current;
    },
    [],
  );
  return (
    <section>
      <h3>Import custom DAG</h3>
      <p>
        JSON Backend validates graph/tools/formal sources and creates a
        proposal; no separate executor or direct execution.
      </p>
      <label>
        Workflow JSON
        <textarea
          aria-label="Workflow JSON"
          value={text}
          disabled={busy}
          onChange={(e) => {
            ++readEpoch.current;
            setText(e.target.value);
            onEdit();
          }}
          rows={5}
        />
      </label>
      <label>
        Read workflow file
        <input
          type="file"
          accept=".json,application/json"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            const stamp = ++readEpoch.current;
            setError("");
            onEdit();
            if (file)
              void file
                .text()
                .then((value) => {
                  if (stamp === readEpoch.current) setText(value);
                })
                .catch(() => {
                  if (stamp === readEpoch.current)
                    setError("Workflow file read failed");
                });
          }}
        />
      </label>
      {error && <p role="alert">{error}</p>}
      <button
        disabled={busy || !enabled || !text.trim()}
        onClick={() => void submit(() => client.validate(JSON.parse(text)))}
      >
        Validate and review custom workflow
      </button>
    </section>
  );
}
