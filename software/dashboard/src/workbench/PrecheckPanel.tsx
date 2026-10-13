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
  if (!result) return null;
  return (
    <section aria-label="Input check issues">
      {stale&&<p>Inputs changed. Check the saved version again.</p>}
      <ul>
          {result.missing.map((item, index) => (
            <li key={index}><strong>{item.stage.toUpperCase()}{item.construct_id?' — '+item.construct_id:''}</strong>: {fieldLabel(item.field_path)}.{' '}
                {item.reason_codes
                  .map((code) => code.replaceAll("_", " "))
                  .join(", ")}
                <button onClick={() => onLocate(item)}>Add data</button></li>
          ))}
      </ul>
      {!result.missing.length && (
        <p>No known contract omissions; final stage gates still apply.</p>
      )}
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
