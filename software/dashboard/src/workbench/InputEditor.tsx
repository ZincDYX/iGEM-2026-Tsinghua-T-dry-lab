import { useEffect, useRef, useState } from "react";
import type {
  ProjectView,
  ImportView,
  ScientificPreviewView,
  ScientificPrecheckView,
} from "../contracts/generated";
import * as client from "./client";
import { LazyJson } from "../contracts/LazyJson";
import { PrecheckPanel, type InputIssue } from "./PrecheckPanel";
import { UnifiedImport } from "./UnifiedImport";
import {ConstructObject,NewConstruct} from "./ScientificInputForms";
import { StructureAnnotationLinker } from "./StructureAnnotationLinker";
import {GenBankDesigns} from './GenBankDesigns';
import {
  mergeImportDraft,
} from "./importDraft";
import {ScientificSetup} from "./ScientificSetup";

export function InputEditor({
  project,
  persisted,
  busy,
  dirty,
  onChange,
  action,
  inputCheck,
  checkStale,
  onCheck,
  onLocate,
  onOpenResource,
  inputTarget,
  onPlanMethod,
  prepareImport,
  onImported,
}: {
  project: ProjectView;
  persisted: boolean;
  busy: boolean;
  dirty: boolean;
  onChange: (value: ProjectView) => void;
  action: (job: () => Promise<unknown>) => Promise<void>;
  inputCheck?: ScientificPrecheckView;
  checkStale: boolean;
  onCheck: () => void;
  onLocate: (issue: InputIssue) => void;
  onOpenResource: (fileId: string) => void;
  inputTarget?: InputIssue;
  onPlanMethod?: (method:'ps-v3-demo')=>void;
  prepareImport:()=>Promise<ProjectView|undefined>;
  onImported:(project:ProjectView)=>void;
}) {
  const [rename,setRename]=useState(false),[selectedSequence,setSelectedSequence]=useState<string>(),[selectedConstruct,setSelectedConstruct]=useState('');
  const [preview, setPreview] = useState<ImportView>();
  const [scientific, setScientific] = useState<ScientificPreviewView>();
  useEffect(() => {
    if (!inputTarget) return;
    if(inputTarget.construct_id){
      const inputs=project.scientific_project?.config.inputs;
      if(inputs?.constructs.some(c=>c.id===inputTarget.construct_id))setSelectedConstruct('definition:'+inputTarget.construct_id);
      else if(inputs?.construct_records.some(c=>c.construct_id===inputTarget.construct_id))setSelectedConstruct('record:'+inputTarget.construct_id);
    }
    const target = Array.from(
      document.querySelectorAll<HTMLElement>("[data-input-path]"),
    ).find((e) => e.dataset.inputPath === inputTarget.field_path);
    if (!target) return;
    for (let p = target.parentElement; p; p = p.parentElement)
      if (p instanceof HTMLDetailsElement) p.open = true;
    target.scrollIntoView({ block: "center" });
    target.focus({ preventScroll: true });
  }, [inputTarget,project.id]);
  const mounted = useRef(true);
  const epoch = useRef(0);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      ++epoch.current;
    };
  }, []);
  function change(value: ProjectView) {
    ++epoch.current;
    onChange(value);
  }
  const scope = project.scientific_project;
  return (
    <section aria-label="Project inputs and evidence">
      <header className="panel-heading">
        <h2>Inputs and evidence</h2>
      </header>
      <fieldset className="input-fields" disabled={busy}>
        <button onClick={()=>setRename(value=>!value)}>Rename project</button>
        {rename&&<label>Project name<input aria-label="Project name" value={project.name} onChange={e=>change({...project,name:e.target.value})}/></label>}
        <section id="input-evidence" aria-label="Biological data">
          <h2>Biological data</h2>
          <UnifiedImport project={project} persisted={persisted} busy={busy} dirty={dirty} action={action} prepare={prepareImport} onCommitted={onImported}/>
          <StructureAnnotationLinker project={project} disabled={busy||dirty} action={action} onPreview={setPreview}/>
          {preview&&<div><p>Reviewed annotation binding candidate; original source is retained.</p>
            <button disabled={busy} onClick={()=>{change(mergeImportDraft(project,preview,{}));setPreview(undefined);}}>Confirm annotation binding into draft</button>
            <button onClick={()=>setPreview(undefined)}>Discard annotation binding</button>
          </div>}
        <GenBankDesigns project={project} dirty={dirty} action={action}/>
        <h3>Input objects</h3>
        <table aria-label="Input objects"><thead><tr><th>Name</th><th>Type</th><th>Status</th></tr></thead><tbody>
          {[...new Map([...project.files,...(scope?.evidence_files??[])].map(file=>[file.id,file])).values()].map(file=>{
            const dataset=project.datasets.find(row=>row.file_id===file.id);
            return <tr key={file.id}><td><button disabled={dirty} onClick={()=>onOpenResource(file.id)}>{file.name}</button></td><td>{String(dataset?.kind??'Evidence')}</td><td>{dataset?.has_unresolved_inputs?'Needs input review':'Imported'}</td></tr>;})}
          {project.sequences.map(sequence=><tr key={sequence.id}><td><button onClick={()=>{setSelectedSequence(sequence.id);setSelectedConstruct('');}}>{sequence.id}</button></td><td>Protein · {sequence.role.replaceAll('_',' ')}</td><td>{sequence.sequence.length} aa · design input</td></tr>)}
          {scope?.config.inputs.constructs.map(c=><tr key={'definition:'+c.id}><td><button onClick={()=>{setSelectedConstruct('definition:'+c.id);setSelectedSequence(undefined);}}>{c.id}</button></td><td>Construct</td><td>{c.m1_review?'Reviewed declaration':'Needs review'}</td></tr>)}
          {scope?.config.inputs.construct_records.map(c=><tr key={'record:'+c.construct_id}><td><button onClick={()=>{setSelectedConstruct('record:'+c.construct_id);setSelectedSequence(undefined);}}>{c.construct_id}</button></td><td>Construct evidence</td><td>{c.review_status.replaceAll('_',' ')}</td></tr>)}
        </tbody></table>
        <ConstructObject project={project} selected={selectedConstruct} onChange={change}/>
        {project.sequences.filter(sequence=>sequence.id===selectedSequence).map(sequence=><section key={sequence.id} aria-label="Selected sequence"><h3>{sequence.id} · {sequence.sequence.length} aa</h3><p className="sequence-text">{sequence.sequence}</p>
          <label>Construct role<select aria-label={`M1 role for ${sequence.id}`} value={sequence.role} onChange={e=>change({...project,sequences:project.sequences.map(row=>row.id===sequence.id?{...row,role:e.target.value}:row)})}>
            <option value={sequence.role} hidden>{sequence.role.replaceAll('_',' ')}</option>{['idr','enzyme_ligand_linker','scaffold_linker','rigid_linker','full_fusion'].map(role=><option key={role} value={role}>{role.replaceAll('_',' ')}</option>)}
          </select></label></section>)}
        {project.datasets.some(row=>row.kind==="wetlab")&&<h3>Measurements and M5</h3>}
        {dirty && (
          <p>
            Save this draft before previewing the backend M5 binding, to
            preserve unsaved changes.
          </p>
        )}
        {project.datasets
          .filter((row) => row.kind === "wetlab")
          .map((row, i) => (
            <article key={i}>
              <p>
                {String(row.name)} · Import / QC does not imply approval of
                fitted parameters.
              </p>
              <LazyJson value={row} />
              {scope && typeof row.file_id === "string" && (
                <button
                  disabled={busy || dirty}
                  onClick={() => {
                    const fileId = row.file_id;
                    if (typeof fileId !== "string") return;
                    const stamp = epoch.current;
                    void action(async () => {
                      const value = await client.bindMeasurement(
                        project.id,
                        project.revision,
                        fileId,
                      );
                      if (mounted.current && stamp === epoch.current)
                        change(value.project);
                    });
                  }}
                >
                  Preview M5 measurement binding (save and review required)
                </button>
              )}
            </article>
          ))}
        <NewConstruct project={project} onChange={change}/>
        </section>
        <section aria-label="Analysis plan and configuration">
        {project.datasets.some(row=>row.kind==='synthetic_ps_v3')&&<section>
          <h3>Synthetic reference demonstration</h3>
          <p>Original M3/competitive amount-model kernels recompute canonical inputs. E3 remains blocked; there is no fermentation or ER advantage claim.</p>
          <button disabled={busy} onClick={()=>onPlanMethod?.('ps-v3-demo')}>Review synthetic demonstration workflow</button>
        </section>}
        <section id="input-conditions" className="input-section">
          <h2>Analysis plan &amp; configuration</h2>
          {!scope && (
            <ScientificSetup
              project={project}
              dirty={dirty}
              busy={busy}
              onPreview={setScientific}
            />
          )}
          {scientific && (
            <div>
              <p>
                Validated typed configuration, binding{" "}
                {scientific.scientific_project.evidence_files.length} original
                files; import does not approve evidence.
              </p>
              <p>M1 sequence screening · {scientific.scientific_project.sequence_index.count} protein records · real mode, no assumed inputs.</p>
              <button
                disabled={busy}
                onClick={() => {
                  change({
                    ...project,
                    scientific_project: scientific.scientific_project,
                  });
                  setScientific(undefined);
                }}
              >
                Confirm scientific inputs into draft
              </button>
            </div>
          )}
          {scope ? (
            <>
              <p>
                Execution mode: {scope.config.execution.mode} · Authoritative
                conditions are below. Ordinary project notes do not enter
                computation.
              </p>
              <div className="field-grid">
                {(["host", "strain", "assay_system"] as const).map((key) => (
                  <label key={key}>
                    {key}
                    <input
                      value={scope.config.experimental_context[key] ?? ""}
                      onChange={(e) =>
                        change({
                          ...project,
                          scientific_project: {
                            ...scope,
                            config: {
                              ...scope.config,
                              experimental_context: {
                                ...scope.config.experimental_context,
                                [key]: e.target.value || null,
                              },
                            },
                          },
                        })
                      }
                    />
                  </label>
                ))}
                {(["temperature_c", "pH"] as const).map((key) => (
                  <label key={key}>
                    {key}
                    <input
                      aria-label={key}
                      type="number"
                      step="any"
                      value={scope.config.experimental_context[key] ?? ""}
                      onChange={(e) =>
                        change({
                          ...project,
                          scientific_project: {
                            ...scope,
                            config: {
                              ...scope.config,
                              experimental_context: {
                                ...scope.config.experimental_context,
                                [key]:
                                  e.target.value === ""
                                    ? null
                                    : Number(e.target.value),
                              },
                            },
                          },
                        })
                      }
                    />
                  </label>
                ))}
              </div>
              <p>
                Network {scope.config.stages.m4_reaction.network_variant} · Unit{" "}
                {scope.config.stages.m4_reaction.unit_mode} · Missing values
                remain absent.
              </p>


            </>
          ) : (
            <p>
              Full scientific pipeline not attached; standalone sequence
              statistics are not a formal M1–M5 project.
            </p>
          )}
        </section>
        </section>
      </fieldset>
      <PrecheckPanel
        result={inputCheck}
        stale={checkStale}
        disabled={busy}
        onCheck={onCheck}
        onLocate={onLocate}
      />
    </section>
  );
}
