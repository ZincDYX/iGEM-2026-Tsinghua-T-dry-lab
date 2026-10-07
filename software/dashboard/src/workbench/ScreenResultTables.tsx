import { show } from "../contracts/resultAdapters";

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
            <th>Recorded engineering priority score</th>
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
              <td>{show(row.engineering_priority_score)}</td>
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

export function M2Metrics({ record }: { record: Record<string, unknown> }) {
  const fields = [
    ["core_ca_rmsd_angstrom", "Core  Cα RMSD (Å)"],
    ["pocket_rmsd_angstrom", "Pocket  RMSD (Å)"],
    ["pocket_sasa_retention", "Pocket  SASA retention ratio"],
    [
      "tail_pocket_min_distance_angstrom",
      "Tail-to-pocket minimum distance (Å)",
    ],
    ["clash_count", "clash count"],
    ["clash_cutoff_angstrom", "Original  clash Truncation (Å)"],
    ["s_sh3", "SH3 site count"],
    ["s_pdz", "PDZ site count"],
    ["site_count_basis", "Site-count basis"],
    ["eta_acc_sh3", "SH3 accessibility factor"],
    ["eta_acc_pdz", "PDZ accessibility factor"],
    ["v_scaffold_nm3", "Scaffold volume (nm³)"],
    ["v_enzyme_nm3", "Enzyme volume (nm³)"],
  ];
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
          {fields.map(([key, label]) => (
            <tr key={key}>
              <td>{label}</td>
              <td>{show(record[key])}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>
        Missing metrics: {show(record.missing_metrics)} · Volume method:{" "}
        {show(record.volume_method)}
      </p>
    </>
  );
}
