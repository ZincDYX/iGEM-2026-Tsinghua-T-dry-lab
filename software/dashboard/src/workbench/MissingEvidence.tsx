import { show } from "../contracts/resultAdapters";

const stageGuidance: Record<
  string,
  { source: string; condition: string; next: string }
> = {
  M1: {
    source:
      "Actual construct sequences / sequenced  DNA, genotype, localization context and original predictor outputs",
    condition:
      "Part/fusion identity, localization and forbidden restriction sites",
    next: "Attach original files/tool evidence for the same construct; retain unconfirmed markers.",
  },
  M2: {
    source:
      "Structure/reference files, residue mappings, SASA / geometry inputs and tool versions",
    condition:
      "The construct and sequence must match M1; confidence checks still apply",
    next: "Resolve upstream omissions, then attach structure evidence of the same identity.",
  },
  M3: {
    source:
      "Protein abundance / volume, recruitment sites, Kd, enzyme distribution, phase volume and density sources",
    condition:
      "Concentration units, site-count basis, temperature  / pH / condition compatibility",
    next: "Add provenance/condition-bound parameter records; do not substitute default concentrations or  K=1  as evidence.",
  },
  M4: {
    source:
      "Compatible kinetics, available enzyme  / phase activity, Kp, transport and boundary evidence",
    condition:
      "Host, assay、pH, temperature, condition ID, detection  / expression mode, feed and steady-state applicability",
    next: "Add compatible records for each reaction and review; never borrow missing parameters from another reaction.",
  },
  M5: {
    source:
      "WetLabResult original measurements, identities, units, times, replicates and  QC",
    condition:
      "Match construct/conditions; keep fit candidates separate from approved parameters",
    next: "Import real measurements and inspect  QC; after parameter approval, create and review an iteration.",
  },
};
export function MissingEvidence({
  module,
  missing,
  status,
}: {
  module: string;
  missing: unknown;
  status: unknown;
}) {
  const items = Array.isArray(missing)
    ? missing.filter((item): item is string => typeof item === "string")
    : [];
  if (!items.length && status !== "insufficient_data") return null;
  const guidance = stageGuidance[module];
  return (
    <section
      className="missing-evidence"
      aria-label={`${module} Missing evidence and next steps`}
    >
      <h3>{module} · Required evidence is missing</h3>
      <p>
        These codes come from backend gates; completion or an empty list does
        not approve evidence.
      </p>
      {items.length ? (
        <ul>
          {items.map((item, index) => (
            <li key={index}>
              <code>{item}</code>
            </li>
          ))}
        </ul>
      ) : (
        <p>
          No itemized list for this candidate; inspect original warning /
          upstream diagnostics.
        </p>
      )}
      <dl>
        <dt>Required source type</dt>
        <dd>{guidance?.source ?? "Original stage evidence"}</dd>
        <dt>Conditions to check</dt>
        <dd>{guidance?.condition ?? "Original claim scope"}</dd>
        <dt>Next steps</dt>
        <dd>
          {guidance?.next ??
            "Attach evidence and review again; no automatic values."}
        </dd>
      </dl>
      <p>Original status: {show(status)}</p>
    </section>
  );
}
