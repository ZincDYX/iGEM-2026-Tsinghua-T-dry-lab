import { show } from "../contracts/resultAdapters";
import { object } from "../contracts/validation";

export function M1Matrix({ records }: { records: Record<string, unknown>[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Candidate / Construct</th>
            <th>linker / IDR (distinct categories)</th>
            <th>Original rule verdict / Eligibility</th>
            <th>Original risk / Missing predictor evidence</th>
          </tr>
        </thead>
        <tbody>
          {records.map((row, index) => (
            <tr key={index}>
              <td>
                {show(row.candidate_id)} / {show(row.construct_id)}
              </td>
              <td>
                {show(row.linker_id)} / {show(row.idr_id)}
              </td>
              <td>
                {show(row.sequence_screen_verdict)} / {show(row.eligibility)}
              </td>
              <td>
                {show(row.screen_flags)} /{" "}
                {show(row.missing_predictor_evidence)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>
        Original backend order, no frontend ranking; current candidate page
        only.
      </p>
    </div>
  );
}

export function M2Metrics({ record, onAddData }: { record: Record<string, unknown>; onAddData?:()=>void }) {
  const fields = [
    ["core_ca_rmsd_angstrom", "Core  Cα RMSD (Å)"],
    ["pocket_rmsd_angstrom", "Pocket  RMSD (Å)"],
    ["pocket_sasa_retention", "Pocket  SASA retention ratio"],
    [
      "tail_pocket_min_distance_angstrom",
      "Tail-to-pocket minimum distance (Å)",
    ],
    ["clash_count", "clash count"],
    ["clash_cutoff_angstrom", "Heavy-atom clash cutoff (Å)"],
    ["s_sh3", "SH3 site count"],
    ["s_pdz", "PDZ site count"],
    ["site_count_basis", "Site-count basis"],
    ["eta_acc_sh3", "SH3 accessibility factor"],
    ["eta_acc_pdz", "PDZ accessibility factor"],
    ["v_scaffold_nm3", "Scaffold volume (nm³)"],
    ["v_enzyme_nm3", "Enzyme volume (nm³)"],
  ];
  const computed = fields.filter(([key])=>typeof record[key] === 'number' || typeof record[key] === 'string');
  if (!fields.some(([key])=>typeof record[key]==='number')) return <section aria-label="M2 needs structure">
    <h3>Structure calculation blocked</h3>
    <p>{show(record.status)}: {show(record.missing_inputs)}</p>
    {typeof record.reference_structure_id === 'string' && <p>Reference structure: {show(record.reference_structure_id)}. A reference does not replace a predicted fusion structure.</p>}
    <p>Next: add the required fusion structure and its confidence / residue mapping evidence in Inputs.</p>{onAddData&&<button onClick={onAddData}>Add data</button>}
  </section>;
  return (
    <>
      <p>Reference structure: {show(record.reference_structure_id)}</p>
      <p>
        Structure source {show(record.structure_source_tool)} /{" "}
        {show(record.structure_source_tool_version)} · Negative screen{" "}
        {show(record.screen_verdict)} · Confidence gate{" "}
        {show(record.confidence_gate)}
      </p>
      <table>
        <thead>
          <tr>
            <th>Original definition / Unit</th>
            <th>Original backend value</th>
          </tr>
        </thead>
        <tbody>
          {computed.map(([key, label]) => (
            <tr key={key}>
              <td>{label}</td>
              <td>{show(record[key])}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {Array.isArray(record.missing_metrics) && record.missing_metrics.length>0 && <p>Missing metrics: {show(record.missing_metrics)}</p>}
      {Array.isArray(record.region_observations) &&
        record.region_observations.filter(object).map((model, index) => (
          <section key={index}>
            <h3>
              Predicted region observations · model {show(model.model_rank)}
            </h3>
            <p>
              Diagnostic only. Isolated SASA uses the same model conformation,
              not an experimental free peptide. No burial verdict or M2
              acceptance is inferred.
            </p>
            <table>
              <thead>
                <tr>
                  <th>Region</th>
                  <th>pLDDT mean</th>
                  <th>Confidence</th>
                  <th>Context SASA (Å²)</th>
                  <th>SASA retention</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(model.regions) &&
                  model.regions.filter(object).map((region) => (
                    <tr key={String(region.name)}>
                      <td>{show(region.name)}</td>
                      <td>{show(region.mean_plddt)}</td>
                      <td>{show(region.confidence_gate)}</td>
                      <td>{show(region.context_sasa_angstrom2)}</td>
                      <td>{show(region.sasa_retention)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
            <p>
              Low-confidence/flexible ligand and linker geometry is
              reference-only.
            </p>
            <table>
              <thead>
                <tr>
                  <th>Region pair</th>
                  <th>Actual interdomain PAE (Å)</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(model.interdomain_pae) &&
                  model.interdomain_pae.filter(object).map((pair, i) => (
                    <tr key={i}>
                      <td>
                        {show(pair.first)} ↔ {show(pair.second)}
                      </td>
                      <td>{show(pair.mean_interdomain_pae_angstrom)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </section>
        ))}
    </>
  );
}
