import { fireEvent, render, screen, waitFor, cleanup } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { useState } from 'react';
import type { WorkflowDocument, Workflow } from '../contracts/generated';
import { WorkflowWorkspace } from './WorkflowWorkspace';
import { defaultPositions } from './WorkflowGraph';

vi.mock('./client', () => ({workflowDocuments: vi.fn(), workflowDocument: vi.fn(), saveWorkflowDocument: vi.fn()}));
import * as client from './client';
afterEach(() => {cleanup(); vi.resetAllMocks();});
const workflow: Workflow = {id:'fixture', name:'Software graph', description:'No science is executed', version:'1', nodes:[
  {id:'a', label:'Input inventory', tool_id:'workflow.gather', inputs:{results:{kind:'literal', value:[]}}, depends_on:[], map:null},
  {id:'b', label:'Left branch', tool_id:'workflow.gather', inputs:{results:{kind:'node', node_id:'a', path:['results']}}, depends_on:[], map:null},
  {id:'c', label:'Right branch', tool_id:'workflow.gather', inputs:{results:{kind:'node', node_id:'a', path:['results']}}, depends_on:[], map:null},
], execution_policy:{target_node_id:null, max_completed_stages:null, checkpoints_before:[], checkpoints_after:[], allowed_tools:['workflow.gather'], max_tool_calls:10, stop_after_seconds:null, memory_limit_mb:null}};
function document(): WorkflowDocument {return {id:'review', project_id:'p', project_revision:1, revision:1, semantic_revision:1, layout_revision:1, workflow, layout:{}, selected_node_id:'a', view:'graph'};}
function Harness({review=vi.fn()}:{review?: (workflow:Workflow)=>Promise<void>}) {
  const [value, setValue] = useState<WorkflowDocument>();
  const [selected,setSelected]=useState('a');
  return <WorkflowWorkspace projectId="p" projectRevision={1} seedId="review" seed={workflow} document={value}
    selected={selected} onSelect={setSelected} onDocument={setValue} onReview={review} busy={false} frozen={false}/>;
}
it('shows actual fan-out edges and Graph/List share persisted selection without changing nodes',async()=>{
  vi.mocked(client.workflowDocuments).mockResolvedValue([document()]);
  vi.mocked(client.saveWorkflowDocument).mockImplementation(async (_p,_id,value) => ({...document(), ...value, revision:2, layout_revision:2}));
  const view=render(<Harness/>);
  await waitFor(()=>expect((screen.getByRole('button',{name:'Graph'}) as HTMLButtonElement).disabled).toBe(false));
  expect(view.container.querySelectorAll('path[data-from="a"]')).toHaveLength(2);
  fireEvent.click(screen.getByRole('button',{name:'Module Right branch'}));
  await waitFor(()=>expect(client.saveWorkflowDocument).toHaveBeenCalledWith('p','review',expect.objectContaining({selected_node_id:'c'}),1,1));
  fireEvent.click(screen.getByRole('button',{name:'List'}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'Right branch'}).getAttribute('aria-pressed')).toBe('true'));
  expect(screen.getByRole('button',{name:'Left branch'}).getAttribute('aria-pressed')).toBe('false');
  const saved=vi.mocked(client.saveWorkflowDocument).mock.calls.at(-1)![2];
  expect(saved.workflow).toBeUndefined(); // Layout-only request does not resend the DAG.
});
it('keyboard movement saves layout, while rejected deletion keeps all nodes and explains affected modules',async()=>{
  vi.mocked(client.workflowDocuments).mockResolvedValue([document()]);
  vi.mocked(client.saveWorkflowDocument).mockImplementationOnce(async (_p,_id,value)=>({...document(),...value,revision:2,layout_revision:2}))
    .mockRejectedValueOnce(new Error('A remaining module still refers to a removed upstream module.'));
  render(<Harness/>);
  await waitFor(()=>expect((screen.getByRole('button',{name:'Graph'}) as HTMLButtonElement).disabled).toBe(false));
  fireEvent.keyDown(screen.getByRole('button',{name:'Module Input inventory'}),{key:'ArrowRight'});
  await waitFor(()=>expect(client.saveWorkflowDocument).toHaveBeenCalledWith('p','review',expect.objectContaining({layout:{a:{x:34,y:24}}}),1,1));
  await waitFor(()=>expect((screen.getByRole('button',{name:'Delete selected module'}) as HTMLButtonElement).disabled).toBe(false));
  expect(screen.getByText(/Removing it affects:/).textContent).toContain('Left branch, Right branch');
  fireEvent.click(screen.getByRole('button',{name:'Delete selected module'}));
  await waitFor(()=>expect(screen.getByRole('alert').textContent).toContain('removed upstream'));
  expect(screen.getByRole('button',{name:'Module Input inventory'})).toBeTruthy();
  expect(screen.getByRole('button',{name:'Module Left branch'})).toBeTruthy();
});
it('fan-out default layout follows dependencies, not source list order',()=>{
  const shuffled={...workflow,nodes:[workflow.nodes[2],workflow.nodes[0],workflow.nodes[1]] as Workflow['nodes']};
  const positions=defaultPositions(shuffled);
  expect(positions.a.x).toBe(24);
  expect(positions.b.x).toBe(284); expect(positions.c.x).toBe(284);
  expect(positions.b.y).not.toBe(positions.c.y);
});
it('arranging modules saves only layout, never the scientific definition or its revision',async()=>{
  vi.mocked(client.workflowDocuments).mockResolvedValue([document()]);
  vi.mocked(client.saveWorkflowDocument).mockImplementation(async (_p,_id,value)=>({...document(),...value,revision:2,layout_revision:2}));
  render(<Harness/>);
  await waitFor(()=>expect((screen.getByRole('button',{name:'Arrange modules'}) as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(screen.getByRole('button',{name:'Arrange modules'}));
  await waitFor(()=>expect(client.saveWorkflowDocument).toHaveBeenCalled());
  const request=vi.mocked(client.saveWorkflowDocument).mock.calls.at(-1)![2];
  expect(request.workflow).toBeUndefined();
  expect(request.layout).toEqual({a:{x:24,y:24},b:{x:284,y:24},c:{x:284,y:264}});
});
it('saved workflow labels advance after a semantic save and reopening fetches the latest server definition',async()=>{
  vi.mocked(client.workflowDocuments).mockResolvedValue([{...document(),selected_node_id:'c'}]);
  const changed={...document(),revision:2,semantic_revision:2,workflow:{...workflow,nodes:workflow.nodes.slice(0,2) as Workflow['nodes']}};
  vi.mocked(client.saveWorkflowDocument).mockResolvedValue(changed);
  const latest={...changed,revision:3,semantic_revision:3,workflow:{...changed.workflow,name:'Newer server definition'}};
  vi.mocked(client.workflowDocument).mockResolvedValue(latest);
  render(<Harness/>);
  await waitFor(()=>expect((screen.getByRole('button',{name:'Delete selected module'}) as HTMLButtonElement).disabled).toBe(false));
  expect(screen.getByText(/Selected module:/).textContent).toContain('Right branch');
  fireEvent.click(screen.getByRole('button',{name:'Delete selected module'}));
  await screen.findByRole('option',{name:'Software graph (revision 2)'});
  fireEvent.change(screen.getByLabelText('Open saved workflow'),{target:{value:'review'}});
  await screen.findByRole('heading',{name:'Newer server definition'});
  expect(client.workflowDocument).toHaveBeenCalledWith('p','review');
  expect(screen.getByRole('option',{name:'Newer server definition (revision 3)'})).toBeTruthy();
  expect(screen.queryByRole('button',{name:'Module Right branch'})).toBeNull();
});
it('a delayed reopen cannot overwrite a newer policy save for the same document',async()=>{
  vi.mocked(client.workflowDocuments).mockResolvedValue([document()]);
  let resolve!: (value:WorkflowDocument)=>void;
  vi.mocked(client.workflowDocument).mockImplementation(()=>new Promise(done=>{resolve=done;}));
  const latest={...document(),revision:3,semantic_revision:2,workflow:{...workflow,execution_policy:{...workflow.execution_policy,max_tool_calls:99}}};
  const accepted=vi.fn();
  function ConcurrentParent() {
    const [value,setValue]=useState(document());
    return <><button onClick={()=>setValue(latest)}>Policy save completed</button>
      <WorkflowWorkspace projectId="p" projectRevision={1} seedId="review" seed={workflow} document={value} selected="a"
        onSelect={vi.fn()} onDocument={doc=>{accepted(doc);setValue(doc);}} onReview={vi.fn()} busy={false} frozen={false}/></>;
  }
  render(<ConcurrentParent/>);
  await screen.findByRole('option',{name:'Software graph (revision 1)'});
  fireEvent.change(screen.getByLabelText('Open saved workflow'),{target:{value:'review'}});
  await waitFor(()=>expect(client.workflowDocument).toHaveBeenCalled());
  fireEvent.click(screen.getByRole('button',{name:'Policy save completed'}));
  resolve(document());
  await waitFor(()=>expect(accepted).toHaveBeenCalledWith(latest));
  expect(screen.getByText('Saved revision 2')).toBeTruthy();
});
it('reopening the Workflow tab adopts the newer server revision instead of its retained old document',async()=>{
  const latest={...document(),revision:2,semantic_revision:2,workflow:{...workflow,name:'Externally revised workflow'}};
  vi.mocked(client.workflowDocuments).mockResolvedValue([latest]);
  const onDocument=vi.fn();
  render(<WorkflowWorkspace projectId="p" projectRevision={1} seedId="review" seed={workflow} document={document()} selected="a"
    onSelect={vi.fn()} onDocument={onDocument} onReview={vi.fn()} busy={false} frozen={false}/>);
  await waitFor(()=>expect(onDocument).toHaveBeenCalledWith(latest));
  expect(client.saveWorkflowDocument).not.toHaveBeenCalled();
});
it('frozen runs have Graph/List selection but no editing or document writes',()=>{
  render(<WorkflowWorkspace projectId="p" projectRevision={1} seedId="run" seed={workflow} selected="b"
    onSelect={vi.fn()} onDocument={vi.fn()} onReview={vi.fn()} busy={false} frozen={true}/>);
  fireEvent.click(screen.getByRole('button',{name:'List'}));
  expect(screen.getByRole('button',{name:'Left branch'}).getAttribute('aria-pressed')).toBe('true');
  expect(screen.queryByRole('button',{name:'Connect modules'})).toBeNull();
  expect(client.workflowDocuments).not.toHaveBeenCalled();
  expect(client.saveWorkflowDocument).not.toHaveBeenCalled();
});
