import { useState } from "react";
import type { PluginInspectionView } from "../contracts/generated";
import { LazyJson } from "../contracts/LazyJson";
import * as client from "./client";

export function PluginPanel({
  busy,
  action,
}: {
  busy: boolean;
  action: (job: () => Promise<unknown>) => Promise<void>;
}) {
  const [url, setUrl] = useState("");
  const [commit, setCommit] = useState("");
  const [inspection, setInspection] = useState<PluginInspectionView>();
  const [trusted, setTrusted] = useState(false);
  return (
    <section>
      <h2>Trusted plugins</h2>
      <p>
        Uses current workspace authorization; venv isolates dependencies, not
        file/network permissions. Pinned source hash does not prove safe code.
      </p>
      <label>
        Public GitHub repository
        <input
          disabled={busy}
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setInspection(undefined);
            setTrusted(false);
          }}
        />
      </label>
      <label>
        Pinned commit
        <input
          disabled={busy}
          value={commit}
          onChange={(e) => {
            setCommit(e.target.value);
            setInspection(undefined);
            setTrusted(false);
          }}
        />
      </label>
      <button
        disabled={busy || !url || !commit}
        onClick={() =>
          void action(async () => {
            const value = await client.fetchPlugin(url, commit);
            if (!value.source_path)
              throw new Error("Registered source identity missing.");
            setInspection(value);
            setTrusted(false);
          })
        }
      >
        Fetch pinned source and inspect
      </button>
      {inspection && (
        <>
          <LazyJson
            value={inspection}
            label="License, capabilities and source  hash"
          />
          <label>
            <input
              type="checkbox"
              disabled={busy}
              checked={trusted}
              onChange={(e) => setTrusted(e.target.checked)}
            />
            I trust this code; capabilities/secrets still require individual
            maintainer grants
          </label>
          <button
            disabled={busy || !trusted || !inspection.source_path}
            onClick={() =>
              void action(() =>
                client.installPlugin(inspection.source_path!, inspection.hash),
              )
            }
          >
            Install inspected plugin
          </button>
        </>
      )}
    </section>
  );
}
