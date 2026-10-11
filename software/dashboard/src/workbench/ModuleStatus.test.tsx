import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import type { RunSummaryView, Workflow, ScientificPrecheckView } from '../contracts/generated';
import { WorkflowGraph } from './WorkflowGraph';
import { PlanPanel } from './PlanPanel';
import { inputCheckLabel } from './ModuleStatus';

afterEach(cleanup);
const workflow: Workflow = {id:'display', name:'Recorded state', description:'Software display fixture; no numerical calculation', version:'1', nodes:[
  {id:'demo', label:'Recorded scenarios', tool_id:'synthetic.ps_v3', inputs:{}, depends_on:[], map:null},
], execution_policy:{target_node_id:null, max_completed_stages:null, checkpoints_before:[], checkpoints_after:[], allowed_tools:['synthetic.ps_v3'], max_tool_calls:1, stop_after_seconds:null, memory_limit_mb:null}};
const run: RunSummaryView = {id:'r', name:'Recorded run', project_id:'p', status:'succeeded', snapshot_hash:'software-fixture',
  created_at:'fixture', updated_at:'fixture', control:null, heartbeat:null, state_version:1, event_cursor:0, project_revision:1,
  workflow, tools:{}, artifacts:[], scientific_assessment:{experimental_validation:'not_established'}, nodes:[{
    id:'demo', parent_id:null, status:'succeeded', attempts:1, tool_id:'synthetic.ps_v3', label:'Recorded scenarios',
    scientific_summary:{module:'synthetic_m3_m4', record_count:5, status_counts:{recorded_synthetic_scenarios:4,blocked_E3:1},
      numerically_solved_count:4, evidence_ready_count:0, missing_input_count:3, claim_scope:'Synthetic reference only; not formal prediction'},
  }]};

it('Graph and List show backend numerical/evidence counts independently of completed jobs',()=>{
  render(<WorkflowGraph workflow={workflow} run={run} selected="demo" onSelect={vi.fn()}/>);
  const module=screen.getByRole('button',{name:'Module Recorded scenarios'});
  expect(module.textContent).toContain('Job: Job completed');
  expect(module.textContent).toContain('Numerical results: 4/5 solved');
  expect(module.textContent).toContain('Evidence: 0/5 ready');
  expect(module.textContent).toContain('Run experimental validation: not established');
  cleanup();
  render(<PlanPanel workflow={workflow} run={run} selected="demo" onSelect={vi.fn()}/>);
  const row=screen.getByRole('button',{name:'Recorded scenarios'}).closest('tr')!;
  expect(within(row).getByText('Job completed')).toBeTruthy();
  expect(row.textContent).toContain('Numerical results: 4/5 solved');
  expect(row.textContent).toContain('Evidence: 0/5 ready');
  expect(row.textContent).toContain('Missing inputs: 3');
  expect(row.textContent).toContain('Synthetic reference only; not formal prediction');
});

it('a changed scientific binding with the same node identity cannot inherit the old run status',()=>{
  const edited=structuredClone(workflow);
  edited.nodes[0].inputs.package_file={kind:'project',path:['files',1,'path']};
  render(<WorkflowGraph workflow={edited} run={run} selected="demo" onSelect={vi.fn()}/>);
  const module=screen.getByRole('button',{name:'Module Recorded scenarios'});
  expect(module.textContent).toContain('Job: Not started');
  expect(module.textContent).toContain('Numerical results: Not assessed');
  expect(module.textContent).not.toContain('4/5 solved');
  cleanup();
  render(<PlanPanel workflow={edited} run={run} selected="demo" onSelect={vi.fn()}/>);
  expect(screen.queryByText('Job completed')).toBeNull();
  expect(screen.queryByText('Numerical results: 4/5 solved')).toBeNull();
});

it('no scientific record is Not assessed rather than a zero-valued or approved record',()=>{
  const unassessed={...run, nodes:[{...run.nodes[0],scientific_summary:null}]};
  render(<WorkflowGraph workflow={workflow} run={unassessed} selected="demo" onSelect={vi.fn()}/>);
  const module=screen.getByRole('button',{name:'Module Recorded scenarios'});
  expect(module.textContent).toContain('Job: Job completed');
  expect(module.textContent).toContain('Evidence: Not assessed');
  expect(module.textContent).not.toContain('0/0');
});

it('input omissions for a different project or saved revision are not attached to a run',()=>{
  const check: ScientificPrecheckView={project_id:'p',project_revision:1,input_sha256:'software-fixture',missing:[{
    stage:'m3',code:'phi',field_path:'scientific_project.config.parameters',construct_id:null,condition_id:null,
    reason_codes:['not_declared'],source_kind:'reviewed_condition_compatible_parameter_record',
  }],scope:'declared_inputs_and_parameter_contracts_only',final_stage_gates_required:true,scientific_approval_granted:false,limitations:[]};
  expect(inputCheckLabel('project.m3',check,run)).toBe('1 known omissions · r1');
  expect(inputCheckLabel('project.m3',{...check,project_id:'other'},run)).toBe('Not checked for these inputs');
  expect(inputCheckLabel('project.m3',{...check,project_revision:2},run)).toBe('Not checked for these inputs');
  expect(inputCheckLabel('custom.project.m3',check,run)).toBe('Not checked for this tool');
});
