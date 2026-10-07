import { useEffect, useRef, useState } from "react";
import type { ScientificPreviewView } from "../contracts/generated";
import { parsePublic } from "../contracts/validation";
import { requestBinary } from "../api";

export function ScientificBundleImporter({
  busy,
  onPreview,
  action,
}: {
  busy: boolean;
  onPreview: (preview: ScientificPreviewView) => void;
  action: (job: () => Promise<unknown>) => Promise<void>;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [entry, setEntry] = useState("");
  const epoch = useRef(0);
  useEffect(
    () => () => {
      ++epoch.current;
    },
    [],
  );
  const relative = (file: File) =>
    file.webkitRelativePath
      ? file.webkitRelativePath.split("/").slice(1).join("/")
      : file.name;
  function choose(values: File[]) {
    ++epoch.current;
    setFiles(values);
    const configs = values.filter((f) => /\.ya?ml$/i.test(f.name));
    setEntry(configs.length === 1 ? relative(configs[0]) : "");
  }
  async function upload() {
    const generation = epoch.current;
    if (
      files.length > 256 ||
      files.reduce((n, f) => n + f.size, 0) > 20_000_000
    )
      throw new Error("Import budget: 256 files / 20 MB.");
    const { zipSync } = await import("fflate");
    const data: Record<string, Uint8Array> = {};
    for (const file of files) {
      const name = relative(file);
      if (name in data) throw new Error("Duplicate logical file name.");
      data[name] = new Uint8Array(await file.arrayBuffer());
    }
    if (generation !== epoch.current) return;
    const bytes = zipSync(data, { level: 0 });
    const response = await requestBinary(
      `/scientific-projects/upload-binary?config_filename=${encodeURIComponent(entry)}`,
      new Blob([bytes as Uint8Array<ArrayBuffer>]),
    );
    const preview = parsePublic("ScientificPreviewView", await response.json());
    if (generation === epoch.current) onPreview(preview);
  }
  return (
    <section aria-label="Scientific project import">
      <h3>Import scientific project folder</h3>
      <p>
        Original bytes and relative directories are preserved. Maximum 256 files
        / 20 MB; runtime tools settings are not scientific inputs.
      </p>
      <label>
        Project files
        <input
          aria-label="Scientific project files"
          type="file"
          multiple
          disabled={busy}
          onChange={(e) => choose(Array.from(e.target.files ?? []))}
        />
      </label>
      <label>
        Project folder
        <input
          aria-label="Scientific project folder"
          type="file"
          multiple
          disabled={busy}
          ref={(el) => el?.setAttribute("webkitdirectory", "")}
          onChange={(e) => choose(Array.from(e.target.files ?? []))}
        />
      </label>
      {!!files.length && (
        <>
          <label>
            Entry YAML
            <select
              aria-label="Scientific project entry"
              value={entry}
              disabled={busy}
              onChange={(e) => {
                ++epoch.current;
                setEntry(e.target.value);
              }}
            >
              <option value="">Select configuration</option>
              {files
                .filter((f) => /\.ya?ml$/i.test(f.name))
                .map((f) => (
                  <option key={relative(f)} value={relative(f)}>
                    {relative(f)}
                  </option>
                ))}
            </select>
          </label>
          <p>{files.length} files</p>
          <button disabled={busy || !entry} onClick={() => void action(upload)}>
            Check scientific inputs
          </button>
        </>
      )}
    </section>
  );
}
