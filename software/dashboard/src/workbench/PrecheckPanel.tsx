import type { ScientificPrecheckView } from "../contracts/generated";
import { fieldLabel } from "./ScientificFields";
export type InputIssue = ScientificPrecheckView["missing"][number];

export function InputIssues({
  result,
  stale,
  onLocate,
}: {
  result?: ScientificPrecheckView;
  stale: boolean;
  onLocate: (issue: InputIssue) => void;
}) {
  if (!result) return <p>No input check recorded for this project.</p>;
  return (
    <section aria-label="Input check issues">
      <p>
        Saved revision {result.project_revision}
        {stale ? " · Stale — inputs changed; check again." : " · Checked"}
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
          {result.missing.map((item, index) => (
            <tr key={index}>
              <td>
                {item.stage} / {item.code}
              </td>
              <td>
                {fieldLabel(item.field_path)}{" "}
                <button onClick={() => onLocate(item)}>Open input</button>
              </td>
              <td>
                {item.construct_id ?? "Not declared"} /{" "}
                {item.condition_id ?? "Not declared"}
              </td>
              <td>
                {item.source_kind.replaceAll("_", " ")} /{" "}
                {item.reason_codes
                  .map((code) => code.replaceAll("_", " "))
                  .join(", ")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!result.missing.length && (
        <p>No known contract omissions; final stage gates still apply.</p>
      )}
      <details>
        <summary>Check scope and provenance</summary>
        {result.limitations.map((text) => (
          <p key={text}>{text}</p>
        ))}
      </details>
    </section>
  );
}

export function PrecheckPanel({
  result,
  stale,
  disabled,
  onCheck,
  onLocate,
}: {
  result?: ScientificPrecheckView;
  stale: boolean;
  disabled: boolean;
  onCheck: () => void;
  onLocate: (issue: InputIssue) => void;
}) {
  return (
    <section aria-label="Saved scientific input check">
      <h3>Input check</h3>
      <p>
        Checks saved inputs without running solvers. Final stage gates still
        apply.
      </p>
      <button disabled={disabled} onClick={onCheck}>
        Check inputs
      </button>
      <InputIssues result={result} stale={stale} onLocate={onLocate} />
    </section>
  );
}
