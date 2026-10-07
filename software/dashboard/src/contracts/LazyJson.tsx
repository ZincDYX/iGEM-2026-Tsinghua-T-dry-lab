import { useState } from "react";
// Presentation only. Full identities remain in backend records and exports.
const technicalKey =
  /^(?:sha256|hash|schema_version|formula_version|snapshot_hash|diagnostic_id|run_id|project_id|file_id|artifact_id|parameter_ids|parent_artifact_id|parent_run_id|workspace_id)$|_(?:sha256|hash)$/;
export function readableData(value: unknown) {
  return JSON.stringify(
    value,
    (key, item) =>
      technicalKey.test(key)
        ? undefined
        : typeof item === "string" && item.startsWith("asset:")
          ? "Attached file"
          : item,
    2,
  );
}
export function LazyJson({
  value,
  label = "Data and provenance",
}: {
  value: unknown;
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <details onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>{label}</summary>
      {open && <pre>{readableData(value)}</pre>}
    </details>
  );
}
