import { object } from "../contracts/validation";
import { show } from "../contracts/resultAdapters";

export function M1MethodResult({
  output,
}: {
  output: Record<string, unknown>;
}) {
  const screen = object(output.screen) ? output.screen : undefined;
  const precheck = object(output.precheck) ? output.precheck : undefined;
  const features =
    precheck && object(precheck.features) ? precheck.features : undefined;
  const steps = Array.isArray(output.steps) ? output.steps.filter(object) : [];
  return (
    <section aria-label="M1 method checks">
      <h2>M1 checks · {show(output.candidate_id)}</h2>
      <p>
        Decision: {show(output.verdict)}. This is not full-candidate acceptance
        or experimental validation.
      </p>
      <p>
        Role: {show(precheck?.sequence_kind)} · Length: {show(features?.length)}{" "}
        aa
      </p>
      <p>
        Hard rejection reasons:{" "}
        {show(screen?.hard_reject_reasons ?? precheck?.hard_reject_reasons)}
      </p>
      <p>
        Missing evidence:{" "}
        {show(screen?.missing_required_evidence ?? output.missing)}
      </p>
      {!!steps.length && (
        <table>
          <thead>
            <tr>
              <th>Original step</th>
              <th>Status</th>
              <th>Missing</th>
            </tr>
          </thead>
          <tbody>
            {steps.map((step) => (
              <tr key={String(step.step)}>
                <td>{show(step.name)}</td>
                <td>{show(step.status)}</td>
                <td>{show(step.missing)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
