import {useState} from "react";
import type {NodePage} from "../contracts/generated";
import {LazyJson} from "../contracts/LazyJson";
import {sequenceOutput,show} from "../contracts/resultAdapters";

export function SequenceMapTable({value,onSelect}: {value: NonNullable<NodePage["sequence_map"]>; onSelect: (nodeId: string) => void}) {
  const [filter,setFilter] = useState("");
  const rows = value.rows.filter(row => (row.sequence_id??row.node_id).toLowerCase().includes(filter.toLowerCase()));
  return <section aria-label="Sequence metrics summary">
    <h2>Sequence metrics summary</h2>
    <p>Statistics, not a biological prediction. {value.total_count} registered children; page starts at {value.offset+1}.</p>
    <p>Frozen run {value.run_id} / snapshot {value.snapshot_hash}</p>
    <label>Filter this page<input aria-label="Filter sequence metrics" value={filter} onChange={event=>setFilter(event.target.value)}/></label>
    <table><thead><tr><th>Sequence / child</th><th>SHA-256</th><th>Job status / issue</th><th>Length</th><th>Molecular weight (Da)</th><th>Theoretical pI</th></tr></thead>
      <tbody>{rows.map(row=>{
        const metrics=sequenceOutput(row.metrics);
        return <tr key={row.node_id}><td><button onClick={()=>onSelect(row.node_id)}>{row.sequence_id??row.node_id}</button></td>
          <td><code>{row.sequence_sha256??"Not available"}</code></td><td>{row.status} / {row.issue??"Verified identity"}</td>
          <td>{show(metrics?.features.length)}</td><td>{show(metrics?.protparam.molecular_weight_da)}</td><td>{show(metrics?.protparam.theoretical_pi)}</td></tr>;
      })}</tbody></table>
    {!value.rows.length&&<p>No registered children on this page. No values were generated.</p>}
    <LazyJson value={value.tool_identity} label="Tool identity"/>
    <LazyJson value={value} label="Data and provenance"/>
  </section>;
}
