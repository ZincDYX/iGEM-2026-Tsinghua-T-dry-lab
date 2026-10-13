import {useEffect, useRef, useState} from 'react';
import type {GenBankPage, ProjectView} from '../contracts/generated';
import {parsePublic} from '../contracts/validation';
import {downloadResource} from '../api';
import * as client from './client';

export function GenBankDesigns({project, dirty, action,fileId}: {
  project: ProjectView; dirty: boolean;fileId?:string;
  action: (job: () => Promise<unknown>) => Promise<void>;
}) {
  const designs = project.datasets.filter(item => item.kind === 'genbank_design'&&(!fileId||item.file_id===fileId))
    .map(item => parsePublic('GenBankDesign', item));
  const [page, setPage] = useState<GenBankPage>();
  const epoch = useRef(0);
  useEffect(() => {++epoch.current;setPage(undefined);return () => {++epoch.current}}, [project.id, project.revision]);
  if (!designs.length) return null;
  const open = (id: string, record = 0, features = 0, dna = 0) => {
    const stamp = ++epoch.current;
    void action(async () => {
      const result = await client.genbankDesign(project.id, id, record, features, dna);
      if (stamp === epoch.current) setPage(result);
    });
  };
  return <section className='input-section' aria-label='Annotated DNA designs'>
    <h3>Annotated DNA designs</h3>
    <p>Original DNA and annotations are retained. Export returns the unchanged source, not a redesigned or reverse-translated sequence. Save draft imports before browsing.</p>
    {designs.map(design => <div key={design.id}>
      <span>{design.name} · {design.records.length} nucleotide records · {design.records.reduce((n,r) => n+r.untranslated_cds_count,0)} CDS without source translation</span>
      <button disabled={dirty} onClick={() => open(design.id)}>View DNA and features</button>
      <button disabled={dirty} onClick={() => void action(() => downloadResource(`/files/${encodeURIComponent(design.file_id)}?project_id=${encodeURIComponent(project.id)}`, design.name))}>Export original GenBank</button>
    </div>)}
    {page && !dirty && <div>
      <h4>{page.record_id} · {page.nucleotide_count} nt · {page.molecule_type}</h4>
      <p>{page.description}</p>
      {designs.find(d=>d.id===page.design_id)!.records.length>1&&<label>Record <select aria-label='GenBank record' value={page.record_index} onChange={e => open(page.design_id, Number(e.target.value))}>
        {designs.find(d => d.id === page.design_id)?.records.map(r => <option key={r.record_index} value={r.record_index}>{r.record_id}</option>)}
      </select></label>}
      <details><summary>Source record annotations and database links</summary><dl>{Object.entries(page.annotations).map(([name,value])=><div key={name}><dt>{name.replaceAll('_',' ')}</dt><dd>{Array.isArray(value)?value.map(String).join('; '):String(value)}</dd></div>)}</dl><p>{page.dbxrefs.join('; ')}</p></details>
      {page.nucleotide_fragment === null ? <p>Source provides no bases for this segment. Annotations and original export remain available.</p> : <p>Nucleotides {page.nucleotide_start_1based}–{page.nucleotide_start_1based+page.nucleotide_fragment.length-1} (1-based)</p>}
      <pre className='dna-fragment'>{page.nucleotide_fragment}</pre>
      {page.nucleotide_count>2000&&<><button disabled={page.nucleotide_start_1based === 1} onClick={() => open(page.design_id,page.record_index,page.feature_offset,Math.max(0,page.nucleotide_start_1based-2001))}>Previous DNA segment</button>
      <button disabled={page.nucleotide_start_1based+2000-1 >= page.nucleotide_count} onClick={() => open(page.design_id,page.record_index,page.feature_offset,page.nucleotide_start_1based+1999)}>Next DNA segment</button></>}
      <p>Locations below use zero-based half-open coordinates; fuzzy positions, strand and compound locations are preserved. Original GenBank export retains its native notation.</p>
      <table><thead><tr><th>Feature</th><th>Location / direction</th><th>Protein link</th><th>Source qualifiers</th></tr></thead>
        <tbody>{page.features.map(f => <tr key={f.feature_index}><td>{f.type}</td><td>{f.location ?? 'Not specified'}</td><td>{f.linked_sequence_id ?? 'Not linked'}<br/>{f.translation_status.replaceAll('_',' ')}</td><td><details><summary>Annotations</summary><dl>{Object.entries(f.qualifiers).map(([name,values])=><div key={name}><dt>{name.replaceAll('_',' ')}</dt><dd>{values.join('; ')}</dd></div>)}</dl></details></td></tr>)}</tbody>
      </table>
      {page.feature_total>100&&<><button disabled={page.feature_offset === 0} onClick={() => open(page.design_id,page.record_index,Math.max(0,page.feature_offset-100),page.nucleotide_start_1based-1)}>Previous features</button>
      <button disabled={page.feature_offset+page.features.length >= page.feature_total} onClick={() => open(page.design_id,page.record_index,page.feature_offset+100,page.nucleotide_start_1based-1)}>Next features</button></>}
    </div>}
  </section>;
}
